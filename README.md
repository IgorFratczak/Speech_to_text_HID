# Speech_to_text_HID

## Overview

**Speech-to-Text HID** is a hardware-based solution designed to convert spoken words into real-time USB keyboard signals.

By leveraging the **HID (Human Interface Device)** protocol, the device is recognized by any computer as a standard physical keyboard. This allows you to "type" with your voice into any software (Word, Excel, Web Browsers, or Terminals) without installing custom drivers or third-party software on the target machine.

## Key Features

- **Real-Time Transcription:** Instant conversion of speech to text with minimal latency.
- **Plug & Play:** Compatible with Windows, macOS, Linux, and Android out of the box.
- **Hardware Emulation:** The system injects text directly into the cursor focus point, just like a mechanical keyboard.
- **Zero-Footprint:** Ideal for restricted environments (e.g., work computers) where installing speech-recognition software is prohibited.

## How It Works

The project follows a three-step processing pipeline:

1.  **Audio Capture:** High-quality microphone picks up the voice signal.
2.  **Speech Recognition:** The audio is processed via a STT (Speech-to-Text) engine to generate string data.
3.  **HID Mapping:** The text is converted into USB Keyboard Scancodes and sent to the host computer.

## Hardware Requirements

- **Raspberry Pi 5 - 2/4/8/16GB RAM**
- **Microphone with audio card (or additional USB sound card)**
- **USB-A to USB-C Cable with Charging and Data Transfer**
- **MicroSD Card 32GB**
- **Micro SD Card Reader**

## Optional

- **Micro HDMI to HDMI Cable Adapter**
- **Raspberry Pi 27W USB-C Power Supply**

## Getting Started

1.  **Install Raspberry Pi OS** on a microSD card. During installation, enable SHH. If you h aven't done so, add an empty file named ssh (without extensions) to the boot folder.
2.  **Turn on your Raspberry Pi** and connect it to the internet. Note the Raspberry Pi's IP address. Install the Xshell application (https://www.netsarang.com/en/free-for-home-school/) on the host device. Connect the host device to the Raspberry Pi's IP address.
3.  **Switch to the root user:** `sudo -i`
4.  **Use nano to edit:** `/boot/firmware/config.txt`

    > nano /boot/firmware/config.txt

    At the end of the file, add:

    > dtoverlay=dwc2

    Comment out the following lines (add # at the beginning of each):

    > #camera_auto_detect=1
    >
    > #display_auto_detect=1
    >
    > #dtoverlay=vc4-kms-v3d
    >
    > #max_framebuffers=2

    At this point, it will not be possible to use the Raspberry Pi graphical interface. Therefore, in the previous step we had to install Xshell and now we will communicate with rasberry through it.

    To save the file, press Ctrl + X, then press Y to confirm and Enter to exit.

5.  **Use nano to edit** `/boot/firmware/cmdline.txt`

    > nano /boot/firmware/cmdline.txt

    At the end of the file, add:

    > modules-load=dwc2

6.  **Use nano to edit** `/etc/modules`

    > nano /etc/modules

    At the end of the file, add:

    > libcomposite

7.  **Next, reboot RPi. After restarting, it should enter USB gadget mode.**

    > reboot

    To confirm, run the command:

    > ls /sys/class/udc

    If the output looks like `1000480000.usb`, RPi is operating properly in gadget mode.

# Creating HID Interfaces on RPi

The final configuration step is to define USB descriptors and create HID interfaces for the gadget device.

In your RPi console, create a new `.sh` file:

> nano /home/hid.sh

Paste the following script into it:

> cd /sys/kernel/config/usb_gadget/
> sudo mkdir -p hidg
> cd hidg
> sudo bash -c 'echo "0x046d" > idVendor' # Logitech Inc.
> sudo bash -c 'echo "0xc539" > idProduct' # USB Receiver
> sudo bash -c 'echo "0x3906" > bcdDevice' # Device version
> sudo bash -c 'echo "0x0200" > bcdUSB' # USB2
> sudo mkdir -p strings/0x409
> sudo bash -c 'echo "0x00" > strings/0x409/serialnumber'
> sudo bash -c 'echo "Logitech" > strings/0x409/manufacturer'
> sudo bash -c 'echo "USB Receiver" > strings/0x409/product'
> sudo mkdir -p configs/c.1
> sudo bash -c 'echo "0x80" > configs/c.1/bmAttributes' # attributes
> sudo bash -c 'echo "200" > configs/c.1/MaxPower' # power consumption
> sudo mkdir -p functions/hid.usb0
> sudo bash -c 'echo 2 > functions/hid.usb0/protocol' # 1 for keyboard, 2 for mouse
> sudo bash -c 'echo 1 > functions/hid.usb0/subclass' # 1 for boot interface subclass
> sudo bash -c 'echo 4 > functions/hid.usb0/report_length' # report length
> sudo bash -c 'echo -ne \\x05\\x01\\x09\\x02\\xa1\\x01\\x09\\x01\\xa1\\x00\\x05\\x09\\x19\\x01\\x29\\x03\\x15\\x00\\x25\\x01\\x95\\x03\\x75\\x01\\x81\\x02\\x75\\x05\\x95\\x01\\x81\\x01\\x05\\x01\\x09\\x30\\x09\\x31\\x09\\x38\\x15\\x81\\x25\\x7f\\x75\\x08\\x95\\x03\\x81\\x06\\xc0\\xc0 > functions/hid.usb0/report_desc'
> sudo mkdir -p functions/hid.usb1
> sudo bash -c 'echo 1 > functions/hid.usb1/protocol' # 1 for keyboard, 2 for mouse
> sudo bash -c 'echo 1 > functions/hid.usb1/subclass' # 1 for boot interface subclass
> sudo bash -c 'echo 8 > functions/hid.usb1/report_length' # report length
> sudo bash -c 'echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb1/report_desc'
> sudo ln -s functions/hid.usb0 configs/c.1/
> sudo ln -s functions/hid.usb1 configs/c.1/
> ls /sys/class/udc
> sudo bash -c 'echo "1000480000.usb" > UDC'

Now run the script:

> sh /home/hid.sh

# Testing HID Interfaces​

Now it's time to send some test instructions to the mouse and keyboard. This can be done using Python.
In your RPi console,

> git clone https://github.com/IgorFratczak/Speach_to_text_HID.git

If you don't have Git CLI, install it

Now run the Python script (go to the appropriate folder):

> python3 test.py

Install additional libraries if you need them
