/*
Adrian Vrouwenvelder
November 2022
March 2023
*/

bool isEchoVal = (false);

bool isEcho() {
    return isEchoVal;
}

void setEcho(bool val) {
    isEchoVal = val;
}

void echo(char *msg) {
    if (isEchoVal) Serial.print(msg);
}