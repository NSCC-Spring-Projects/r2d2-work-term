#!/usr/bin/env python3

"""
CronTab:https://www.makeuseof.com/how-to-run-a-raspberry-pi-program-script-at-startup/
Make HC06 work: https://dev.to/ivanmoreno/how-to-connect-raspberry-pi-with-hc-05-bluetooth-module-arduino-programm-3h7a
"""

import pygame
import time
import atexit
# Communicate with serial ports on Raspberry Pi.
import serial
import random
# Motor controllers for the feet and head, respectively.
import lib.MD49 as MD49
from pysabertooth import Sabertooth
# Stuff for the LCD display.
from lib.lcd_api import LcdApi
from lib.i2c_lcd import I2cLcd
# import rf24 libraries
from pyrf24 import RF24, RF24_PA_LOW
import sys
import time
import datetime
import logging
import os
from evdev import InputDevice, categorize, ecodes, list_devices

# Configure logging
logging.basicConfig(filename='/home/pi/Desktop/r2d2-application.log',
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger
logger = logging.getLogger(__name__)

logger.info("Starting with the application logs")

# List of selected sounds
hums = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM1.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM7.mp3",
        "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM13.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM17.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM23.mp3"]
screams = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM1.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM2.mp3",
           "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM3.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM4.mp3"]
sents = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT2.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT4.mp3",
         "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT5.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT17.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT20.mp3"]
procs = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC2.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC3.mp3",
         "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC5.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC13.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC15.mp3"]

logging.info("Loaded the music files ....")

# Button mapping for controller.
aBtn = 304
bBtn = 305
xBtn = 308
yBtn = 307

# Mapping for back-side buttons
l1Btn = 310
r1Btn = 311
l2Trig = 2
r2Trig = 5

# Mapping for Left Axis
lhaxis = 0
lvaxis = 1

# Mapping for right Axis
rhaxis = 4
rvaxis = 3

# Click mode for l2 and r2 trig, which needs to be ignored.
clickL2Trig = 312
clickR2Trig = 313

logging.info("Defining the LCD constants")

# Define LCD screen
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

