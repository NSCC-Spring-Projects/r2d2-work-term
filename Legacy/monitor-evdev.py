import evdev
from evdev import InputDevice

import selectors

def monitor_input_devices():
	sel = selectors.DefaultSelector()
	
	devices = [InputDevice(path) for path in evdev.list_devices()]
	print(devices)
	
	for device in devices:
		sel.register(device, selectors.EVENT_READ)
		
	while True:
		events = sel.select()
			
		for key, _ in events:
			device = key.fileobj
				
			for event in device.read():
				print(event)
					
					
def main():
	monitor_input_devices()
					
if __name__ == "__main__":
	#monitor_input_devices()
	main()
