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

# Kolejka na dane audio
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """Przekazuje dane z mikrofonu do kolejki."""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def cpu_monitor():
    """Monitoruje zasoby w tle."""
    while True:
        cpu_usage = psutil.cpu_percent(interval=None)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
        except:
            temp = 0.0
        print(f"[MONITOR] CPU: {cpu_usage}% | Temp: {temp:.1f}°C", end='\r')
        time.sleep(1)

def run_vosk():
    # Sprawdzenie czy model istnieje
    if not os.path.exists("model"):
        print("Błąd: Nie znaleziono folderu 'model'. Pobierz go i wypakuj jako 'model'.")
        return

    # Inicjalizacja modelu Vosk
    model = Model("model")
    rec = KaldiRecognizer(model, 16000)

    print("\n[VOSK] Silnik gotowy. Zacznij mówić...")

    # Otwarcie strumienia audio
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                # Wynik końcowy (po pauzie w mowie)
                result = json.loads(rec.Result())
                text = result.get('text', '')
                if text:
                    print(f"\n[SPEECH] Rozpoznano: {text}")
                    Keyboard.send_string(text)
            else:
                # Wynik częściowy (w trakcie mówienia - opcjonalnie)
                # partial = json.loads(rec.PartialResult())
                pass

if __name__ == "__main__":
    # Uruchomienie monitora CPU
    threading.Thread(target=cpu_monitor, daemon=True).start()

    try:
        run_vosk()
    except KeyboardInterrupt:
        print("\nZamykanie...")