from ArduinoHardware import ArduinoHardware
from Ender3 import Ender3
import time

arduino = ArduinoHardware(PORT='/dev/tty.usbmodem1201')
ender3 = Ender3('/dev/tty.usbmodem1401')

ender3.init_homing()

time.sleep(2)

ender3.move_to_sample(0)
ender3.move_to_stage()
ender3.move_to_rest()
ender3.move_to_stage()
ender3.move_to_rest()
ender3.move_to_sample(0)

# arduino.linear_rail.move_up()
# ishomed = arduino.linear_rail.home()
# print(ishomed)

# ishomed = arduino.linear_rail.home()
# print(ishomed)

# ishomed = arduino.linear_rail.home()
# print(ishomed)

# ishomed = arduino.linear_rail.home()
# print(ishomed)

