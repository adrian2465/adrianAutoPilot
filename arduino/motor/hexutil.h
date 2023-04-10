/*
Adrian Vrouwenvelder
November 2022
*/
#define hexDigit2Dec(h) (((h) >= '0' && (h) <= '9') ? ((h) - '0') : ((h) | 0x20) + 10 - 'a')
// Convert a two-nibble hex value (one byte, 8 bits) to a uint8_t.
// Always expectes there to be 2 bytes at hex.
// "7f" -> 127
uint8_t hexToDec(char *hex) {
  return (hexDigit2Dec(hex[0]) << 4) + hexDigit2Dec(hex[1]);
}

#define dec2hexDigit(nibble) ((nibble) <= 9 ? (nibble) + '0' : (nibble) - 10 + 'a')
// Print a 2-digit (one byte, two nibble) hex number for an 8-bit decimal value.
void printHex(uint8_t dec) {
  Serial.print(dec2hexDigit(dec >> 4));
  Serial.print(dec2hexDigit(dec & 0x0F));
}
