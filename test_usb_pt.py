import evdev

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    print(f"Ścieżka: {device.path} | Nazwa: {device.name}")