import threading
import pyudev
import signal
from evdev import ecodes
import hid.usb_pt as usb_pt
from hid.keyboard import Keyboard
from hid.device_listener import DeviceListener

OUTPUT_DEV_PATH = '/dev/hidg1' 
listeners = []
current_host_caps_state = False
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

        # 3. Jeśli przeszło test, dodajemy listenera
        l = DeviceListener(path, on_change, remove_listener, usb_pt.EV_TO_HID, usb_pt.EV_MODIFIERS)
        l.update_led_safe(ecodes.LED_CAPSL, current_host_caps_state)
        
        threading.Thread(target=l.listen_loop, daemon=True).start()
        listeners.append(l)
        print(f"[+] Dodano nową klawiaturę: {d.name} ({path})")
        
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
    global current_host_caps_state
    last_state = None
    try:
        with open(OUTPUT_DEV_PATH, 'rb', buffering=0) as f:
            while True:
                report = f.read(8)
                if report:
                    # Bit 1 (0x02) to Caps Lock
                    current_host_caps_state = bool(report[0] & 0x02)
                    
                    if current_host_caps_state != last_state:
                        for l in listeners_list:
                            l.update_led_safe(ecodes.LED_CAPSL, current_host_caps_state)
                        last_state = current_host_caps_state
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