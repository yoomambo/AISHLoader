import numpy as np

pos_0 = np.array([39.1, 176.7, 3]) # Row 1, these are found center positions (have +/-0.3mm tolerance)
pos_4 = np.array([40.1, 17.4, 3])
pos_5 = np.array([0,0,0]) # Row 2, these are found center positions (have +/-0.3mm tolerance)
pos_9 = np.array([0,0,0])
SAMPLE_POSITIONS = np.append(np.linspace(pos_0, pos_4, num=5), np.linspace(pos_5, pos_9, num=5), axis=0)
print(SAMPLE_POSITIONS)

for i in range(len(SAMPLE_POSITIONS)):
    print(f"pos_{i} = np.array({SAMPLE_POSITIONS[i]})")


# from AISHLoader import AISHLoader

# AISH = AISHLoader('/dev/tty.usbmodem1401', '/dev/tty.usbmodem1201')

# # Test all the load/unload by moving the sample from each position to the next
# for i in range(4):
#     AISH.ender3.move_to_sample(i)
#     AISH.arduino.gripper.close()
#     AISH.ender3.move_to_sample(i+1)
#     AISH.arduino.gripper.open()




# from AISH_utils import *

# @ErrorChecker.user_confirm_action()
# def test_func():
#     print(commerror_tester(False))
#     print(commerror_tester(True))

# def commerror_tester(throwerror):
#     if throwerror:
#         raise CommunicationError("Test error")
#     else:
#         print("No error thrown")
#         return "HELLO"


# test_func()