#import pygame
import serial
import time
import MD49

# Set the serial port and baud rate based on your configuration
serial_port = '/dev/ttyS0'  # For Raspberry Pi GPIO serial
baud_rate = 38400  # Baud rate for MD49

# Initialize the serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=10)

try:
    # MD49 at 
    motors = MD49.MotorBoardMD49(uartBus='/dev/ttyS0')
    print(motors)
    motors.DisableTimeout()
    motors.SetSpeed1(140)
    motors.SetSpeed2Turn(140)
        #version = motors.GetVersion()
        #print(f"version is {version} ....")
    time.sleep(5)
    motors.SetSpeed1(128)
    motors.SetSpeed2Turn(128)
except Exception as ex:
    print(f"Could not connect to MD49 {ex}")
