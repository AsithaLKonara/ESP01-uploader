/*
 * Simple LED Matrix Test for ESP-01
 * This sketch tests basic LED matrix output functionality
 * Connect LED matrix data pin to GPIO3 (RX)
 */

// LED Matrix Pin Configuration
#define MATRIX_DATA_PIN 3   // GPIO3 (RX) - Data pin
#define MATRIX_CLOCK_PIN 1  // GPIO1 (TX) - Clock pin (if needed)

// Test patterns
byte testPattern1[] = {0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00}; // Alternating
byte testPattern2[] = {0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80}; // Walking bit
byte testPattern3[] = {0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55}; // Checkerboard

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Simple LED Matrix Test ===");
  
  // Configure LED matrix pins
  pinMode(MATRIX_DATA_PIN, OUTPUT);
  pinMode(MATRIX_CLOCK_PIN, OUTPUT);
  digitalWrite(MATRIX_DATA_PIN, LOW);
  digitalWrite(MATRIX_CLOCK_PIN, LOW);
  
  Serial.println("LED Matrix pins configured:");
  Serial.printf("Data Pin (GPIO3): OUTPUT, LOW\n");
  Serial.printf("Clock Pin (GPIO1): OUTPUT, LOW\n");
  Serial.println("Starting test patterns...");
}

void loop() {
  // Test Pattern 1: Alternating bytes
  Serial.println("\n--- Pattern 1: Alternating (0xFF, 0x00) ---");
  sendPattern(testPattern1, sizeof(testPattern1));
  delay(2000);
  
  // Test Pattern 2: Walking bit
  Serial.println("\n--- Pattern 2: Walking bit ---");
  sendPattern(testPattern2, sizeof(testPattern2));
  delay(2000);
  
  // Test Pattern 3: Checkerboard
  Serial.println("\n--- Pattern 3: Checkerboard ---");
  sendPattern(testPattern3, sizeof(testPattern3));
  delay(2000);
  
  // Test Pattern 4: Simple counting
  Serial.println("\n--- Pattern 4: Counting 0-255 ---");
  sendCountingPattern();
  delay(3000);
  
  Serial.println("\n--- Pattern cycle complete, restarting ---");
}

// Send a pattern to the LED matrix
void sendPattern(byte* pattern, int length) {
  Serial.printf("Sending %d bytes to LED matrix...\n", length);
  
  for (int i = 0; i < length; i++) {
    byte data = pattern[i];
    Serial.printf("Byte %d: 0x%02X (", i, data);
    
    // Send each bit to the data pin
    for (int bit = 7; bit >= 0; bit--) {
      int bitValue = (data >> bit) & 0x01;
      digitalWrite(MATRIX_DATA_PIN, bitValue);
      
      // Print bit value
      Serial.print(bitValue);
      
      // Clock pulse (if needed)
      digitalWrite(MATRIX_CLOCK_PIN, HIGH);
      delayMicroseconds(10);
      digitalWrite(MATRIX_CLOCK_PIN, LOW);
      delayMicroseconds(10);
    }
    
    Serial.println(")");
    delay(100); // Small delay between bytes
  }
  
  // Reset pins
  digitalWrite(MATRIX_DATA_PIN, LOW);
  digitalWrite(MATRIX_CLOCK_PIN, LOW);
  Serial.println("Pattern sent!");
}

// Send counting pattern (0-255)
void sendCountingPattern() {
  Serial.println("Sending counting pattern 0-255...");
  
  for (int count = 0; count <= 255; count++) {
    byte data = (byte)count;
    
    // Send each bit
    for (int bit = 7; bit >= 0; bit--) {
      digitalWrite(MATRIX_DATA_PIN, (data >> bit) & 0x01);
      delayMicroseconds(100); // Slower for visibility
    }
    
    // Progress indicator every 32 counts
    if (count % 32 == 0) {
      Serial.printf("Count: %d (0x%02X)\n", count, data);
    }
    
    delay(50); // Small delay between numbers
  }
  
  digitalWrite(MATRIX_DATA_PIN, LOW);
  Serial.println("Counting pattern complete!");
}

// Alternative: WS2812-style timing (if your matrix uses that)
void sendWS2812Pattern(byte* pattern, int length) {
  Serial.println("Sending WS2812-style pattern...");
  
  for (int i = 0; i < length; i++) {
    byte data = pattern[i];
    
    for (int bit = 7; bit >= 0; bit--) {
      if ((data >> bit) & 0x01) {
        // Send '1' bit: 0.8us HIGH + 0.45us LOW
        digitalWrite(MATRIX_DATA_PIN, HIGH);
        delayMicroseconds(800);
        digitalWrite(MATRIX_DATA_PIN, LOW);
        delayMicroseconds(450);
      } else {
        // Send '0' bit: 0.4us HIGH + 0.85us LOW
        digitalWrite(MATRIX_DATA_PIN, HIGH);
        delayMicroseconds(400);
        digitalWrite(MATRIX_DATA_PIN, LOW);
        delayMicroseconds(850);
      }
    }
  }
  
  // WS2812 reset signal
  digitalWrite(MATRIX_DATA_PIN, LOW);
  delayMicroseconds(50);
  Serial.println("WS2812 pattern sent!");
}
