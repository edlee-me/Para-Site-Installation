/*
 * 4 Relays + 4 Dimmers (RobotDyn AC dimmer via RBDDimmer) — same serial protocol as Pico/Mega.
 * TouchDesigner → bridge (Mac) → USB serial → this sketch.
 *
 * Board: Arduino UNO. Commands: R,1,1  D,1,0.75 (relay/dimmer 1–4).
 * RobotDyn 4ch: https://github.com/RobotDynOfficial/RBDDimmer
 *
 * Monitoring: TD must keep the port open. Read Arduino replies in TouchDesigner
 * (Serial DAT: read received data and print to Text DAT or textport), not a separate
 * serial monitor — only one process can open the port. Baud: 115200.
 */

#include <Arduino.h>
#include <RBDdimmer.h>

// --- CONFIG: UNO = 4 relays + 4 dimmers ---
#define NUM_RELAYS 4
#define NUM_DIMMERS 4

// UNO: D2 = zero-cross (fixed). D3–D6 = dimmer outputs. D7–D10 = relays.
const int RELAY_PINS[] = {7, 8, 9, 10};
const int DIMMER_PINS[] = {3, 4, 5, 6};

#define ZERO_CROSS_PIN 2

// --- RBDDimmer: one per channel. AVR (Mega/UNO): ZC fixed D2. ---
#if defined(ARDUINO_ARCH_AVR) || defined(ARDUINO_ARCH_SAMD)
dimmerLamp dimmer0(DIMMER_PINS[0]);
dimmerLamp dimmer1(DIMMER_PINS[1]);
dimmerLamp dimmer2(DIMMER_PINS[2]);
dimmerLamp dimmer3(DIMMER_PINS[3]);
dimmerLamp* dimmers[] = {&dimmer0, &dimmer1, &dimmer2, &dimmer3};
#else
dimmerLamp dimmer0(DIMMER_PINS[0], ZERO_CROSS_PIN);
dimmerLamp dimmer1(DIMMER_PINS[1], ZERO_CROSS_PIN);
dimmerLamp dimmer2(DIMMER_PINS[2], ZERO_CROSS_PIN);
dimmerLamp dimmer3(DIMMER_PINS[3], ZERO_CROSS_PIN);
dimmerLamp* dimmers[] = {&dimmer0, &dimmer1, &dimmer2, &dimmer3};
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
  Serial.println("Relay + RobotDyn dimmer ready (4ch). Commands: R,1,1  D,1,0.75");
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
