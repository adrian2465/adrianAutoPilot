#define RPWM (10)
#define LPWM (9)
#define R_EN (3)
#define L_EN (2)
#define MOTOR_MAX (255)
#define PWM_OFF (0)
#define CLUTCHPIN (11)

boolean clutchEnabled = false;
enum MotorDirection {Stopped, Clockwise, Counterclockwise};
uint8_t motorSpeed = 0;
MotorDirection motorDirection = Stopped;
boolean motorStateChanged = true;
uint8_t leftLimit=0, centerLimit=127, upperLimit=255; // Rudder limits; turn motor until rudder-limit hits one of these values, then no more.
enum MotorDirection currentMotorDirection = Clockwise;
int currentMotorSpeed = 0;

void setMotorSpeed(int speed) {
  uint8_t localMotorSpeed = constrain(speed, 0, MOTOR_MAX);
  if (localMotorSpeed == motorSpeed) return;
  motorSpeed = localMotorSpeed;
  motorStateChanged = true;
}

void initClutch() {
  pinMode(CLUTCHPIN, OUTPUT);
}

void initMotor() {
  initClutch();
  pinMode(RPWM, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_EN, OUTPUT);
  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
}

void setClutch(boolean enabled) {
  if (enabled == clutchEnabled) return;
  clutchEnabled = enabled;
  motorStateChanged = true;
}

boolean isClutchEnabled() {
  return clutchEnabled;
}



void setMotorDirection(MotorDirection direction) {
  if (direction == motorDirection) return;
  motorDirection = direction;
  motorStateChanged = true;
}

void setLimits(int left, int center, int right) {}

void executeMotor() {
  if (!motorStateChanged) return;
  motorStateChanged = false;
  if (clutchEnabled) {
    digitalWrite(CLUTCHPIN, HIGH);
  } else { 
    digitalWrite(CLUTCHPIN, LOW);
  }
  if (motorSpeed == 0 || motorDirection == Stopped) {
    analogWrite(LPWM, PWM_OFF);
    analogWrite(RPWM, PWM_OFF);
  } else {
    switch (motorDirection) {
      case Clockwise: 
        analogWrite(LPWM, PWM_OFF);
        analogWrite(RPWM, motorSpeed);
        break;
      case Counterclockwise: 
        analogWrite(RPWM, PWM_OFF);
        analogWrite(LPWM, motorSpeed);
        break;
      default: 
        analogWrite(RPWM, PWM_OFF);
        analogWrite(LPWM, PWM_OFF);
        break;
    }
  }
}

