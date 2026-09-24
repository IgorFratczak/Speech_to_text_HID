#!/usr/bin/env python3
import time
from hid.keyboard import Keyboard

"""Testuje funkcjonalność klawiatury HID."""
def test_keyboard():
    print("Masz 5 sekund na skoncentrowanie się na polu tekstowym...")
    time.sleep(5)  
    test_string = "Hello, World!"
    Keyboard.send_string(test_string)
    print(f"Wysłano do klawiatury HID: {test_string}")

if __name__ == "__main__":
    test_keyboard()