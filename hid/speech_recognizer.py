import os
import sys
import queue
import json
import sounddevice as sd
import speech_recognition as sr
from abc import ABC, abstractmethod
import socket
class SpeechRecognizer(ABC):
    @abstractmethod
    def __init__(self):
        pass
    @abstractmethod
    def recognize_speech(self):
        pass

class GoogleSpeechRecognizer(SpeechRecognizer):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.6 
        self.recognizer.dynamic_energy_threshold = True
    def recognize_speech(self):
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio, language="pl-PL")
                if text.count(" ") >= 2:
                    text = text[0].upper() + text[1:] + '.'
                else:
                    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
                text = text + " " if not text.endswith(" ") else text
                
                return text
        except sr.WaitTimeoutError:
            return None  
        except sr.UnknownValueError:
            return None
        except (sr.RequestError, socket.timeout, socket.gaierror):
            print(">>> BŁĄD SIECI: Google nie odpowiada.")
            raise ConnectionError("Brak internetu")
        except Exception as e:
            return None
    
class VoskSpeechRecognizer(SpeechRecognizer):
    def __init__(self, model_path="model"):
        from vosk import Model, KaldiRecognizer,SetLogLevel
        SetLogLevel(-1)
        if not os.path.exists(model_path):
            raise FileNotFoundError("Model Vosk nie został znaleziony.")

        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        self.stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                        channels=1, callback=self.audio_callback)
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def recognize_speech(self):
        while True:
            data = self.audio_queue.get()
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '')
                return text if text else None

