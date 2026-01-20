from evdev import InputDevice, ecodes,list_devices
class DeviceListener:
    def __init__(self, in_dev_path, on_change_callback, ev_to_hid, ev_modifiers):
        self.in_dev_path = in_dev_path
        self.on_change_callback = on_change_callback
        self.ev_to_hid = ev_to_hid
        self.ev_modifiers = ev_modifiers
        
        self.dev = InputDevice(self.in_dev_path)
        self.active_modifiers = 0
        self.active_keys = set() 
        self.running = False
        self.last_state = (set(), 0)

    def grab_device(self):
        self.dev.grab()

    def release_device(self):
        try:
            self.dev.ungrab()
        except:
            pass

    def _update_state(self, key_code, value):
        if key_code in self.ev_modifiers:
            mod_val = self.ev_modifiers[key_code]
            if value >= 1: 
                self.active_modifiers |= mod_val
            else: 
                self.active_modifiers &= ~mod_val
            return True

        if key_code in self.ev_to_hid:
            hid_val = self.ev_to_hid[key_code]
            if value == 1: 
                self.active_keys.add(hid_val)
            elif value == 0:
                self.active_keys.discard(hid_val)
            return True
            
        return False

    def listen_loop(self):
        self.running = True
        self.grab_device()
        
        try:
            for event in self.dev.read_loop():
                if not self.running:
                    break
                if event.type == ecodes.EV_KEY:
                    if self._update_state(event.code, event.value):                        
                        current_state = (set(self.active_keys), self.active_modifiers)                        
                        if current_state != self.last_state:
                            self.on_change_callback(list(current_state[0]), current_state[1])
                            self.last_state = current_state
        finally:
            self.release_device()

    def stop(self):
        self.running = False
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