import time
import psutil
import csv
import threading
import os
from hid.speech_recognizer import GoogleSpeechRecognizer
from hid.keyboard import Keyboard
"""Testy rozpoznawania mowy z użyciem Google Speech-to-Text API w czasie rzeczywistym z automatycznym logowaniem wyników do pliku CSV. Bez czytania z pliku csv."""
CSV_FILE = "wyniki_testow.csv"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read()) / 1000.0
    except:
        return 0.0

def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

if __name__ == "__main__":
    recognizer = GoogleSpeechRecognizer()
    print("Inicjalizacja mikrofonu... Gotowy do testów.")
    
    try:
        print("\n[CZEKAM NA WYPOWIEDŹ] (Naciśnij Ctrl+C aby przerwać)")

        while True:

            start_proc = time.perf_counter()
            cpu_before = psutil.cpu_percent(interval=None)
            ram_before = psutil.virtual_memory().used / (1024 * 1024) # MB
            

            result = recognizer.recognize_speech()
            
            end_proc = time.perf_counter()
            duration_proc = end_proc - start_proc
            
            if result:
                cpu_after = psutil.cpu_percent(interval=None)
                ram_after = psutil.virtual_memory().used / (1024 * 1024)
                temp = get_cpu_temp()
                rtf = duration_proc / duration_proc 
                
                print(f"\nWYKRYTO: {result}")
                potwierdzenie = input("Czy zaliczyć ten test? (t/n): ").lower()
                
                if potwierdzenie == 't':
                    
                    log_data = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tekst": result,
                        "cpu_usage_pct": cpu_after,
                        "ram_usage_mb": ram_after,
                        "temp_c": temp,
                        "processing_time_s": round(duration_proc, 4),
                        "status": "OK"
                    }
                    save_to_csv(log_data)
                    print("[LOG] Zapisano do CSV.")
                else:
                    print("[LOG] Odrzucono błąd rozpoznawania.")
                    
    except KeyboardInterrupt:
        print("\nZamykanie i generowanie raportu...")