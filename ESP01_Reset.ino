#include <ESP8266WiFi.h>

void setup() {
  Serial.begin(115200);
  Serial.println("ESP01 Reset Sketch - Forcing Complete Restart");
  Serial.println("This will reset the ESP01 completely...");
  
  // Force a complete restart
  delay(1000);
  Serial.println("Restarting ESP01 in 3 seconds...");
  delay(1000);
  Serial.println("Restarting ESP01 in 2 seconds...");
  delay(1000);
  Serial.println("Restarting ESP01 in 1 second...");
  delay(1000);
  
  Serial.println("FORCING RESTART NOW!");
  ESP.restart();
}

void loop() {
  // This should never execute
  Serial.println("ERROR: ESP01 did not restart!");
  delay(1000);
}
