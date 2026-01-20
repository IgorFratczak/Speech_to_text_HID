from evdev import InputDevice, ecodes
from hid.device_listener import DeviceListener
IN_DEV = '/dev/input/event0'
OUT_DEV = '/dev/hidg1'



def test_usb_pt():
    DeviceListener.list_all_input_devices().print()



if    __name__ == "__main__":
    test_usb_pt()