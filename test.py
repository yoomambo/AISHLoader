from AISHLoader import AISHLoader

AISH = AISHLoader('/dev/tty.usbmodem1401', '/dev/tty.usbmodem1201')

# Test all the load/unload by moving the sample from each position to the next
for i in range(4):
    AISH.ender3.move_to_sample(i)
    AISH.arduino.gripper.close()
    AISH.ender3.move_to_sample(i+1)
    AISH.arduino.gripper.open()




# from AISH_utils import *

# @ErrorChecker.user_confirm_action()
# def test_func():
#     commerror_tester(False)
#     commerror_tester(True)

# def commerror_tester(throwerror):
#     if throwerror:
#         raise CommunicationError("Test error")
#     else:
#         print("No error thrown")


# test_func()