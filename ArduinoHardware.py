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

LINRAIL_UP = 0x20
LINRAIL_DOWN = 0x21
LINRAIL_COUNT = 0x22
LINRAIL_HOME = 0x23

TEST_ECHO = 0x01
TEST_RESPONSE = 0x02

class ArduinoHardware:
    def __init__(self, port) -> None:
        # Create a new board instance at the specified port
        self.board = pyfirmata.Arduino(port)


        # Start iterator to avoid buffer overflow
        it = pyfirmata.util.Iterator(self.board)
        it.start()
        print("Arduino connected")

        # Attach the callback functions to the test commands
        self.board.add_cmd_handler(TEST_RESPONSE, self._default_callback)
        self.board.add_cmd_handler(TEST_ECHO, self._default_callback)

        # Initialize the hardware components
        self.gripper = self.Gripper(self.board)
        self.linear_rail = self.LinearRail(self.board)

    # Default callback function for handling SysEx messages. Parses the data and converts it to a list of bytes
    def _default_callback(self, *data):
        conv_data, data = ArduinoHardware._unpack_sysex(*data)

        print("\tReceived SysEx message:", [d for d in data])
        print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")
    
    @staticmethod
    def _unpack_sysex(*data):
        print("unpacking....")
        conv_data = []
        for d in range(0, len(data), 2):
            conv_data.append(data[d] + (data[d+1] << 7))
        return conv_data, data
    


    class LinearRail:
        def __init__(self, board) -> None:
            # Attach the callback functions to the appropriate Firmata events
            self.board = board

            self.board.add_cmd_handler(LINRAIL_UP, self._linrail_move_callback)
            self.board.add_cmd_handler(LINRAIL_DOWN, self._linrail_move_callback)
            self.board.add_cmd_handler(LINRAIL_COUNT, self._linrail_count_callback)
            self.board.add_cmd_handler(LINRAIL_HOME, self._linrail_home_callback)
            
            self._linrail_count = None
            self._linrail_home_success = None
            self._linrail_move_done = None
        
        def move_up(self):
            self._linrail_move_done = None
            self.board.send_sysex(LINRAIL_UP, [])       # Send the move up command
            
            # Wait for the move to complete, or timeout after 5 seconds
            start_time = time.time()
            while not self._linrail_move_done and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if self._linrail_move_done is None:
                raise("Communication Timeout: Linear rail move up failed")
            return self._linrail_move_done            

        def move_down(self):
            self._linrail_move_done = None
            self.board.send_sysex(LINRAIL_DOWN, [])     # Send the move down command

            # Wait for the move to complete, or timeout after 5 seconds            
            start_time = time.time()
            while not self._linrail_move_done and time.time() - start_time < 5:
                time.sleep(0.1)
            
            if self._linrail_move_done is None:
                raise("Communication Timeout: Linear rail move down failed")
            return self._linrail_move_done

        def home(self):
            self._linrail_home_success = None
            self.board.send_sysex(LINRAIL_HOME, [])

            # Wait for the homing to complete, or timeout after 10 seconds
            start_time = time.time()
            while self._linrail_home_success is None and time.time() - start_time < 10:
                time.sleep(0.1)
            
            if self._linrail_home_success is None:
                raise("Communication Timeout: Linear rail homing failed")
            return self._linrail_home_success

        def check_count(self):
            self._linrail_count = None
            self.board.send_sysex(LINRAIL_COUNT, [])
            
            # Wait for the count to be received, or timeout after 2 seconds
            start_time = time.time()
            while self._linrail_count is None and time.time() - start_time < 2:
                time.sleep(0.1)
            
            if self._linrail_count is None:
                raise("Communication Timeout: Linear rail count failed")
            
            return self._linrail_count
        
        def _linrail_move_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)
            if conv_data[0] == 0xFF:
                self._linrail_move_done = True
            else:
                self._linrail_move_done = False
        
        def _linrail_count_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)

            print("Linear rail count")
            print("\tReceived SysEx message:", [d for d in data])
            print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")

            # The total count is a 16-bit value, so we need to combine the two bytes
            self._linrail_count = int.from_bytes(bytes([conv_data[0], conv_data[1]]), byteorder='big', signed=True)
        
        def _linrail_home_callback(self, *data):
            print("Linear rail homing")

            conv_data, data = ArduinoHardware._unpack_sysex(*data)

            print("\tReceived SysEx message:", [d for d in data])
            print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")
            
            if conv_data[0] == 0xFF:
                self._linrail_home_success = True
            else:
                self._linrail_home_success = False

    class Gripper:
        def __init__(self, board) -> None:
            # Attach the callback functions to the appropriate Firmata events
            self.board = board
            self.board.add_cmd_handler(GRIPPER_STATE, self._gripper_state_callback)
            self.board.add_cmd_handler(GRIPPER_STATE_ANGLE, self._gripper_angle_callback)
            self._is_Grabbed_State = None;
            self._servo_angle = None;
        
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