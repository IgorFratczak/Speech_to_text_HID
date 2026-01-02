from evdev import InputDevice, ecodes
import time

# Urządzenie wejściowe (Twoja klawiatura) i wyjściowe (Gadget)
IN_DEV = '/dev/input/event0'
OUT_DEV = '/dev/hidg1'

# Mapa: kod Linux (evdev) -> kod USB HID
# Musisz ją sukcesywnie uzupełniać
EV_TO_HID = {
    30: 0x04, # A
    31: 0x16, # S
    32: 0x07, # D
    33: 0x09, # F
    34: 0x0a, # G
    35: 0x0b, # H
    36: 0x0d, # J
    38: 0x0f, # L
    28: 0x28, # Enter
    57: 0x2c, # Space
}

def send_hid_report(modifier, keycode):
    report = bytearray(8)
    report[0] = modifier
    report[2] = keycode
    with open(OUT_DEV, 'rb+') as fd:
        fd.write(report)

try:
    dev = InputDevice(IN_DEV)
    dev.grab() # Przejmij klawiaturę na wyłączność Maliny
    print("Most aktywny. Klikaj na klawiaturze!")

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            # Reagujemy na naciśnięcie (1) i puszczenie (0)
            if event.value == 1: # DOWN
                if event.code in EV_TO_HID:
                    send_hid_report(0, EV_TO_HID[event.code])
            elif event.value == 0: # UP
                send_hid_report(0, 0) # Wyślij pusty raport (klawisz puszczony)

except KeyboardInterrupt:
    print("\nZamykanie...")
finally:
    dev.ungrab()