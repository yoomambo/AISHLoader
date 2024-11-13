from AISH_utils import *

@CommunicationErrorChecker.confirm_action()
def test_func():
    commerror_tester(False)
    commerror_tester(True)

def commerror_tester(throwerror):
    if throwerror:
        raise CommunicationError("Test error")
    else:
        print("No error thrown")


test_func()