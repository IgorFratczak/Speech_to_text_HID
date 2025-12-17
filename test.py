#!/usr/bin/env python3
import time
import hid.keyboard as keyboard

def test_keyboard():
    print("You have 5 seconds to focus the text input area...")
    time.sleep(5)  
    test_string = "Hello, World!"
    keyboard.Keyboard.send_string(test_string)
    print(f"Sent string to HID keyboard: {test_string}")




test_keyboard()