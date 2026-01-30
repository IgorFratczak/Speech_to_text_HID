import queue
import time

from hid.keyboard import Keyboard

class OutputManager:
    """
    Zarządza kolejką zadań wyjściowych dla emulatora klawiatury HID.
    
    Klasa ta działa jako centralny punkt synchronizacji, zapobiegając 
    konfliktom między fizyczną klawiaturą a rozpoznawaniem mowy.
    """
    def __init__(self):
        """Inicjalizuje OutputManager z pustą kolejką zadań."""
        self.msg_queue = queue.Queue()
        self.active_physical_keys = []
        self.active_physical_modifiers = 0

    def process_loop(self):
        while True:
            task = self.msg_queue.get()
            
            if task['type'] == 'PHYSICAL':
                self.active_physical_keys = task['keys']
                self.active_physical_modifiers = task['mods']
                Keyboard.send_env_keys(self.active_physical_modifiers, self.active_physical_keys)
                
            elif task['type'] == 'SPEECH':
                text = task['text']
                Keyboard.send_string(text)
            
            self.msg_queue.task_done()