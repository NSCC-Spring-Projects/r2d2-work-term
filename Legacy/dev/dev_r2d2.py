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
#import rf24 libraries
from pyrf24 import RF24, RF24_PA_LOW
import sys
import time
import datetime
import logging
import os

# Configure logging
logging.basicConfig(filename='/home/pi/Desktop/r2d2-application.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger
logger = logging.getLogger(__name__)
	
logger.info("Starting with the application logs")

#List of selected sounds
hums = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM1.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM7.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM13.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM17.mp3","/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/hum/HUM23.mp3"]
screams = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM1.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM2.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM3.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/scream/SCREAM4.mp3"]
sents = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT2.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT4.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT5.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT17.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/sent/SENT20.mp3"]
procs = ["/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC2.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC3.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC5.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC13.mp3", "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC15.mp3"]

logging.info("Loaded the music files ....")
	
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
lcd.move_to(0,1)

logging.info("Testing successful for the LCD display ....")


# Function for clearing the second line of the display.
def clearLCDLine():
	i = 0
	while i < I2C_NUM_COLS:
		lcd.move_to(i, 1)
		lcd.putchar(" ")
		i += 1
	lcd.move_to(0, 1)
    

#function to translate analog axis inputs to motor speeds    
def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)
    

# Function to initialize joystick
def initialize_joystick():
    pygame.joystick.init()
    joystick_count = pygame.joystick.get_count()
    if joystick_count == 0:
        logging.info("No controller found. Waiting for controller to be connected ...")
        time.sleep(2)
        return None
    else:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        logging.info("Joystick Initialized ....")
        clearLCDLine()
        lcd.putstr("CTRL CONN")
        return joystick
        
        
# Initialize the pygame window. Key inputs will be picked up by
# it and get translated into commands.
logging.info("before pygame init")
#os.putenv('SDL_VIDEODRIVER', 'dummy')

logging.info("Dummy display init ")
#os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()
logging.info("after pygame intit")
screen = pygame.display.set_mode((400,400))

# Initialize joystick
joystick = initialize_joystick()

if joystick is None:
    # Wait for joystick to be connected
	lcd.putstr("WAITING FOR CTRL")
	while joystick is None:
		pygame.event.get()
		joystick = initialize_joystick()


# Set the serial port and baud rate based on your configuration
serial_port = '/dev/ttyS0'  # For Raspberry Pi GPIO serial
baud_rate = 38400  # Baud rate for MD49

# Initialize the serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=10)

try:
    # MD49 at 
    motors = MD49.MotorBoardMD49(uartBus='/dev/ttyS0')
    motors.DisableTimeout()

    motors.SetSpeed1(240)
    motors.SetSpeed2Turn(240)
    time.sleep(2)
    motors.SetSpeed1(128)
    motors.SetSpeed2Turn(128)
        #motors.SetSpeed2Turn(128)
        #version = motors.GetVersion()
        #print(f"version is {version} ....")
        #time.sleep(5)
except Exception as ex:
    logging.info(f"Could not connect to MD49 {ex} ....")


# Test if the motors work, giving them a little jolt.
try:
    #md49_set_speed(speed1, speed2)
    # Sabretooth at ttyAMA2.
    saber = Sabertooth("/dev/ttyAMA3", timeout=0.1, baudrate=9600, address=128)
    saber.drive(1,0)
    logging.info("Connected to Sabretooth controller ....")
except Exception as ex:
	logging.info(f"Could not connect to sabretooth {ex} ....")
	sys.exit(0)
    
logging.info("After sabretooth ....")

# Attempt to establish a link with the head via bluetooth.
#arduinoHead = RF24(22, 0)
#headAddress  = b"00001"

#arduinoHead.begin()
#arduinoHead.open_tx_pipe(headAddress)
#arduinoHead.print_details()

# Initialize variables that describe the states of flaps and arms and stuff
# openFlap1 = True
# openFlap2 = True
# openFlap3 = True
# openFlap4 = True
#joystick = 0


forwardValue = 128
turnValue = 0
deadzone = 0.02

