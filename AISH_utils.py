from functools import wraps
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s",
    datefmt='%y-%m-%d %H:%M:%S'
)

class CommunicationError(Exception):
    """Exception raised for communication-related errors."""
    def __init__(self, message="Communication error occurred"):
        self.message = message
        super().__init__(self.message)

class CommunicationErrorChecker:
    # Class variable to keep track of whether the system is halted and asking for user confirmation
    is_halted = False  
    get_state = lambda: None

    @staticmethod
    def set_get_state_callback(new_get_state):
        """
        Sets the callback function to get additional state information when a communication error occurs.

        Args:
            callback (function): A function that returns additional state information when a communication error occurs.
        """
        CommunicationErrorChecker.get_state = new_get_state 

    @staticmethod
    def confirm_action(get_state = None):
        """
        A decorator that handles `CommunicationError` exceptions by prompting the user 
        to confirm if an action completed successfully. If the action fails, it re-raises 
        the exception to halt the program.

        Args:
            get_state (function): A function that returns additional state information 
                                when a communication error occurs.

        Returns:
            function: A wrapper that catches `CommunicationError`, logs details, and 
                    asks for user confirmation.
        """

        # If get_state is not provided, use the default get_state method
        # otherwise, use the provided get_state method, but only for this instance of the decorator
        if get_state is None:
            get_state = CommunicationErrorChecker.get_state

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                except CommunicationError as e:
                    logging.error(f"Communication Error: {e}")

                    state_info = get_state()
                    logging.info(f"Current state: {state_info}")

                    user_input = input("Did the action complete successfully? (y/n): ").strip().lower()
                    if user_input == 'y':
                        logging.info("User confirmed the action completed.")
                    else:
                        logging.error("Action did not complete successfully. Raising exception and exiting.")
                        raise e
                except Exception as e:
                    logging.error(f"Error not related to communication, so uncaught:")
                    raise e
                finally:
                    # Write cleanup code here
                    pass
            return wrapper
        return decorator


@CommunicationErrorChecker.confirm_action(None)
def commerror_tester(throwerror):
    if throwerror:
        raise CommunicationError("Test error")
    else:
        print("No error thrown")


commerror_tester(False)
commerror_tester(True)

