import queue
import time
import Debug from hid.debug as DEBUG
from hid.keyboard import Keyboard

class OutputManager:
    """
    Dokumentacja klasy OutputManager:
    """
    def __init__(self):
        """Inicjalizuje OutputManager z pustą kolejką zadań."""
        self.msg_queue = queue.Queue()
        self.active_physical_keys = []
        self.active_physical_modifiers = 0
    def debug_log(self, message):
        if DEBUG.debug_status():
            print(f"[OUTPUT MANAGER] {message}")
    def process_loop(self):
        while True:
            task = self.msg_queue.get()
            
            if task['type'] == 'PHYSICAL':
                self.active_physical_keys = task['keys']
                self.active_physical_modifiers = task['mods']
                Keyboard.send_env_keys(self.active_physical_modifiers, self.active_physical_keys)
                self.debug_log(f"Przetworzono zadanie PHYSICAL: klawisze={self.active_physical_keys}, modyfikatory={self.active_physical_modifiers}")
            elif task['type'] == 'SPEECH':
                text = task['text']
                Keyboard.send_string(text)
                self.debug_log(f"Przetworzono zadanie SPEECH: tekst='{text}'")
            else:
                self.debug_log(f"Otrzymano nieznany typ zadania: {task['type']}")
            self.msg_queue.task_done()