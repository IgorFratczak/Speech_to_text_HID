from keyboard_keys import *
import time
KEYBOARD_DEVICE = "/dev/hidg1"

try :
    keyboard_path = open(KEYBOARD_DEVICE, "wb", buffering=0)
except PermissionError:
    print("You need to run this script with elevated permissions (e.g., using sudo).")
    exit(1)
except FileNotFoundError:
    print("HID keyboard device not found. Make sure the HID module is properly configured.")
    exit(1)


class Keyboard:
    @staticmethod
    def send_event(modifier, keycode):
        report = bytearray(8)
        report[0] = modifier
        report[2] = keycode
        keyboard_path.write(report)
        time.sleep(0.01)
        keyboard_path.write(bytearray(8))
        time.sleep(0.01)
    @staticmethod
    def send_key(character):
        if character in KEY_MAP:
            modifier, keycode = KEY_MAP[character]
            Keyboard.send_event(modifier, keycode)
    @staticmethod
    def send_string(string):
        for char in string:
            Keyboard.send_key(char)

