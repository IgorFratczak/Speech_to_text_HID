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
                # TIMEOUT=1 sprawia, że funkcja nie wisi w nieskończoność
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio, language="pl-PL")
                if text:
                    if text.count(' ') >= 1:
                        text = text[0].upper() + text[1:] + "."
                return text.strip() + " " if text else None
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None  
        except (sr.RequestError, socket.timeout, socket.gaierror):
            raise ConnectionError("Brak internetu")
        except Exception:
            raise RuntimeError("Błąd sprzętowy mikrofonu")
    
class VoskSpeechRecognizer(SpeechRecognizer):
    def __init__(self, model_path="model"):
        from vosk import Model, KaldiRecognizer, SetLogLevel
        SetLogLevel(-1)
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        self.stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                        channels=1, callback=self.audio_callback)
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))

    def recognize_speech(self):
        try:
            # timeout=1.0 pozwala pętli głównej sprawdzić sygnał Ctrl+C
            data = self.audio_queue.get(timeout=1.0)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                return result.get('text', '')
            return None
        except queue.Empty:
            return None
        except Exception:
            raise RuntimeError("Błąd strumienia Vosk")