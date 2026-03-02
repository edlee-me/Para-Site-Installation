/*
 * 8 Relays + 8 Dimmers (RobotDyn AC dimmer via RBDDimmer) — same serial protocol as Pico.
 * TouchDesigner → bridge (Mac) → USB serial → this sketch.
 *
 * Board: Arduino Mega. UNO: use 4 relays + 4 dimmers — see comments below.
 * RobotDyn 4ch: https://github.com/RobotDynOfficial/RBDDimmer
 */

#include <Arduino.h>
#include <RBDdimmer.h>

// --- CONFIG: Mega = 8 relays + 8 dimmers. UNO = change to 4,4 and use UNO pin arrays. ---
#define NUM_RELAYS 8
#define NUM_DIMMERS 8

// Mega: D21 = zero-cross (INT0). D54-D61 = relays. D4-D11 = dimmers.
// UNO: ZERO_CROSS_PIN 2 (INT0), RELAY_PINS {7,8,9,10}, DIMMER_PINS {3,4,5,6}, NUM_RELAYS 4, NUM_DIMMERS 4.
const int RELAY_PINS[] = {54, 55, 56, 57, 58, 59, 60, 61};
// dimmer0→D11, dimmer1→D10, dimmer2→D9, dimmer3→D8, dimmer4→D7, dimmer5→D6, dimmer6→D5, dimmer7→D4
const int DIMMER_PINS[] = {11, 10, 9, 8, 7, 6, 5, 4};

#if defined(ARDUINO_AVR_MEGA2560)
#define ZERO_CROSS_PIN 21   // Mega: INT0 is on D21 (see Arduino Mega 2560 pinout)
#else
#define ZERO_CROSS_PIN 2    // UNO etc.: INT0 is on D2
#endif

// --- RBDDimmer: one per channel. AVR: ZC must be an interrupt pin (Mega INT0=D21, UNO INT0=D2). ESP32/ESP8266: pass ZC. ---
#if defined(ARDUINO_ARCH_AVR) || defined(ARDUINO_ARCH_SAMD)
dimmerLamp dimmer0(DIMMER_PINS[0]);
dimmerLamp dimmer1(DIMMER_PINS[1]);
dimmerLamp dimmer2(DIMMER_PINS[2]);
dimmerLamp dimmer3(DIMMER_PINS[3]);
dimmerLamp dimmer4(DIMMER_PINS[4]);
dimmerLamp dimmer5(DIMMER_PINS[5]);
dimmerLamp dimmer6(DIMMER_PINS[6]);
dimmerLamp dimmer7(DIMMER_PINS[7]);
dimmerLamp* dimmers[] = {&dimmer0, &dimmer1, &dimmer2, &dimmer3, &dimmer4, &dimmer5, &dimmer6, &dimmer7};
#else
dimmerLamp dimmer0(DIMMER_PINS[0], ZERO_CROSS_PIN);
dimmerLamp dimmer1(DIMMER_PINS[1], ZERO_CROSS_PIN);
dimmerLamp dimmer2(DIMMER_PINS[2], ZERO_CROSS_PIN);
dimmerLamp dimmer3(DIMMER_PINS[3], ZERO_CROSS_PIN);
dimmerLamp dimmer4(DIMMER_PINS[4], ZERO_CROSS_PIN);
dimmerLamp dimmer5(DIMMER_PINS[5], ZERO_CROSS_PIN);
dimmerLamp dimmer6(DIMMER_PINS[6], ZERO_CROSS_PIN);
dimmerLamp dimmer7(DIMMER_PINS[7], ZERO_CROSS_PIN);
dimmerLamp* dimmers[] = {&dimmer0, &dimmer1, &dimmer2, &dimmer3, &dimmer4, &dimmer5, &dimmer6, &dimmer7};
#endif

char lineBuf[64];
uint8_t lineLen = 0;

static void setRelay(int index, int value) {
  if (index >= 0 && index < NUM_RELAYS) {
    digitalWrite(RELAY_PINS[index], value ? HIGH : LOW);
    Serial.print("relay ");
    Serial.print(index + 1);
    Serial.print(" = ");
    Serial.println(value);
  }
}

static void setDimmer(int index, float value01) {
  if (index >= 0 && index < NUM_DIMMERS) {
    int pct = (int)(value01 * 100.0f);
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    dimmers[index]->setPower(pct);
    Serial.print("dimmer ");
    Serial.print(index + 1);
    Serial.print(" = ");
    Serial.println(pct);
  }
}

static void processLine() {
  lineBuf[lineLen] = '\0';
  if (lineLen < 3) { lineLen = 0; return; }
  char cmd = lineBuf[0];
  if (cmd != 'R' && cmd != 'r' && cmd != 'D' && cmd != 'd') { lineLen = 0; return; }
  int i = 1;
  while (lineBuf[i] == ',' || lineBuf[i] == ' ') i++;
  int idx = atoi(lineBuf + i);
  while (lineBuf[i] && lineBuf[i] != ',') i++;
  if (lineBuf[i] == ',') i++;
  float val = atof(lineBuf + i);
  if (cmd == 'R' || cmd == 'r') {
    setRelay(idx - 1, (int)val ? 1 : 0);
  } else {
    setDimmer(idx - 1, (float)val);
  }
  lineLen = 0;
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_RELAYS; i++) {
    pinMode(RELAY_PINS[i], OUTPUT);
    digitalWrite(RELAY_PINS[i], LOW);
  }
  for (int i = 0; i < NUM_DIMMERS; i++) {
    dimmers[i]->begin(NORMAL_MODE, ON);
    dimmers[i]->setPower(0);
  }
  Serial.println("Relay + RobotDyn dimmer ready. Commands: R,1,1  D,1,0.75");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) processLine();
    } else if (lineLen < (int)sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    } else {
      lineLen = 0;
    }
  }
}
