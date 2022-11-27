/*
Adrian Vrouwenvelder
November 2022
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
MotorDirection limitException = MotorDirectionNeither;
boolean motorSettingsChanged = true;
int leftPositionLimit, rightPositionLimit; 
unsigned long statusInterval = DEFAULT_STATUS_INTERVAL_MS;
boolean lowerLimitIsLeft = true; // True iff the lower limit is left and the upper limit is right.

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
MotorDirection getLimitExceptionDirection() {
  int position = getPosition();
  MotorDirection direction;
  // Since the position sensor may read either right > left , or left > right, detect this from the limits
  // and handle accordingly.
  int lowerLimit = (lowerLimitIsLeft) ? leftPositionLimit : rightPositionLimit;
  int upperLimit = (lowerLimitIsLeft) ? rightPositionLimit : leftPositionLimit;
  if (position < lowerLimit) direction = lowerLimitIsLeft ? MotorDirectionLeft : MotorDirectionRight;
  else if (position > upperLimit) direction = lowerLimitIsLeft ? MotorDirectionRight : MotorDirectionLeft;
  else direction = MotorDirectionNeither;
  if (direction != MotorDirectionNeither && direction == motorDirection) return direction;
  else return MotorDirectionNeither; // No fault if we're no longer going in the direction of the fault.
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
  lowerLimitIsLeft = (leftPositionLimit < rightPositionLimit);
}

// Set the pins as required.
void readAndWritePins() {
  MotorDirection _limitException = getLimitExceptionDirection();
  motorSettingsChanged |= (_limitException != limitException);
  limitException = _limitException;
  if (motorSettingsChanged) {
    switch (motorDirection) {
    case MotorDirectionRight: 
      analogWrite(LEFT_PWM_PIN, MOTOR_STOP_VAL);
      analogWrite(RIGHT_PWM_PIN, (limitException == MotorDirectionRight) ? MOTOR_STOP_VAL : motorSpeed); 
      break;
    case MotorDirectionLeft: 
      analogWrite(RIGHT_PWM_PIN, MOTOR_STOP_VAL);
      analogWrite(LEFT_PWM_PIN, (limitException == MotorDirectionLeft) ? MOTOR_STOP_VAL : motorSpeed); 
      break;
    default: 
      analogWrite(RIGHT_PWM_PIN, MOTOR_STOP_VAL);
      analogWrite(LEFT_PWM_PIN, MOTOR_STOP_VAL);
    }
    motorSettingsChanged = false;
  }
}

