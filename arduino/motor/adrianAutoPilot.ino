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
#include "echo.h"
#include "commandbuffer.h"
#include "motorController.h"
#include "clutch.h"
#include "hexutil.h"
#include "commandProcessor.h"

unsigned long latestStatusReportTime=0;
bool rebooted = true;


void setup() {
  Serial.begin(115200);
  initClutch();
  initMotor();
}


// master loop
void loop() {
  if (rebooted) {
    rebooted = false;
    Serial.println("m=REBOOTED"); // Signal to client that reinitialization may need to take place
  }
  unsigned long now = millis();

  updateStatusFn statusUpdater = NULL;

  // Get and process command
  char *command = getCommandOrNULL();
  if (command != NULL && strlen(command) > 0) statusUpdater = processCommand(command);

  // Actuate motor
  readAndWritePins();

  if (statusUpdater != NULL) statusUpdater();

  // Possibly emit position reports.
  if (now < latestStatusReportTime) latestStatusReportTime = 0; // Deal with rollover (about 50 days)
  // Report rudder position (limit) if it's time to do so.
  if ((now - latestStatusReportTime) >= getStatusInterval()) {
    reportPosition();
    latestStatusReportTime = now; // Update latest report time
  }
}
