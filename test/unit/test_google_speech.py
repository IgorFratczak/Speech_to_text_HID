import speech_recognition as sr
import threading
import psutil
import os
import time
from hid.keyboard import Keyboard

def cpu_monitor():
    """Wątek monitorujący zasoby co sekundę."""
    while True:
        # Pobieramy zużycie CPU (średnia ze wszystkich rdzeni)
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # Pobieramy temperaturę (tylko dla Raspberry Pi / Linux)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
        except:
            temp = 0.0

        # Wypisujemy w jednej linii (używamy \r aby nie śmiecić w konsoli)
        print(f"[MONITOR] CPU: {cpu_usage}% | Temp: {temp:.1f}°C", end='\r')
        time.sleep(1)

import os
import sys
from contextlib import contextmanager

@contextmanager
def ignore_stderr():
    """Tymczasowo przekierowuje stderr do null, aby uciszyć błędy ALSA."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)

# W Twoim kodzie użyj tego tak:
if __name__ == "__main__":
    threading.Thread(target=cpu_monitor, daemon=True).start()
    
    r = sr.Recognizer()
    print("Inicjalizacja mikrofonu (wyciszanie sterowników)...")
    
    while True:
        try:
            # Używamy menedżera kontekstu tylko przy otwieraniu mikrofonu
            with ignore_stderr():
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.2)
                    audio = r.listen(source)
            
            # Tutaj już normalnie rozpoznajemy
            text = r.recognize_google(audio, language="pl-PL")
            print(f"\n[SPEECH] {text.lower()}")
            Keyboard.send_string(text.lower())
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"\nBłąd połączenia: {e}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break