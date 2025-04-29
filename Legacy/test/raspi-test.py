import serial
import time

ser = serial.Serial(port='/dev/ttyS0', baudrate=38400)
time.sleep(2)

data_to_send = "Hello Arduino!"
ser.write(data_to_send.encode())

ser.close()