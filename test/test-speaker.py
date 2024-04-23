
import os
import pygame
import time

os.environ["DISPLAY"] = ":0"

def play_sound(file_path):
	pygame.mixer.init()
	pygame.mixer.music.load(file_path)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy():
		pygame.time.Clock().tick(10)
		
		
def main():
	sound_file_path = "/home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2/Jedi/proc/PROC3.mp3"
	
	time.sleep(2)
	print("start playing sound")
	try:
		play_sound(sound_file_path)
	except Exception as ex:
		print(f"Error while playins sound {ex} ....")
	
	
	
if __name__ == "__main__":
	main()
