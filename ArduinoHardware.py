# Handles commmunication with the Arduino to control hardware
# Uses pyFirmata to communicate reliably
# Hardware components connected to Arduino:
# - Gripper: For grabbing the samples
# - Linear Rail: For raising the sample stage

# pyFirmata VARIABLEs
LINEAR_RAIL_ADDR = 0x01
GRIPPER_ADDR = 0x02

class ArduinoHardware:
    def __init__(self) -> None:
        self.lin_rail = LinearRail(LINEAR_RAIL_ADDR)
        self.gripper = Gripper(GRIPPER_ADDR)

    def connect(port):
        pass

class LinearRail:
    def __init__(self, address) -> None:
        self.address = address
        pass

    @property
    def STATE(self):
        # (1) Send request to Arduino to get state
        # (2) Parse response
        # (3) Return state
        pass

    @STATE.setter
    def STATE(self, new_state):
        # (1) Send request to Arduino to set state
        # (2) Send request to Arduino to get state
        # (3) Parse response
        # (3) Return state
        pass

class Gripper:
    def __init__(self, address) -> None:
        self.address = address
        pass

    @property
    def STATE(self):
        # (1) Send request to Arduino to get state
        # (2) Parse response
        # (3) Return state
        pass

    @STATE.setter
    def STATE(self, new_state):
        # (1) Send request to Arduino to set state
        # (2) Send request to Arduino to get state
        # (3) Parse response
        # (3) Return state
        pass

    