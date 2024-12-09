# Sample holder calibration routine
from AISHLoader import AISHLoader
PORT_ENDER = '/dev/tty.usbmodem141101'
PORT_ARDUINO = '/dev/tty.usbmodem141201'
aish_loader = AISHLoader(PORT_ENDER, PORT_ARDUINO)

pos = (79.75, 17.4, 15.5)
ender = aish_loader.ender3

# Move to a position above the sample
ender._move_to(ender.current_position[0]  , ender.current_position[1]  , ender.SAMPLE_MIN_Z, 1200) #Move only Z first
ender._move_to(pos[0]             , pos[1]             , ender.SAMPLE_MIN_Z, 4000) #Move above the sample position

# Now loop through: move down and grab sample, move up, then back down and release sample and ask for user input
stop = False
dx, dy, dz = 0, 0, 0
while not stop:
    pos = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
    print('New position:', pos)
    ender._move_to(pos[0], pos[1], pos[2]) #Move down to the sample position
    aish_loader.arduino.gripper.close() #Close the gripper
    ender._move_to(pos[0], pos[1], pos[2]+10) #Move up
    ender._move_to(pos[0], pos[1], pos[2]) #Move down to the sample position
    aish_loader.arduino.gripper.open() #Open the gripper

    # Ask for user input, the dx, dy, dz values to move the sample holder
    dx = input('dx: ') or 0
    dy = input('dy: ') or 0
    dz = input('dz: ') or 0

    try:
        dx = float(dx)
        dy = float(dy)
        dz = float(dz)
    except ValueError:
        dx, dy, dz = float('nan'), float('nan'), float('nan')
    #Stop if any of the values is not a number
    if (dx != dx or dy != dy or dz != dz):
        stop = True
    

print('Calibration routine finished, final position:', pos)
    