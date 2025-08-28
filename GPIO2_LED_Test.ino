/*
 * Simple GPIO2 LED Matrix Test
 * Tests if GPIO2 can control the LED matrix
 */

#define LED_PIN 2  // GPIO2 (the pin we're using for matrix data)

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== GPIO2 LED Matrix Test ===");
  
  // Configure GPIO2 as output
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("✅ GPIO2 configured as OUTPUT");
  Serial.println("🎯 LED matrix should be connected to GPIO2");
  Serial.println("🔌 Check your wiring: Matrix Data Pin → GPIO2");
}

void loop() {
  Serial.println("\n--- Test Pattern 1: Blinking ---");
  
  // Pattern 1: Simple blinking (1 second intervals)
  for (int i = 0; i < 5; i++) {
    Serial.println("💡 LED ON");
    digitalWrite(LED_PIN, HIGH);
    delay(1000);
    
    Serial.println("⚫ LED OFF");
    digitalWrite(LED_PIN, LOW);
    delay(1000);
  }
  
  Serial.println("\n--- Test Pattern 2: Fast Pulses ---");
  
  // Pattern 2: Fast pulses (100ms intervals)
  for (int i = 0; i < 10; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
  
  Serial.println("\n--- Test Pattern 3: Binary Data ---");
  
  // Pattern 3: Send binary pattern (like matrix data)
  byte testPattern[] = {0xFF, 0x00, 0xFF, 0x00, 0xAA, 0x55, 0xAA, 0x55};
  
  for (int i = 0; i < sizeof(testPattern); i++) {
    Serial.printf("📤 Sending byte: 0x%02X\n", testPattern[i]);
    
    // Send each bit (MSB first)
    for (int bit = 7; bit >= 0; bit--) {
      digitalWrite(LED_PIN, (testPattern[i] >> bit) & 0x01);
      delayMicroseconds(1000); // 1ms delay for visibility
    }
    
    delay(500); // Wait between bytes
  }
  
  Serial.println("\n--- Test Complete ---");
  Serial.println("🎯 If you see any LED activity, GPIO2 is working!");
  Serial.println("❌ If no LEDs light up, check wiring and power");
  Serial.println("⏳ Waiting 5 seconds before next test...");
  delay(5000);
}
