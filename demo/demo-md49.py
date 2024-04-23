import pygame
import serial
import time

# Set the serial port and baud rate based on your configuration
serial_port = '/dev/ttyS0'  # For Raspberry Pi GPIO serial
baud_rate = 38400  # Baud rate for MD49

# Initialize the serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Initialize the pygame joystick module
pygame.init()
pygame.joystick.init()

# Connect to the first available joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

def md49_set_speed(speed1, speed2):
    # Send speed commands to MD49
    cmd = f"{speed1:03}{speed2:03}\r"
    ser.write(cmd.encode())

try:
    print("MD49 Control with PS3 Joystick")

    while True:
        for event in pygame.event.get():
            print(f"Event is {event} ....")
            if event.type == pygame.JOYAXISMOTION:
                # The PS3 joystick has two axes for each joystick, one for X and one for Y
                # Adjust the axis numbers based on your controller
                if event.axis == 0:
                    # Left joystick X-axis
                    speed1 = int(50 * joystick.get_axis(0))
                    speed2 = int(50 * joystick.get_axis(1))

                    md49_set_speed(speed1, speed2)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    # Stop the motors when the script is interrupted
    md49_set_speed(0, 0)
    ser.close()
    pygame.quit()
