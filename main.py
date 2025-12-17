
import speech_recognition as sr
import sounddevice as sd
# Inicjalizacja rozpoznawania
r = sr.Recognizer()
print("Słucham... ")
# Pętla nasłuchująca mikrofonu
while True:
    try:
        with sr.Microphone() as source:
            
            
            # Dostosowanie do szumów otoczenia
            r.adjust_for_ambient_noise(source, duration=0.5) #duration zmiana czasu próbkowania
            
            # Nagrywanie mowy użytkownika
            audio = r.listen(source)
            
            # Rozpoznanie mowy (Google Speech Recognition)
            text = r.recognize_google(audio,language = "pl-PL") #language="pl-PL"
            text = text.lower()

            print("Rozpoznano:", text)

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Błąd połączenia z usługą rozpoznawania: {e}")
