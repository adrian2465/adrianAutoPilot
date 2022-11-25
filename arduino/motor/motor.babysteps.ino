
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

enum MotorDirection {Clockwise, Counterclockwise};

void debug(char *msg) {
  #ifdef DEBUG
  Serial.println(msg);
  #endif
}

void enableClutch() {
  digitalWrite(CLUTCHPIN, HIGH);
  debug("Clutch ON");
}

void disableClutch() {
  digitalWrite(CLUTCHPIN, LOW);
  debug("Clutch OFF");
}


// Stop motor.
void stopMotor() {
  analogWrite(LPWM, PWM_OFF);
  analogWrite(RPWM, PWM_OFF);
  debug("Motor stopped");
}


enum MotorDirection currentMotorDirection = Clockwise;
int currentMotorSpeed = 0;

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


// Turn motor. 
// speed: 0 .. MOTOR_MAX. 
// motorDirection: Clockwise or Counterclockwise
void setMotor(int speed, MotorDirection motorDirection) {
  if (speed == 0) {
    stopMotor();
  } else {
    uint8_t speed8 = 
      (speed > MOTOR_MAX) ? MOTOR_MAX 
      : (speed < 0) ? 0 
      : speed;
    switch (motorDirection) {
      case Clockwise: 
        debug("CW");
        analogWrite(LPWM, PWM_OFF);
        analogWrite(RPWM, speed8);
        break;
      default: // Counterclockwise
        debug("CCW");
        analogWrite(RPWM, PWM_OFF);
        analogWrite(LPWM, speed8);
        break;
    }
    currentMotorSpeed = speed;
    currentMotorDirection = motorDirection;
  }
}

void setup() {
  Serial.begin(9600);
  initClutch();
  initMotor();
  debug("Setup complete");
}

void loop() {
  // Enable and disable clutch.
  enableClutch();

  // Clockwise test
  setMotor(MOTOR_MAX / 10, Clockwise);
  delay(1000); // Run for 1 second
  stopMotor();

  delay(500);
  // Counterclockwise test
  setMotor(MOTOR_MAX / 10, Counterclockwise);
  delay(1000); // Run for 1 second
  stopMotor();

  disableClutch();
  delay(2000);
}
