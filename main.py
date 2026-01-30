import threading
import speech_recognition as sr
import sounddevice as sd
from hid.keyboard import Keyboard
from hid.output_manager import OutputManager
from hid.keyboard_control import KeyboardControl
from hid.speech_recognizer import SpeechRecognizer, GoogleSpeechRecognizer, VoskSpeechRecognizer

DEBUG_MODE = True

if __name__ == "__main__":
    output_manager = OutputManager()
    bridge = KeyboardControl(output_manager=output_manager, debug_mode=DEBUG_MODE)
    threading.Thread(target=output_manager.process_loop, daemon=DEBUG_MODE).start()
    threading.Thread(target=bridge.start, daemon=DEBUG_MODE).start()
    google_speech_recognizer = GoogleSpeechRecognizer()
    vosk_speech_recognizer = VoskSpeechRecognizer(model_path="model")
    recognize = vosk_speech_recognizer  
    print("Inicializing microphone...")
    while True:
        try:
            text = recognize.recognize_speech()
            if text:
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
