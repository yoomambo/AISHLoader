// Linear rail takes 25000 to go up, use 25100 to ensure spring loading

#include <Boards.h>
// Using Frimata 2.5.9 (BXL 241203)
#include <Firmata.h>
#include <FirmataConstants.h>
#include <FirmataDefines.h>
#include <FirmataMarshaller.h>
#include <FirmataParser.h>

#include <Servo.h>

Servo gripperServo;  // create Servo object to control a servo
#define SERVO_SPEED_DELAY 15
#define servoPin 9


// Define stepper motor connection pins
#define RAIL_limPin 5   //Limit switch
#define RAIL_dirPin 6   // Direction pin
#define RAIL_stepPin 7  // Step pin
#define RAIL_enPin 8    //Enable pin

// Define the number of steps per revolution for motor
#define RAIL_STEPS_PER_REV 400
#define RAIL_PULSEWIDTH 300  // Controls the speed, longer = slower
#define RAIL_TRAVELREVS 63
int RAIL_stepCount = -1;     // Tracks the current number of steps of the stepper motor rail.  75*400 = 30 000, which is storable in signed int

void setup() {
  Firmata.setFirmwareVersion(FIRMATA_FIRMWARE_MAJOR_VERSION, FIRMATA_FIRMWARE_MINOR_VERSION);
  Firmata.begin(57600);

  // Attach SysEx callback handler
  for (uint8_t i = 0; i < 0x50; i++)
    Firmata.attach(i, sysexCallback);

  //Initialize servo to 0 (open)
  gripperServo.attach(servoPin);  // attaches the servo to the Servo object
  moveServo(0);

  //Initialize the input/output pins for the linear rail
  pinMode(RAIL_stepPin, OUTPUT);
  pinMode(RAIL_dirPin, OUTPUT);
  pinMode(RAIL_enPin, OUTPUT);
  pinMode(RAIL_limPin, INPUT_PULLUP);  //Normally open

  digitalWrite(RAIL_enPin, LOW);    //Turn off current through the motor
  digitalWrite(RAIL_stepPin, LOW);  //Initialize the pulsing pin to low
  digitalWrite(RAIL_dirPin, HIGH);  //Set direction to up
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
    case 0x20:  //Linear rail go up
      {
        rotateMotor(RAIL_TRAVELREVS * RAIL_STEPS_PER_REV);
        byte data = 0xFF;
        Firmata.sendSysex(command, 1, &data);  //Send a 0xFF byte to indicate it is finished and successful
        break;
      }
    case 0x21:  //Linear rail go down
      {
        rotateMotor(-RAIL_TRAVELREVS * RAIL_STEPS_PER_REV);
        byte data = 0xFF;
        Firmata.sendSysex(command, 1, &data);  //Send a 0xFF byte to indicate it is finished and successful
        break;
      }
    case 0x22:  //Get the stepper motor count of the linear rail
      {
        byte data[2];

        // Break the int into 2 bytes
        data[0] = (RAIL_stepCount >> 8) & 0xFF;
        data[1] = RAIL_stepCount & 0xFF;

        // Send the data as a Sysex message
        Firmata.sendSysex(command, 2, data);  
        break;
      }
    case 0x23:  //Home the rail
      {
        bool homeSuccess = homeRail();
        if (homeSuccess) {
          byte data = 0xFF;
          Firmata.sendSysex(command, 1, &data);  //Send a 0xFF byte to indicate it is finished and successful
        } else {
          byte data = 0x00;
          Firmata.sendSysex(command, 1, &data);  //Send a 0xFF byte to indicate it is finished and successful
        }
        break;
      }


    //GRIPPER CALLBACKS
    //Gripper grabbing commands
    case 0x10:  //Open Gripper
      {
        gripper_grab(false);
        byte data = 0xFF;
        Firmata.sendSysex(command, 1, &data);  //Send a 0xFF byte to indicate it is finished and successful
        break;
      }
    case 0x11:  //Close Gripper
      {
        gripper_grab(true);
        byte data = 0xFF;
        Firmata.sendSysex(command, 1, &data);  //Send a 0xFF byte to indicate it is finished and successful
        break;
      }
    // Check the state of the gripper
    case 0x12:  //Get gripper state (Open/closed)
      {
        byte value_to_send = (gripperServo.read() == 30) ? 1 : 0;  // Convert boolean to integer
        Firmata.sendSysex(command, 1, &value_to_send);             // Send the integer value
        break;
      }
    case 0x14:  //Get gripper servo angle
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


/**
 * @brief Performs the homing procedure for the rail by moving towards a limit switch.
 *
 * This function first checks if the limit switch is already pressed. If pressed, it rotates the motor 
 * upwards by 4 full revolutions to disengage the switch. Then, the motor moves towards the limit switch 
 * until either the limit switch is triggered (indicating successful homing) or a maximum step count is 
 * reached (indicating timeout).  Ths maximum is half of the total throw of the linear rail (75/2 rotations)
 *
 * @return bool - Returns true if homing is successful (limit switch triggered), otherwise false (timeout).
 */
bool homeRail() {
  long maxSteps = (20 * RAIL_STEPS_PER_REV);  // Timeout condition
  long stepsMoved = 0;

  // Serial.print("Max Steps (homing): ");
  // Serial.println(maxSteps);

  // (1) Check if the limit switch is already pressed.  If so, translate upwards by a little bit
  if (digitalRead(RAIL_limPin) == LOW) {  // Limit switch is already pressed
    rotateMotor(4 * RAIL_STEPS_PER_REV);
  }

  // (2) Do homing procedure
  // Serial.println("Starting homing");
  digitalWrite(RAIL_dirPin, LOW);                                      // Set direction towards the limit switch
  digitalWrite(RAIL_enPin, HIGH);                                      // Enable motor
  while (digitalRead(RAIL_limPin) == HIGH && stepsMoved < maxSteps) {  // Move until the limit switch is pressed or timeout
    digitalWrite(RAIL_stepPin, LOW);
    delayMicroseconds(RAIL_PULSEWIDTH);  // Adjust this delay to control speed
    digitalWrite(RAIL_stepPin, HIGH);
    delayMicroseconds(RAIL_PULSEWIDTH);
    stepsMoved++;
    RAIL_stepCount--;
  }

  digitalWrite(RAIL_enPin, LOW);  // Disable motor once homed or timeout (no locking)

  // Serial.println(stepsMoved);
  if (stepsMoved >= maxSteps) {
    // Serial.println("Homing failed: Timeout reached");
    return false;
  } else {
    RAIL_stepCount = 0;  // Reset the step count after successful homing
    // Serial.print("Homing successful.");
    // Serial.print("  Steps Moved: ");
    // Serial.println(stepsMoved);
    return true;
  }
}



/**
 * Rotates the stepper motor a specified number of revolutions.
 *
 * This function controls the direction and steps of a stepper motor based on the input
 * revolutions. Positive values will rotate the motor clockwise, while negative values will
 * rotate it counter-clockwise. The motor is enabled before rotation and disabled afterward.
 *
 * @param pulseCount  The number of pulses to send to the motor. Rotates pulseCount*RAIL_STEPS_PER_REV revolutions
 *                    Use a positive float for clockwise rotation and a negative 
 *                    float for counter-clockwise rotation.
 */
void rotateMotor(long pulseCount) {
  if (abs(pulseCount) > 75 * RAIL_STEPS_PER_REV)
    return;

  digitalWrite(RAIL_enPin, HIGH);
  delay(500);

  int dir = 1;
  // Determine direction and total steps
  if (pulseCount > 0) {
    digitalWrite(RAIL_dirPin, HIGH);  // Clockwise
    dir = 1;
  } else {
    digitalWrite(RAIL_dirPin, LOW);  // Counter-clockwise
    dir = -1;
  }

  int totalSteps = abs(pulseCount);

  for (int x = 0; x < totalSteps; x++) {
    digitalWrite(RAIL_stepPin, LOW);
    delayMicroseconds(RAIL_PULSEWIDTH);  // Adjust this delay to control speed
    digitalWrite(RAIL_stepPin, HIGH);
    delayMicroseconds(RAIL_PULSEWIDTH);

    RAIL_stepCount += dir;  //Keep a running count of the steps
  }

  digitalWrite(RAIL_enPin, LOW);  //Cut current to motor (no locking)
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
    moveServo(45);
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
