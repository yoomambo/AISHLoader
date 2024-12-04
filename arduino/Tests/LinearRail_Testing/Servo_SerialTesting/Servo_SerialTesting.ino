#include <Servo.h>

Servo gripperServo;  // create Servo object to control a servo
#define SERVO_SPEED_DELAY 15

void setup() {
  gripperServo.attach(9);  // attaches the servo on pin 9 to the Servo object
  moveServo(0);
  Serial.begin(9600);
}

// void loop() {
//   if (Serial.available() > 0) {
//     if (Serial.peek() >= '0' && Serial.peek() <= '9') {   // check if the input is numeric
//       int targetPos = Serial.parseInt();                  // read the input position
//       moveServo(targetPos);                        // call the function with position and speed
//     } else {
//       Serial.read();  // discard non-numeric characters
//     }
//   }
// }

void loop() {
  if (Serial.available() > 0) {
    int input = Serial.parseInt();
    moveServo(input);
    // if (input == 1) {
    //   gripper_grab(true);  // call gripper_grab with true if input is 1
    // } else if (input == 0) {
    //   gripper_grab(false); // call gripper_grab with false if input is 0
    // }
  }
}

void gripper_grab(bool isGrabOn) {
  if (isGrabOn)
    moveServo(30);
  else
    moveServo(0);
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
        gripperServo.write(pos);         // move the servo to the next position
        delay(SERVO_SPEED_DELAY);               // control the speed
      }
    } else {
      for (int pos = currentPos; pos >= targetPos; pos--) {
        gripperServo.write(pos);         // move the servo to the next position
        delay(SERVO_SPEED_DELAY);               // control the speed
      }
    }
  }
}



