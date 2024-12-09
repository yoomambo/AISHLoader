import serial
import time
from StateTracker import StateTracker
import numpy as np
import re
from AISH_utils import CommunicationError, ErrorChecker

import logging

#Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)

STAGE_POSITION = (231, 0, 141)  #Position of the stage in Ender3 coordinates (only XZ matters, but insert Y=0)
STAGE_Z_OFFSET_POS = 149              #Offset to avoid collision with the stage
# List of sample positions (x,y,z) in Ender3 coordinates
pos_0 = np.array([39.1, 176, 3]) # Row 1, these are found center positions (have +/-0.3mm tolerance)
pos_4 = np.array([40.1, 17.4, 3])
pos_5 = np.array([79.65, 177.0, 12.0]) # Row 2, these are found center positions (have +/-0.3mm tolerance)
pos_9 = np.array([0,0,0])
SAMPLE_POSITIONS = np.append(np.linspace(pos_0, pos_4, num=5), np.linspace(pos_5, pos_9, num=5), axis=0)
print(SAMPLE_POSITIONS)

SAMPLE_MIN_Z = 30       #Minimum Z position to avoid collision with the samples

ENDER_LIMITS = [(0, 230), (0, 220), (0, 143)]
ENDER_MAX_SPEED = np.array([1000, 1000, 300])

