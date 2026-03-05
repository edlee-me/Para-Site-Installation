/*
 * 8 Relays + 8 Dimmers — same serial protocol as Pico.
 * TouchDesigner → bridge (Mac) → USB serial → this sketch.
 * Dimmer: Dimmable Light for Arduino (lib/Dimmable Light for Arduino).
 *
 * Board: Arduino Mega. UNO: use 4 relays + 4 dimmers — see comments below.
 */

 #include <Arduino.h>
 #include <dimmable_light.h>
 
 // --- CONFIG: Mega = 8 relays + 8 dimmers. UNO = change to 4,4 and use UNO pin arrays. ---
 #define NUM_RELAYS 8
 #define NUM_DIMMERS 8
 
 // Mega: D54-D61 = relays. D4-D11 = dimmers. Zero-cross = D2 (setSyncPin).
 // UNO: RELAY_PINS {7,8,9,10}, DIMMER_PINS {3,4,5,6}, zero-cross D2.
 const int RELAY_PINS[] = {54, 55, 56, 57, 58, 59, 60, 61};
 // dimmer0→D11, dimmer1→D10, dimmer2→D9, dimmer3→D8, dimmer4→D7, dimmer5→D6, dimmer6→D5, dimmer7→D4
 const int DIMMER_PINS[] = {11, 10, 9, 8, 7, 6, 5, 4};
 
 #if defined(ARDUINO_AVR_MEGA2560) || defined(__AVR_ATmega2560__)
 #define ZERO_CROSS_PIN 2   // Mega: any interrupt pin (2,3,18,19,20,21). D2 matches examples.
 #else
 #define ZERO_CROSS_PIN 2   // UNO etc.
 #endif
 
 // Dimmable Light: one instance per output pin; brightness 0–255.
 DimmableLight dimmer0(DIMMER_PINS[0]);
 DimmableLight dimmer1(DIMMER_PINS[1]);
 DimmableLight dimmer2(DIMMER_PINS[2]);
 DimmableLight dimmer3(DIMMER_PINS[3]);
 DimmableLight dimmer4(DIMMER_PINS[4]);
 DimmableLight dimmer5(DIMMER_PINS[5]);
 DimmableLight dimmer6(DIMMER_PINS[6]);
 DimmableLight dimmer7(DIMMER_PINS[7]);
 DimmableLight* dimmers[] = {&dimmer0, &dimmer1, &dimmer2, &dimmer3, &dimmer4, &dimmer5, &dimmer6, &dimmer7};
 
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
     if (value01 <= 0.0f) {
       dimmers[index]->setBrightness(0);
     } else if (value01 >= 1.0f) {
       dimmers[index]->setBrightness(255);
     } else {
       dimmers[index]->setBrightness((uint8_t)(value01 * 255.0f));
     }
     int pct = (int)(value01 * 100.0f);
     if (pct < 0) pct = 0;
     if (pct > 100) pct = 100;
     Serial.print("dimmer ");
     Serial.print(index + 1);
     Serial.print(" = ");
     Serial.println(pct);
   }
 }
 
 static void processLine() {
   lineBuf[lineLen] = '\0';
   Serial.println(lineBuf);
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
   DimmableLight::setSyncPin(ZERO_CROSS_PIN);
   DimmableLight::begin();
   for (int i = 0; i < NUM_DIMMERS; i++) {
     dimmers[i]->setBrightness(0);
   }
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
 