import ArduinoHardware
import time

# Create a new instance of the ArduinoHardware class
port = '/dev/tty.usbmodem1301'
arduino = ArduinoHardware.ArduinoHardware(port)
time.sleep(1)

def main():
    while True:
        user_input = input("Enter command (1 to grab, 0 to release, 'check' to see state, 'exit' to quit): ")

        if user_input == '1':
            arduino.gripper.close()
        elif user_input == '0':
            arduino.gripper.open()
        elif user_input.lower() == 'check':
            state = arduino.gripper.check_state()
            print(f"Gripper grabbing: {state}")
        elif user_input.lower() == 'angle':
            angle = arduino.gripper.check_angle()
            print(f"Gripper angle: {angle}")
        elif user_input.lower() == 'exit':
            print("Exiting program.")
            break
        else:
            print("Invalid command. Please enter 0, 1, 'check', or 'exit'.")
        time.sleep(1)  # Optional: add a small delay for readability

if __name__ == "__main__":
    main()
