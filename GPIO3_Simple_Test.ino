/*
 * Simple GPIO3 LED Matrix Test
 * Tests if GPIO3 (RX) can control the LED matrix
 * This temporarily disables Serial to free GPIO3 for output
 */

#define LED_PIN 3  // GPIO3 (RX) - your soldered connection

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== GPIO3 LED Matrix Test ===");
  Serial.println("🎯 LED matrix should be connected to GPIO3 (RX)");
  Serial.println("🔌 Check your wiring: Matrix Data Pin → GPIO3");
  delay(2000);
}

void loop() {
  Serial.println("\n--- Test Pattern 1: Simple Blinking ---");
  
  // Pattern 1: Simple blinking (2 second intervals)
  for (int i = 0; i < 3; i++) {
    Serial.println("💡 LED ON - GPIO3 HIGH");
    Serial.flush();
    Serial.end();  // Disable Serial to free GPIO3
    
    // Configure GPIO3 as output
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH);
    delay(2000);
    
    Serial.begin(115200);
    delay(100);
    Serial.println("⚫ LED OFF - GPIO3 LOW");
    Serial.flush();
    Serial.end();
    
    digitalWrite(LED_PIN, LOW);
    delay(2000);
    
    Serial.begin(115200);
    delay(100);
  }
  
  Serial.println("\n--- Test Pattern 2: Binary Data ---");
  
  // Pattern 2: Send binary pattern (like your test_pattern.bin)
  byte testPattern[] = {0xFF, 0xFF, 0xFF, 0xFF}; // Same as your file
  
  for (int i = 0; i < sizeof(testPattern); i++) {
    Serial.printf("📤 Sending byte: 0x%02X\n", testPattern[i]);
    Serial.flush();
    Serial.end();
    
    // Configure GPIO3 as output
    pinMode(LED_PIN, OUTPUT);
    
    // Send each bit (MSB first)
    for (int bit = 7; bit >= 0; bit--) {
      digitalWrite(LED_PIN, (testPattern[i] >> bit) & 0x01);
      delayMicroseconds(1000); // 1ms delay for visibility
    }
    
    delay(1000); // Wait between bytes
    
    Serial.begin(115200);
    delay(100);
  }
  
  Serial.println("\n--- Test Complete ---");
  Serial.println("🎯 If you see any LED activity, GPIO3 is working!");
  Serial.println("❌ If no LEDs light up, check wiring and power");
  Serial.println("⏳ Waiting 10 seconds before next test...");
  delay(10000);
}
