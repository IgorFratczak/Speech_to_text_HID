import threading
import time
import json
import os
import socket
import sys
import signal
import gc
import queue
import sounddevice as sd
from hid.output_manager import OutputManager
from hid.keyboard_control import KeyboardControl
from hid.speech_recognizer import GoogleSpeechRecognizer, VoskSpeechRecognizer
from hid.hidra_server import run_hidra_server
import Debug from hid.debug as DEBUG
DEBUG_MODE = DEBUG.debug_status()

CONFIG_FILE = "config.json"

# Zmienne globalne
recognize = None
is_active = False  
running = True
audio_lock = threading.Lock() 
model_queue = queue.Queue() 

def debug_log(message):
    if DEBUG_MODE:
        print(f"[MAIN] {message}")
START_COMMANDS = {"start", "startuj", "uruchom", "włącz"}
STOP_COMMANDS = {"stop", "zatrzymaj", "wyłącz", "przestań"}

def signal_handler(sig, frame):
    debug_log("Ręczne zamykanie systemu przez użytkownika...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)


def has_microphone():
    try:
        devices = sd.query_devices()
        mic_present = any(d['max_input_channels'] > 0 for d in devices)
        if DEBUG_MODE:
            debug_log(f"Sprawdzanie mikrofonu... {'Znaleziono' if mic_present else 'Nie znaleziono'}")
        return mic_present

    except:
        return False

def check_internet():
    try:
        socket.setdefaulttimeout(1)
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        self.debug_log("Połączenie z internetem: OK")
        return True
    except: return False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                data = data.get("last_model", "VOSK").upper()
                debug_log(f"Wczytano z configu: {data}")
                return data
        except: return "VOSK"
    return "VOSK"

def save_config(model_name):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"last_model": model_name.upper()}, f)
            debug_log(f"Zapisano do configu: {model_name.upper()}")
    except Exception as e:
        debug_log(f"Błąd zapisu configu: {e}")
    except: pass

def change_model(name):
    """Logika zmiany modelu - teraz wywoływana bezpiecznie z pętli."""
    global recognize
    with audio_lock:
        name = name.upper().strip()
        
        if recognize is not None:
            debug_log(f"Zamykanie silnika przed zmianą...")
            try:
                if hasattr(recognize, 'close'): recognize.close()
            except: pass
            recognize = None
            gc.collect() 
            time.sleep(0.5)

        if not has_microphone():
            debug_log(f"Błąd: Brak mikrofonu dla {name}!")
            return

        try:
            if name == "GOOGLE":
                if check_internet():
                    recognize = GoogleSpeechRecognizer()
                    save_config("GOOGLE")
                    debug_log("Model zmieniony na GOOGLE")
                else:
                    debug_log("Brak internetu! Fallback na VOSK...")
                    name = "VOSK"

            if name == "VOSK":
                recognize = VoskSpeechRecognizer(model_path="model")
                save_config("VOSK")
                debug_log("Model zmieniony na VOSK")
                
        except Exception as e:
            debug_log(f"Błąd inicjalizacji {name}: {e}")
            recognize = None

# --- START SYSTEMU ---
if __name__ == "__main__":
    output_manager = OutputManager()
    bridge = KeyboardControl(output_manager=output_manager)
    
    threading.Thread(target=output_manager.process_loop, daemon=True).start()
    threading.Thread(target=bridge.start, daemon=True).start()
    
    # BLE wrzuca do kolejki (model_queue.put)
    threading.Thread(
        target=run_hidra_server, 
        args=(model_queue.put), 
        daemon=True
    ).start()

    initial_model = load_config()
    change_model(initial_model)
    debug_log("System HIDRA: ONLINE")

    
    while running:
        try:
            try:
                req = model_queue.get_nowait()
                change_model(req)
            except queue.Empty:
                pass

            with audio_lock:
                mic_present = has_microphone()
                
                if not mic_present:
                    if recognize is not None:
                        debug_log("MIKROFON ODŁĄCZONY!")
                        if hasattr(recognize, 'close'): recognize.close()
                        recognize = None
                    sys.stdout.write(".")
                    sys.stdout.flush()
                    time.sleep(2)
                    continue

                if mic_present and recognize is None:
                    debug_log("Wykryto mikrofon! Przywracanie silnika...")
                    change_model(load_config())
                    continue

            # 3. TWOJA LOGIKA ROZPOZNAWANIA I KOMEND
            if recognize:
                text = recognize.recognize_speech()
                
                if text:
                    clean_text = text.strip()
                    word = clean_text.lower()
                    
                    if DEBUG_MODE:
                        debug_log(f"Słyszę: {clean_text} | Nasłuch: {'ON' if is_active else 'OFF'}")

                    # TWOJE ORYGINALNE WARUNKI
                    if any(cmd in word for cmd in START_COMMANDS):
                        is_active = True
                        debug_log(">>> NASŁUCH: ON")
                    elif any(cmd in word for cmd in STOP_COMMANDS):
                        is_active = False
                        debug_log(">>> NASŁUCH: OFF")
                    
                    elif is_active:
                        output_manager.msg_queue.put({'type': 'SPEECH', 'text': text})
            else:
                time.sleep(0.5)

        except Exception as e:
            if any(x in str(e).lower() for x in ["device", "input", "audio", "stream"]):
                debug_log(f"Błąd strumienia: {e}")
                with audio_lock:
                    if recognize and hasattr(recognize, 'close'): recognize.close()
                    recognize = None
            elif DEBUG_MODE:
                debug_log(f"BŁĄD PĘTLI: {e}")
            time.sleep(1)