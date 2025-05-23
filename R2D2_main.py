#!/usr/bin/env python3

"""
R2D2 Main Control Script - May 2025

May 23, 2025 NOTE: We did not have time time to complete all of our ToDos in this script. It's significantly better than what we received, however
there is still much room for improvement.

Resources:
CronTab:https://www.makeuseof.com/how-to-run-a-raspberry-pi-program-script-at-startup/
Make HC06 work: https://dev.to/ivanmoreno/how-to-connect-raspberry-pi-with-hc-05-bluetooth-module-arduino-programm-3h7a
"""

#TODO: Add more comments to the code
#TODO: Clean up imports
#TODO: Look into consolidating error handling
#TODO: Clean up constants and global vars.
#TODO: Look into using a config file for constants
#TODO: Look into displaying diagnostic information on the LCD
#TODO: Diagnose/Fix full forward motor cutout
#TODO: Look into retreiving battery voltage and displaying it on the LCD

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

motors = None
saber = None

# Global joystick state
global_forward_value = 128
global_turn_value = 0
global_head_value = 0

INVERT_FORWARD_AXIS = False

last_left_speed = 128
last_right_speed = 128
last_motor_update_time = 0
last_refresh_time = 0
update_interval = 0.05  # 50 ms normal update rate
refresh_interval = 1.0  # 1.0 s to refresh MD49 to prevent timeout



logging.basicConfig(filename='/home/pi/Desktop/r2d2-2025.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

#TODO: Clean up button mappings

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

# Global drive values (updated by joystick handler)
desired_forward = 0.0
desired_turn = 0.0
desired_head_value = 0.0

arduino_queue = asyncio.Queue()

# Function for clearing the second line of the display.
def clearLCDLine():
    i = 0
    while i < I2C_NUM_COLS:
        lcd.move_to(i, 1)
        lcd.putchar(" ")
        i += 1
    lcd.move_to(0, 1)

async def play_sound(sound_list, display_message):
    global lcd
    clearLCDLine()
    lcd.putstr(display_message)
    pygame.mixer.music.load(random.choice(sound_list))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)  # Yield control while waiting for the sound to finish

# TODO: integrate the R2 heads arduino & test the code
async def send_to_arduino(message, arduino_head):
    try:
        arduino_head.write((message))
        clearLCDLine()
        lcd.putstr("SENT ARDUINO")
        await asyncio.sleep(0)  # Yield control
    except Exception as e:
        logger.error(f"Error sending to Arduino: {e}")

async def saber_drive_loop(saber, get_head_value_fn, interval=0.05):
    """
    Continuously sends Saber drive commands at a safe refresh rate.
    Ensures head movement stays responsive.

    :param saber: Sabertooth controller instance
    :param get_head_value_fn: Callable that returns latest head axis value (-1.0 to 1.0)
    :param interval: Update interval in seconds (default 50ms)
    """
    logger.info("Starting Saber drive loop")

    while True:
        try:
            head_value = get_head_value_fn()
            saber.drive(1, int(head_value * 40))
        except Exception as e:
            logger.error(f"Saber drive failed: {e}")

        await asyncio.sleep(interval)

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

# Apply a stronger correction at lower speeds, tapering off at higher speeds
def calculate_drift_correction(forward_value):
    base_strength = 0.28  # Base strength of the correction
    scaled_strength = base_strength * abs(forward_value)
    return scaled_strength if forward_value >= 0 else -scaled_strength

# TODO: Adjust response curve for better low-end control
def apply_response_curve(input_value, curve_factor=1.0):  # Adjusted for finer low-end control
    sign = 1 if input_value >= 0 else -1
    return sign * (abs(input_value) ** curve_factor)

# TODO: remove magic numbers and create constants for the joystick values & deadzone
async def process_joystick(event):
    global desired_forward, desired_turn, desired_head_value

    deadzone = 5 / 128.0  # increased deadzone

    if event.code == lvaxis:
        normalized_value = (event.value - 127) / 128.0
        if INVERT_FORWARD_AXIS:
            normalized_value *= -1
        value = apply_response_curve(normalized_value, curve_factor=2.0)
        desired_forward = value if abs(normalized_value) >= deadzone else 0.0

    elif event.code == lhaxis:
        normalized_value = (event.value - 127) / 128.0
        desired_turn = apply_response_curve(normalized_value, curve_factor=2.0) if abs(normalized_value) >= deadzone else 0.0

    elif event.code == rhaxis:
        normalized_value = (event.value - 127) / 128.0
        desired_head_value = normalized_value if abs(normalized_value) >= deadzone else 0.0

    # DPAD actions, queue Arduino messages safely
    if event.code == ABS_HAT0X:
        if event.value == padLeft:
            await arduino_queue.put(bytes([4]))
        elif event.value == padRight:
            await arduino_queue.put(bytes([5]))
            asyncio.create_task(play_sound(screams, "DPAD: RIGHT"))

    elif event.code == ABS_HAT0Y:
        if event.value == padUp:
            await arduino_queue.put(bytes([1]))
            await arduino_queue.put(bytes([2]))
            await arduino_queue.put(bytes([3]))
        elif event.value == padDown:
            await arduino_queue.put(bytes([11]))


#TODO: Either do more with the MD49 polling or remove it
async def poll_md49_telemetry(motors, interval=0.5):
    logger.info("Starting MD49 telemetry polling loop")
    while True:
        try:
            volts = motors.get_volts()
            encoder1 = motors.get_encoder(1)
            encoder2 = motors.get_encoder(2)
            logger.info(f"MD49 Telemetry: Volts={volts}, Encoder1={encoder1}, Encoder2={encoder2}")
        except Exception as e:
            logger.error(f"Telemetry polling failed: {e}")
        await asyncio.sleep(interval)

