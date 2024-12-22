import sys
import time
import numpy as np
try:
    import serial
except ImportError:
    print("pyserial is not installed. Please run: pip install pyserial")
    sys.exit(1)
from serial.tools import list_ports

class iTCLab(object):

    def __init__(self, port=None, baud=115200):
        port = self.findPort()
        if not port:
            raise ValueError("No valid COM port found. Ensure the Arduino is connected.")
        print('Opening connection')
        try:
            self.sp = serial.Serial(port=port, baudrate=baud, timeout=2)
            self.sp.flushInput()
            self.sp.flushOutput()
            time.sleep(3)
            print('iTCLab connected via Arduino on port ' + port)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to port {port}: {e}")

    def findPort(self):
        for port in list_ports.comports():
            if any(
                vid_pid in port.hwid
                for vid_pid in [
                    'VID:PID=16D0:0613',  # Arduino Uno
                    'VID:PID=1A86:7523',  # Arduino HDuino
                    'VID:PID=2341:8036',  # Arduino Leonardo
                    'VID:PID=10C4:EA60',  # Arduino ESP32
                    'VID:PID=1A86:55D4'   # Arduino ESP32 (different type)
                ]
            ):
                return port.device
        print('No Arduino COM port found.')
        print('Ensure the USB cable is connected and check your device manager or terminal.')
        return None

    def stop(self):
        return self.read('X')

    def version(self):
        return self.read('VER')

    @property
    def T1(self):
        value = self.read('T1')
        try:
            self._T1 = float(value)
        except ValueError:
            raise ValueError(f"Invalid data received for T1: '{value}'")
        return self._T1

    @property
    def T2(self):
        value = self.read('T2')
        try:
            self._T2 = float(value)
        except ValueError:
            raise ValueError(f"Invalid data received for T2: '{value}'")
        return self._T2

    def LED(self, pwm):
        pwm = max(0.0, min(100.0, pwm)) / 2.0
        self.write('LED', pwm)
        return pwm

    def Q1(self, pwm):
        pwm = max(0.0, min(100.0, pwm))
        self.write('Q1', pwm)
        return pwm

    def Q2(self, pwm):
        pwm = max(0.0, min(100.0, pwm))
        self.write('Q2', pwm)
        return pwm

    def save_txt(self, t, u1, u2, y1, y2, sp1, sp2):
        data = np.vstack((t, u1, u2, y1, y2, sp1, sp2))  # vertical stack
        data = data.T  # transpose data
        top = (
            'Time (sec), Heater 1 (%), Heater 2 (%), '
            'Temperature 1 (degC), Temperature 2 (degC), '
            'Set Point 1 (degC), Set Point 2 (degC)'
        )
        np.savetxt('data.txt', data, delimiter=',', header=top, comments='')

    def read(self, cmd):
        cmd_str = self.build_cmd_str(cmd, '')
        try:
            self.sp.write(cmd_str.encode())
            self.sp.flush()
            response = self.sp.readline().decode('UTF-8').strip()
            if not response:
                raise ValueError("No response received from device.")
            return response
        except Exception as e:
            print(f"Error reading command '{cmd}': {e}")
            return ''

    def write(self, cmd, pwm):
        cmd_str = self.build_cmd_str(cmd, (pwm,))
        try:
            self.sp.write(cmd_str.encode())
            self.sp.flush()
            response = self.sp.readline().decode('UTF-8').strip()
            if not response:
                raise ValueError("No response received from device after write.")
            return response
        except Exception as e:
            print(f"Error writing command '{cmd}' with PWM {pwm}: {e}")
            return ''

    def build_cmd_str(self, cmd, args=None):
        """
        Build a command string that can be sent to the Arduino.

        Input:
            cmd (str): the command to send to the Arduino, must not
                contain a % character
            args (iterable): the arguments to send to the command
        """
        if args:
            args = ' '.join(map(str, args))
        else:
            args = ''
        return f"{cmd} {args}\n"

    def close(self):
        try:
            self.sp.close()
            print('Arduino disconnected successfully')
        except Exception as e:
            print(f'Error disconnecting from Arduino: {e}')
        return True
