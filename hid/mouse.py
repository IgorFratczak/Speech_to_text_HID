MOUSE_DEVICE = "/dev/hidg0"

try :
    mouse_path = open(MOUSE_DEVICE, "wb", buffering=0)
except PermissionError:
    print("You need to run this script with elevated permissions (e.g., using sudo).")

LEFT_BUTTON = 0x01
RIGHT_BUTTON = 0x02


class Mouse:

    @staticmethod
    def send_report(report):
        mouse_path.write(report)

    @staticmethod
    def send_mouse_event(x, y, buttons=0):
        report = bytearray(3)
        report[0] = buttons  
        report[1] = x & 0xFF  
        report[2] = y & 0xFF  
        Mouse.send_report(report)

    @staticmethod
    def click(button):
        Mouse.send_mouse_event(0, 0, button)

    @staticmethod
    def move(x, y):
        Mouse.send_mouse_event(x, y)