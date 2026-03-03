import threading
import pyudev
import signal
from evdev import ecodes, InputDevice
import hid.usb_pt as usb_pt
from hid.keyboard import Keyboard
from hid.device_listener import DeviceListener
import time
from hid.debug import Debug as DEBUG
DEVICE_PATH = '/dev/hidg0'
""" Ścieżka do urządzenia HID, z którego odczytywane są stany LED z hosta. """

class KeyboardControl:
    """Klasa odpowiedzialna za monitorowanie klawiatury, synchronizację stanu LED z hostem i wysyłanie zdarzeń klawiszy do hosta lub menedżera wyjścia."""
    def __init__(self, output_manager=None):
        """Inicjalizuje kontroler klawiatury, opcjonalnie z menedżerem wyjścia do wysyłania zdarzeń klawiszy."""
        self.output_manager = output_manager
        """Lista aktywnych listenerów dla klawiatury."""
        self.listeners = []
        """Słownik przechowujący aktualne stany LED z hosta, aby uniknąć niepotrzebnych aktualizacji."""
        self.current_host_led_states = {
            ecodes.LED_NUML: False,
            ecodes.LED_CAPSL: False,
            ecodes.LED_SCROLLL: False
        }
        """Zwalnia wszystkie klawisze przy starcie, aby uniknąć zablokowanych klawiszy po restarcie."""
    def debug_log(self, message):
        """Wyświetla komunikat debugowy, jeśli debugowanie jest włączone."""
        if DEBUG.debug_status():
            print(f"[KEYBOARD CONTROL] {message}")
    def start(self): 
        """Uruchamia system zdarzeniowy, monitoruje klawiatury i synchronizuje stany LED z hostem."""
        Keyboard.release_keys()

        threading.Thread(target=self._sync_leds_from_host, daemon=True).start()
        threading.Thread(target=self._hotplug_monitor, daemon=True).start()
        
        for path in DeviceListener.list_all_keyboard_devices():
            self._add_new_device(path)

        self.debug_log("System zdarzeniowy uruchomiony. Czekam na sygnały...")
        try:
            signal.pause()
        except KeyboardInterrupt:
            Keyboard.release_keys()

    def _on_change(self, keys, modifiers):
        """Obsługuje zdarzenia zmiany stanu klawiszy i wysyła je do hosta lub menedżera wyjścia."""
        if self.output_manager:
            self.output_manager.msg_queue.put({
                'type': 'PHYSICAL',
                'keys': keys,
                'mods': modifiers
            })
        else:
            Keyboard.send_env_keys(modifiers, list(keys))

    def _remove_listener(self, l):
        """Usuwa listener z listy, gdy urządzenie jest odłączane."""
        if l in self.listeners:
            self.listeners.remove(l)
            self.debug_log(f"Usunięto urządzenie: {l.in_dev_path}. Aktywnych: {len(self.listeners)}")

    def _add_new_device(self, path):
        """Dodaje nową klawiaturę, jeśli jest nią urządzenie wejściowe i nie jest już monitorowane."""
        try:
            if any(l.in_dev_path == path for l in self.listeners): return

            d = InputDevice(path)
            caps = d.capabilities()
            
            is_keyboard = False
            if ecodes.EV_KEY in caps:
                if usb_pt.EV_KEY_A in caps[ecodes.EV_KEY]:
                    is_keyboard = True
            
            if not is_keyboard: return

            try:
                l = DeviceListener(
                    path, 
                    self._on_change, 
                    self._remove_listener, 
                    usb_pt.EV_TO_HID, 
                    usb_pt.EV_MODIFIERS
                )
            
                for led_code, state in self.current_host_led_states.items():
                    l.update_led_safe(led_code, state)
            
                threading.Thread(target=l.listen_loop, daemon=True).start()
                self.listeners.append(l)
          
                self.debug_log(f"Dodano klawiaturę: {path}")
            except Exception as e:
                self.debug_log(f"Błąd inicjalizacji urządzenia: {e}")
        except Exception:
            pass

    def _hotplug_monitor(self):
        """Monitoruje zdarzenia hotplug dla urządzeń wejściowych i dodaje nowe klawiatury."""
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='input')
        for device in iter(monitor.poll, None):
            if device.action == 'add' and 'DEVNAME' in device:
                threading.Timer(0.5, self._add_new_device, args=[device.get('DEVNAME')]).start()

    def _sync_leds_from_host(self):
        """Odczytuje stan LED z hosta i aktualizuje go w listenerach."""
        last_raw_state = None
        try:
            with open(DEVICE_PATH, 'rb', buffering=0) as f:
                initial_report = f.read(8)
                if initial_report:
                    raw_leds = initial_report[0]
                    self.current_host_led_states = {
                        ecodes.LED_NUML: bool(raw_leds & 0x01),
                        ecodes.LED_CAPSL: bool(raw_leds & 0x02),
                        ecodes.LED_SCROLLL: bool(raw_leds & 0x04)
                    }
                    for l in self.listeners:
                        for led_code, state in self.current_host_led_states.items():
                            l.update_led_safe(led_code, state)
                    last_raw_state = raw_leds

                while True:
                    report = f.read(8)
                    if report:
                        raw_leds = report[0]
                        if raw_leds != last_raw_state:
                            new_states = {
                                ecodes.LED_NUML: bool(raw_leds & 0x01),
                                ecodes.LED_CAPSL: bool(raw_leds & 0x02),
                                ecodes.LED_SCROLLL: bool(raw_leds & 0x04)
                            }
                            self.current_host_led_states.update(new_states)
                            for l in self.listeners:
                                for led_code, state in new_states.items():
                                    l.update_led_safe(led_code, state)
                                    time.sleep(0.005)
                            last_raw_state = raw_leds
        except Exception as e:
            self.debug_log(f"Błąd sync LED: {e}")