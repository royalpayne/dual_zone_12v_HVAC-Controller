/*
 * Whynter IR Transmitter for ESP32
 * Uses IRremoteESP8266 library for proper 38kHz carrier
 *
 * Install library: Arduino IDE -> Sketch -> Include Library -> Manage Libraries
 * Search for "IRremoteESP8266" by crankyoldgit
 */

#include <Arduino.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>

// IR LED connected to GPIO 18
const uint16_t kIrLed = 18;

IRsend irsend(kIrLed);

// Whynter power code captured from remote (NEC-like protocol)
// These are the raw timings in microseconds
uint16_t powerCode[] = {
  9075, 4568,  // Leader
  625, 548, 624, 544, 571, 598, 567, 1742,  // Data bits
  545, 650, 541, 623, 572, 1748, 603, 575,
  571, 598, 567, 1742, 545, 650, 541, 1748,
  603, 575, 571, 598, 567, 1742, 545, 1748,
  603, 1748, 571, 598, 567, 1742, 545, 650,
  541, 1748, 603, 1748, 571, 1748, 567, 1742,
  545, 650, 541, 1748, 603, 575, 571, 598,
  567, 1742, 545, 650, 541, 623, 572, 1748, 577
};

void setup() {
  Serial.begin(115200);
  irsend.begin();

  Serial.println("\n=== Whynter IR Transmitter ===");
  Serial.println("Commands:");
  Serial.println("  p - Send power toggle");
  Serial.println("  t - Test LED (steady on for 2 sec)");
  Serial.println("==============================\n");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    switch (cmd) {
      case 'p':
      case 'P':
        Serial.println("Sending POWER...");
        irsend.sendRaw(powerCode, sizeof(powerCode) / sizeof(powerCode[0]), 38);
        Serial.println("Sent!");
        break;

      case 't':
      case 'T':
        Serial.println("Testing LED for 2 seconds...");
        // Use carrier to test - should be visible on phone camera
        for (int i = 0; i < 20; i++) {
          irsend.sendRaw(powerCode, sizeof(powerCode) / sizeof(powerCode[0]), 38);
          delay(100);
        }
        Serial.println("Done!");
        break;
    }
  }
}
