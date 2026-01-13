MOUSE_DEVICE = "/dev/hidg0"


# def send_mouse_event(buttons, x, y, wheel=0):
#     report = bytearray([
#         buttons,
#         x & 0xFF,
#         y & 0xFF,
#         wheel & 0xFF
#     ])
#     with open(MOUSE_DEVICE, "wb") as mouse:
#         mouse.write(report)

class Mouse: