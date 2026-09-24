import queue
import time
from hid.debug import Debug as DEBUG
from hid.keyboard import Keyboard

class OutputManager:
    """
    Zarządza kolejkowaniem i wysyłaniem danych wyjściowych do interfejsu HID.
    Obsługuje zarówno fizyczne naciśnięcia klawiszy, jak i tekst z mowy.
    """
    def __init__(self):
        """Inicjalizuje OutputManager z pustą kolejką zadań."""
        self.msg_queue = queue.Queue()
        """Kolejka zadań typu FIFO przechowująca instrukcje dla klawiatury."""
        self.active_physical_keys = []
        """Lista aktualnie wciśniętych klawiszy fizycznych."""
        self.active_physical_modifiers = 0
        """Maska bitowa aktywnych modyfikatorów (Ctrl, Shift, Alt)."""
    def debug_log(self, message):
        """Wypisuje komunikat diagnostyczny, jeśli tryb DEBUG jest aktywny."""
        if DEBUG.debug_status():
            print(f"[OUTPUT MANAGER] {message}")
    def process_loop(self):
        """
        Główna pętla przetwarzająca zadania z kolejki `msg_queue`.
        Rozróżnia typy zadań 'PHYSICAL' oraz 'SPEECH'.
        """
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