#TODO: Write proper commenting / function description
async def md49_drive_loop(motors, interval=0.05):
    global desired_forward, desired_turn
    global last_left_speed, last_right_speed

    logger.info("Starting MD49 drive loop")

    while True:
        # Combine forward and turn
        left_motor = desired_forward + desired_turn
        right_motor = desired_forward - desired_turn

        # Clamp before drift correction
        left_motor = max(-1.0, min(1.0, left_motor))
        right_motor = max(-1.0, min(1.0, right_motor))

        # Apply drift correction only if going straight
        if abs(desired_forward) > 0.01 and abs(desired_turn) <= 0.01:
            correction = calculate_drift_correction(desired_forward)
            left_motor += correction
            right_motor -= correction

        # Clamp again after correction
        left_motor = max(-1.0, min(1.0, left_motor))
        right_motor = max(-1.0, min(1.0, right_motor))

        # Apply response curve
        left_motor = apply_response_curve(left_motor, curve_factor=1.0)
        right_motor = apply_response_curve(right_motor, curve_factor=1.0)

        mapped_left = int(128 + (left_motor) * 127)
        mapped_right = int(128 + (right_motor) * 127)

        if abs(desired_forward) <= 0.01 and abs(desired_turn) <= 0.01:
            if last_left_speed != 128 or last_right_speed != 128:
                motors.set_speed(1, 128)
                motors.set_speed(2, 128)
                last_left_speed = 128
                last_right_speed = 128
        else:
            if abs(mapped_left - last_left_speed) > 1:
                motors.set_speed(1, mapped_left)
                last_left_speed = mapped_left

            if abs(mapped_right - last_right_speed) > 1:
                motors.set_speed(2, mapped_right)
                last_right_speed = mapped_right

        await asyncio.sleep(interval)

#TODO: Write proper commenting / function description
async def saber_drive_loop(saber, interval=0.05):
    global desired_head_value
    logger.info("Starting Saber drive loop")

    while True:
        try:
            saber.drive(1, int(desired_head_value * 80))
        except Exception as e:
            logger.error(f"Saber drive error: {e}")
        await asyncio.sleep(interval)

#TODO: Write proper commenting / function description
async def arduino_send_loop(arduino_head):
    logger.info("Starting Arduino send loop")
    while True:
        message = await arduino_queue.get()
        try:
            arduino_head.write(message)
            clearLCDLine()
            lcd.putstr(f"SENT ARD@: {message}")
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Arduino send failed: {e}")

async def arduino_read_loop(arduino_head):
    """
    Asynchronously reads lines from the Arduino serial connection
    and logs each response with a timestamp.
    """
    logger.info("Starting Arduino read loop")

    # Non-blocking read workaround using threads
    loop = asyncio.get_event_loop()
    
    def read_line_blocking():
        try:
            line = arduino_head.readline()
            return line
        except Exception as e:
            logger.error(f"Serial read failed: {e}")
            return None

    while True:
        line = await loop.run_in_executor(None, read_line_blocking)
        if line:
            logger.info(f"Arduino: {line}")
        await asyncio.sleep(0.01)  # Prevent tight loop

#TODO: Write proper commenting / function description
#TODO: Look into why saber is undefined here (suspect not in scope)
async def main_loop(gamepad):
    async for event in gamepad.async_read_loop():
        try:
            if event.type == ecodes.EV_KEY:
                asyncio.create_task(process_event(event))
            elif event.type == ecodes.EV_ABS:
                asyncio.create_task(process_joystick(event))

        except (OSError, IOError) as ex:
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
                    motors.set_speed(1, 128)
                    motors.set_speed(2, 128)
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
                    motors.set_speed(1, 128)
                    motors.set_speed(2, 128)
                except Exception as e:
                    logger.error(f"Failed stopping motors: {e}")
            break

# Write additional commenting
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
            await asyncio.sleep(2)

    pygame.mixer.init()

    serial_port = '/dev/ttyUSB0'
    # arduino_serial_port = '/dev/ttyUSB0'
    baud_rate = 9600

    try:
        motors = MD49.MotorBoardMD49(port='/dev/ttyS0')
        motors.reset_to_defaults()
        motors.set_speed(1, 128)  
        motors.set_speed(2, 128)

        # ### REMOVE ME - TEMP TESTING ###
        # lcd.clear()
        # lcd.putstr("Testing L Motor")
        # motors.set_speed(1, 200)  # Left motor forward
        # motors.set_speed(2, 128)  # Right motor neutral
        # time.sleep(3)

        # motors.set_speed(1, 128)  # Left motor neutral
        # motors.set_speed(2, 200)  # Right motor forward
        # lcd.clear()
        # lcd.putstr("Testing R Motor")
        # time.sleep(3)

        # motors.set_speed(1, 128)  # Stop both motors
        # motors.set_speed(2, 128)
        # lcd.clear()
        # lcd.putstr("Test Complete")
        # ### REMOVE ME - TEMP TESTING ###


        logging.info(f"md49 motor controller connected: {motors}")
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
        logging.error(f"Failed to open serial to Arduino: {e}")
        arduino_head = None

    if motors:
        asyncio.create_task(md49_drive_loop(motors))
    if saber:
        asyncio.create_task(saber_drive_loop(saber))
    if arduino_head:
        asyncio.create_task(arduino_send_loop(arduino_head))
        asyncio.create_task(arduino_read_loop(arduino_head))

    await main_loop(gamepad)

if __name__ == "__main__":
    asyncio.run(main())