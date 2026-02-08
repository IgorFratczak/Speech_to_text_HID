import threading
import time
import json
import os
import socket
import sys
import signal
import gc
import sounddevice as sd
from hid.output_manager import OutputManager
from hid.keyboard_control import KeyboardControl
from hid.speech_recognizer import GoogleSpeechRecognizer, VoskSpeechRecognizer
from hid.hidra_server import run_hidra_server

# --- KONFIGURACJA ---
DEBUG_MODE = True
CONFIG_FILE = "config.json"

# Zmienne globalne
recognize = None
is_active = False  
running = True
audio_lock = threading.Lock() # Blokada zapobiegająca konfliktom BLE vs Pętla Główna

# Komendy sterujące
START_COMMANDS = {"start", "startuj", "uruchom", "włącz"}
STOP_COMMANDS = {"stop", "zatrzymaj", "wyłącz", "przestań"}

# --- HANDLER DLA CTRL+C ---
def signal_handler(sig, frame):
    print("\n[!] Zamykanie systemu (Ctrl+C)...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

# --- FUNKCJE POMOCNICZE ---
def has_microphone():
    """Sprawdza dostępność mikrofonu bez agresywnego restartu sterowników."""
    try:
        # Odświeżamy listę urządzeń tylko gdy to konieczne
        devices = sd.query_devices()
        return any(d['max_input_channels'] > 0 for d in devices)
    except:
        return False

def check_internet():
    try:
        socket.setdefaulttimeout(1)
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return True
    except: return False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_model", "VOSK").upper()
        except: return "VOSK"
    return "VOSK"

def save_config(model_name):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"last_model": model_name.upper()}, f)
    except: pass

def change_model(name):
    """Zmienia model z użyciem blokady audio, aby nie zderzyć się z pętlą główną."""
    global recognize
    
    with audio_lock:
        name = name.upper().strip()
        
        # Test sprzętu przed próbą inicjalizacji
        if not has_microphone():
            print(f"\n[!] Nie można ustawić {name}: Brak mikrofonu!")
            recognize = None
            return

        # Sprzątanie starego silnika
        if recognize is not None:
            recognize = None
            gc.collect() 
            time.sleep(0.3)

        try:
            if name == "GOOGLE":
                if check_internet():
                    recognize = GoogleSpeechRecognizer()
                    save_config("GOOGLE")
                    print("\n>>> AKTYWNY MODEL: GOOGLE")
                else:
                    print("\n[!] Brak sieci: Fallback na VOSK")
                    name = "VOSK"

            if name == "VOSK" or name != "GOOGLE":
                recognize = VoskSpeechRecognizer(model_path="model")
                save_config("VOSK")
                print("\n>>> AKTYWNY MODEL: VOSK")
                
        except Exception as e:
            print(f"\n[!] Błąd inicjalizacji {name}: {e}")
            recognize = None

# --- GŁÓWNA PĘTLA ---
if __name__ == "__main__":
    output_manager = OutputManager()
    bridge = KeyboardControl(output_manager=output_manager, debug_mode=DEBUG_MODE)
    
    # Start wątków (Bluetooth i Klawiatura)
    threading.Thread(target=output_manager.process_loop, daemon=True).start()
    threading.Thread(target=bridge.start, daemon=True).start()
    threading.Thread(
        target=run_hidra_server, 
        args=(DEBUG_MODE, change_model), 
        daemon=True
    ).start()

    # Start z modelu zapisanego w pliku
    initial_model = load_config()
    print(f"[*] Wczytuję z configu: {initial_model}")
    change_model(initial_model)
    
    print("-" * 40)
    print(" SYSTEM HIDRA: ONLINE")
    print("-" * 40)
    
    while running:
        try:
            # 1. Zarządzanie stanem mikrofonu pod blokadą
            with audio_lock:
                mic_present = has_microphone()
                
                if not mic_present:
                    if recognize is not None:
                        print("\n[!] Mikrofon utracony!")
                        recognize = None
                    sys.stdout.write(".")
                    sys.stdout.flush()
                    time.sleep(2)
                    continue

                if mic_present and recognize is None:
                    print("\n[+] Mikrofon powrócił! Inicjalizacja...")
                    # Podnosimy to, co jest w configu
                    current_cfg = load_config()
                    # Wywołujemy bezpośrednio logikę bez podwójnej blokady
                    if current_cfg == "GOOGLE" and check_internet():
                        recognize = GoogleSpeechRecognizer()
                    else:
                        recognize = VoskSpeechRecognizer(model_path="model")
                    print(f">>> Przywrócono: {current_cfg}")
                    continue

            # 2. Rozpoznawanie mowy (wyciągnięte poza Lock, by BLE mogło przerwać)
            if recognize:
                text = recognize.recognize_speech()
                
                if text:
                    word = text.strip().lower()
                    
                    if word in START_COMMANDS:
                        is_active = True
                        print("\n>>> NASŁUCH: ON")
                    elif word in STOP_COMMANDS:
                        is_active = False
                        print("\n>>> NASŁUCH: OFF")
                    elif is_active:
                        if DEBUG_MODE: print(f"Text: {text.strip()}")
                        output_manager.msg_queue.put({'type': 'SPEECH', 'text': text})
            else:
                time.sleep(1)

        except Exception as e:
            # Obsługa nagłego błędu wejścia
            if any(x in str(e).lower() for x in ["device", "input", "audio"]):
                with audio_lock:
                    recognize = None
            elif DEBUG_MODE:
                print(f"\nBłąd: {e}")
            time.sleep(0.5)