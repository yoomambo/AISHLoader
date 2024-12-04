//FUYU RAIL IS 75 REVOLUTIONS END TO END (Leaves a small gap)

// Define Stepper motor limit switch
#define limPin 5

// Define stepper motor connection pins
#define dirPin 6   // Direction pin
#define stepPin 7  // Step pin
#define enPin 8

// Define the number of steps per revolution for your motor
#define STEPS_PER_REV 400
#define PULSEWIDTH 300  // Controls the speed, longer = slower
long stepCount = -1;

void setup() {
  // Declare pins as outputs
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(enPin, OUTPUT);
  pinMode(limPin, INPUT_PULLUP);  //Normally open

  Serial.begin(9600);  // Initialize serial communication
  digitalWrite(enPin, LOW);
  digitalWrite(stepPin, LOW);
  digitalWrite(dirPin, HIGH);

  delay(1000);
}

void loop() {
  // Serial.println(digitalRead(limPin));
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');  // Read the input as a string

    if (input.equals("home")) {
      homeRail();  // Call homeRail() if "home" is input
    } else {
      int revolutions = input.toInt();  // Convert input to an integer
      rotateMotor(revolutions);         // Rotate based on the input value
    }

    delay(1000);  // Wait for 2 seconds after each operation
    Serial.println(stepCount);
  }
}

/**
 * @brief Performs the homing procedure for the rail by moving towards a limit switch.
 *
 * This function first checks if the limit switch is already pressed. If pressed, it rotates the motor 
 * upwards by 4 full revolutions to disengage the switch. Then, the motor moves towards the limit switch 
 * until either the limit switch is triggered (indicating successful homing) or a maximum step count is 
 * reached (indicating timeout).
 *
 * @return bool - Returns true if homing is successful (limit switch triggered), otherwise false (timeout).
 */
bool homeRail() {
  long maxSteps = (75 * STEPS_PER_REV / 2);  // Timeout condition
  long stepsMoved = 0;

  // Serial.print("Max Steps (homing): ");
  // Serial.println(maxSteps);

  // (1) Check if the limit switch is already pressed.  If so, translate upwards by a little bit
  if (digitalRead(limPin) == LOW) {  // Limit switch is already pressed
    rotateMotor(4*STEPS_PER_REV);
  }

  // (2) Do homing procedure
  // Serial.println("Starting homing");
  digitalWrite(dirPin, LOW);                                      // Set direction towards the limit switch
  digitalWrite(enPin, HIGH);                                      // Enable motor
  while (digitalRead(limPin) == HIGH && stepsMoved < maxSteps) {  // Move until the limit switch is pressed or timeout
      digitalWrite(stepPin, LOW);
      delayMicroseconds(PULSEWIDTH);  // Adjust this delay to control speed
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(PULSEWIDTH);
      stepsMoved++;
      stepCount--;
  }

  digitalWrite(enPin, LOW);  // Disable motor once homed or timeout (no locking)

  Serial.println(stepsMoved);
  if (stepsMoved >= maxSteps) {
    Serial.println("Homing failed: Timeout reached");
    return false;
  } else {
    stepCount = 0;  // Reset the step count after successful homing
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
 * @param pulseCount  The number of pulses to send to the motor. Rotates pulseCount*STEPS_PER_REV revolutions
 *                    Use a positive float for clockwise rotation and a negative 
 *                    float for counter-clockwise rotation.
 */
void rotateMotor(long pulseCount) {
  if (abs(pulseCount) > 75 * STEPS_PER_REV)
    return;

  digitalWrite(enPin, HIGH);
  delay(500);

  int dir = 1;
  // Determine direction and total steps
  if (pulseCount > 0) {
    digitalWrite(dirPin, HIGH);  // Clockwise
    dir = 1;
  } else {
    digitalWrite(dirPin, LOW);  // Counter-clockwise
    dir = -1;
  }

  int totalSteps = abs(pulseCount);

  for (int x = 0; x < totalSteps; x++) {
    digitalWrite(stepPin, LOW);
    delayMicroseconds(PULSEWIDTH);  // Adjust this delay to control speed
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(PULSEWIDTH);

    stepCount += dir;  //Keep a running count of the steps
  }

  digitalWrite(enPin, LOW);  //Cut current to motor (no locking)
}
