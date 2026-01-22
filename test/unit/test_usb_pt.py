from hid.keyboard_control import KeyboardControl

if __name__ == "__main__":
    bridge = KeyboardControl(debug_mode=True)
    bridge.start()