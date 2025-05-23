
# R2D2 IoT Project (May 2025)

This repository contains the control code for a custom-built, interactive R2D2 droid. The project is split into two main components: the **body**, which houses the drive systems and speakers, and the **dome** (head), which contains servos, LED arrays, and additional display logic. The body is controlled via a **Raspberry Pi 4**, and the dome is managed by an **Arduino Mega**, with serial communication between them routed through a **slip-ring**.

---

## 📦 Project Structure

### 1. **Body (Base Platform)**
- **Controller:** Raspberry Pi 4 running PiOS
- **Language:** Python 3
- **Startup:** Automatically runs the main control script via crontab on boot
- **Motor Control:** 
  - *MD49* motor controller for differential drive wheels
  - *Sabertooth* controller for dome rotation
- **Audio Playback:** Randomized soundboard functionality using `pygame`
- **Input:** Gamepad (mapped via `evdev`)
- **Displays:** LCD for status readouts
- **Logging:** All events logged to `~/Desktop/r2d2-2025.log`

### 2. **Dome (Head Unit)**
- **Controller:** Arduino Mega
- **Display:**
  - Matrix LED panels using MD_MAXPanel / MD_MAX72XX
  - Neopixel RGB LEDs
- **Motion:**
  - 3x servo flaps
  - Custom animation patterns
- **Wireless Receiver:** NRF24L01 with IRQ interrupt-based control
- **Communication:** Serial input from the Raspberry Pi via slip-ring

---

## 🚀 Getting Started

### Raspberry Pi Setup
1. **PiOS Required:** Ensure PiOS is installed and up to date.
2. **Dependencies:**
   - `pygame`, `evdev`, `pyserial`
3. **Auto-Start Configuration:**
   - Uses `crontab` to launch the main control script on boot.
4. **Log Location:**
   - `~/Desktop/r2d2-2025.log`

> 📌 **Note:** The Python script integrates joystick input, sound playback, LCD status display, motor control, and dome communication.

### Arduino Mega Setup
1. **Upload the Dome Code:** Use the Arduino IDE or PlatformIO.
2. **❗ Important:** Disconnect the Arduino from the Raspberry Pi before uploading new code. The serial connection may interfere with programming.
3. **Libraries Used:**
   - `MD_MAXPanel`, `MD_MAX72XX`, `Servo`, `Adafruit_NeoPixel`, `RF24`

---

## 🧠 Key Functional Highlights

### Python (Raspberry Pi)
- Modular async event system
- Differential drive with adjustable response curve and drift correction
- Background motor loops for real-time control
- Audio queues and randomized sound effects
- Error handling and gamepad reconnection logic
- Queue-based messaging system for safe serial communication with the Arduino

### Arduino (Dome)
- Interrupt-driven RF24 command listener
- LED matrix and Neopixel animations
- Smooth servo operation with non-blocking behavior
- Modular effect cases for visual and mechanical responses
- Flap synchronization and energy-saving animations

---

## 🔧 Maintenance Notes

- **Battery Monitoring:** Functionality is scaffolded; display integration and telemetry display are planned but not implemented.
- **Motor Cutout at Full Forward:** Identified as an unresolved bug; suspect overcurrent or motor controller configuration issue.
- **Joystick Drift Correction:** Implemented with dynamic correction based on forward velocity.
- **Config Management:** All constants are hardcoded; future versions should externalize these into a config file.
- **Sound Files:** Stored locally in organized subdirectories (hum, scream, sent, etc.)

---

## 📋 To-Do (Unfinished Tasks)

- [ ] Comment and document all major functions
- [ ] Clean and organize imports
- [ ] Move configuration and constants into a separate file
- [ ] Add live voltage readout to LCD display
- [ ] Improve serial error handling and retry logic
- [ ] Optimize joystick input response for finer control
- [ ] Expand audio mappings and button effects
- [ ] Integrate Arduino return messaging into status feedback

---

## 🛠 Troubleshooting

- **Joystick Not Detected:** Check device path in `main.py` (`/dev/input/event6`); may vary between devices.
- **Arduino Communication Not Working:** Confirm serial cable integrity through the slip-ring. Make sure baud rate and port (`/dev/ttyUSB0`) match.
- **Audio Not Playing:** Verify `pygame.mixer` initializes correctly. Ensure audio files are not corrupted and paths are correct.
- **Motors Non-Responsive:** Check power supply to MD49. Monitor log for initialization errors or incorrect speed values.
- **Sabertooth Error:** Inspect `/dev/ttyAMA3` for conflicts or misconfiguration.

---

## 📁 File Overview

- `main.py` – Primary control script for the Raspberry Pi
- `MD49.py` – Motor controller library for the MD49 (custom-written)
- `r2d2-2025.log` – Runtime log stored on Pi Desktop
- `arduino_dome.ino` – Arduino Mega sketch for controlling dome behavior
- `audio-files/` – Sound library organized by effect type
- `lib/` – Local libraries (e.g., LCD control)

---

## 📞 Support

For issues or questions about the R2D2 project, check the project logs or refer to the comments within the code. If you're taking over the project, review the `TODOs` inside the main script and use the logging output to debug unexpected behavior.
