from .keyboard_keys import *
import time
from evdev import InputDevice, ecodes
DEVICE_PATH = "/dev/hidg0"
""" Ścieżka do urządzenia HID, które będzie używane do symulacji klawiatury."""
from hid.debug import Debug as DEBUG
try :
    keyboard_path = open(DEVICE_PATH, "wb", buffering=0)
except PermissionError:
    if DEBUG.debug_status():
        print("[KEYBOARD] Potrzebne są uprawnienia do zapisu do urządzenia HID. Uruchom program z odpowiednimi uprawnieniami.")
except FileNotFoundError:
    print("[KEYBOARD] Urządzenie HID nie zostało znalezione. Upewnij się, że moduł HID jest poprawnie skonfigurowany.")

class Keyboard:
    """Klasa do symulacji klawiatury HID. Umożliwia wysyłanie raportów klawiatury, pojedynczych klawiszy, ciągów znaków oraz zarządzanie stanem klawiszy."""
    @staticmethod
    def send_report(report):
        """Wysyła raport klawiatury do urządzenia HID."""
        keyboard_path.write(report)
    @staticmethod
    def send_event(modifier, keycode, hold_time = 0.01):
        """Wysyła pojedynczy klawisz z określonym modyfikatorem i czasem trzymania."""
        report = bytearray(8)
        report[0] = modifier
        report[2] = keycode
        Keyboard.send_report(report)
        time.sleep(hold_time)
        Keyboard.release_keys()
        time.sleep(0.01)

    @staticmethod
    def send_key(character, hold_time = 0.01):
        """Wysyła pojedynczy znak jako klawisz."""
        if character in KEY_MAP:
            modifier, keycode = KEY_MAP[character]
            Keyboard.send_event(modifier, keycode, hold_time)
    
    @staticmethod
    def send_string(string, hold_time = 0.01):
        """Wysyła ciąg znaków jako sekwencję klawiszy."""
        if not isinstance(string, str):
            return
        for char in string:
            Keyboard.send_key(char, hold_time)

    @staticmethod
    def hold_key(modifier, keycode):
        """Trzyma określony klawisz bez zwalniania."""
        report = bytearray(8)
        report[0] = modifier
        report[2] = keycode
        Keyboard.send_report(report)
    
    @staticmethod
    def release_keys():
        """Zwalnia wszystkie klawisze, wysyłając pusty raport."""
        Keyboard.send_report(bytearray(8))
    

    @staticmethod
    def send_env_keys(modifier, keycodes, hold_time = 0.01):
        """Wysyła sekwencję klawiszy z modyfikatorem i czasem trzymani, bez zwalniania klawiszy po wysłaniu."""
        report = bytearray(8)
        report[0] = modifier
        for i, keycode in enumerate(keycodes):
            if i + 2 < len(report):
                report[i + 2] = keycode
        Keyboard.send_report(report)
        time.sleep(hold_time)