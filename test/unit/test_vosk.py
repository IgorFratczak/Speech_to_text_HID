import os
import sys
import threading
import psutil
import time
import queue
import json
from vosk import Model, KaldiRecognizer
import sounddevice as sd
from hid.keyboard import Keyboard
from hid.speech_recognizer import VoskSpeechRecognizer
""" Testowanie Vosk Speech Recognition API z nagraniem dźwięku z mikrofonu. """

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


if __name__ == "__main__":
    threading.Thread(target=cpu_monitor, daemon=True).start()
    recognizer = VoskSpeechRecognizer(model_path="model")
    print("Inicjalizacja mikrofonu z Vosk...")
    try:
        while True:
            result = recognizer.recognize_speech()
            Keyboard.send_string(result)
    except KeyboardInterrupt:
        print("\nZamykanie...")