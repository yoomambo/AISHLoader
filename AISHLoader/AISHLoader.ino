#include <Boards.h>
#include <Firmata.h>
#include <FirmataConstants.h>
#include <FirmataDefines.h>
#include <FirmataMarshaller.h>
#include <FirmataParser.h>

#include <Servo.h>

Servo gripperServo;  // create Servo object to control a servo
#define SERVO_SPEED_DELAY 15

int pos = 0;  // variable to store the servo position

void setup() {
  Firmata.setFirmwareVersion(FIRMATA_FIRMWARE_MAJOR_VERSION, FIRMATA_FIRMWARE_MINOR_VERSION);
  Firmata.begin(57600);

  // Attach SysEx callback handler
  for (uint8_t i = 0; i < 0x50; i++)
    Firmata.attach(i, sysexCallback);

  //Initialize servo to 0 (open)
  gripperServo.attach(9);  // attaches the servo on pin 9 to the Servo object
  moveServo(0);
}

void loop() {
  // Handle any incoming Firmata messages
  while (Firmata.available()) {
    Firmata.processInput();
  }
}

void sysexCallback(byte command, byte argc, byte* argv) {
  // Echo back the received SysEx message
  switch (command) {
    //LINEAR RAIL CALLBACKS
    case 0x20:
    {

    }


    //GRIPPER CALLBACKS
    //Gripper grabbing commands
    case 0x10:
      {
        gripper_grab(false);
        break;
      }
    case 0x11:
      {
        gripper_grab(true);
        break;
      }
    // Check the state of the gripper
    case 0x12:
      {
        byte value_to_send = (gripperServo.read() == 30) ? 1 : 0;        // Convert boolean to integer
        Firmata.sendSysex(command, 1, &value_to_send);  // Send the integer value
        break;
      }
    case 0x14:
      {
        byte value_to_send = byte(gripperServo.read());
        Firmata.sendSysex(command, 1, &value_to_send);  // Send the integer value
        break;
      }



    //Test, echo back the command
    case 0x01:
      {
        Firmata.sendSysex(command, argc, argv);
        break;
      }
    //Test, send back 4 bytes of data [23, 14, 22, 14]
    case 0x02:
      {
        byte data[4];
        data[0] = 23;
        data[1] = 14;
        data[2] = 22;
        data[3] = 14;

        Firmata.sendSysex(command, 4, data);
        break;
      }
  }
}

void linearRail_up(bool isRailUp) {
  
}


/**
 * Controls the gripper's grab action by setting the servo position.
 *
 * This function activates or deactivates the gripper based on the `isGrabOn` parameter.
 * When `isGrabOn` is true, the servo moves to the "grab" position (30 degrees).
 * When `isGrabOn` is false, the servo moves to the "release" position (0 degrees).
 *
 * @param isGrabOn A boolean value where true activates the grab action, 
 *                 and false releases the gripper.
 */
void gripper_grab(bool isGrabOn) {
  if (isGrabOn) {
    moveServo(30);
  } else {
    moveServo(0);
  }
}
/**
 * Moves the servo to the specified target position at the given speed.
 *
 * This function gradually moves the servo from its current position to the target 
 * position by incrementing or decrementing in 1-degree steps. The speed of movement 
 * is controlled by the delay between each step.
 *
 * @param targetPos The target position to move the servo to (0 to 180 degrees).
 * @param speed The speed of movement, where a higher value results in slower movement. 
 *              This is the delay in milliseconds between each degree step.
 */
void moveServo(int targetPos) {
  int currentPos = gripperServo.read();  // get the current position of the servo
  if (targetPos >= 0 && targetPos <= 180) {
    if (currentPos < targetPos) {
      for (int pos = currentPos; pos <= targetPos; pos++) {
        gripperServo.write(pos);   // move the servo to the next position
        delay(SERVO_SPEED_DELAY);  // control the speed
      }
    } else {
      for (int pos = currentPos; pos >= targetPos; pos--) {
        gripperServo.write(pos);   // move the servo to the next position
        delay(SERVO_SPEED_DELAY);  // control the speed
      }
    }
  }
}
