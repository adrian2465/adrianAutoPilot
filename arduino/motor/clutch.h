/*
Adrian Vrouwenvelder
November 2022
March 2023
*/

#define CLUTCH_PIN (11) // OUTPUT

enum ClutchStatus {ClutchDisabled, ClutchEnabled};
ClutchStatus clutchStatus = ClutchDisabled;
 
ClutchStatus getClutch() {
    return clutchStatus;
}

void setClutch(ClutchStatus s) {
  if (s != clutchStatus) {
    clutchStatus = s;
    digitalWrite(CLUTCH_PIN, (clutchStatus == ClutchEnabled) ? HIGH: LOW);
  }
}

void initClutch() {
  pinMode(CLUTCH_PIN, OUTPUT);
  setClutch(ClutchDisabled); // Ensure clutch will be off initially, if not already so
}