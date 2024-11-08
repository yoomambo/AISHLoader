from Ender3 import Ender3
from ArduinoHardware import ArduinoHardware
from StateTracker import StateTracker
import time
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)


class AISHLoader(StateTracker):
    
    def __init__(self, PORT_ENDER, PORT_ARDUINO):
        super().__init__()
        # State variable to keep track of whether movement is allowed or not, 
        # do not move when sample buffer is ejected
        self.ALLOW_MOVEMENT = True      # Movement is allowed on initialization

        logging.info(f"AISHLoader - Connecting to Ender3 on port: {PORT_ENDER}")
        self.ender3 = Ender3(PORT_ENDER)
        logging.info(f"AISHLoader - Connecting to Arduino on port: {PORT_ARDUINO}")
        self.arduino = ArduinoHardware(PORT_ARDUINO)

        # State variable to keep track of whether a sample is loaded or not
        self.SAMPLE_LOADED = None     
        


    def command(self, sample_num, xrd_params):
        """
        Executes a command to load a sample, run XRD, and unload the sample.
        Args:
            sample_num (int): The number of the sample to be loaded.
            xrd_params (dict): Parameters for the XRD process.
        Raises:
            Exception: If movement is not allowed (self.ALLOW_MOVEMENT is False).
        """
        if self.ALLOW_MOVEMENT == False:
            raise Exception('StateError: Movement is not allowed')
        
        self._track_state("COMMAND")

        # Load sample
        self.load_sample(sample_num)

        # Run XRD
        print("Running XRD")

        # Unload sample
        self.unload_sample()

    def get_state(self):
        return {
            'sample_loaded': self.SAMPLE_LOADED,
            'allow_movement': self.ALLOW_MOVEMENT,

            'ender3': self.ender3.get_state(),
            'stage': self.arduino.linear_rail.get_state(),
            'gripper': self.arduino.gripper.get_state(),
        }

    def home_all(self):
        """
        Homes the linear rail and initializes the homing process for the Ender 3 printer.
        This method performs the following steps:
        1. Checks if movement is allowed. If not, raises a StateError.
        2. Tracks the state as "HOMING".
        3. Releases the gripper using the Arduino.
        4. Initiates the homing process for the Ender 3 printer.
        5. Attempts to home the linear rail up to a maximum number of attempts.
           - If homing fails, prompts the user to retry.
           - If the user chooses not to retry or the maximum number of attempts is reached, raises an Exception.
           - If homing is successful, prints a success message.
        Raises:
            Exception: If movement is not allowed.
            Exception: If the user stops the process.
            Exception: If the maximum number of homing attempts is reached.
        """
        if self.ALLOW_MOVEMENT == False:
            raise Exception('StateError: Movement is not allowed')
        
        self._track_state("HOMING")

        self.arduino.gripper.open()
        self.ender3.init_homing()

        result = self.arduino.linear_rail.home()
        print(result)
        max_attempts = 3
        attempt = 1
        while result == False and attempt <= max_attempts:
            user_input = input(f"Homing failed (attempt {attempt} out of {max_attempts}). Do you want to try again? (y/n): ")
            if user_input.lower() != 'y':
                raise Exception("User stopped the process.")
            attempt += 1

        if attempt > max_attempts:
            raise Exception("Max attempts reached. Homing failed.")
        
        print("Homing successful")


    def load_sample(self, sample_num):
        """
        Loads a sample onto the sample stage using the Ender3 and an Arduino-controlled gripper.
        Parameters:
        sample_num (int): The identifier of the sample to be loaded.
        Raises:
        Exception: If movement is not allowed or if a sample is already loaded.

        Updates:
        self.SAMPLE_LOADED: Sets to the sample_num of the loaded sample.
        """
        if self.ALLOW_MOVEMENT == False:
            raise Exception('StateError: Movement is not allowed')
        
        self._track_state("LOAD_SAMPLE")

        # Check state to see if sample is loaded already
        if self.SAMPLE_LOADED is not None:
            raise Exception('StateError: Sample already loaded')
            return
        
        # Execute the procedure to load a sample
        #(1) Move 3D printer to sample in sample buffer
        self.ender3.move_to_sample(sample_num)

        #(2) Grab Sample with Gripper
        self.arduino.gripper.close()

        #(3) Move 3D printer to sample stage
        self.ender3.move_to_stage()

        #(4) Release sample with Gripper
        self.arduino.gripper.open()

        #(5) Return 3D printer to home, elevate sample stage into furnace
        self.ender3.move_to_rest()
        # time.sleep(5)

        #(6) Move stage up into furnace
        self.arduino.linear_rail.move_up()

        self.SAMPLE_LOADED = sample_num
    
    def unload_sample(self):
        """
        Unloads a sample from the furnace and returns it to its original storage position.

        Raises:
            Exception: If movement is not allowed (self.ALLOW_MOVEMENT is False).
            Exception: If no sample is loaded (self.SAMPLE_LOADED is None).
        """
        if self.ALLOW_MOVEMENT == False:
            raise Exception('StateError: Movement is not allowed')

        self._track_state("UNLOAD_SAMPLE")

        # Check state to see if sample is loaded already
        if self.SAMPLE_LOADED is None:
            raise Exception('StateError: No Sample loaded')
        
        #(1) Remove sample stage from furnace
        self.arduino.linear_rail.move_down()
        # time.sleep(5)

        #(2) Move 3D printer to stage
        self.ender3.move_to_stage()

        #(3) Grab Sample with Gripper
        self.arduino.gripper.close()
        self.ender3.move_to_rest()

        #(4) Move 3D printer to Sample position (where it was originally stored)
        self.ender3.move_to_sample(self.SAMPLE_LOADED)

        #(5) Release sample with Gripper
        self.arduino.gripper.open()

        #(6) Return 3D printer to rest position
        self.ender3.move_to_rest()
        self.SAMPLE_LOADED = None

    def change_samples(self, is_buffer_ejected):
        """
        Change the state of the sample buffer.

        This method handles the ejection or loading of the sample buffer based on the 
        provided flag. If the samples are to be ejected, it updates the state, disables 
        movement, and moves the ender3 to the rest and eject bed positions. 
        
        If the buffer is to be loaded, it updates the state, enables movement, 
        and moves the ender3 to the rest position.

        Args:
            is_buffer_ejected (bool): A flag indicating whether the buffer should be 
                                      ejected (True) or loaded (False).
        """
        #Eject the sample buffer
        if is_buffer_ejected:
            self._track_state("EJECT_BUFFER")
            self.ALLOW_MOVEMENT = False
            self.ender3.move_eject_bed()
        else:
            self._track_state("LOAD_BUFFER")
            self.ALLOW_MOVEMENT = True
            self.ender3.move_to_rest()
            
            