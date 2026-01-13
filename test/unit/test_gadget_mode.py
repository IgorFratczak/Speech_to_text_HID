#!/usr/bin/env python3
import time
from hid.keyboard import Keyboard


def test_keyboard():
    print("You have 5 seconds to focus the text input area...")
    time.sleep(5)  
    test_string = "Hello, World!"
    Keyboard.send_string(test_string)
    print(f"Sent string to HID keyboard: {test_string}")

if __name__ == "__main__":
    test_keyboard()