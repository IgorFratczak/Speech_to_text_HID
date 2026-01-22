import threading
import speech_recognition as sr
import sounddevice as sd
from hid.keyboard import Keyboard
from hid.output_manager import OutputManager
from hid.keyboard_control import KeyboardControl

if __name__ == "__main__":
    output_manager = OutputManager()
    bridge = KeyboardControl(output_manager=output_manager, debug_mode=True)
    threading.Thread(target=output_manager.process_loop, daemon=True).start()
    threading.Thread(target=bridge.start, daemon=True).start()
    r = sr.Recognizer()
    print("Inicializing microphone...")
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5) 
                audio = r.listen(source)
                text = r.recognize_google(audio,language = "pl-PL") 
                text = text.lower()
                output_manager.msg_queue.put({
                    'type': 'SPEECH',
                    'text': text
                })
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Błąd połączenia z usługą rozpoznawani: {e}")
        except KeyboardInterrupt:
            print("Zakończono przez użytkownika.")
            break
