import os
import sys
import queue
import json
import sounddevice as sd
import speech_recognition as sr
from abc import ABC, abstractmethod
import socket
from vosk import Model, KaldiRecognizer, SetLogLevel
import Debug from hid.debug as DEBUG
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
    def debug_log(self, message):
        if DEBUG.debug_status():
            print(f"[GOOGLE SPEECH RECOGNIZER] {message}")
    def recognize_speech(self):
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=7)
                text = self.recognizer.recognize_google(audio, language="pl-PL")
                if text:
                    debug_log(f"Rozpoznany tekst: {text}")
                    if text.count(' ') >= 1:
                        text = text[0].upper() + text[1:] + "."
                    self.debug_log(f"Przetworzony tekst: {text}")
                return text.strip() + " " if text else None
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None  
        except (sr.RequestError, socket.timeout, socket.gaierror):
            debug_log("Brak połączenia z internetem. Google Speech Recognition wymaga dostępu do sieci.")
            raise ConnectionError("Brak internetu")
        except Exception:
            debug_log("Nieoczekiwany błąd podczas rozpoznawania mowy Google: " + str(sys.exc_info()[0]))
            raise RuntimeError("Błąd sprzętowy mikrofonu")
    
class VoskSpeechRecognizer(SpeechRecognizer):
    def __init__(self, model_path="model"):
        SetLogLevel(-1)
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        self.stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                        channels=1, callback=self.audio_callback)
        self.stream.start()
    def debug_log(self, message):
        if DEBUG.debug_status():
            print(f"[VOSK SPEECH RECOGNIZER] {message}")
    def audio_callback(self, indata, frames, time, status):
        if status:
            return 
        self.audio_queue.put(bytes(indata))

    def close(self):
        """Kluczowa funkcja zwalniająca mikrofon"""
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass

    def recognize_speech(self):
        try:
            data = self.audio_queue.get(timeout=1.0)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '')
                if text:
                    self.debug_log(f"Rozpoznany tekst: {text}")
                    if text.count(' ') >= 1:
                        text = text[0].upper() + text[1:] + "."
                    self.debug_log(f"Przetworzony tekst: {text}")
                return text.strip() + " " if text else None
            return None
        except queue.Empty:
            return None
        except Exception:
            raise RuntimeError("Błąd strumienia Vosk")