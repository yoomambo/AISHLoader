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

    def __getstate__(self) -> object:
        pass

    def change_state(state):
        pass

class Gripper:
    def __init__(self, address) -> None:
        self.address = address
        pass

    def __getstate__(self) -> object:
        pass

    def change_state(state):
        pass

    