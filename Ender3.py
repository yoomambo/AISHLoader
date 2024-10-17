import serial
import time
from enum import Enum

NUM_SAMPLE_POSITIONS = 10

class Ender3:
    class SystemState(Enum):
        HOME = 1
        STAGE = 2
        SAMPLE = 3

    def __init__(self, PORT = '/dev/tty.usbmodem1401') -> None:
        self.PORT = PORT
        try:
            self.serial = serial.Serial(PORT, 115200)
        except:
            raise Exception("Failed to connect to Ender 3")
            return

        # Home all axes
        self.serial.write(str.encode("G28\r\n"))
        # Set units to mm, set positioning to absolute mode
        self.serial.write(str.encode("G21 G90\r\n")) 

        self.current_position = [0, 0, 0]
        self.state_history = []
        self._state = (self.SystemState.HOME, None)

    def move_to_sample(self, sample_num):
        # (1) Gcode to move to sample position
        # (2) Update current_position (XYZ)
        # (3) Update state to (SAMPLE, sample_num)
        # (4) Halt until movement is complete
        pass

    def move_to_sample_stage(self):
        # (1) Gcode to move to Stage position
        # (2) Update current_position (XYZ)
        # (3) Update state to (STAGE, None)
        # (4) Halt until movement is complete
        pass

    def move_to_home(self):
        # (1) Gcode to move to HOME, do homing routine
        self.serial.write(str.encode("G28\r\n"))

        # (2) Update current_position (XYZ)
        self.current_position = [0, 0, 0]

        # (3) Update state to (HOME, None)
        self.STATE = (self.SystemState.HOME, None)

        # (4) Halt until movement is complete
    
    def get_Ender_XYZ(self):
        pass

    #STATE is always a tuple of (SystemState, position), position is None for HOME, STAGE
    @property
    def STATE(self):
        if self._state[0] == self.SystemState.SAMPLE and self._state[1] is not None:
            return f"{self._state[0].name}_{self._state[1]}"
        else:
            return self._state[0].name

    @STATE.setter
    def STATE(self, new_state):
        #Check if the state is valid: first part is System State, second part is None, or position number in range
        if isinstance(new_state[0], self.SystemState):
            #Set the HOME, STAGE States
            if new_state[0] in [self.SystemState.HOME, self.SystemState.STAGE]:
                new_state = (new_state[0], None)
                self._state = new_state
            #Set the SAMPLE State
            elif new_state[0] == self.SystemState.SAMPLE and new_state[1] in range(NUM_SAMPLE_POSITIONS):
                self._state = new_state
            else:
                raise ValueError("Invalid state value")
            
            self._track_state(new_state)    #Add the new state to the history
        else:
            raise ValueError("Invalid state value")

    def _track_state(self, state):
        self.state_history.append(state)
        self.STATE = state

        #Limit history to 100 states
        if len(self.state_history) > 100:
            self.state_history.pop(0)