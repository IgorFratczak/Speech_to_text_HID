import threading
import time
import json
import os
import socket
from hid.output_manager import OutputManager
from hid.keyboard_control import KeyboardControl
from hid.speech_recognizer import GoogleSpeechRecognizer, VoskSpeechRecognizer
from hid.hidra_server import run_hidra_server

# Konfiguracja
DEBUG_MODE = True
CONFIG_FILE = "config.json"

# Zmienne globalne dla modeli
recognize = None
google_speech_recognizer = None
vosk_speech_recognizer = None

def check_internet():
    """Sprawdza połączenie z internetem (ping do DNS Google)."""
    try:
        socket.setdefaulttimeout(2)
        # Próba połączenia z portem 53 (DNS) Google
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53))
        s.close()
        return True
    except Exception:
        return False

def save_config(model_name):
    """Zapisuje aktualny model do pliku."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"last_model": model_name}, f)
    except Exception as e:
        print(f"Błąd zapisu config: {e}")

def load_config():
    """Wczytuje ostatnio używany model."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_model", "VOSK")
        except Exception:
            return "VOSK"
    return "VOSK"

def change_model(name):
    """Zmiana modelu z weryfikacją dostępności sieci."""
    global recognize
    name = name.upper().strip()
    
    if name == "GOOGLE":
        if check_internet():
            recognize = google_speech_recognizer
            save_config("GOOGLE")
            if DEBUG_MODE:
                print(f"\n>>> AKTYWOWANO MODEL: GOOGLE (Online)")
        else:
            if DEBUG_MODE:
                print("\n>>> BRAK INTERNETU: Automatyczne przełączenie na VOSK")
            recognize = vosk_speech_recognizer
            save_config("VOSK")
    else:
        recognize = vosk_speech_recognizer
        save_config("VOSK")
        if DEBUG_MODE:
            print(f"\n>>> AKTYWOWANO MODEL: VOSK (Offline)")

if __name__ == "__main__":
    # Inicjalizacja managerów wyjścia i klawiatury
    output_manager = OutputManager()
    bridge = KeyboardControl(output_manager=output_manager, debug_mode=DEBUG_MODE)
    
    # Inicjalizacja obu silników rozpoznawania
    if DEBUG_MODE:
        print("Inicjalizacja modeli mowy...")
    google_speech_recognizer = GoogleSpeechRecognizer()
    vosk_speech_recognizer = VoskSpeechRecognizer(model_path="model")
    
    # Wczytanie zapisanego stanu i ustawienie modelu na start
    last_saved_model = load_config()
    if DEBUG_MODE:
        print(f"Ostatnio używany model: {last_saved_model}")
    change_model(last_saved_model)
    
    # Uruchomienie wątków pomocniczych
    threading.Thread(target=output_manager.process_loop, daemon=True).start()
    threading.Thread(target=bridge.start, daemon=True).start()
    
    # Krótka pauza dla stabilizacji przed startem BLE
    time.sleep(2)
    
    # Start serwera BLE (przekazujemy funkcję change_model jako callback)
    threading.Thread(
        target=run_hidra_server, 
        args=(DEBUG_MODE, change_model), 
        daemon=True
    ).start()
    if DEBUG_MODE:
        print("-" * 30)
        print("SYSTEM HIDRA GOTOWY")
        print("Nasłuchiwanie uruchomione. Czekam na komendy BLE...")
        print("-" * 30)
    
    while True:
        try:
            text = recognize.recognize_speech()
            
            if text:
                if DEBUG_MODE:
                    print(f"Odebrano tekst: {text}")
                output_manager.msg_queue.put({'type': 'SPEECH', 'text': text})
        
        except ConnectionError:
            print("\n[!] Wykryto problem z siecią podczas pracy. Przełączam na VOSK...")
            change_model("VOSK")
            
        except KeyboardInterrupt:
            print("\nZatrzymywanie przez użytkownika...")
            break
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Błąd pętli głównej: {e}")
            time.sleep(0.1)