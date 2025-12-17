#!/usr/bin/env python3
import time

# Paths to HID devices
mouse_path = "/dev/hidg0"
keyboard_path = "/dev/hidg1"

def send_mouse_event(buttons, x, y, wheel=0):
    report = bytearray([
        buttons,
        x & 0xFF,
        y & 0xFF,
        wheel & 0xFF
    ])
    with open(mouse_path, "wb") as mouse:
        mouse.write(report)

def send_keyboard_event(modifier, keycode):
    report = bytearray(8)
    report[0] = modifier
    report[2] = keycode
    with open(keyboard_path, "wb") as keyboard:
        keyboard.write(report)
        time.sleep(0.1)
        # Release keys
        keyboard.write(bytearray(8))

def test_mouse():
    send_mouse_event(0x00, 20, 10)     # Move mouse
    time.sleep(1)
    send_mouse_event(0x01, 0, 0)       # Left button down
    time.sleep(1)
    send_mouse_event(0x00, 0, 0)       # Release
    time.sleep(1)
    send_mouse_event(0x00, -20, -10)   # Move back

def test_keyboard():
    time.sleep(10)
    send_keyboard_event(0x00, 0x04)    # 'a' key
    send_keyboard_event(0x00, 0x04)
    send_keyboard_event(0x00, 0x04)
    send_keyboard_event(0x00, 0x04)
if __name__ == "__main__":
    test_mouse()
    test_keyboard()
    print("✅ HID interfaces tested successfully.")
