import speech_recognition as sr
import threading
import psutil
import os
import time
from hid.keyboard import Keyboard
from hid.speech_recognizer import GoogleSpeechRecognizer
from contextlib import contextmanager
import sys
def cpu_monitor():
    while True:
        cpu_usage = psutil.cpu_percent(interval=None)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
        except:
            temp = 0.0
        print(f"[MONITOR] CPU: {cpu_usage}% | Temp: {temp:.1f}°C", end='\r')
        time.sleep(1)


@contextmanager
def ignore_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)

if __name__ == "__main__":
    threading.Thread(target=cpu_monitor, daemon=True).start()
    
    recognizer = GoogleSpeechRecognizer()
    
    while True:
        try:
            text = recognizer.recognize_speech()
            if text:
                Keyboard.send_string(text)
        except KeyboardInterrupt:
            print("\nZamykanie...")
            sys.exit(0)