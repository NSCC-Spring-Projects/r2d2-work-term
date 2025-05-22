#include <MD_Parola.h>              
#include <MD_MAXPanel.h>             
#include <MD_MAX72xx.h>              
#include <SPI.h>                    
#include <Servo.h>                  
#include <Adafruit_NeoPixel.h>       

// === Hardware Pin Setup ===
#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define NEOPIXELPIN 12

// === Constants for servo angles and counts === 
#define OPEN 0          // Angle to open servo flap
#define CLOSE 160        // Angle to close servo flap
#define SERVO_COUNT 3    // Number of servo motors

// Create two LED panel instances for the display
MD_MAXPanel myDisplay = MD_MAXPanel(HARDWARE_TYPE, 0, 1, 2, 4, 1);
MD_MAXPanel myDisplay2 = MD_MAXPanel(HARDWARE_TYPE, 4, 5, 6, 3, 1);

bool whichTriangle = true;  // Tracks which triangle to draw in animation

// Create NeoPixel object (7 LEDs connected to NEOPIXELPIN)
Adafruit_NeoPixel pixels(7, NEOPIXELPIN, NEO_GRB + NEO_KHZ800);

// Variables for command reception over serial
bool receivedCommand = false;
uint8_t command = 0;

// Servo objects for the 3 flaps and their open/closed state flags
Servo servos[SERVO_COUNT];
bool flapsOpen[SERVO_COUNT] = {false, false, false};

// Move a servo to a given angle
void moveServo(Servo& servo, int toAngle) {
  servo.write(toAngle);
}

// Toggle flap open/close state by index
void toggleFlap(int index) {
  if (!flapsOpen[index]) { // If flap closed, open it
    moveServo(servos[index], OPEN);
    flapsOpen[index] = true;
  } else { // Otherwise, close it
    moveServo(servos[index], CLOSE);
    flapsOpen[index] = false;
  }
}

// Close all flaps if open
void closeAllFlaps() {
  for (int i = 0; i < SERVO_COUNT; i++) {
    if (flapsOpen[i]) {
      moveServo(servos[i], CLOSE);
      flapsOpen[i] = false;
    }
  }
}

// === Wave animation variables ===
bool waveActive = false;            // Flag to track if wave sequence is running
int waveIndex = 0;                  // Current flap index being animated
bool waveOpening = true;            // True when opening flaps, false when closing
unsigned long waveLastMoveTime = 0; // Timestamp of last flap move
const unsigned long waveDelay = 300;  // Delay (ms) between flap moves

// Update function to perform one step of wave animation (called repeatedly in loop)
void updateWave() {
  if (!waveActive) return;  // Skip if wave animation inactive

  unsigned long now = millis();

  if (now - waveLastMoveTime >= waveDelay) {
    waveLastMoveTime = now;

    if (waveOpening) {
      // Open the current flap if not already open
      if (!flapsOpen[waveIndex]) {
        moveServo(servos[waveIndex], OPEN);
        flapsOpen[waveIndex] = true;
        Serial.print("Wave opening flap ");
        Serial.println(waveIndex);
      }

      waveIndex++;

      if (waveIndex >= SERVO_COUNT) {
        // All flaps opened, prepare to close in reverse order after a pause
        waveOpening = false;
        waveIndex = SERVO_COUNT - 1;  
        waveLastMoveTime = now + 500; // Half-second pause before closing
      }
    } else {
      // Close the current flap if open
      if (flapsOpen[waveIndex]) {
        moveServo(servos[waveIndex], CLOSE);
        flapsOpen[waveIndex] = false;
        Serial.print("Wave closing flap ");
        Serial.println(waveIndex);
      }

      if (waveIndex == 0) {
        // All flaps closed, end wave animation
        waveActive = false;
        Serial.println("Wave sequence complete.");
      } else {
        waveIndex--;
      }
    }
  }
}

// === Startled sequence variables ===
bool startledActive = false;       // Flag to track if startled sequence is running
unsigned long startledStartTime = 0; // Timestamp when startled sequence started

// Start startled sequence: open all flaps immediately and set timer
void startStartledSequence() {
  if (!startledActive) {
    for (int i = 0; i < SERVO_COUNT; i++) {
      if (!flapsOpen[i]) {
        moveServo(servos[i], OPEN);
        flapsOpen[i] = true;
      }
    }
    startledStartTime = millis();
    startledActive = true;
    Serial.println("Startled sequence started: all flaps opened.");
  }
}

// Update function for startled sequence: closes all flaps after 3 seconds
void updateStartled() {
  if (!startledActive) return;

  unsigned long now = millis();

  // If 3 seconds have passed since opening, close all flaps
  if (now - startledStartTime >= 3000) {
    for (int i = 0; i < SERVO_COUNT; i++) {
      if (flapsOpen[i]) {
        moveServo(servos[i], CLOSE);
        flapsOpen[i] = false;
      }
    }
    startledActive = false;
    Serial.println("Startled sequence ended: all flaps closed.");
  }
}

void stopAllSequences() {
  // Stop wave sequence if running
  if (waveActive) {
    waveActive = false;
  }
  
  // Stop startled sequence if running
  if (startledActive) {
    startledActive = false;
  }

  // Close all flaps immediately
  closeAllFlaps();

  Serial.println("All sequences stopped.");
}

