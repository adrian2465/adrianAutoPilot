
/*
IBT-2 Motor Control Board driven by Arduino.
 
Connection to the IBT-2 board:
IBT-2
pin desc  Arduino - MODE
===================================
  1 RPWM  PWM Green D10 - ANALOG
  2 LPWM  PWM Blue  D9 - ANALOG
  3 R_EN  +5v Yellow D3 - DIGITAL
  4 L_EN  +5v Lt. Brown D2 - DIGITAL
  5 R_IS  NOT CONNECTED
  6 L_IS  NOT CONNECTED
  7 VCC   +5v Red +5v
  8 GND   GND
IBT-2 pin 1 (RPWM) to Arduino pin 5(PWM)
IBT-2 pin 2 (LPWM) to Arduino pin 6(PWM)
IBT-2 pins 3 (R_EN), 4 (L_EN), 7 (VCC) to Arduino 5V pin
IBT-2 pin 8 (GND) to Arduino GND
IBT-2 pins 5 (R_IS) and 6 (L_IS) not connected
*/
 

#define DEBUG 1
#define CLUTCHPIN (11)
#define RPWM (10)
#define LPWM (9)
#define R_EN (3)
#define L_EN (2)
#define MOTOR_MAX (255)
#define PWM_OFF (0)

enum MotorDirection {Stopped, Clockwise, Counterclockwise};
uint8_t motorSpeed = 0;
MotorDirection motorDirection = Stopped;
boolean motorStateChanged = true;

void debug(char *msg) {
  #ifdef DEBUG
  Serial.println(msg);
  #endif
}

enum MotorDirection currentMotorDirection = Clockwise;
int currentMotorSpeed = 0;
boolean clutchEnabled = false;

void initMotor() {
  pinMode(RPWM, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_EN, OUTPUT);
  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
  debug("Motor initialized");
}

void initClutch() {
  pinMode(CLUTCHPIN, OUTPUT);
  debug("Clutch initialized");
}

void setClutch(boolean enabled) {
  if (enabled == clutchEnabled) return;
  clutchEnabled = enabled;
  motorStateChanged = true;
}

boolean isClutchEnabled() {
  return clutchEnabled;
}

void setMotorSpeed(int speed) {
  uint8_t localMotorSpeed = constrain(speed, 0, MOTOR_MAX);
  if (localMotorSpeed == motorSpeed) return;
  motorSpeed = localMotorSpeed;
  motorStateChanged = true;
}

void setMotorDirection(MotorDirection direction) {
  if (direction == motorDirection) return;
  motorDirection = direction;
  motorStateChanged = true;
}

void execute() {
  if (!motorStateChanged) return;
  motorStateChanged = false;
  if (clutchEnabled) {
    digitalWrite(CLUTCHPIN, HIGH);
    debug("Clutch ON");
  } else { 
    digitalWrite(CLUTCHPIN, LOW);
    debug("Clutch OFF");
  }
  if (motorSpeed == 0 || motorDirection == Stopped) {
    analogWrite(LPWM, PWM_OFF);
    analogWrite(RPWM, PWM_OFF);
  } else {
    switch (motorDirection) {
      case Clockwise: 
        analogWrite(LPWM, PWM_OFF);
        analogWrite(RPWM, motorSpeed);
        debug("CW");
        break;
      case Counterclockwise: 
        analogWrite(RPWM, PWM_OFF);
        analogWrite(LPWM, motorSpeed);
        debug("CCW");
        break;
      default: 
        analogWrite(RPWM, PWM_OFF);
        analogWrite(LPWM, PWM_OFF);
        debug("STOPPED");
        break;
    }
  }
}

void setup() {
  Serial.begin(9600);
  initClutch();
  initMotor();
  setMotorSpeed(MOTOR_MAX / 10);
  debug("setup");
}

void loop() {

  if (Serial.available() > 0) {
    int incomingByte = Serial.read();
    switch (incomingByte) {
    case 'e': // Enable clutch
      setClutch(true);
      break;
    case 'd': // Enable clutch
      setClutch(false);
      break;
    case 'r': // Turn right (CW)
      setMotorDirection(Clockwise);
      break;
    case 'l': // Turn left (CCW)
      setMotorDirection(Counterclockwise);
      break;
    default: 
      setMotorSpeed((incomingByte - '0') * MOTOR_MAX / 9);
    }
    execute();
  }
}
