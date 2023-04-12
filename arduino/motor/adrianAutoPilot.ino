/*
Adrian Vrouwenvelder
April 2023

Code is designed for Arduino Nano.
Code is designed to operate with the PWM-based IBT-2 Motor Control Board.
 
This motorcontroller is ascii-command driven. 
Commands are single-letter, followed by one or more parameters.
Commands are terminated by newlines ('\n').
All other characters are ignored.

*/
 
#include "commandbuffer.h"
#include "motorController.h"
#include "clutch.h"
#include "hexutil.h"

unsigned long latestStatusReportTime=0;
bool rebooted = true;
char printbuf[80];

void setup() {
  // Serial.begin(9600);
  Serial.begin(115200);
  initClutch();
  initMotor();
}

void reportLimits() {
  sprintf(printbuf, "l=%04d\nr=%04d\n", getLimit(MotorDirectionLeft), getLimit(MotorDirectionRight));
  Serial.print(printbuf);
}

void reportMotorSpeed() {
  sprintf(printbuf, "s=%03d\n", getMotorSpeed());
  Serial.print(printbuf);
}

void reportClutchStatus() {
  if (getClutch() == ClutchEnabled)
    Serial.print("c=1\n")
  else
    Serial.print("c=0\n")
}

void reportMotorDirection() {
  MotorDirection md = getMotorDirection();
  switch (getMotorDirection()) {
    case MotorDirectionLeft: Serial.print("d=1\n"); break;
    case MotorDirectionRight: Serial.print("d=2\n"); break;
    default: Serial.print("d=0\n"); break;
  }
}

void reportPosition() {
  sprintf(printbuf, "p=%04d\n", getPosition());
  Serial.print(printbuf);
  switch (getLimitFaultDirection()) {
    case MotorDirectionLeft: Serial.print("x=1\n"); break;
    case MotorDirectionRight: Serial.print("x=2\n"); break;
    default: Serial.print("x=0\n ");
  }
}

void reportEchoStatus() {
  if (getEcho())
    Serial.print("e=1\n")
  else
    Serial.print("e=0\n")
}

void reportStatus() {
  reportClutchStatus();
  reportLimits();
  reportMotorSpeed();
  reportMotorDirection();
  reportPosition();
  reportEchoStatus();
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
    char *parm = &command[1];
    int parmlen = str(parm);
    switch (command[0]) {
    case 'c': // Engage or disengage Clutch. c1 is engage. c0 disengage
      if (parmlen != 1) {
        sprintf(printbuf, "m=Wrong parm length for 'c' Expected 1 but got %d\n", parmlen);
        Serial.print(printbuf);
      }
      else switch(*parm) {
        case '1': setClutch(ClutchEnabled); break;
        case '0': setClutch(ClutchDisabled); break;
        default: {
            sprintf(printbuf, "m=Bad parm for 'c'. Expected 0 or 1 but got %d\n", *parm)
            Serial.print(printbuf);
        }
      } 
      break;
    case 'd': // Set motor direction. d1 d2 for left. d0 for stop.
      if (parmlen != 1) {
           sprintf(printbuf, "m=Wrong parm length for 'd' Expected 1 but got %d\n", parmlen);
           Serial.print(printbuf);
      }
      else switch(*parm) {
        case '1': setMotorDirection(MotorDirectionLeft); break;
        case '2': setMotorDirection(MotorDirectionRight); break;
        case '0': setMotorDirection(MotorDirectionNeither); break;
        default: {
            sprintf(printbuf, "m=Bad parm for 'd'.  Expected 0, 1, or 2 but got %c\n", *parm)
            Serial.print(printbuf);
        }
      } 
      break;
    case 's': // Set motor speed. s123 = speed 123
      if (parmlen != 3) {
           sprintf(printbuf, "m=Wrong parm length for 's' Expected 3 but got %d\n", parmlen);
           Serial.print(printbuf);
      }
      else {
        uint8_t val = (uint8_t) getDecimal(parm, 3);
        if (val > 255) {
            sprintf(printbuf, "m=Invalid value for 's'. Expected s < 255 but got %d\n", val);
            Serial.print(printbuf);
        } else {
            setMotorSpeed(val);
        }
      }
      break;
    case 'l': // Set left limit. e.g. l0020 - Set left limit to 20.
      if (parmlen != 4) {
           sprintf(printbuf, "m=Wrong parm length for 'l' Expected 4 but got %d\n", parmlen);
           Serial.print(printbuf);
      }
      else {
        int val = getDecimal(parm, 4);
        if (val < 0 || val > 1023) {
            sprintf(printbuf, "m=Invalid value for 'l'. Expected 0 <= l <= 1023 but got %d\n", val);
            Serial.print(printbuf);
        } else {
            setLimit(MotorDirectionLeft, val);
        }
      }
      break;
    case 'r': // Set right limit. e.g. r0200 - Set left limit to 200.
      if (parmlen != 4) {
           sprintf(printbuf, "m=Wrong parm length for 'r' Expected 4 but got %d\n", parmlen);
           Serial.print(printbuf);
      }
      else {
        int val = getDecimal(parm, 4);
        if (val < 0 || val > 1023) {
            sprintf(printbuf, "m=Invalid value for 'r'. Expected 0 <= r <= 1023 but got %d\n", val);
            Serial.print(printbuf);
        } else {
            setLimit(MotorDirectionRight, val);
        }
      }
      break;
    case 'i': // Set status interval. i0010 means set to 10ms
      if (parmlen != 4) {
           sprintf(printbuf, "m=Wrong parm length for 'i' Expected 4 but got %d\n", parmlen);
           Serial.print(printbuf);
      }
      else {
        int val = getDecimal(parm, 4);
        if (val < 0 || val > 9999) {
            sprintf(printbuf, "m=Invalid value for 'i'. Expected 0 <= i <= 9999 but got %d\n", val);
            Serial.print(printbuf);
        } else {
            setStatusInterval(val);
        }
      }
      break;
    case 'e': // echo command
       if (parmlen != 1) {
         sprintf(printbuf, "m=Wrong parm length for 'e' Expected 1 but got %d\n", parmlen);
         Serial.print(printbuf);
       }
       else switch(*parm) {
         case '1': setEcho(true); break;
         case '0': setEcho(false); break;
         default: {
             sprintf(printbuf, "m=Bad parm for 'e'. Expected 0 or 1 but got %d\n", *parm)
             Serial.print(printbuf);
         }
       }
       break;
    default:
      Serial.print("m=Unrecognized command: ");
      Serial.println(command);
    }
}

// master loop
void loop() {
  if (rebooted) {
    rebooted = false;
    Serial.println("m=REBOOTED"); // Signal to client that reinitialization may need to take place
  }
  unsigned long now = millis();

  // Get and process command
  if (Serial.available() > 0) {
    char *command = getCommandOrNULL(Serial.read()); 
    if (command != NULL && strlen(command) > 0) {
        processCommand(command);
    }
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
