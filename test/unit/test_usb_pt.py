import threading
import pyudev
import signal
from evdev import ecodes
import hid.usb_pt as usb_pt
from hid.keyboard import Keyboard
from hid.device_listener import DeviceListener
import time
OUTPUT_DEV_PATH = '/dev/hidg1' 
listeners = []
current_host_led_states = {
    ecodes.LED_NUML: False,
    ecodes.LED_CAPSL: False,
    ecodes.LED_SCROLLL: False
}
def on_change(keys, modifiers):

    
    # Wysyłanie klawiszy do gadżetu USB
    Keyboard.send_env_keys(modifiers, list(keys))
def remove_listener(l):
    if l in listeners:
        listeners.remove(l)
        print(f"[-] Usunięto: {l.in_dev_path}. Aktywnych: {len(listeners)}")

def add_new_device(path):
    try:
        # 1. Sprawdź, czy już nie obsługujemy tego ścieżki
        if any(l.in_dev_path == path for l in listeners): return

        # 2. SPRAWDZENIE: Czy to urządzenie to faktycznie klawiatura?
        # Tworzymy tymczasowy obiekt urządzenia, żeby sprawdzić jego możliwości
        from evdev import InputDevice
        d = InputDevice(path)
        caps = d.capabilities()
        
        # Sprawdzamy, czy urządzenie obsługuje klawisze (EV_KEY)
        # i czy ma klawisz 'A' (standardowa klawiatura)
        is_keyboard = False
        if ecodes.EV_KEY in caps:
            if usb_pt.EV_KEY_A in caps[ecodes.EV_KEY]:
                is_keyboard = True
        
        if not is_keyboard:
            # Jeśli to nie klawiatura (np. tylko przyciski głośności), ignorujemy
            return

        try:
            l = DeviceListener(path, on_change, remove_listener, usb_pt.EV_TO_HID, usb_pt.EV_MODIFIERS)
        
        # Synchronizacja wszystkich trzech diod przy podpięciu
            for led_code, state in current_host_led_states.items():
                l.update_led_safe(led_code, state)
        
            threading.Thread(target=l.listen_loop, daemon=True).start()
            listeners.append(l)
            print(f"[+] Dodano klawiaturę i zsynchronizowano LEDy: {path}")
        except Exception as e:
            pass
        
    except Exception as e:
        # Często błąd występuje, gdy próbujemy otworzyć urządzenie, 
        # do którego system jeszcze nie nadał uprawnień
        pass

def hotplug_monitor():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='input')
    for device in iter(monitor.poll, None):
        if device.action == 'add' and 'DEVNAME' in device:
            threading.Timer(0.5, add_new_device, args=[device.get('DEVNAME')]).start()



def sync_leds_from_host(listeners_list):
    global current_host_led_states
    last_raw_state = None
    
    try:
        # Otwieramy urządzenie wyjściowe (gadget)
        with open(OUTPUT_DEV_PATH, 'rb', buffering=0) as f:
            # --- TO JEST KLUCZOWA ZMIANA ---
            # Próbujemy odczytać stan początkowy zaraz po otwarciu
            # Laptop często wysyła raport LED przy inicjalizacji połączenia
            initial_report = f.read(8)
            if initial_report:
                raw_leds = initial_report[0]
                current_host_led_states = {
                    ecodes.LED_NUML: bool(raw_leds & 0x01),
                    ecodes.LED_CAPSL: bool(raw_leds & 0x02),
                    ecodes.LED_SCROLLL: bool(raw_leds & 0x04)
                }
                # Od razu aktualizujemy wszystkie podpięte klawiatury
                for l in listeners_list:
                    for led_code, state in current_host_led_states.items():
                        l.update_led_safe(led_code, state)
                last_raw_state = raw_leds
            # -------------------------------

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
                        current_host_led_states.update(new_states)
                        for l in listeners_list:
                            for led_code, state in new_states.items():
                                l.update_led_safe(led_code, state)
                        last_raw_state = raw_leds
    except Exception as e:
        print(f"Błąd sync LED: {e}")

def test_usb_pt():
    Keyboard.release_keys()
    threading.Thread(target=sync_leds_from_host, args=(listeners,), daemon=True).start()
    threading.Thread(target=hotplug_monitor, daemon=True).start()
    
    # Wstępne skanowanie
    for path in DeviceListener.list_all_keyboard_devices():
        add_new_device(path)

    print("System zdarzeniowy uruchomiony. Czekam na sygnały...")
    try:
        signal.pause()
    except KeyboardInterrupt:
        Keyboard.release_keys()

if __name__ == "__main__":
    test_usb_pt()