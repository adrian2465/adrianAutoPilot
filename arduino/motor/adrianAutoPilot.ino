/*
Adrian Vrouwenvelder
November 2022

Code is designed for Arduino Nano.
Code is designed to operate with the PWM-based IBT-2 Motor Control Board.
 
This motorcontroller is ascii-command driven. 
Commands are single-letter, followed by one or more parameters.
Commands are terminated by newlines ('\n').
Carriage returns ('\r') are discarded and ignored.

*/
 
#include "commandbuffer.h"
#include "motorController.h"
#include "clutch.h"
#include "hexutil.h"

unsigned long latestStatusReportTime=0;

void setup() {
  Serial.begin(9600);
  initClutch();
  initMotor();
  Serial.println("m=REBOOTED;"); // Signal to client that reinitialization may need to take place
}

void reportLimits() {
  Serial.print("l="); 
  Serial.print(getLimit(MotorDirectionLeft), DEC); 
  Serial.print(";r="); 
  Serial.print(getLimit(MotorDirectionRight), DEC); 
  Serial.print(";");
}

void reportMotorSpeed() {
  Serial.print("s="); 
  Serial.print(getMotorSpeed(), DEC); 
  Serial.print(";");
}

void reportPosition() {
  int position = getPosition();
  Serial.print("p="); 
  Serial.print(position, DEC); 
  Serial.print(";");
  switch (getLimitExceptionDirection()) {
    case MotorDirectionLeft: Serial.print("x=1;"); break;
    case MotorDirectionRight: Serial.print("x=2;"); break;
    default: Serial.print("x=0;");
  }
}

void reportMotorDirection() {
  Serial.print("d=");
  MotorDirection md = getMotorDirection();
  switch (getMotorDirection()) {
    case MotorDirectionLeft: Serial.print("1"); break;
    case MotorDirectionRight: Serial.print("2"); break;
    default: Serial.print("0"); break;
  }
  Serial.print(";");
}

void reportStatus() {
  reportLimits();
  reportMotorSpeed();
  reportMotorDirection();
  reportPosition();
  Serial.println("");
}


// Read a n-digit decimal number. Max is 255.
int getDecimal(char *decStr, uint8_t n) {
  int digits = n;
  int multiplier = 1;
  int result = 0;
  while (digits-- > 0) {
    result += multiplier * (decStr[digits] - '0');
    multiplier = multiplier * 10;
  }
  return result;
}


// Command interpreter and processor
void processCommand(char *command) {
  int cmdlen = (command != NULL) ? strlen(command) : 0;
  if (cmdlen > 0)  {
    char *parm = &command[1];
    switch (command[0]) {
    case 'c': // Engage or disengage Clutch. c1 is engage. c0 disengage
      if (cmdlen < 2) Serial.println("m=Missing parm for 'c';");
      else switch(command[1]) {
        case '1': setClutch(ClutchEnabled); break;
        case '0': setClutch(ClutchDisabled); break;
        default: Serial.println("m=Bad parm for 'c';");
      } 
      break;
    case 'd': // Set motor direction. d1 d2 for left. d0 for stop.
      if (cmdlen < 2) Serial.println("m=Missing parm for 'd';");
      else switch(command[1]) {
        case '1': setMotorDirection(MotorDirectionLeft); break;
        case '2': setMotorDirection(MotorDirectionRight); break;
        case '0': setMotorDirection(MotorDirectionNeither); break;
        default: Serial.println("m=Bad parm for 'd';");
      } 
      break;
    case 's': // Set motor speed. s123 = speed 123
      if (cmdlen < 4) Serial.println("m=Missing parm for 's';");
      else setMotorSpeed((uint8_t) getDecimal(parm, 3));
      break;
    case 'l': // Set left limit. e.g. l020 - Set left limit to 20.
      if (cmdlen < 5) Serial.println("m=Missing parm for 'l';");
      else setLimit(MotorDirectionLeft, getDecimal(parm, 4));
      break;
    case 'r': // Set right limit. e.g. r200 - Set left limit to 200.
      if (cmdlen < 5) Serial.println("m=Missing parm for 'r';");
      else setLimit(MotorDirectionRight, getDecimal(parm, 4));
      break;
    case 'i': // Set status interval. i0010 means set to 10ms
      if (cmdlen < 5) Serial.println("m=Missing parm for 'i';");
      else setStatusInterval(getDecimal(parm, 4));
      break;
    default: 
      Serial.print("m=Unrecognized command:"); 
      Serial.print(command);
      Serial.println(";");
    }
  }
}

void loop() {
  unsigned long now = millis();

  // Get and process command
  if (Serial.available() > 0) {
    char *command = getCommandOrNULL(Serial.read()); 
    processCommand(command);
  }

  // Actuate motor
  readAndWritePins();

  // Possibly print reports.
  if (now < latestStatusReportTime) latestStatusReportTime = 0; // Deal with rollover (about 50 days)
  // Report motor position (limit) if it's time to do so.
  if ((now - latestStatusReportTime) >= getStatusInterval()) {
    reportStatus();
    latestStatusReportTime = now; // Update latest report time
  }
}
