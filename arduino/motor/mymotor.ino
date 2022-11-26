
/*

This motorcontroller is ascii-command driven.
Commands are single-letter, followed by one or more parameters.
Commands are terminated by newlines ('\n').
Carriage returns ('\r') are ignored.

Commands:
* c - clutch.  c+ is clutch on. c- is clutch off.
* d - direction. d+ is CW, d- is CCW
* s - Speed.  s0 is stop.  s9 is MAX
* l - motor limits. 3 digit decimal. E.g. l050127205 = Limits 50, 127, 205.  Min is 0. MAX is 255. 


Code is designed for Arduino Nano.
Code is designed to operate with the PWM-based IBT-2 Motor Control Board.
 
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
 
// #define DEBUG // DEFINE TO ENABLE DEBUG STATEMENTS
#include "commandbuffer.h"
#include "motorController.h"

void setup() {
  Serial.begin(9600);
  initMotor();
  Serial.println("REBOOTED"); // Signal to client that reinitialization may need to take place
}

void execute() {
   executeMotor();
}

void loop() {
  if (Serial.available() > 0) {
    char *command = getCommandOrNULL(Serial.read()); 
    if (command != NULL) {
      Serial.print("RECD:"); Serial.println(command);
      
      switch (command[0]) {
      case 'c': // Clutch
        if (strlen(command)<2) {
          Serial.println("ERR:MISSINGPARAM");
          break;
        } else switch(command[1]) {
          case '+': setClutch(true); break;
          case '-': setClutch(false); break;
          default: Serial.println("ERR:BADPARAM");
        } 
        break;
      case 'd': // Set direction
        if (strlen(command)<2) {
          Serial.println("ERR:MISSINGPARAM");
          break;
        } else switch(command[1]) {
          case '+': setMotorDirection(Clockwise); break;
          case '-': setMotorDirection(Counterclockwise); break;
          default: Serial.println("ERR:BADPARAM");
        } 
        break;
      case 'l': // Set limits
        setLimits(leftLimit, centerLimit, upperLimit);
        break;
      case 's': // Set motor speed.
        if (strlen(command)<2) {
          Serial.println("ERR:MISSINGPARAM");
        } else if (command[1] > '9' || command[1] < '0') {
          Serial.println("ERR:BADPARAM");
        } else {
          setMotorSpeed((command[1] - '0') * MOTOR_MAX / 9);
        }
        break;
      default: 
        Serial.println("ERR:BADCMD"); 
      }
      execute();
    }
  } else {
    delay(10); // Wait for new command.
  }
}
