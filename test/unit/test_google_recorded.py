import os
import sys
import tempfile
import time
import threading
import psutil
import wave
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from hid.keyboard import Keyboard
""" Testowanie Google Speech Recognition API z nagraniem dźwięku z mikrofonu. """
try:
    from hid.speech_recognizer import process_raw_speech
except ImportError:
    def process_raw_speech(text):
        return text

SAMPLE_RATE = 16000

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

def save_temp_wav(pcm_data):
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data.tobytes())
    return temp_file.name

if __name__ == "__main__":
    threading.Thread(target=cpu_monitor, daemon=True).start()
    recognizer = sr.Recognizer()

    print("\n=== TEST GOOGLE SPEECH (PRESS ENTER TO RECORD) ===")

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
                input("[NAGRYWANIE INTERNETOWE...] -> Mów do mikrofonu i naciśnij ENTER, aby WYSŁAĆ...")
                recording = False

            if not audio_data:
                print("Brak nagranego dźwięku!")
                continue

            pcm_np = np.concatenate(audio_data, axis=0).flatten()
            wav_path = save_temp_wav(pcm_np)

            print("\nWysyłanie do API Google Speech...")
            try:
                with sr.AudioFile(wav_path) as source:
                    audio_file_data = recognizer.record(source)
                    raw_text = recognizer.recognize_google(audio_file_data, language="pl-PL")
                    
                    if raw_text:
                        processed_text = process_raw_speech(raw_text)
                        print(f"[GOOGLE TEXT]: {processed_text}")
                        Keyboard.send_string(processed_text + " ")
                    else:
                        print("[GOOGLE]: Brak tekstu.")

            except sr.UnknownValueError:
                print("[GOOGLE]: Nie rozpoznano mowy (próbka pusta lub za cicha).")
            except sr.RequestError as e:
                print(f"[GOOGLE BŁĄD API/SIECI]: {e}")
            except Exception as e:
                print(f"[BŁĄD]: {e}")
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)

    except KeyboardInterrupt:
        print("\nZamykanie...")
        sys.exit(0)