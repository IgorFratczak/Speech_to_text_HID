import json
import os
import sys
import threading
import time
import psutil
import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel
from hid.keyboard import Keyboard
""" Testowanie Vosk Speech Recognition API z nagraniem dźwięku z mikrofonu. """
try:
    from hid.speech_recognizer import process_raw_speech
except ImportError:
    def process_raw_speech(text):
        return text

SAMPLE_RATE = 16000
MODEL_PATH = "model"  

def cpu_monitor():
    while True:
        cpu_usage = psutil.cpu_percent(interval=None)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
        except Exception:
            temp = 0.0
        print(f"[MONITOR] CPU: {cpu_usage}% | Temp: {temp:.1f}°C", end='\r')
        time.sleep(1)

if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        print(f"Brak katalogu z modelem Vosk w ścieżce: {MODEL_PATH}")
        sys.exit(1)

    SetLogLevel(-1)
    print("Wczytywanie modelu Vosk...")
    model = Model(MODEL_PATH)
    
    threading.Thread(target=cpu_monitor, daemon=True).start()

    print("\n=== TEST VOSK (PRESS ENTER TO RECORD) ===")

    try:
        while True:
            input("\n[ENTER] -> Naciśnij, aby ROZPOCZĄĆ nagrywanie...")
            
            audio_data = []
            recording = True

            def callback(indata, frames, time_info, status):
                if recording:
                    audio_data.append(indata.copy())

            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16',
                callback=callback
            )

            with stream:
                input("[NAGRYWANIE VOSK...] -> Mów do mikrofonu i naciśnij ENTER, aby PRZETWORZYĆ...")
                recording = False

            if not audio_data:
                print("Brak nagranego dźwięku!")
                continue

            pcm_np = np.concatenate(audio_data, axis=0).flatten()
            raw_bytes = pcm_np.tobytes()

            print("\nPrzetwarzanie audio w Vosk...")
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)
            
            recognizer.AcceptWaveform(raw_bytes)
            result = json.loads(recognizer.FinalResult())
            raw_text = result.get('text', '').strip()

            if raw_text:
                processed_text = process_raw_speech(raw_text)
                print(f"[VOSK TEXT]: {processed_text}")
                Keyboard.send_string(processed_text + " ")
            else:
                print("[VOSK]: Nie rozpoznano mowy.")

    except KeyboardInterrupt:
        print("\nZamykanie...")
        sys.exit(0)