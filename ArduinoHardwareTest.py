from ArduinoHardware import ArduinoHardware
import time

arduino = ArduinoHardware(port='/dev/tty.usbmodem1201')


# time.sleep(2)
arduino.linear_rail.move_up()
ishomed = arduino.linear_rail.home()
print(ishomed)

ishomed = arduino.linear_rail.home()
print(ishomed)

ishomed = arduino.linear_rail.home()
print(ishomed)

ishomed = arduino.linear_rail.home()
print(ishomed)

ishomed = arduino.linear_rail.home()
print(ishomed)


# arduino.board.send_sysex(0x01,[124])
# time.sleep(2)
# arduino.board.send_sysex(0x02,[])
