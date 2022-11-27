/*
Adrian Vrouwenvelder
November 2022
*/

#define CLUTCH_PIN (11) // OUTPUT

enum ClutchStatus {ClutchDisabled, ClutchEnabled};
ClutchStatus clutchStatus = ClutchDisabled;

void initClutch() {
  pinMode(CLUTCH_PIN, OUTPUT);
}

void setClutch(ClutchStatus s) {
  if (s != clutchStatus) {
    clutchStatus = s;
    digitalWrite(CLUTCH_PIN, (clutchStatus == ClutchEnabled) ? HIGH: LOW);
  }
}
