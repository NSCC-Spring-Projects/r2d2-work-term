#!/usr/bin/env python3

"""
CronTab:https://www.makeuseof.com/how-to-run-a-raspberry-pi-program-script-at-startup/
Make HC06 work: https://dev.to/ivanmoreno/how-to-connect-raspberry-pi-with-hc-05-bluetooth-module-arduino-programm-3h7a
"""

import asyncio
import pygame
import time
# Communicate with serial ports on Raspberry Pi.
import serial
import random
# Motor controllers for the feet and head, respectively.
import lib.MD49 as MD49
from pysabertooth import Sabertooth
# Stuff for the LCD display.
from lib.i2c_lcd import I2cLcd
import sys
import time
import logging
from evdev import InputDevice, ecodes
from evdev.ecodes import ABS_HAT0X, ABS_HAT0Y


# Constants for LCD and global variables
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

lcd = I2cLcd(1, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

# Global joystick state
global_forward_value = 128
global_turn_value = 0
global_head_value = 0

# Configure logging
logging.basicConfig(filename='/home/pi/Desktop/r2d2-2025.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger
logger = logging.getLogger(__name__)

logger.info("Starting with the application logs")

# List of selected sounds
hums = ["/home/pi/Desktop/r2d2-new/audio-files/hum/HUM1.mp3", "/home/pi/Desktop/r2d2-new/audio-files/hum/HUM7.mp3",
        "/home/pi/Desktop/r2d2-new/audio-files/hum/HUM13.mp3", "/home/pi/Desktop/r2d2-new/audio-files/hum/HUM17.mp3", "/home/pi/Desktop/r2d2-new/audio-files/hum/HUM23.mp3"]
screams = ["/home/pi/Desktop/r2d2-new/audio-files/scream/SCREAM1.mp3", "/home/pi/Desktop/r2d2-new/audio-files/scream/SCREAM2.mp3",
           "/home/pi/Desktop/r2d2-new/audio-files/scream/SCREAM3.mp3", "/home/pi/Desktop/r2d2-new/audio-files/scream/SCREAM4.mp3"]
sents = ["/home/pi/Desktop/r2d2-new/audio-files/sent/SENT2.mp3", "/home/pi/Desktop/r2d2-new/audio-files/sent/SENT4.mp3",
         "/home/pi/Desktop/r2d2-new/audio-files/sent/SENT5.mp3", "/home/pi/Desktop/r2d2-new/audio-files/sent/SENT17.mp3", "/home/pi/Desktop/r2d2-new/audio-files/sent/SENT20.mp3"]
procs = ["/home/pi/Desktop/r2d2-new/audio-files/proc/PROC2.mp3", "/home/pi/Desktop/r2d2-new/audio-files/proc/PROC3.mp3",
         "/home/pi/Desktop/r2d2-new/audio-files/proc/PROC5.mp3", "/home/pi/Desktop/r2d2-new/audio-files/proc/PROC13.mp3", "/home/pi/Desktop/r2d2-new/audio-files/proc/PROC15.mp3"]
starwars = ["/home/pi/Desktop/r2d2-new/audio-files/starwars/ALARM9.mp3", "/home/pi/Desktop/r2d2-new/audio-files/starwars/MISC14.mp3"]

# Button mapping for controller.
aBtn = 304
bBtn = 305
xBtn = 307
yBtn = 308

# Mapping for back-side buttons
l1Btn = 310
r1Btn = 311
l2Trig = 10
r2Trig = 9

# Mapping for Left Axis
lhaxis = 0
lvaxis = 1

# Mapping for right Axis
rhaxis = 2
rvaxis = 5

# Click mode for l2 and r2 trig, which needs to be ignored.
clickL2Trig = 312
clickR2Trig = 313

# mapping for D-Pad
padLeft = -1
padRight = 1
padUp = -1
padDown = 1

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

async def play_sound(sound_list, display_message):
    global lcd
    clearLCDLine()
    lcd.putstr(display_message)
    pygame.mixer.music.load(random.choice(sound_list))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)  # Yield control while waiting for the sound to finish

async def send_to_arduino(message, arduino_head):
    try:
        arduino_head.write((message))
        clearLCDLine()
        lcd.putstr("SENT ARDUINO")
        await asyncio.sleep(0)  # Yield control
    except Exception as e:
        logger.error(f"Error sending to Arduino: {e}")

async def process_event(event):
    global lcd
    if event.type == ecodes.EV_KEY:
        if event.code == yBtn:
            asyncio.create_task(play_sound(hums, "SOUND: HUM"))
        elif event.code == xBtn:
            asyncio.create_task(play_sound(procs, "SOUND: PROC"))
        elif event.code == aBtn:
            asyncio.create_task(play_sound(sents, "SOUND: SENT"))
        elif event.code == bBtn:
            asyncio.create_task(play_sound(["/home/pi/Desktop/r2d2-new/audio-files/mix/ANNOYED.mp3"], "SOUND: ANNOYED"))
        elif event.code == l1Btn:
            asyncio.create_task(play_sound(["/home/pi/Desktop/r2d2-new/audio-files/mix/CANTINA.mp3"], "SOUND: CANTINA"))
        elif event.code == r1Btn:
            asyncio.create_task(play_sound(screams, "SOUND: SCREAM"))
        else:
            logging.info(f"Unsupported Button: {event}")
            lcd.putstr("Unsupported")

async def process_joystick(event, motors, saber, arduino_head):
    global global_forward_value, global_turn_value, global_head_value
    deadzone = 10

    if event.code == lhaxis:
        if abs(event.value - 127) > deadzone:
            global_turn_value = translate(event.value, 0, 255, -60, 60)
        else:
            global_turn_value = 0
    if event.code == lvaxis:
        if abs(event.value - 127) > deadzone:
            global_forward_value = translate(event.value, 0, 255, 66, 190)
        else:
            global_forward_value = 128
    if event.code == rhaxis:
        if abs(event.value - 127) > deadzone:
            global_head_value = translate(event.value, 0, 255, -40, 40)
        else:
            global_head_value = 0
    # mapping for values on the D-Pad
    if event.code == ABS_HAT0X:
        if event.value == padLeft:
            asyncio.create_task(send_to_arduino(bytes([1]), arduino_head))
        elif event.value == padRight:
            asyncio.create_task(play_sound(screams, "DPAD: RIGHT"))
    elif event.code == ABS_HAT0Y:
        if event.value == padUp:
            asyncio.create_task(play_sound(sents, "DPAD: UP"))
        elif event.value == padDown:
            asyncio.create_task(play_sound(procs, "DPAD: DOWN"))

    # Now use the latest values to drive
    leftMotorValue = max(1, min(254, global_forward_value + global_turn_value))
    rightMotorValue = max(1, min(254, global_forward_value - global_turn_value))

    if motors:
        motors.SetSpeed2Turn(int(rightMotorValue))
        motors.SetSpeed1(int(leftMotorValue))
    if saber:
        saber.drive(1, int(global_head_value))


async def main_loop(gamepad, gamepad_path, motors, saber, arduino_head):
    while True:
        try:
            async for event in gamepad.async_read_loop():
                logging.info(f"Received event: {event}")
                if event.type == ecodes.EV_KEY:
                    asyncio.create_task(process_event(event))
                elif event.type == ecodes.EV_ABS:
                    asyncio.create_task(process_joystick(event, motors, saber, arduino_head))
        except (OSError, IOError) as ex:
            # Gamepad likely disconnected
            logger.warning(f"Gamepad disconnected: {ex}")
            lcd.clear()
            lcd.putstr("CTRL LOST")

            # Stop motors and saber safely
            if saber:
                try:
                    saber.drive(1, 0)
                except Exception as e:
                    logger.error(f"Failed stopping saber: {e}")
            if motors:
                try:
                    motors.SetSpeed1(128)
                    motors.SetSpeed2Turn(128)
                except Exception as e:
                    logger.error(f"Failed stopping motors: {e}")

            # Try to reconnect
            gamepad = None
            while gamepad is None:
                try:
                    lcd.clear()
                    lcd.putstr("WAITING FOR CTRL")
                    gamepad = InputDevice(gamepad_path)
                    lcd.clear()
                    lcd.putstr("CTRL CONNECTED")
                except Exception:
                    await asyncio.sleep(2)
        except Exception as ex:
            logger.exception(f"Unexpected exception in main loop: {ex}")
            lcd.clear()
            lcd.putstr("R2D2 offline!")
            if saber:
                try:
                    saber.drive(1, 0)
                except Exception as e:
                    logger.error(f"Failed stopping saber: {e}")
            if motors:
                try:
                    motors.SetSpeed1(128)
                    motors.SetSpeed2Turn(128)
                except Exception as e:
                    logger.error(f"Failed stopping motors: {e}")
            break  # Break only on unexpected non-recoverable error



async def main():
    gamepad_path = '/dev/input/event6'

    while True:
        try:
            lcd.clear()
            lcd.putstr("WAITING FOR CTRL")
            gamepad = InputDevice(gamepad_path)
            lcd.clear()
            lcd.putstr("CTRL CONNECTED")
            break
        except Exception:
            logger.info("Waiting for controller...")
            await asyncio.sleep(2)

    pygame.mixer.init()

    motors = None
    saber = None
    # Set the serial port and baud rate based on your configuration
    serial_port = '/dev/ttyACM0'
    baud_rate = 9600
    
    try:
        motors = MD49.MotorBoardMD49(uartBus='/dev/ttyS0')
        motors.DisableTimeout()
        motors.SetSpeed1(128)
        motors.SetSpeed2Turn(128)
    except Exception as e:
        logger.error(f"Error connecting to MD49: {e}")

    try:
        saber = Sabertooth("/dev/ttyAMA3", timeout=0.1, baudrate=9600, address=128)
        saber.drive(1, 50)
        await asyncio.sleep(0.2)
        saber.drive(1, -50)
        await asyncio.sleep(0.2)
        asyncio.create_task(play_sound(starwars, "SOUND: STARWARS"))
        saber.drive(1, 0)
    except Exception as e:
        logger.error(f"Error connecting to Sabertooth: {e}")

    # Initialize the serial connection
    try:
        arduino_head = serial.Serial(serial_port, baud_rate, timeout=10)
        await asyncio.sleep(2)
    except Exception as e:
        logging.error(f" Failed to open serial to Arduino: {e}")
        arduino_head = None

    await main_loop(gamepad, gamepad_path, motors, saber, arduino_head)


if __name__ == "__main__":
    asyncio.run(main())
