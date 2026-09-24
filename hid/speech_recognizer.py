import os
import sys
import queue
import json
import sounddevice as sd
import speech_recognition as sr
from abc import ABC, abstractmethod
import socket
from vosk import Model, KaldiRecognizer, SetLogLevel
from hid.debug import Debug as DEBUG
class SpeechRecognizer(ABC):
    """Abstrakcyjna klasa bazowa dla rozpoznawania mowy. Definiuje interfejs dla różnych implementacji rozpoznawania mowy, takich jak Google Speech Recognition i Vosk."""
    @abstractmethod
    def __init__(self):
        pass
    @abstractmethod
    def recognize_speech(self):
        pass

class GoogleSpeechRecognizer(SpeechRecognizer):
    def __init__(self):
        """Inicjalizuje rozpoznawanie mowy Google Speech Recognition z odpowiednimi ustawieniami."""
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.6
        self.recognizer.dynamic_energy_threshold = True
    def debug_log(self, message):
        """Wypisuje komunikat diagnostyczny, jeśli tryb DEBUG jest aktywny."""
        if DEBUG.debug_status():
            print(f"[GOOGLE SPEECH RECOGNIZER] {message}")
    def recognize_speech(self):
        """Przechwytuje dźwięk z mikrofonu i rozpoznaje tekst za pomocą Google Speech Recognition. Obsługuje różne wyjątki związane z brakiem internetu, problemami sprzętowymi oraz błędami rozpoznawania."""
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=7)
                text = self.recognizer.recognize_google(audio, language="pl-PL")
                if text:
                    self.debug_log(f"Rozpoznany tekst: {text}")
                    text = process_raw_speech(text) 
                    self.debug_log(f"Przetworzony tekst: {text}")
                return text + " " if text else None
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None  
        except (sr.RequestError, socket.timeout, socket.gaierror):
            self.debug_log("Brak połączenia z internetem. Google Speech Recognition wymaga dostępu do sieci.")
            raise ConnectionError("Brak internetu")
        except Exception:
            self.debug_log("Nieoczekiwany błąd podczas rozpoznawania mowy Google: " + str(sys.exc_info()[0]))
            raise RuntimeError("Błąd sprzętowy mikrofonu")
    




class VoskSpeechRecognizer(SpeechRecognizer):
    def __init__(self, model_path="model"):
        """Inicjalizuje rozpoznawanie mowy Vosk z modelem znajdującym się w `model_path`. Ustawia poziom logowania Vosk na -1, aby wyciszyć niepotrzebne komunikaty, oraz konfiguruje strumień audio do przechwytywania dźwięku z mikrofonu."""
        SetLogLevel(-1)
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        self.stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                        channels=1, callback=self.audio_callback)
        self.stream.start()
    def debug_log(self, message):
        """Wypisuje komunikat diagnostyczny, jeśli tryb DEBUG jest aktywny."""
        if DEBUG.debug_status():
            print(f"[VOSK SPEECH RECOGNIZER] {message}")
    def audio_callback(self, indata, frames, time, status):
        """Funkcja zwrotna dla strumienia audio, która umieszcza przechwycone dane audio w kolejce `audio_queue` do późniejszego przetwarzania przez funkcję `recognize_speech`. Obsługuje statusy błędów związane z dźwiękiem."""
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
        """Przetwarza dane audio z kolejki `audio_queue` i rozpoznaje tekst za pomocą Vosk. Obsługuje wyjątki związane z brakiem danych audio oraz błędami strumienia Vosk."""
        try:
            data = self.audio_queue.get(timeout=1.0)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '')
                if text:
                    self.debug_log(f"Rozpoznany tekst: {text}")
                    text = process_raw_speech(text) 
                    self.debug_log(f"Przetworzony tekst: {text}")
                return text + " " if text else None
            return None
        except queue.Empty:
            return None
        except Exception:
            raise RuntimeError("Błąd strumienia Vosk")


def process_raw_speech(raw_text):
    """Przetwarza surowy tekst rozpoznany z mowy, dodając interpunkcję i poprawiając formatowanie. Funkcja identyfikuje spójniki i słowa pytające, aby odpowiednio dodać przecinki i znaki zapytania, a także zapewnia, że zdanie zaczyna się wielką literą i kończy odpowiednią interpunkcją."""
    if not raw_text:
        return None

    text = raw_text.strip()
    words = text.split()
    
    if len(words) <= 1:
        return text  

    conjunctions = {
        'że', 'żeby', 'iż', 'bo', 'ponieważ', 'gdyż', 'albowiem',
        'ale', 'lecz', 'jednak', 'wszakże', 'a', 'ze', 'poniewaz',
        'który', 'ktory', 'która', 'ktora', 'które', 'ktore', 'których', 
        'któremu', 'którą', 'gdy', 'kiedy', 'jeśli', 'jesli', 'jeżeli', 
        'zanim', 'chociaż', 'choć', 'skoro', 'gdyz'
    }
    
    
    question_marks = {'czy', 'jak', 'dlaczego', 'ile', 'gdzie', 'kto', 'czym', 'kogo', 'skąd', 'skad'}

    words_lower = [w.lower() for w in words]
    processed_words = []

    for i, word in enumerate(words_lower):
        if word in conjunctions and i > 0:
            if not processed_words[-1].endswith(','):
                processed_words[-1] += ','
        
        elif word in question_marks and i > 0:
             if not processed_words[-1].endswith(','):
                processed_words[-1] += ','

        processed_words.append(word)
 
    result = " ".join(processed_words)
    result = result[0].upper() + result[1:]

    is_question = any(p in words_lower for p in question_marks)
    
    if is_question:
        if not result.endswith('?'):
            result += '?'
    else:
        if not result.endswith('.'):
            result += '.'

    return result

