from pysabertooth import Sabertooth
import sys
import datetime
import time

try:
	saber = Sabertooth("/dev/ttyAMA3", timeout=0.1, baudrate=9600, address=128)
	saber.drive(1,40)
	time.sleep(20)
	saber.drive(1, 0)
	time.sleep(2)
	saber.drive(1,-40)
	time.sleep(20)
	saber.drive(1,0)
	saber.stop()
	#time.sleep(2)
	#saber.drive(1, 10)
	#time.sleep(5)
    
	with open('/home/pi/Desktop/test.log', 'w') as phile:
		timestamp = datetime.datetime.now()
		timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
		phile.write(timestamp_str)

    
    #time.sleep(10)
	print("Connected to Sabretooth controller")
except Exception as ex:
	print(f"Could not connect to sabretooth {ex}")
	sys.exit(0)
