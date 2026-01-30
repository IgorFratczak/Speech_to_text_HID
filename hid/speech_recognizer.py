import os
import sys
import queue
import json
import sounddevice as sd
import speech_recognition as sr
from abc import ABC, abstractmethod

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

    def recognize_speech(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5) 
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio, language="pl-PL")
                return text.lower()
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"Błąd połączenia z usługą rozpoznawani: {e}")
                return None

class VoskSpeechRecognizer(SpeechRecognizer):
    def __init__(self, model_path="model"):
        from vosk import Model, KaldiRecognizer
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

