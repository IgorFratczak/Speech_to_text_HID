import threading
import traceback
from evdev import InputDevice, ecodes, list_devices
import hid.usb_pt as usb_pt
from hid.debug import Debug as DEBUG
class DeviceListener:
    """ Klasa odpowiedzialna za nasłuchiwanie zdarzeń z urządzeń wejściowych (klawiatur) i przekazywanie ich do systemu HID. """
    def __init__(self, in_dev_path, on_change_callback, on_disconnect_callback, ev_to_hid, ev_modifiers):
        """Inicjalizuje DeviceListener dla danego urządzenia wejściowego."""
        self.in_dev_path = in_dev_path
        """Ścieżka do urządzenia wejściowego (np. /dev/input/eventX)."""
        self.on_change_callback = on_change_callback
        """Funkcja callback wywoływana przy zmianie stanu klawiszy."""
        self.on_disconnect_callback = on_disconnect_callback
        """Funkcja callback wywoływana przy odłączeniu urządzenia."""
        self.ev_to_hid = ev_to_hid
        """Mapowanie kodów evdev na kody HID."""
        self.ev_modifiers = ev_modifiers
        """Mapowanie kodów evdev na modyfikatory HID."""
        
        self.active_keys = set()
        """Zbiór aktualnie wciśniętych klawiszy (kodów HID)."""
        self.active_modifiers = 0
        """Maska bitowa aktualnie aktywnych modyfikatorów."""
        self.last_state = (set(), 0)
        """Ostatni stan klawiszy i modyfikatorów, używany do wykrywania zmian."""
        self.dev = InputDevice(self.in_dev_path)
        """Obiekt reprezentujący urządzenie wejściowe do nasłuchiwania."""
        self.running = False
        """Flaga kontrolująca działanie pętli nasłuchiwania."""
        self.lock = threading.Lock()
        """Blokada do synchronizacji dostępu do urządzenia i stanu."""
        self.caps_lock_active = False
        """Flaga stanu Caps Lock."""
        self.num_lock_active = False
        """Flaga stanu Num Lock."""    
        self.scroll_lock_active = False
        """Flaga stanu Scroll Lock.""" 
        self._sync_initial_leds()
    def debug_log(self, message):
        """Wypisuje komunikat diagnostyczny, jeśli tryb DEBUG jest aktywny."""
        if DEBUG.debug_status():
            print(f"[DEVICE LISTENER] {message}")

    def _sync_initial_leds(self):
        """Synchronizuje początkowy stan diod LED (Num Lock, Caps Lock, Scroll Lock) z urządzeniem."""
        try:
            leds = self.dev.leds()
            self.num_lock_active = 0 in leds
            self.caps_lock_active = 1 in leds
            self.scroll_lock_active = 2 in leds
        except:
            self.num_lock_active = False
            self.caps_lock_active = False
            self.scroll_lock_active = False

    def grab_device(self):
        """Odłącza urządzenie od systemu, aby móc je kontrolować bez zakłóceń."""
        with self.lock:
            try: self.dev.grab()
            except: pass

    def release_device(self):
        """Ponownie udostępnia urządzenie systemowi, przywracając jego normalne działanie."""
        with self.lock:
            try: self.dev.ungrab()
            except: pass

    def _update_state(self, key_code, value):
        """Aktualizuje stan klawiszy i modyfikatorów na podstawie zdarzenia z urządzenia."""
        if key_code in self.ev_modifiers:
            mod_val = self.ev_modifiers[key_code]
            if value >= 1: self.active_modifiers |= mod_val
            else: self.active_modifiers &= ~mod_val
            return True

        if key_code in self.ev_to_hid:
            hid_val = self.ev_to_hid[key_code]
            if value == 1: self.active_keys.add(hid_val)
            elif value == 0: self.active_keys.discard(hid_val)
            return True
        return False

    def update_led_safe(self, led_code, value):
        """Bezpiecznie aktualizuje stan diody LED na urządzeniu, obsługując potencjalne błędy."""
        with self.lock: 
            try:
                self.dev.write(ecodes.EV_LED, led_code, 1 if value else 0)
                self.dev.syn() 
            except Exception as e:
                self.debug_log(f"Błąd aktualizacji LED: {e}")

    def listen_loop(self):
        """Główna pętla nasłuchiwania zdarzeń z urządzenia. Przetwarza zdarzenia klawiszy i modyfikatorów, wywołując odpowiednie callbacki."""
        self.running = True
        self.grab_device()
        self.debug_log(f"Rozpoczęto nasłuch urządzenia: {self.dev.name} ({self.in_dev_path})")
        
        try:
            for event in self.dev.read_loop():
                if not self.running:
                    break
                
                if event.type == ecodes.EV_KEY:
                    if self._update_state(event.code, event.value):
                        self._trigger_callback()

        except Exception as e:
            self.debug_log(f"Wykryto odłączenie urządzenia: {e}")
        
        finally:
            self.running = False
            self.release_device()
            self.debug_log(f"Zakończono nasłuch urządzenia: {self.dev.name} ({self.in_dev_path})")
            if self.on_disconnect_callback:
                self.on_disconnect_callback(self)
    def _trigger_callback(self):
        """Sprawdza aktualny stan klawiszy i modyfikatorów, porównuje z ostatnim stanem i wywołuje callback, jeśli nastąpiła zmiana."""
        current_state = (set(self.active_keys), self.active_modifiers)
        if current_state != self.last_state:
            self.debug_log(f"Klawisze: {current_state[0]}, Modyfikatory: {current_state[1]}")
            try:
                self.on_change_callback(list(current_state[0]), current_state[1])
                self.last_state = current_state
            except Exception as e:
                self.debug_log(f"Błąd w callbacku: {e}")
               
    @staticmethod
    def list_all_keyboard_devices():
        """Zwraca słownik wszystkich urządzeń wejściowych typu klawiatura, dostępnych w systemie."""
        keyboards = {}
        for path in list_devices():
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps and usb_pt.EV_KEY_A in caps[ecodes.EV_KEY]:
                    keyboards[dev.path] = dev.name
            except: continue
        return keyboards
    @staticmethod
    def list_all_input_devices():
        """Zwraca słownik wszystkich urządzeń wejściowych, niezależnie od typu."""
        devices = {}
        for path in list_devices():
            try:
                dev = InputDevice(path)
                devices[dev.path] = dev.name
            except:
                continue
        return devices
