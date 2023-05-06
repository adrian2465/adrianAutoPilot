/*
Adrian Vrouwenvelder
April 2023
*/

// Pin definitions
#define LEFT_ENABLE_PIN (2) // OUTPUT
#define RIGHT_ENABLE_PIN (3) // OUTPUT
#define POSITION_PIN (A4) // INPUT. Position of thing being moved by the motor.
#define LEFT_PWM_PIN (9) // OUTPUT
#define RIGHT_PWM_PIN (10) // OUTPUT

#define DEFAULT_STATUS_INTERVAL_MS (1000)

// Defaults
#define MOTOR_FULLSPEED_VAL (255)
#define MOTOR_STOP_VAL (0)

enum MotorDirection {MotorDirectionNeither, MotorDirectionRight, MotorDirectionLeft};
uint8_t motorSpeed = MOTOR_STOP_VAL;
MotorDirection motorDirection = MotorDirectionNeither;
MotorDirection faultDirection = MotorDirectionNeither;
bool motorSettingsChanged = true;
int leftPositionLimit = 0;
int rightPositionLimit = 1023;
unsigned long statusInterval = DEFAULT_STATUS_INTERVAL_MS;

// speed is a value from 0 to 255.
void setMotorSpeed(uint8_t s) {
  if (s != motorSpeed) {
    motorSpeed = s;
    motorSettingsChanged = true;
  }
}

uint8_t getMotorSpeed() {
  return motorSpeed;
}

int getPosition() {
  return analogRead(POSITION_PIN);
}

// Returns: MotorDirectionLeft if beyond left. MotorDirectionRight if beyond right. MotorDirectionNeither if no limits exceeded.
MotorDirection getLimitFaultDirection() {
  int position = getPosition();
  MotorDirection faultDirection = (position < leftPositionLimit) ? MotorDirectionLeft
     : (position > rightPositionLimit) ? MotorDirectionRight
     : MotorDirectionNeither;
  return (faultDirection == motorDirection) ? faultDirection
     : MotorDirectionNeither; // No fault if we're no longer going in the direction of the fault.
}

void initMotor() {
  pinMode(RIGHT_PWM_PIN, OUTPUT);
  pinMode(LEFT_PWM_PIN, OUTPUT);
  pinMode(RIGHT_ENABLE_PIN, OUTPUT);
  pinMode(LEFT_ENABLE_PIN, OUTPUT);
  pinMode(POSITION_PIN, INPUT);
  digitalWrite(RIGHT_ENABLE_PIN, HIGH);
  digitalWrite(LEFT_ENABLE_PIN, HIGH);
}

void setMotorDirection(MotorDirection direction) {
  if (direction != motorDirection) {
    motorDirection = direction;
    motorSettingsChanged = true;
  }
}

MotorDirection getMotorDirection() {
  return motorDirection;
}

void setStatusInterval(int intervalMs) {
  statusInterval = intervalMs;
}

int getStatusInterval() {
  return statusInterval;
}

int getLimit(MotorDirection limitSelector) {
  return (limitSelector == MotorDirectionRight) ? rightPositionLimit : leftPositionLimit;
}

void setLimit(MotorDirection limitSelector, int limit) {
  switch(limitSelector) {
  case MotorDirectionRight:
    rightPositionLimit = limit; 
    motorSettingsChanged = true;
    break;
  case MotorDirectionLeft:
    leftPositionLimit = limit;
    motorSettingsChanged = true;
    break;
  }
}

// Set the pins as required.
void readAndWritePins() {
  MotorDirection _faultDirection = getLimitFaultDirection();
  motorSettingsChanged |= (_faultDirection != faultDirection);  // Consider motor changed if fault direction changed.
  faultDirection = _faultDirection;
  if (motorSettingsChanged) {
    switch (motorDirection) {
    case MotorDirectionRight: 
      analogWrite(LEFT_PWM_PIN, MOTOR_STOP_VAL);
      analogWrite(RIGHT_PWM_PIN, (faultDirection == MotorDirectionRight)
        ? MOTOR_STOP_VAL // If we are in a fault situation, stop going in that direction
        : motorSpeed);  // Apply motor speed if not in a fault, or if fault is in the opposite direction.
      break;
    case MotorDirectionLeft: 
      analogWrite(RIGHT_PWM_PIN, MOTOR_STOP_VAL);
      analogWrite(LEFT_PWM_PIN, (faultDirection == MotorDirectionLeft)
        ? MOTOR_STOP_VAL // If we are in a fault situation, stop going in that direction
        : motorSpeed); // Apply motor speed if not in a fault, or if fault is in the opposite direction.
      break;
    default: 
      analogWrite(RIGHT_PWM_PIN, MOTOR_STOP_VAL);
      analogWrite(LEFT_PWM_PIN, MOTOR_STOP_VAL);
    }
    motorSettingsChanged = false;
  }
}

