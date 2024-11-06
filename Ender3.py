import serial
import time

STAGE_POSITION = (200, 0, 50)  #Position of the stage in Ender3 coordinates (only XZ matters, but insert Y=0)
SAMPLE_POSITIONS =  [(12, y_pos, 10) for y_pos in [77, 107, 137, 167]]   #List of sample positions (x,y,z) in Ender3 coordinates, all Z should be the same

ENDER_LIMITS = {
    'X': (0, 220),
    'Y': (0, 220),
    'Z': (0, 250)
}

class Ender3:

    def __init__(self, PORT = '/dev/tty.usbmodem1401') -> None:
        self.PORT = PORT
        try:
            self.serial = serial.Serial(PORT, 115200)
        except:
            raise Exception("Failed to connect to Ender 3")
            return

        print("Ender3 connected on port: ", PORT)

        self.state_history = []

        # Set units to mm, set positioning to absolute mode
        self.serial.write(str.encode("G21 G90\r\n")) 
        
        self.init_homing()
        self.current_position = [0, 0, 0]


    def move_to_sample(self, sample_num):
        self._track_state(f"MOVE_SAMPLE_{sample_num}")
        sample_pos = SAMPLE_POSITIONS[sample_num]

        #Move to above the sample position first
        self._move_to(sample_pos[0], self.current_position[1], sample_pos[2]+15, 1200) #Hold Y constant

        #Move the sample stage to under the grabber
        self._move_to(sample_pos[0], sample_pos[1], sample_pos[2]+15, 4000)

        #Now we can move down to the sample position and grab the sample
        self._move_to(*sample_pos, 1000)

    def move_to_stage(self):
        self._track_state("MOVE_STAGE")
        stage_z_offset = 20

        #First move Z to avoid collision with stage, also enables pickup
        self._move_to(self.current_position[0], self.current_position[1], STAGE_POSITION[2]+stage_z_offset, 6000)

        #Then move X to stage position
        self._move_to(STAGE_POSITION[0], self.current_position[1], STAGE_POSITION[2]+stage_z_offset, 4000)

        #Then move Z to stage position to place down the sample
        self._move_to(STAGE_POSITION[0], self.current_position[1], STAGE_POSITION[2], 1000)

    #Rest position is away from the stage, with sample holder at the current sample.
    #This is intended to be used after the sample is loaded and the XRD is running
    def move_to_rest(self):
        self._track_state("MOVE_REST")
        # Move Z back up to avoid collision with the stage
        self._move_to(STAGE_POSITION[0], self.current_position[1], STAGE_POSITION[2]+stage_z_offset, 1000)

        # Move X backwards, gripper out of the way of everything
        self._move_to(0, self.current_position[1], self.current_position[2], 4000)

    # Moves the bed to the eject position, for loading/unloading the samples
    def move_eject_bed(self):
        self._track_state("MOVE_EJECT")
        self._move_to(self.current_position[0], ENDER_LIMITS.Y[1], self.current_position[2])

    def move_to_home(self):
        self._track_state("MOVE_HOME")

        #Move Y to 0 first to avoid collisions, then XZ to 0
        self._move_to(0, self.current_position[1], self.current_position[2])
        self._move_to(0, 0, 0)

    def init_homing(self): 
        print("ENDER3: Starting homing routine")
        self._track_state( "HOMING" )

        # (1) Gcode to move to HOME, do homing routine
        self.serial.write(str.encode("G28\r\n"))

        # (2) Update current_position (XYZ)
        self.current_position = [0, 0, 0]
        
        # TODO: (4) Halt until movement is complete
    
    def _move_to(self, x, y, z, speed=1200):
        #Calculate the distance to move, time
        distance = ((x - self.current_position[0])**2 + (y - self.current_position[1])**2 + (z - self.current_position[2])**2)**0.5
        time_to_move = distance / (speed/60)

        # Gcode to move to XYZ
        self.serial.write(str.encode(f"G01 X{x} Y{y} Z{z} F{speed}\r\n"))

        # Update current_position (XYZ)
        self.current_position = [x, y, z]

        # Halt until movement is complete
        time.sleep(time_to_move + 2)
        print("Movement complete")

    def get_state(self):
        return self.state_history[-1]

    def _track_state(self, state):
        self.state_history.append(state)

        #Limit history to 100 states
        if len(self.state_history) > 100:
            self.state_history.pop(0)