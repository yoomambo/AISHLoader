# Handles commmunication with the Arduino to control hardware
# Uses pyFirmata to communicate reliably
# Hardware components connected to Arduino:
# - Gripper: For grabbing the samples
# - Linear Rail: For raising the sample stage

import pyfirmata
import time

# Define pyfirmata commands
GRIPPER_OPEN = 0x10
GRIPPER_CLOSE = 0x11
GRIPPER_STATE = 0x12
GRIPPER_STATE_ANGLE = 0x14


class ArduinoHardware:
    def __init__(self, port) -> None:
        # Create a new board instance at the specified port
        self.board = pyfirmata.Arduino(port)
        # Start iterator to avoid buffer overflow
        it = pyfirmata.util.Iterator(self.board)
        it.start()
        print("Arduino connected")

        self.gripper = Gripper(self.board)


class LinearRail:
    def __init__(self) -> None:
        pass
    
    def move_up(self):
        pass

    def move_down(self):
        pass

    def check_state(self):
        pass

class Gripper:
    def __init__(self, board) -> None:
        # Attach the callback functions to the appropriate Firmata events
        self.board = board
        self.board.add_cmd_handler(GRIPPER_STATE, self._gripper_state_callback)
        self.board.add_cmd_handler(GRIPPER_STATE_ANGLE, self._gripper_angle_callback)
        self._is_Grabbed_State = None;
        self._servo_angle = None;

    def _gripper_state_callback(self, *data):
        conv_data = []
        for d in range(0, len(data), 2):
            conv_data.append(data[d] + (data[d+1] << 7))
        # print("\tReceived SysEx message:", [d for d in data])
        # print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")
        self._is_Grabbed_State = bool(conv_data[0])

    def _gripper_angle_callback(self, *data):
        conv_data = []
        for d in range(0, len(data), 2):
            conv_data.append(data[d] + (data[d+1] << 7))
        # print("\tReceived SysEx message:", [d for d in data])
        # print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")
        self._servo_angle = (conv_data[0])
    
    def grab(self):
        self.board.send_sysex(GRIPPER_CLOSE, [])
        time.sleep(0.5)
    
    def release(self):
        self.board.send_sysex(GRIPPER_OPEN, [])
        time.sleep(0.5)
    
    def check_state(self):
        # TODO: Implement a timeout, stale checking
        self.board.send_sysex(GRIPPER_STATE, [])
        time.sleep(0.2) # Wait for response
        return self._is_Grabbed_State
    
    def check_angle(self):
        self.board.send_sysex(GRIPPER_STATE_ANGLE, [])
        time.sleep(0.2)
        return self._servo_angle

    