lcd = I2cLcd(1, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

# Testing LCD
logging.info("Going to test the LCD screen ....")
lcd.clear()
lcd.putstr("Start R2D2")
time.sleep(1)
lcd.clear()
lcd.putstr("R2D2 NSCC!")
lcd.move_to(0, 1)

logging.info("Testing successful for the LCD display ....")


# Function for clearing the second line of the display.
def clearLCDLine():
    i = 0
    while i < I2C_NUM_COLS:
        lcd.move_to(i, 1)
        lcd.putchar(" ")
        i += 1
    lcd.move_to(0, 1)


# function to translate analog axis inputs to motor speeds
def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


def getControllerName():
    while True:
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if device.name == 'Wireless Controller':
                return device.path
        print("Waiting for controller ....")
        time.sleep(2)


# Function to initialize joystick
logging.info("Going to initialize controller ....")
print("Going to initialize controller ....")
gamepad = None
while gamepad is None:
    clearLCDLine()
    lcd.putstr("WAITING FOR CTRL")
    try:
        gamepadDevice = getControllerName()
        gamepad = InputDevice(gamepadDevice)
        logging.info("Gamepad controller connnected ....")
        print("Gamepad controller connected ....")
        break
    except Exception as ex:
        logging.info(f"Exception while  connecting to gamepad {ex} ....")
        sys.exit(1)

clearLCDLine()
lcd.putstr("CTRL CONN")


# Set the serial port and baud rate based on your configuration
serial_port = '/dev/ttyS0'  # For Raspberry Pi GPIO serial
baud_rate = 38400  # Baud rate for MD49

# Initialize the serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=10)

try:
    # MD49 at
    motors = MD49.MotorBoardMD49(uartBus='/dev/ttyS0')
    motors.DisableTimeout()

    motors.SetSpeed1(140)
    motors.SetSpeed2Turn(140)
    time.sleep(2)
    motors.SetSpeed1(128)
    motors.SetSpeed2Turn(128)
except Exception as ex:
    logging.info(f"Could not connect to MD49 {ex} ....")


# Test if the motors work, giving them a little jolt.
try:
    # Sabretooth at ttyAMA2.
    saber = Sabertooth("/dev/ttyAMA3", timeout=0.1, baudrate=9600, address=128)
    saber.drive(1, 0)
    logging.info("Connected to Sabretooth controller ....")
except Exception as ex:
    logging.info(f"Could not connect to sabretooth {ex} ....")
    sys.exit(0)

# Attempt to establish a link with the head via bluetooth.
# arduinoHead = RF24(22, 0)
# headAddress  = b"00001"

# arduinoHead.begin()
# arduinoHead.open_tx_pipe(headAddress)
# arduinoHead.print_details()

# Initialize variables that describe the states of flaps and arms and stuff
# openFlap1 = True
# openFlap2 = True
# openFlap3 = True
# openFlap4 = True


forwardValue = 128
turnValue = 0
deadzone = 0.02

try:
    # An event loop in Pygame is where the majority of the program happens.
    # This is where we take key inputs and make the robot do things.
    logging.info("Entering in the pygame while loop")
    while True:
        for event in gamepad.read_loop():
            logging.info(f"Event is {event} .... ")
            print(f"Event is {event} ....")
# TODO
# joystick hotplug handling
# place holder code will be implemented later.

            if gamepad is not None:
                # If a button is pushed:
                if event.type == ecodes.EV_KEY:
                    # Triangle on PS3/ Y on X-box
                    if event.code == yBtn:
                        print("TRIANGLE | Y | HUM")
                        logging.info("TRIANGLE | Y | HUM")
                        clearLCDLine()
                        lcd.putstr("SOUND: HUM")
                        pygame.mixer.init()
                        # Choose a random sound
                        soundChoice = random.randint(0, 4)
                        # Load into memory and play.
                        # Same logic will apply every time we play a sound from now on.
                        pygame.mixer.music.load(hums[soundChoice])
                        pygame.mixer.music.play()

                    # Square on PS3/ X on X-box
                    elif event.code == xBtn:
                        print("SQUARE | X | PROC")
                        logging.info("SQUARE | X | PROC")
                        clearLCDLine()
                        lcd.putstr("SOUND: PROC")
                        pygame.mixer.init()
                        soundChoice = random.randint(0, 4)
                        pygame.mixer.music.load(procs[soundChoice])
                        pygame.mixer.music.play()

                    # Cross on PS3/ A on  X-box
                    elif event.code == aBtn:
                        print("CROSS | A | SENT")
                        logging.info("CROSS | A | SENT")
                        clearLCDLine()
                        lcd.putstr("SOUND: SENT")
                        pygame.mixer.init()
                        soundChoice = random.randint(0, 4)
                        pygame.mixer.music.load(sents[soundChoice])
                        pygame.mixer.music.play()

                    # Circle on PS3/ B on X-Box
                    elif event.code == bBtn:
                        print("CIRCLE | B | SCREAM")
                        logging.info("CIRCLE | B | SCREAM")
                        clearLCDLine()
                        lcd.putstr("SOUND: SCREAM")
                        pygame.mixer.init()
                        soundChoice = random.randint(0, 3)
                        pygame.mixer.music.load(screams[soundChoice])
                        pygame.mixer.music.play()

                    # L1 Button on the controller
                    elif event.code == l1Btn:
                        print("L1 | CANTINA")
                        logging.info("L1 | CANTINA")
                        clearLCDLine()
                        lcd.putstr("SOUND: CANTINA")
                        pygame.mixer.init()
                        pygame.mixer.music.load(
                            "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/mix/CANTINA.mp3")
                        pygame.mixer.music.play()

                    # R1 Button on the controller
                    elif event.code == r1Btn:
                        print("R1 | SHORT CIRCUIT")
                        logging.info("R1 | SHORT CIRCUIT")
                        clearLCDLine()
                        lcd.putstr("SOUND: SH.CIRC")
                        pygame.mixer.init()
                        pygame.mixer.music.load(
                            "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/mix/SHORTCKT.mp3")
                        pygame.mixer.music.play()

                    # No other button supported.
                    # Might be changed.
                    else:
                        print("Unsupported Button")
                        logging.info(
                            f"Unsupported Button in the click button else {event} ....")
                        clearLCDLine()
                        lcd.putstr("Unsupported")
                elif event.type == ecodes.EV_ABS:

                    #reset values before polling new ones  
                    headValue = 0
                    forwardValue = 128
                    turnValue = 0

                    if event.code == lhaxis:
                        logging.info("Left Horizontal axis ....")
                        logging.info(
                            f"Event on left horizontal axis is {event} ....")
                        if abs(event.value - 127) > deadzone:
                            turnValue = translate(event.value, 0, 255, -60, 60)

                    if event.code == lvaxis:
                        logging.info("Left veritical axis ....")
                        logging.info(
                            f"Event on left vertical axis is {event} ....")
                        forwardValue = event.value #speed forward
                
                        #account for stick drift by it not resetting exactly to center by adding a "deadzone"
                        if abs(event.value - 127) > deadzone:
                            forwardValue = translate(event.value, 0, 255, 66, 190) #forwards/backwards

                    if event.code == rhaxis:
                        logging.info("Right Horizontal axis ....")
                        logging.info(
                            f"Event on right horizontal axis is {event} ....")
                        if abs(event.value - 127) > deadzone:
                            headValue = translate(event.value, 0, 255, -60, 60)
                            logging.info(f"transformed value is {headValue}. Turning the saber with this value ....")

                    #account for left/right
                    leftMotorValue = forwardValue + turnValue
                    rightMotorValue = forwardValue - turnValue
            
                    #handle overshoot
                    if leftMotorValue > 254:
                        leftMotorValue = 254
                    if leftMotorValue < 1:
                        leftMotorValue = 1

                    if rightMotorValue > 254:
                        rightMotorValue = 254
                    if rightMotorValue < 1:
                        rightMotorValue = 1

                    # Finally set the motor speeds
                    # Sometimes the motor keeps rotating, filtering out the change.
                    logging.info(f"Setting speed for left motor as {leftMotorValue} and right motor as {rightMotorValue} ....")
                    motors.SetSpeed2Turn(int(rightMotorValue))
                    motors.SetSpeed1(int(leftMotorValue))
 
                    saber.drive(1, int(headValue))

                elif event.code == rvaxis:
                    pass
                elif event.code == l2Trig:
                    pass
                elif event.code == r2Trig:
                    pass
                else:
                    pass
            else:
                print("Gamepad is not connected ....")
                logging.info("Gamepad is not connected ....")
except Exception as ex:
    saber.stop()
    motors.SetSpeed1(128)
    motors.SetSpeed2Turn(128)
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("R2D2 offline!")
    lcd.move_to(0, 1)
    logging.info(f"Fatal crash error {ex} ....")
    saber.drive(1, 0)
    quit()


