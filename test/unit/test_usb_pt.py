from hid.keyboard_control import KeyboardControl
""" Test jednostkowy dla modułu sterowania klawiaturą HID. """
if __name__ == "__main__":
    print("Uruchamianie mostu klawiatury HID...")
    bridge = KeyboardControl(debug_mode=True)
    bridge.start()