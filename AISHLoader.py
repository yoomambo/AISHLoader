from Ender3 import Ender3
from ArduinoHardware import ArduinoHardware

class AISHLoader:
    
    def __init__(self, PORT_ENDER, PORT_ARDUINO):
        self.ender3 = Ender3(PORT_ENDER)
        self.arduino = ArduinoHardware(PORT_ARDUINO)

        self.home()     # Home the system on initialization

        self.SAMPLE_LOADED = None     # State variable to keep track of whether a sample is loaded or not

    def home(self):
        self.arduino.gripper.release()
        self.ender3.init_homing()

        result = self.arduino.linear_rail.home()
        max_attempts = 3
        attempt = 1
        while result == False or attempt <= max_attempts:
            user_input = input(f"Homing failed (attempt {attempt} out of {max_attempts}). Do you want to try again? (y/n): ")
            if user_input.lower() != 'y':
                raise Exception("User stopped the process.")
            
            attempt += 1

        if attempt > max_attempts:
            raise Exception("Max attempts reached. Homing failed.")
        
        print("Homing successful")


    def load_sample(self, sample_num):
        # Check state to see if sample is loaded already
        if self.SAMPLE_LOADED is not None:
            raise Exception('StateError: Sample already loaded')
            return
        
        # Execute the procedure to load a sample
        #(1) Move 3D printer to sample in sample buffer
        self.ender3.move_to_sample(sample_num)

        #(2) Grab Sample with Gripper
        self.arduino.gripper.grab()

        #(3) Move 3D printer to sample stage
        self.ender3.move_to_stage()

        #(4) Release sample with Gripper
        self.arduino.gripper.release()

        #(5) Return 3D printer to home, elevate sample stage into furnace
        self.ender3.move_to_rest()
        time.sleep(1)

        #(6) Move stage up into furnace
        self.arduino.linear_rail.move_up()

        self.SAMPLE_LOADED = sample_num
    
    def unload_sample(self):
        # Check state to see if sample is loaded already
        if self.SAMPLE_LOADED is None:
            raise Exception('StateError: No Sample loaded')
        
        #(1) Remove sample stage from furnace
        self.arduino.linear_rail.move_down()
        time.sleep(1)

        #(2) Move 3D printer to stage
        self.ender3.move_to_stage()

        #(3) Grab Sample with Gripper
        self.arduino.gripper.grab()
        self.arduino.move_to_rest()

        #(4) Move 3D printer to Sample position (where it was originally stored)
        self.ender3.move_to_sample(self.ender3.SAMPLE_POS)

        #(5) Release sample with Gripper
        self.arduino.gripper.release()

        #(6) Return 3D printer to rest position
        self.ender3.move_to_rest()
        self.SAMPLE_LOADED = None