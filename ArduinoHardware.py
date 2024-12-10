# Handles commmunication with the Arduino to control hardware
# Uses pyFirmata to communicate reliably
# Hardware components connected to Arduino:
# - Gripper: For grabbing the samples
# - Linear Rail: For raising the sample stage

import pyfirmata
import time
from StateTracker import StateTracker
import logging
from AISH_utils import CommunicationError, ErrorChecker

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)

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
    def __init__(self, PORT) -> None:
        try:
            # Create a new board instance at the specified port
            self.board = pyfirmata.Arduino(PORT)

            # Start iterator to avoid buffer overflow
            it = pyfirmata.util.Iterator(self.board)
            it.start()
            logging.info(f"Arduino - Connected on port: {PORT}")
        except:
            raise Exception("Failed to connect to Arduino")
        
        # Attach the callback functions to the test commands
        self.board.add_cmd_handler(TEST_RESPONSE, self._default_callback)
        self.board.add_cmd_handler(TEST_ECHO, self._default_callback)

        # Initialize the hardware components
        self.gripper = self.Gripper(self.board)
        self.linear_rail = self.LinearRail(self.board)

        # Set the callback function for the CommunicationErrorChecker
        ErrorChecker.set_get_state_callback(self.get_state)

        self.gripper.open()  # Release the gripper on initialization
        self.linear_rail.home() # Home the linear rail on initialization

    def get_state(self):
        return {
            'gripper': self.gripper.get_state(),
            'linear_rail': self.linear_rail.get_state()
        }

    # Default callback function for handling SysEx messages. Parses the data and converts it to a list of bytes
    def _default_callback(self, *data):
        conv_data, data = ArduinoHardware._unpack_sysex(*data)

        logging.debug("\tTEST SYSEX - Received SysEx message:", [d for d in data])
        logging.debug(f"\tTEST SYSEX - Converted data: {[bin(d) for d in conv_data]} = {conv_data}")
    
    @staticmethod
    def _unpack_sysex(*data):
        conv_data = []
        for d in range(0, len(data), 2):
            conv_data.append(data[d] + (data[d+1] << 7))
        return conv_data, data
    

    class LinearRail(StateTracker):

        MOVE_TIMEOUT = 30
        HOME_TIMEOUT = 10
        CHECK_TIMEOUT = 1
        RAIL_STEPS_PER_REV = 400

        def __init__(self, board) -> None:
            super().__init__()      # Initialize the StateTracker class
            
            # Attach the callback functions to the appropriate Firmata events
            self.board = board

            self.board.add_cmd_handler(LINRAIL_UP, self._linrail_move_callback)
            self.board.add_cmd_handler(LINRAIL_DOWN, self._linrail_move_callback)
            self.board.add_cmd_handler(LINRAIL_COUNT, self._linrail_count_callback)
            self.board.add_cmd_handler(LINRAIL_HOME, self._linrail_home_callback)
            
            self._linrail_count = None              # Stores the count of the linear rail
            self._linrail_home_success = None       # Stores the success of the homing operation
            self._linrail_move_success = None       # Stores the success of the move operation

            # Set the callback function for the CommunicationErrorChecker
            ErrorChecker.set_get_state_callback(self.get_state)
        
        @ErrorChecker.user_confirm_action()
        def move_up(self):
            self._track_state("MOVE_UP")
            #First check if it is already at the top
            count = self.check_count()
            if count >= (74*self.RAIL_STEPS_PER_REV) - 10*self.RAIL_STEPS_PER_REV:
                logging.error("Linear Rail - Already at the top, cannot move up")
                self.check_count()  #Run to output the count
                return False

            self._linrail_move_success = None
            self.board.send_sysex(LINRAIL_UP, [])       # Send the move up command
            
            # Wait for the move to complete, or timeout 
            start_time = time.time()
            while not self._linrail_move_success and time.time() - start_time < self.MOVE_TIMEOUT:
                time.sleep(0.1)
            
            if self._linrail_move_success is None:
                raise CommunicationError("Linear Rail - Timeout, Move up failed")
            
            logging.info("Arduino - Linear Rail - Moved up")
            self.check_count()  #Run to output the count

            return self._linrail_move_success            

        @ErrorChecker.user_confirm_action()
        def move_down(self):
            self._track_state("MOVE_DOWN")
            #First check if it is already at the bottom
            count = self.check_count()
            if count <= 0:
                logging.error("Linear Rail - Already at the bottom, cannot move down")
                self.check_count()  #Run to output the count
                return False

            self._linrail_move_success = None
            self.board.send_sysex(LINRAIL_DOWN, [])     # Send the move down command

            # Wait for the move to complete, or timeout             
            start_time = time.time()
            while not self._linrail_move_success and time.time() - start_time < self.MOVE_TIMEOUT:
                time.sleep(0.1)
            
            if self._linrail_move_success is None:
                raise CommunicationError("Linear Rail - Timeout, Move down failed")
            
            logging.info("Arduino - Linear Rail - Moved down")
            self.check_count()  #Run to output the count

            return self._linrail_move_success

        @ErrorChecker.user_confirm_action()
        def home(self):
            self._track_state("HOME")
            self._linrail_home_success = None
            self.board.send_sysex(LINRAIL_HOME, [])

            # Wait for the homing to complete, or timeout
            start_time = time.time()
            while self._linrail_home_success is None and time.time() - start_time < self.HOME_TIMEOUT:
                time.sleep(0.1)
            
            if self._linrail_home_success is None:
                raise CommunicationError("Linear Rail - Timeout, Homing failed")
            
            logging.info(f"Arduino - Linear Rail - Homing successful {self._linrail_home_success}")
            return self._linrail_home_success

        def check_count(self):
            self._linrail_count = None
            self.board.send_sysex(LINRAIL_COUNT, [])
            
            # Wait for the count to be received, or timeout
            start_time = time.time()
            while self._linrail_count is None and time.time() - start_time < self.CHECK_TIMEOUT:
                time.sleep(0.1)
            
            if self._linrail_count is None:
                raise CommunicationError("Linear Rail - Timeout, Count check failed")
            
            logging.info(f"Arduino - Linear Rail - Count: {self._linrail_count}")

            return self._linrail_count
        
        def _linrail_move_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)
            if conv_data[0] == 0xFF:
                self._linrail_move_success = True
            else:
                self._linrail_move_success = False
        
        def _linrail_count_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)

            # print("Linear rail count")
            # print("\tReceived SysEx message:", [d for d in data])
            # print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")

            # The total count is a 16-bit value, so we need to combine the two bytes
            self._linrail_count = int.from_bytes(bytes([conv_data[0], conv_data[1]]), byteorder='big', signed=True)
            # print(f"\tCount: {self._linrail_count}")
        
        def _linrail_home_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)

            # print("\tReceived SysEx message:", [d for d in data])
            # print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")
            
            if conv_data[0] == 0xFF:
                self._linrail_home_success = True
            else:
                self._linrail_home_success = False

    class Gripper(StateTracker):

        MOVE_TIMEOUT = 3
        CHECK_TIMEOUT = 1

        def __init__(self, board) -> None:
            super().__init__()      # Initialize the StateTracker class

            # Attach the callback functions to the appropriate Firmata events
            self.board = board
            
            self.board.add_cmd_handler(GRIPPER_OPEN, self._gripper_move_callback)
            self.board.add_cmd_handler(GRIPPER_CLOSE, self._gripper_move_callback)
            self.board.add_cmd_handler(GRIPPER_STATE, self._gripper_state_callback)
            self.board.add_cmd_handler(GRIPPER_STATE_ANGLE, self._gripper_angle_callback)
            
            self._gripper_is_grabbed = None;    # Stores the state of the gripper
            self._gripper_servo_angle = None;   # Stores the angle of the servo
            self._gripper_move_success = None;  # Stores the success of the grab operation

            # Set the callback function for the CommunicationErrorChecker
            ErrorChecker.set_get_state_callback(self.get_state)
        
        @ErrorChecker.user_confirm_action()
        def close(self):
            self._track_state("MOVE_CLOSE")
            self._gripper_move_success = None
            self.board.send_sysex(GRIPPER_CLOSE, [])
            
            # Wait for the grab to complete, or timeout
            start_time = time.time()
            while not self._gripper_move_success and time.time() - start_time < self.MOVE_TIMEOUT:
                time.sleep(0.1)
            
            if self._gripper_move_success is None:
                raise CommunicationError("Gripper - Timeout, close failed")
            
            logging.debug("Arduino - Gripper - Closed")
            
            return self._gripper_move_success
        
        @ErrorChecker.user_confirm_action()
        def open(self):
            self._track_state("MOVE_OPEN")
            self._gripper_move_success = None
            self.board.send_sysex(GRIPPER_OPEN, [])
            
            # Wait for the release to complete, or timeout
            start_time = time.time()
            while not self._gripper_move_success and time.time() - start_time < self.MOVE_TIMEOUT:
                time.sleep(0.1)
            
            if self._gripper_move_success is None:
                raise CommunicationError("Gripper - Timeout, Release failed")
            
            logging.debug("Arduino - Gripper - Opened")

            return self._gripper_move_success
        
        @ErrorChecker.user_confirm_action()
        def check_state(self):
            self._gripper_is_grabbed = None
            self.board.send_sysex(GRIPPER_STATE, [])

            # Wait for the state to be received, or timeout
            start_time = time.time()
            while self._gripper_is_grabbed is None and time.time() - start_time < self.CHECK_TIMEOUT:
                time.sleep(0.1)
            
            if self._gripper_is_grabbed is None:
                raise CommunicationError("Gripper - Timeout, State check failed")
            
            logging.info(f"Arduino - Gripper - is grabbing: {self._gripper_is_grabbed}")
            
            return self._gripper_is_grabbed
        
        @ErrorChecker.user_confirm_action()
        def check_angle(self):
            self._gripper_servo_angle = None
            self.board.send_sysex(GRIPPER_STATE_ANGLE, [])

            # Wait for the angle to be received, or timeout
            start_time = time.time()
            while self._gripper_servo_angle is None and time.time() - start_time < self.CHECK_TIMEOUT:
                time.sleep(0.1)

            if self._gripper_servo_angle is None:
                raise CommunicationError("Gripper - Timeout, Angle check failed")
            
            logging.info(f"Arduino - Gripper - Angle: {self._gripper_servo_angle}")
            return self._gripper_servo_angle
        
        def _gripper_move_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)
            if conv_data[0] == 0xFF:
                self._gripper_move_success = True
            else:
                self._gripper_move_success = False

        def _gripper_state_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)
            # print("\tReceived SysEx message:", [d for d in data])
            # print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data

            self._gripper_is_grabbed = bool(conv_data[0])

        def _gripper_angle_callback(self, *data):
            conv_data, data = ArduinoHardware._unpack_sysex(*data)
            # print("\tReceived SysEx message:", [d for d in data])
            # print(f"\tConverted data: {[bin(d) for d in conv_data]} = {conv_data}")
            
            self._gripper_servo_angle = (conv_data[0])