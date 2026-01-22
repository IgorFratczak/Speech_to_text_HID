import threading
import traceback
from evdev import InputDevice, ecodes, list_devices
import hid.usb_pt as usb_pt

class DeviceListener:
    def __init__(self, in_dev_path, on_change_callback, on_disconnect_callback, ev_to_hid, ev_modifiers, debug_mode=False):
        self.in_dev_path = in_dev_path
        self.on_change_callback = on_change_callback
        self.on_disconnect_callback = on_disconnect_callback
        self.ev_to_hid = ev_to_hid
        self.ev_modifiers = ev_modifiers
        self.debug_mode = debug_mode
        
        self.active_keys = set()
        self.active_modifiers = 0
        self.last_state = (set(), 0)
        
        self.dev = InputDevice(self.in_dev_path)
        self.running = False
        self.lock = threading.Lock()
        self.caps_lock_active = False
        self.num_lock_active = False    
        self.scroll_lock_active = False 
        self._sync_initial_leds()

    def _sync_initial_leds(self):
        try:
            leds = self.dev.leds()
            # ecodes: LED_NUML=0, LED_CAPSL=1, LED_SCROLLL=2
            self.num_lock_active = 0 in leds
            self.caps_lock_active = 1 in leds
            self.scroll_lock_active = 2 in leds
        except:
            self.num_lock_active = False
            self.caps_lock_active = False
            self.scroll_lock_active = False

    def grab_device(self):
        with self.lock:
            try: self.dev.grab()
            except: pass

    def release_device(self):
        with self.lock:
            try: self.dev.ungrab()
            except: pass

    def _update_state(self, key_code, value):
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
        with self.lock: 
            try:
                self.dev.write(ecodes.EV_LED, led_code, 1 if value else 0)
                self.dev.syn() 
            except Exception as e:
                print(f"Błąd zapisu LED: {e}")

    def listen_loop(self):
        self.running = True
        self.grab_device()
        if self.debug_mode:
            print(f"[OK] Rozpoczęto nasłuch urządzenia: {self.dev.name} ({self.in_dev_path})")
        
        try:
            for event in self.dev.read_loop():
                if not self.running:
                    break
                
                if event.type == ecodes.EV_KEY:
                    if self._update_state(event.code, event.value):
                        self._trigger_callback()

        except Exception as e:
            if self.debug_mode:
                print(f"\n[!] Błąd pętli nasłuchu dla {self.in_dev_path}: {e}")
        
        finally:
            self.running = False
            self.release_device()
            if self.debug_mode:
                print(f"[*] Zatrzymano nasłuch: {self.in_dev_path}")
            if self.on_disconnect_callback:
                self.on_disconnect_callback(self)
    def _trigger_callback(self):
        current_state = (set(self.active_keys), self.active_modifiers)
        if current_state != self.last_state:
            try:
                self.on_change_callback(list(current_state[0]), current_state[1])
                self.last_state = current_state
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] Błąd w callbacku: {e}")

    @staticmethod
    def list_all_keyboard_devices():
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
        devices = {}
        for path in list_devices():
            try:
                dev = InputDevice(path)
                devices[dev.path] = dev.name
            except:
                continue
        return devices
