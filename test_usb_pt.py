#!/usr/bin/env python3
import time
import hid.keyboard as keyboard

from evdev import InputDevice, categorize, ecodes
import hid.keyboard as keyboard # Twoja istniejąca klasa


devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    print(f"Ścieżka: {device.path} | Nazwa: {device.name}")


# Ścieżka do Twojej fizycznej klawiatury podpiętej do RPi
# Możesz ją znaleźć wpisując w terminalu: ls /dev/input/by-id/
dev = InputDevice('/dev/input/event0') 

print(f"Przechwytywanie urządzenia: {dev.name}")

# 'Grab' sprawia, że Raspberry Pi przestaje samo reagować na tę klawiaturę
dev.grab()

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        data = categorize(event)
        if data.keystate == 1: # Klawisz wciśnięty
            # Tutaj musisz zmapować kod z evdev na kod HID
            # i wysłać go przez Twoją funkcję:
            # keyboard.Keyboard.send_event(modifier, hid_keycode)
            pass