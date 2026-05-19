#include <Arduino.h>
#include <ACS712.h>

#define ACS_PIN 34
#define RELAY_PIN 25       // Relay control pin
#define VREF 3.3
#define ADC_RES 4095
#define ACS_SENSITIVITY 100
#define SAMPLE_COUNT 100
#define DEAD_BAND 0.03

ACS712 sensor(ACS_PIN, VREF, ADC_RES, ACS_SENSITIVITY);
float zeroOffset = 0;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Relay OFF initially (load powered, NO contact)

  delay(1000);
  sensor.autoMidPointDC(1000);
  zeroOffset = sensor.mA_DC(200) / 1000.0;
}

void loop() {
  // --- Current sensing ---
  float mA = sensor.mA_DC(SAMPLE_COUNT);
  float currentA = mA / 1000.0 - zeroOffset;
  if (fabs(currentA) < DEAD_BAND) currentA = 0;
  Serial.println(currentA, 3);  // Send current to PC
  delay(500);

  // --- Check for relay commands from PC ---
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "R0") {          // Relay OFF (isolate load)
      digitalWrite(RELAY_PIN, LOW);  // energize relay coil
      Serial.println("ACK: Relay OFF");
    } 
    else if (cmd == "R1") {     // Relay ON (restore load)
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("ACK: Relay ON");
    }
  }
}
