'''
Refactored MD49 driver for Python 3
By: Sloan Corey

This driver is designed to control the MD49 Dual 24V Motor Controller.
It provides methods for motor speed control, encoder readings,
voltage and current monitoring, and regulator/timeout control.
It also includes a method to reset the controller to safe default settings.
'''


import serial
from struct import unpack
 
class MotorBoardMD49:
    """
    Python driver for the MD49 Dual 24V Motor Controller.
 
    Supports motor speed control, encoder readings, voltage, current monitoring,
    regulator/timeout control, and safe default initialization.
    """
 
    SYNC_BYTE = 0x00  # Sync byte required at the start of every command
 
    # Command bytes from MD49 documentation
    CMD_GET_SPEED_1 = 0x21
    CMD_GET_SPEED_2 = 0x22
    CMD_GET_ENCODER_1 = 0x23
    CMD_GET_ENCODER_2 = 0x24
    CMD_GET_VOLTS = 0x26
    CMD_GET_CURRENT_1 = 0x27
    CMD_GET_CURRENT_2 = 0x28
    CMD_GET_ERROR = 0x2D
    CMD_SET_SPEED_1 = 0x31
    CMD_SET_SPEED_2 = 0x32
    CMD_SET_ACCELERATION = 0x33
    CMD_SET_MODE = 0x34
    CMD_RESET_ENCODERS = 0x35
    CMD_DISABLE_REGULATOR = 0x36
    CMD_ENABLE_REGULATOR = 0x37
    CMD_DISABLE_TIMEOUT = 0x38
    CMD_ENABLE_TIMEOUT = 0x39
 
    def __init__(self, port, baudrate=38400, timeout=1):
        """
        Initialize serial connection to MD49 motor controller.
 
        :param port: Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
        :param baudrate: Communication baud rate (default 38400)
        :param timeout: Serial read timeout in seconds
        """
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
 
    def _write(self, command, *data):
        """
        Send a command to the MD49.
 
        :param command: Command byte (e.g., 0x21 for GET SPEED 1)
        :param data: Optional data bytes (e.g., speed value)
        """
        packet = bytes([self.SYNC_BYTE, command] + list(data))
        self.ser.write(packet)
 
    def _read_bytes(self, count):
        """
        Read raw bytes from the MD49.
 
        :param count: Number of bytes to read
        :return: Byte string of length 'count'
        """
        return self.ser.read(count)
 
    def _read_byte(self):
        """
        Read a single byte from the MD49.
 
        :return: Byte as integer or None if timeout
        """
        data = self._read_bytes(1)
        return data[0] if data else None
 
    def _read_long(self):
        """
        Read a 4-byte signed integer from the MD49 (big-endian).
 
        :return: 32-bit signed integer
        """
        data = self._read_bytes(4)
        if len(data) != 4:
            raise IOError("Failed to read 4 bytes from MD49")
        return unpack('>i', data)[0]
 
    # -------------------- GET Commands --------------------
    def get_speed(self, motor):
        """
        Get the requested speed of a motor.
 
        :param motor: 1 or 2
        :return: Speed value (0-255 or -128 to 127 depending on mode)
        """
        cmd = self.CMD_GET_SPEED_1 if motor == 1 else self.CMD_GET_SPEED_2
        self._write(cmd)
        return self._read_byte()
 
    def get_encoder(self, motor):
        """
        Get encoder count of a motor.
 
        :param motor: 1 or 2
        :return: Signed 32-bit encoder count
        """
        cmd = self.CMD_GET_ENCODER_1 if motor == 1 else self.CMD_GET_ENCODER_2
        self._write(cmd)
        return self._read_long()
 
    def get_volts(self):
        """
        Get battery voltage.
 
        :return: Voltage value in volts (e.g., 24)
        """
        self._write(self.CMD_GET_VOLTS)
        return self._read_byte()
 
    def get_current(self, motor):
        """
        Get current draw of a motor.
 
        :param motor: 1 or 2
        :return: Current in tenths of an ampere (e.g., 25 = 2.5A)
        """
        cmd = self.CMD_GET_CURRENT_1 if motor == 1 else self.CMD_GET_CURRENT_2
        self._write(cmd)
        return self._read_byte()
 
    def get_error(self):
        """
        Get error status byte.
 
        :return: Error byte (bits indicate specific faults)
        """
        self._write(self.CMD_GET_ERROR)
        return self._read_byte()
 
    # -------------------- SET Commands --------------------
    def set_speed(self, motor, speed):
        """
        Set the speed of a motor.
 
        :param motor: 1 or 2
        :param speed: Speed value (0-255 or -128 to 127 depending on mode)
        """
        cmd = self.CMD_SET_SPEED_1 if motor == 1 else self.CMD_SET_SPEED_2
        speed = max(0, min(255, speed))  # Clamp to 0-255 range
        self._write(cmd, speed)
 
    def set_acceleration(self, value):
        """
        Set the acceleration rate.
 
        :param value: Acceleration (1-10)
        """
        value = max(1, min(10, value))  # Clamp to 1-10 range
        self._write(self.CMD_SET_ACCELERATION, value)
 
    def set_mode(self, mode):
        """
        Set the MD49 operation mode.
 
        :param mode: 0, 1, 2, or 3
        """
        if mode not in (0, 1, 2, 3):
            raise ValueError("Mode must be 0, 1, 2, or 3")
        self._write(self.CMD_SET_MODE, mode)
 
    def reset_encoders(self):
        """
        Reset both encoder counts to zero.
        """
        self._write(self.CMD_RESET_ENCODERS)
 
    # -------------------- Regulator Control --------------------
    def disable_regulator(self):
        """
        Disable automatic speed regulation using encoder feedback.
        """
        self._write(self.CMD_DISABLE_REGULATOR)
 
    def enable_regulator(self):
        """
        Enable automatic speed regulation using encoder feedback.
        """
        self._write(self.CMD_ENABLE_REGULATOR)
 
    # -------------------- Timeout Control --------------------
    def disable_timeout(self):
        """
        Disable the 2-second serial communication timeout safety feature.
        """
        self._write(self.CMD_DISABLE_TIMEOUT)
 
    def enable_timeout(self):
        """
        Enable the 2-second serial communication timeout safety feature.
        """
        self._write(self.CMD_ENABLE_TIMEOUT)
 
    # -------------------- Safe Defaults --------------------
    def reset_to_defaults(self):
        """
        Reset the MD49 to safe default settings:
        - Mode 0 (unsigned speed control)
        - Acceleration 5 (default value)
        - Enable regulator
        - Enable timeout safety
        """
        self.set_mode(0)
        self.set_acceleration(5)
        self.enable_regulator()
        self.reset_encoders()
        self.enable_timeout()
 
    def close(self):
        """
        Close the serial connection to the MD49.
        """
        self.ser.close()
