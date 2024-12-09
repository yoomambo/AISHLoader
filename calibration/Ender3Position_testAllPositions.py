# Sample holder calibration routine
import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import and start the AISHLoader
from AISHLoader import AISHLoader
PORT_ENDER = '/dev/tty.usbmodem141101'
PORT_ARDUINO = '/dev/tty.usbmodem141201'
aish_loader = AISHLoader(PORT_ENDER, PORT_ARDUINO)


# Grab a sample at position 0, then move to next position and release, repeat for all positions
num_samps = len(aish_loader.ender3.SAMPLE_POSITIONS)
success_pos = np.ones(num_samps)
for i in range(2):
    aish_loader.ender3.move_to_sample(i)
    aish_loader.arduino.gripper.close()
    aish_loader.ender3.move_to_sample((i + 1) % num_samps)
    aish_loader.arduino.gripper.open()

    # Ask for user input to continue
    user_in = input(f"Was sample {i} successful? (y/n): ")

    if user_in.lower() == 'n':
        success_pos[i] = 0
        

print('Calibration routine finished')
print('Success positions:', np.where(success_pos == 1)[0])
print('Failed positions:', np.where(success_pos == 0)[0])