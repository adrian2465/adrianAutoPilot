/*
Adrian Vrouwenvelder
April 2023
*/
#define CMDLEN (64)

char cmdBuffer[CMDLEN]; // Circular buffer for collecting serial input
char cmd[CMDLEN]; // Completed null-terminated command if isCommandComplete is true.
int cmdReadIdx = 0, cmdWriteIdx=0;
bool isEcho = false;

int nextIdx(int idx) {
  return (idx + 1) % CMDLEN;
}

// echo can be useful to debug communication issues.
bool getEcho() {
    return isEcho;
}

void setEcho(bool echo) {
    isEcho = echo;
}

bool isValidChar(char c) {
  return c == '\n' || c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c == '=';
}

// Append character to command buffer. 
// If command is complete and ready to consume, Return NULL-terminated command, without line termination (\n or \r) characters.
// If the command is incomplete or otherwise not ready to consume, return NULL .
char *getCommandOrNULL(char c) {
  if (!isValidChar(c)) {
    char errprintbuf[32];
    sprintf(errprintbuf, "m=Ignoring char '%c'", c);
    Serial.println(errprintbuf);
    return NULL;
  }
  if (nextIdx(cmdWriteIdx) == cmdReadIdx) {
    Serial.println("m=Command Buffer Full");
    return NULL;
  }
  if (c == '\n') {
      char *cp = cmd;
      // We have a complete command - copy it into cmd buffer and return it.
      while (cmdReadIdx != cmdWriteIdx) {
        *cp++ = cmdBuffer[cmdReadIdx];
        cmdReadIdx = nextIdx(cmdReadIdx);
      }
      *cp = '\0';
  } else {
      // Append character to command buffer.
      cmdBuffer[cmdWriteIdx] = c;
      cmdWriteIdx = nextIdx(cmdWriteIdx);
      return NULL;
  }
  if (isEcho) {
      char echoBuff[32];
      sprintf(echoBuff, "m=ECHO '%s'", cmd);
      Serial.println(echoBuff);
  }
  return cmd;
}

