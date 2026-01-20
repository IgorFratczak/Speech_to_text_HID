from .keyboard_keys import *
import time
from evdev import InputDevice, ecodes
KEYBOARD_DEVICE_OUT = "/dev/hidg1"
# KEYBOARD_DEVICE_IN = "/dev/input/event0"


try :
    keyboard_path = open(KEYBOARD_DEVICE_OUT, "wb", buffering=0)
except PermissionError:
    print("You need to run this script with elevated permissions (e.g., using sudo).")
except FileNotFoundError:
    print("HID keyboard device not found. Make sure the HID module is properly configured.")

class Keyboard:
    @staticmethod
    def send_event(modifier, keycode, hold_time = 0.01):
        report = bytearray(8)
        report[0] = modifier
        report[2] = keycode
        Keyboard.send_report(report)
        time.sleep(hold_time)
        Keyboard.release_keys()
        time.sleep(0.01)

    @staticmethod
    def send_key(character, hold_time = 0.01):
        if character in KEY_MAP:
            modifier, keycode = KEY_MAP[character]
            Keyboard.send_event(modifier, keycode, hold_time)
    
    @staticmethod
    def send_string(string, hold_time = 0.01):
        for char in string:
            Keyboard.send_key(char, hold_time)

    @staticmethod
    def hold_key(modifier, keycode):
        report = bytearray(8)
        report[0] = modifier
        report[2] = keycode
        Keyboard.send_report(report)
    
    @staticmethod
    def release_keys():
        Keyboard.send_report(bytearray(8))
    
    @staticmethod
    def send_report(report):
        keyboard_path.write(report)