class Ender3(StateTracker):

    def __init__(self, PORT = '/dev/tty.usbmodem1401'):
        super().__init__()      # Initialize the StateTracker class
        self.PORT = PORT

        try:
            self.serial = serial.Serial(PORT, 115200)
        except:
            raise Exception("Failed to connect to Ender 3")

        logging.info(f"Ender3 - Connected on port: {PORT}")
        self.serial.flushInput(); self.serial.flushOutput()

        # Set units to mm, set positioning to absolute mode
        self.serial.write(str.encode("G21 G90\r\n")) 
        
        self.current_position = np.array([0, 0, 0])
        self._update_current_position()     #Get the current position of the Ender3
        self.init_homing()

        # Set the callback function for the CommunicationErrorChecker
        ErrorChecker.set_get_state_callback(self.get_state)
        

    def move_to_sample(self, sample_num):
        """
        Moves the machine to the specified sample position.

        Parameters:
        sample_num (int): The index of the sample position to move to.
        """
        self._track_state(f"MOVE_SAMPLE_{sample_num}")
        sample_pos = SAMPLE_POSITIONS[sample_num]

        #Move to above the sample position first
        self._move_to(self.current_position[0]  , self.current_position[1]  , SAMPLE_MIN_Z, 1200) #Move only Z first
        self._move_to(sample_pos[0]             , sample_pos[1]             , SAMPLE_MIN_Z, 4000) #Move above the sample position

        #Now we can move down to the sample position and grab the sample
        self._move_to(*sample_pos, 1000)

    def move_to_stage(self):
        """
        Moves the device to the stage position in a three-step process to avoid collisions and enable sample pickup.
        This method uses predefined constants for the stage position and a Z-axis offset to ensure safe movements.

        There is a ~0.6mm x 0.6mm tolerance in XY for picking up the sample.

        Raises:
            Any exceptions raised by the _move_to or _track_state methods.
        """
        self._track_state("MOVE_STAGE")

        #First move Z to avoid collision with stage, also enables pickup
        self._move_to(self.current_position[0], self.current_position[1], STAGE_Z_OFFSET_POS, 3000)

        #Then move X to stage position
        self._move_to(STAGE_POSITION[0], self.current_position[1], STAGE_Z_OFFSET_POS, 3000)

        #Then move Z to stage position to place down the sample
        self._move_to(STAGE_POSITION[0], self.current_position[1], STAGE_POSITION[2], 1000)

    def move_to_rest(self):
        """
        Moves the machine to its rest position. This is intended to be used after 
        the sample is loaded and the XRD is running. Rest position is away from 
        the stage, with sample holder at the current sample

        This method performs the following steps:
        1. Moves the Z-axis up to avoid collision with the stage.
        2. Moves the X-axis backwards to position the gripper out of the way.

        The movement speeds are set to 1000 for the Z-axis and 4000 for the X-axis.

        Raises:
            Any exceptions raised by the _move_to method.
        """
        self._track_state("MOVE_REST")

        # Move Z back up to avoid collision with the stage
        self._move_to(self.current_position[0], self.current_position[1], STAGE_Z_OFFSET_POS, 1000)

        # Move X backwards, gripper out of the way of everything
        self._move_to(0, self.current_position[1], self.current_position[2], 4000)

    # Moves the bed to the eject position, for loading/unloading the samples
    def move_eject_bed(self):
        """
        Moves the bed to the eject position, for loading/unloading the samples

        This method updates the state to "MOVE_EJECT" and moves the bed to the 
        maximum Y position while keeping the current X and Z positions unchanged.
        """
        self._track_state("MOVE_EJECT")
        self._move_to(self.current_position[0]  , self.current_position[1]  , SAMPLE_MIN_Z)     #First move Z up to avoid collision with the bed
        self._move_to(0                         , self.current_position[1]  , SAMPLE_MIN_Z)     #Move bed to the eject position
        self._move_to(0                         , ENDER_LIMITS[1][1]         , SAMPLE_MIN_Z, 4000)     #Move bed to the eject position

    def move_to_home(self):
        """
        Moves the machine to its home position.
        """
        self._track_state("MOVE_HOME")

        #Move Z up to avoid collision with the bed
        self._move_to(self.current_position[0], self.current_position[1], SAMPLE_MIN_Z)

        #Now move bed out of the way
        self._move_to(0, self.current_position[1], self.current_position[2])
        self._move_to(0, 0, 0)

    def init_homing(self): 
        """
        Initiates the homing routine for the Ender3 3D printer.
        TODO:
        - Halt until the movement is complete.
        Returns:
            None
        """
        logging.info("Ender3 - Initiating homing routine")
        self._track_state("MOVE_HOME")

        # Update current_position (XYZ)
        self._update_current_position()
        #Move Z up to avoid collision with the bed
        self._move_to(self.current_position[0], self.current_position[1], self.current_position[2]+SAMPLE_MIN_Z)
        
        # (1) Gcode to move to HOME, do homing routine
        self.serial.write(str.encode("G28\r\n"))
        self._wait_for_response(60)

        # (2) Update current_position (XYZ)
        self._update_current_position()
        
        logging.info("Ender3 - Homing routine complete")
    
    @ErrorChecker.user_confirm_action()
    def _move_to(self, x, y, z, speed=2000):
        #Calculate the distance to move, time to set the timeout
        distances = np.array( [(x - self.current_position[0]), (y - self.current_position[1]), (z - self.current_position[2])] )
        MAX_TIMEOUT = max( np.abs(distances)/ENDER_MAX_SPEED *60 ) + 10
        # print(f"Distance: {distances}, Time: {MAX_TIMEOUT}")

        logging.debug(f"Ender3 - Starting move from {self.current_position} to {float(x), float(y), float(z)}")
        self.serial.write(str.encode(f"G01 X{x} Y{y} Z{z} F{speed}\r\n"))   # Gcode to move to XYZ
        #Wait for the move to complete
        self._wait_for_response(MAX_TIMEOUT)

        #Update the current position
        self.current_position = np.array([x, y, z], dtype=float)
        self._update_current_position()

        logging.debug(f"Ender3 - Moved to:  {float(x), float(y), float(z)}")

    @ErrorChecker.user_confirm_action()
    def _update_current_position(self):
        # Gcode to get current position
        self.serial.write(str.encode("M114\n"))
        time.sleep(0.1)
        
        response = self.serial.read_all().decode('utf-8').strip()

        # Parse the response and update the current position
        match = re.search(r"X:(\d+\.\d+) Y:(\d+\.\d+) Z:(\d+\.\d+)", response)

        if match:
            x, y, z = match.groups()
            measured_position = np.array([float(x), float(y), float(z)], dtype=float)

            if np.linalg.norm( measured_position - self.current_position ) > 0.001:
                logging.debug(f"Ender3 - Position updated from {self.current_position} to {measured_position}")

            self.current_position = measured_position
        else:
            raise CommunicationError("Ender3 - No response to update current position")

    def _wait_for_response(self, MAX_TIMEOUT=20):
        self.serial.write(str.encode("M400\n")) #Command to wait until movement is complete before moving to next command
        self.serial.write(str.encode("M114\n")) #Command to get current position, this will only return when the move command is complete

        #Keep checking the serial port every 0.5s until the move is complete and M114 returns the current position
        start_time = time.time()
        while time.time()-start_time < MAX_TIMEOUT:
            response = self.serial.read_all().decode('utf-8').strip()
            if "X" in response and "Y" in response and "Z" in response:
                return
            time.sleep(0.5)
        
        raise CommunicationError("Ender3 - Wait command timed out")