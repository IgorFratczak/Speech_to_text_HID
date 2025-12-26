# Speach_to_text_HID

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
- **Microphone:**
- **USB-A to USB-C Cable with Charging and Data Transfer**
- **MicroSD Card 32GB**
- **Micro SD Card Reader**

## Optional

- **Micro HDMI to HDMI Cable Adapter**
- **Raspberry Pi 27W USB-C Power Supply**

## Getting Started
