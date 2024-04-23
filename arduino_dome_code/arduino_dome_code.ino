#include <MD_Parola.h>
#include <MD_MAXPanel.h>
#include <MD_MAX72xx.h>
#include <SPI.h>
#include <Servo.h>
#include <Adafruit_NeoPixel.h>
#include <nRF24L01.h>
#include <RF24.h>

#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
//#define HARDWARE_TYPE MD_MAX72XX::GENERIC_HW

#define NEOPIXELPIN   12

MD_MAXPanel myDisplay = MD_MAXPanel(HARDWARE_TYPE, 0, 1, 2, 4, 1); // DATA, CLK, CS, x devices, y devices
MD_MAXPanel myDisplay2 = MD_MAXPanel(HARDWARE_TYPE, 4, 5, 6, 3, 1);
Servo myservo;
Servo myservo2;
Servo myservo3;
Adafruit_NeoPixel pixels(7, NEOPIXELPIN, NEO_GRB + NEO_KHZ800);
RF24 radio(48, 49);  // CE, CSN
const byte address[6] = "00001";

bool flap1Open = 0;
bool flap2Open = 0;
bool flap3Open = 0;

//IMPORTANT: DON'T CONNECT ALL 3 SERVOS/HINGES AT ONCE, IT MAKES THE ARDUINO BOOTLOOP!

bool recievedCommand = false;
uint8_t command;


#define IRQ_PIN 18 //can only use specific pins for interrupts - didn't realize this and wasted a lot of time
void interruptHandler();

void setup() {
  myDisplay.begin();
  myDisplay2.begin();

  // // Set the intensity (brightness) of the display (0-15):
  myDisplay.setIntensity(5);
  myDisplay2.setIntensity(5);

  // // Clear the display:
  myDisplay.clear();
  myDisplay2.clear();

  myservo.attach(8);
  myservo2.attach(10);
  myservo3.attach(13);

  pixels.begin();

  // radio setup
  radio.begin();
  radio.openReadingPipe(1, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();

  //setup interrupt for triggering on a recieved message
  pinMode(IRQ_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(IRQ_PIN), interruptHandler, FALLING);
  radio.maskIRQ(1, 1, 0); //tx_ok, tx_fail, rx_ready (only one enabled)

  myDisplay.setPoint(22, 6, true);
  //big blue display: min-x = 1, max-x = 22, min-y = 4, max=y = 6

  //reset servos
  for (int i=65; i<=175; i++) {
    myservo.write(i);
    myservo2.write(i);
    myservo3.write(i);
    delay(10);
  }
}

int randomColour() {
  if (random(0,8) > 6) { //use an offset because for some reason it's red too often
    return 150;
  } else {
    return 0;
  }
}

bool whichTriangle = true;
void loop() {

  if (recievedCommand) {
    switch (command) {
      case 1:
        //raise and lower panel 1
        if (!flap1Open) {
          for (int i=175; i>=65; i--) {
            myservo.write(i);
            delay(3);
          }
          flap1Open = 1; 
        } else {
          for (int i=65; i<=175; i++) {
            myservo.write(i);
            delay(3);
          }
          flap1Open = 0;
        }
        break;
      case 2:
        //raise and lower panel 2
        if (!flap2Open) {
          for (int i=175; i>=65; i--) {
            myservo2.write(i);
            delay(3);
          }
          flap2Open = 1; 
        } else {
          for (int i=65; i<=175; i++) {
            myservo2.write(i);
            delay(3);
          }
          flap2Open = 0;
        }
        break;

      case 3:
        //raise and lower panel 2
        if (!flap3Open) {
          for (int i=175; i>=65; i--) {
            myservo3.write(i);
            delay(3);
          }
          flap3Open = 1; 
        } else {
          for (int i=65; i<=175; i++) {
            myservo3.write(i);
            delay(3);
          }
          flap3Open = 0;
        }
        break;
      case 4:
      //"short circuit"
        float flickerLen = 11;
        for (int i=1; i<= 50; i++) { //number of times to flicker
          myDisplay.setIntensity(15);
          myDisplay2.setIntensity(15);
          pixels.setBrightness(254);
          pixels.show();
          delay((int) (exp(flickerLen)/70));
          myDisplay.setIntensity(0);
          myDisplay2.setIntensity(0);
          pixels.setBrightness(1);
          pixels.show();
          delay((int) (exp(flickerLen)/70));
          if (i % 2 == 0 && flickerLen-1 != 0) {
            flickerLen--;
          }
        }
        myDisplay.clear();
        myDisplay2.clear();
        pixels.setBrightness(0);
        pixels.show();
        delay(3000);
        myDisplay.setIntensity(5);
        myDisplay2.setIntensity(5);
        pixels.setBrightness(254);
        pixels.show();
        break;
    }

    recievedCommand = false;
  }

  pixels.clear();

  for(int i=0; i<7; i++) {
    pixels.setPixelColor(i, pixels.Color(randomColour(), randomColour(), randomColour()));
  }
  pixels.show();


  //random vertical pattern, sweeping sideways for main blue display
  for (int x = 1; x <= 22; x++) {
    for (int y = 4; y<=6; y++) {
      myDisplay.setPoint(x, y, random(0, 2));
    }
  }

  //stacked red displays on the front
  for (int x = 1; x <= 15; x++) {
    for (int y = 1; y<=8; y++) {
      myDisplay2.setPoint(x, y, random(0, 2));
    }
  }
  if (whichTriangle) {
    for (int i=1; i<=4; i++) {
      for (int x=16; x<=24; x++) {
        for (int y = 0; y<8; y++) {
          myDisplay2.setPoint(x, y, 0); //resetting causes flickering between "frames", no easy fix
        }
      }
      delay(20);
      myDisplay2.drawCircle(20, 4, i);
    }
  } else {
    for (int i=4; i>=1; i--) {
      for (int x=16; x<=24; x++) {
        for (int y = 0; y<8; y++) {
          myDisplay2.setPoint(x, y, 0);
        }
      }
      delay(20);
      myDisplay2.drawCircle(20, 4, i);
    }
  }


  delay(300);
  for (int x=16; x<=24; x++) {
    for (int y = 0; y<8; y++) {
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
  


  //green display
  for (int x = 24; x <= 32; x++) {
    for (int y = 1; y<=8; y++) {
      myDisplay.setPoint(x, y, random(0, 2));
    }
  }

  delay(30);
}


void interruptHandler() {
  //clear the interrupt pin
  bool tx_ds, tx_df, rx_dr;
  radio.whatHappened(tx_ds, tx_df, rx_dr);

  while (radio.available()) {
    radio.read(&command, sizeof(command));
    recievedCommand = true;
  }
}
