
import speech_recognition as sr
import sounddevice as sd
import hid.keyboard as keyboard
r = sr.Recognizer()
print("Inicializing microphone...")
while True:
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5) 
            audio = r.listen(source)
            #TO DO: Change spech recognition to offile model
            text = r.recognize_google(audio,language = "pl-PL") 
            text = text.lower()
            keyboard.Keyboard.send_string(text)
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Błąd połączenia z usługą rozpoznawani: {e}")