try:
    # An event loop in Pygame is where the majority of the program happens.
    # This is where we take key inputs and make the robot do things.
	logging.info("Entering in the pygame while loop")
	while True:
		for event in pygame.event.get():
			logging.info(f"Event is {event} .... ")
            #joystick hotplug handling
			if event.type == pygame.JOYDEVICEADDED:
				logging.info(f"Add device event {event} ....")
                # This event will be generated when the program starts for every
                # joystick, filling up the list without needing to create them manually.
                #joy = pygame.joystick.Joystick(0)
                #joy.init()
				joystick = initialize_joystick()
                #joystick.init()
				try:
					clearLCDLine()
					logging.info("CONTROLLER CONNECTED")
					clearLCDLine()
					lcd.putstr("CTRL CONN +")
				except Exception as ex:
					print(f"something wrong with lcd display :- {ex} ....")


			if event.type == pygame.JOYDEVICEREMOVED:
				logging.info(f"Remove device event {event} ....")
				joystick = 0
				try:
					clearLCDLine()
					logging.info("Disconnected controller ....")
					clearLCDLine()
					lcd.putstr("CTRL DCONN")
				except Exception as ex:
					logging.info(f"Something wrong with lcd display:- {ex} ....")
			logging.info(f"Joystick is {joystick} ....")
			if joystick != 0:
				# If a button is pushed:
				if event.type == pygame.JOYBUTTONDOWN:
					#Triangle on PS3
					if event.button == 2:
						logging.info("TRIANGLE | HUM")
						clearLCDLine()
						lcd.putstr("SOUND: HUM")
						pygame.mixer.init()
						# Choose a random sound
						soundChoice = random.randint(0, 4)
						# Load into memory and play.
						# Same logic will apply every time we play a sound from now on.
						pygame.mixer.music.load(hums[soundChoice])
						pygame.mixer.music.play()
                    
					# Square on PS3
					elif event.button == 3:
						logging.info("SQUARE | PROC")
						clearLCDLine()
						lcd.putstr("SOUND: PROC")
						pygame.mixer.init()
						soundChoice = random.randint(0, 4)
						pygame.mixer.music.load(procs[soundChoice])
						pygame.mixer.music.play()
                    
					# Cross on PS3
					elif event.button == 0:
						logging.info("CROSS | SENT")
						clearLCDLine()
						lcd.putstr("SOUND: SENT")
						pygame.mixer.init()
						soundChoice = random.randint(0, 4)
						pygame.mixer.music.load(sents[soundChoice])
						pygame.mixer.music.play()
                    
					# Circle on PS3
					elif event.button == 1:
						logging.info("CIRCLE | SCREAM")
						clearLCDLine()
						lcd.putstr("SOUND: SCREAM")
						pygame.mixer.init()
						soundChoice = random.randint(0, 3)
						pygame.mixer.music.load(screams[soundChoice])
						pygame.mixer.music.play()
                        
					elif event.button == 13:
						logging.info("D-PAD UP")
						toSend = 1
						result = arduinoHead.write(toSend.to_bytes(5, 'little'))
						if not result:
							logging.info("Transaction failed")
						else:
							logging.info("Transaction successful")
						time.sleep(1)                   

					elif event.button == 15:
						logging.info("D-PAD LEFT")
						toSend = 2
						result = arduinoHead.write(toSend.to_bytes(5, 'little'))
						if not result:
							logging.info("Transaction failed")
						else:
							logging.info("Transaction successful")
						time.sleep(1)
                    
					elif event.button == 14:
						logging.info("D-PAD DOWN")
						toSend = 3
						result = arduinoHead.write(toSend.to_bytes(5, 'little'))
						if not result:
							logging.info("Transaction failed")
						else:
							logging.info("Transaction successful")
						time.sleep(1)
                        
					elif event.button == 16:
						logging.info("D-PAD RIGHT")
						toSend = 4
						result = arduinoHead.write(toSend.to_bytes(5, 'little'))
						if not result:
							logging.info("Transaction failed")
						else:
							logging.info("Transaction successful")
						time.sleep(1)
                        
					elif event.button == 8:
						logging.info("SELECT | CANTINA")
						clearLCDLine()
						lcd.putstr("SOUND: CANTINA")
						pygame.mixer.init()
						pygame.mixer.music.load("/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/mix/CANTINA.mp3")
						pygame.mixer.music.play()
                    
					elif event.button == 10:
						logging.info("PS button | ANNOYED")
						pygame.mixer.init()
						pygame.mixer.music.load("/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/mix/ANNOYED.mp3")
						pygame.mixer.music.play()
                        
					elif event.button == 9:
						logging.info("START | SHORT CIRCUIT")
						clearLCDLine()
						lcd.putstr("SOUND: SH.CIRC")
						pygame.mixer.init()
						pygame.mixer.music.load("/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/mix/SHORTCKT.mp3")
						pygame.mixer.music.play()
				elif event.type == pygame.JOYAXISMOTION:
                    
					#reset values before polling new ones  
					headValue = 0
					forwardValue = 128
					turnValue = 0
                    
					forwardValue += translate(joystick.get_axis(5), -1, 1, 128, 1) #speed forward
					forwardValue -= translate(joystick.get_axis(2), -1, 1, 128, 1) #speed backwards
                    
                    #account for stick drift by it not resetting exactly to center by adding a "deadzone"
					if joystick.get_axis(1) > deadzone or joystick.get_axis(1) < -1*deadzone:
						forwardValue = translate(joystick.get_axis(1), -1, 1, 66, 190) #forwards/backwards
						logging.info(f"forward vallue is {forwardValue} ....")
                        
					if joystick.get_axis(0) > deadzone or joystick.get_axis(0) < -1*deadzone:
						turnValue = translate(joystick.get_axis(0), -1, 1, -80, 80)
						logging.info(f"turnValue is {turnValue} ....")
                        
					if joystick.get_axis(3) > deadzone or joystick.get_axis(3) < -1*deadzone:
						headValue = translate(joystick.get_axis(3), 1, -1, -99, 99)
						logging.info(f"headValue is {headValue} ....")
                        
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
                        
                    #send commands to motors
                    #print(f" Right motor value being set {rightMotorValue} ....")
                    #print(f"Left motor value being set {leftMotorValue} ....")
					motors.SetSpeed2Turn(int(rightMotorValue))
					motors.SetSpeed1(int(leftMotorValue))
					saber.drive(1, int(headValue))
    
                    
            # Kill everything when you press X.
			if event.type == pygame.QUIT:
                #saber.stop()
				pygame.quit()
                # Notify user
				lcd.clear()
				lcd.move_to(0,0)
				lcd.putstr("R2D2 offline!")
				quit()
except Exception as ex:
	saber.stop()
	motors.SetSpeed1(128)
	motors.SetSpeed2Turn(128)
	lcd.clear()
	lcd.move_to(0,0)
	lcd.putstr("R2D2 offline!")
	lcd.move_to(0,1)
	lcd.putstr(f"{ex}")
	logging.info(f"Fatal crash error {ex} ....")
	pygame.quit()
	saber.drive(1, 0)
quit()
