/*
Adrian Vrouwenvelder
November 2022
*/
#define CMDLEN (64)

char cmdBuffer[CMDLEN] = ""; // Circular buffer for collecting serial input
char cmd[CMDLEN] = ""; // Completed null-terminated command if isCommandComplete is true.
int cmdReadIdx = 0, cmdWriteIdx=0;


// Append character to command buffer. 
// If command is complete and ready to consume, Return NULL-terminated command, without line termination (\n or \r) characters.
// If the command is incomplete or otherwise not ready to consume, return NULL .
char *getCommandOrNULL(char c) {
  if (c == '\r') return NULL; // Ignore carriage return chars.
  if (((cmdWriteIdx + 1) % CMDLEN) == cmdReadIdx) {
    Serial.println("ERR:FULLBUFF"); 
    return NULL;
  }
  cmdBuffer[cmdWriteIdx] = c;
  cmdWriteIdx = ((cmdWriteIdx + 1) % CMDLEN);
  if (c == '\n') {
    // We have a complete command - gather it and return it.
    int idx = 0;
    while (cmdReadIdx != cmdWriteIdx) {
      cmd[idx] = cmdBuffer[cmdReadIdx];
      if (cmd[idx] == '\n') cmd[idx] = '\0';
      cmdReadIdx = (cmdReadIdx + 1) % CMDLEN;
      ++idx;
    }
    return cmd;
  } else {
    cmd[0] = '\0';
    return NULL;
  }
}

