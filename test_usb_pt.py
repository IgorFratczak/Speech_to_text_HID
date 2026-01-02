from evdev import InputDevice, ecodes

IN_DEV = '/dev/input/event0'
OUT_DEV = '/dev/hidg1'

# Mapa modyfikatorów (kod evdev: bit HID)
MODIFIERS = {
    42:  0x02, # Lewy Shift
    54:  0x20, # Prawy Shift
    29:  0x01, # Lewy Ctrl
    100: 0x40, # Prawy Alt (AltGr) - kluczowy dla 'ą', 'ę' itd.
    56:  0x04, # Lewy Alt
}

# Mapa zwykłych klawiszy (evdev: HID)
EV_TO_HID = {
    30: 0x04, # A
    31: 0x16, # S
    18: 0x08, # E
    # ... dodaj resztę liter ...
}

active_modifiers = 0
active_keys = set() # Zbiór aktualnie trzymanych klawiszy

def send_report():
    report = bytearray(8)
    report[0] = active_modifiers
    # W HID możemy wysłać do 6 klawiszy naraz w bajtach 2-7
    for i, key in enumerate(list(active_keys)[:6]):
        report[2 + i] = key
    
    with open(OUT_DEV, 'rb+') as fd:
        fd.write(report)

dev = InputDevice(IN_DEV)
dev.grab()

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        # 1. Sprawdź czy to modyfikator
        if event.code in MODIFIERS:
            bit = MODIFIERS[event.code]
            if event.value == 1:   # Wciśnięty
                active_modifiers |= bit
            elif event.value == 0: # Puszczony
                active_modifiers &= ~bit
            send_report()

        # 2. Sprawdź czy to zwykły klawisz
        elif event.code in EV_TO_HID:
            hid_code = EV_TO_HID[event.code]
            if event.value == 1:   # Wciśnięty
                active_keys.add(hid_code)
            elif event.value == 0: # Puszczony
                active_keys.discard(hid_code)
            send_report()