// Animation state variables
unsigned long animStartTime = 0;
int animPhase = 0;
int circleRadius = 1;
bool circleGrowing = true;

// === Helper: random color for NeoPixels ===
uint8_t randomColour() {
  return random(0, 255);
}

// === Handle animation in non-blocking fashion ===
void handleAnimation() {
  unsigned long now = millis();

  switch(animPhase) {
    case 0:
      // Initialize animation frame
      pixels.clear();
      for (int i = 0; i < 7; i++) {
        pixels.setPixelColor(i, pixels.Color(randomColour(), randomColour(), randomColour()));
      }
      pixels.show();

      for (int x = 1; x <= 22; x++) {
        for (int y = 4; y <= 6; y++) {
          myDisplay.setPoint(x, y, random(0, 2));
        }
      }

      for (int x = 1; x <= 15; x++) {
        for (int y = 1; y <= 8; y++) {
          myDisplay2.setPoint(x, y, random(0, 2));
        }
      }

      circleRadius = 1;
      circleGrowing = whichTriangle;
      animStartTime = now;
      animPhase = 1;
      break;

    case 1:
      // Animate circle growing or shrinking every 50ms
      if (now - animStartTime >= 50) {
        animStartTime = now;

        // Clear circle area
        for (int x = 16; x <= 24; x++) {
          for (int y = 0; y < 8; y++) {
            myDisplay2.setPoint(x, y, 0);
          }
        }

        myDisplay2.drawCircle(20, 4, circleRadius);

        if (circleGrowing) {
          circleRadius++;
          if (circleRadius > 4) {
            animPhase = 2;
            animStartTime = now;
          }
        } else {
          circleRadius--;
          if (circleRadius < 1) {
            animPhase = 2;
            animStartTime = now;
          }
        }
      }
      break;

    case 2:
      // Pause 100ms, then draw triangle
      if (now - animStartTime >= 100) {
        // Clear circle area before drawing triangle
        for (int x = 16; x <= 24; x++) {
          for (int y = 0; y < 8; y++) {
            myDisplay2.setPoint(x, y, 0);
          }
        }

        if (whichTriangle) {
          myDisplay2.drawTriangle(20, 0, 16, 7, 24, 7);
          whichTriangle = false;
        } else {
          myDisplay2.drawTriangle(20, 7, 16, 1, 24, 1);
          whichTriangle = true;
        }

        animPhase = 3;
        animStartTime = now;
      }
      break;

    case 3:
      // Draw random dots on right side
      for (int x = 24; x <= 32; x++) {
        for (int y = 1; y <= 8; y++) {
          myDisplay.setPoint(x, y, random(0, 2));
        }
      }
      animPhase = 4;
      animStartTime = now;
      break;

    case 4:
      // Small pause before restarting animation
      if (now - animStartTime >= 30) {
        animPhase = 0;  // Restart animation
      }
      break;
  }
}

// === Setup function: initialize serial, displays, servos, LEDs ===
void setup() {
  Serial.begin(9600);
  while (!Serial);    // Wait for serial to connect (Leonardo/Micro)

  Serial.println("Arduino booting... initializing display and servos...");

  myDisplay.begin();       
  myDisplay2.begin();      

  myDisplay.setIntensity(5);
  myDisplay2.setIntensity(5);

  myDisplay.clear();       
  myDisplay2.clear();

  servos[0].attach(8);
  servos[1].attach(9);
  servos[2].attach(13);

  for (int i = 0; i < SERVO_COUNT; i++) {
  servos[i].write(CLOSE); // Force initial position
  flapsOpen[i] = false;
  delay(100);
  }

  pixels.begin();          

  myDisplay.setPoint(22, 6, true); 

  Serial.println("Setup complete. Waiting for command...");
}

// === Main loop: read commands and run animations ===
void loop() {
  // Check for new serial command and set flags accordingly
  if (Serial.available()) {
    command = Serial.read();
    receivedCommand = true;
    Serial.print("ACK: ");
    Serial.println(command, DEC);
  } else {
    // Periodically print waiting message if no command received
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 2000) {
      Serial.println("Waiting for serial command...");
      lastPrint = millis();
    }
  }

  // Process received commands
  if (receivedCommand) {
    if (command == 11) { 
      // Command 11: Close all flaps immediately
      closeAllFlaps();
    } else if (command >= 1 && command <= 3) {
      // Commands 1-3: Toggle respective flap (0-based index)
      toggleFlap(command - 1);
    } else if (command == 4) { 
      // Command 4: Start wave sequence if not already running
      closeAllFlaps();
      if (!waveActive) {
        waveActive = true;
        waveOpening = true;
        waveIndex = 0;
        waveLastMoveTime = millis();
        Serial.println("Starting wave sequence");
      }
    } else if (command == 5) { 
      // Command 5: Start startled sequence
      closeAllFlaps();
      startStartledSequence();
    }
    receivedCommand = false; 
  }

  // Run regular animation (LEDs and display)
  handleAnimation();

  // Update wave sequence if active
  updateWave();

  // Update startled sequence if active
  updateStartled();
}