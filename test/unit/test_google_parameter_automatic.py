import time
import psutil
import csv
import os
from hid.speech_recognizer import GoogleSpeechRecognizer
"""Automatyczne testy rozpoznawania mowy z użyciem Google Speech-to-Text API w czasie rzeczywistym."""
CSV_FILE = "google.csv"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read()) / 1000.0
    except:
        return 0.0

def load_csv_rows():
    """Wczytuje wszystkie wiersze z pliku CSV zachowując ich strukturę."""
    if not os.path.isfile(CSV_FILE):
        print(f"[BŁĄD] Plik {CSV_FILE} nie istnieje! Upewnij się, że wzorzec jest w tym samym folderze.")
        return [], []
    
    rows = []
    fieldnames = []
    with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    return rows, fieldnames

def save_all_to_csv(fieldnames, rows):
    """Zapisuje całą strukturę z powrotem do pliku CSV ze średnikami."""
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    recognizer = GoogleSpeechRecognizer()
    print("Inicjalizacja mikrofonu... Gotowy do automatycznych testów.")
    
    try:
        rows, fieldnames = load_csv_rows()
        if not rows:
            print("[KONIEC] Brak danych do przetworzenia.")
            exit()

        total_rows = len(rows)
        
        for index, row in enumerate(rows):
            if row.get("status") and row.get("status").strip() != "":
                continue
                
            print(f"\n" + "="*50)
            print(f"Postęp: {index + 1}/{total_rows} (ID: {row['id']})")
            print(f"Kategoria: {row['kategoria']}")
            print(f"FRAZA DO WYPOWIEDZENIA: \033[1;32m{row['tekst_wzorcowy']}\033[0m")
            print("="*50)

            print("\n[CZEKAM NA WYPOWIEDŹ] (Naciśnij Ctrl+C aby przerwać)...")
            
            # Zmienna do kontrolowania czasu spamu powiadomień (w sekundach)
            last_log_time = time.time()

            while True:
                start_proc = time.perf_counter()
                cpu_before = psutil.cpu_percent(interval=None)
                ram_before = psutil.virtual_memory().used / (1024 * 1024)
                
                result = recognizer.recognize_speech()
                
                end_proc = time.perf_counter()
                duration_proc = end_proc - start_proc
                
                if result:
                    cpu_after = psutil.cpu_percent(interval=None)
                    ram_after = psutil.virtual_memory().used / (1024 * 1024)
                    temp = get_cpu_temp()
                    
                    print(f"\nWYKRYTO: \033[1;33m{result}\033[0m")
                    potwierdzenie = input("Decyzja -> [t] - zalicz / [n] - powtórz nagranie / [p] - pomiń wiersz: ").lower().strip()
                    
                    if potwierdzenie == 't':
                        row["timestamp"] = time.strftime("%d.%m.%Y %H:%M")
                        row["tekst"] = result.strip()
                        row["cpu_usage_pct"] = round(cpu_after, 1)
                        row["ram_usage_mb"] = round(ram_after, 4)
                        row["temp_c"] = temp
                        row["processing_time_s"] = round(duration_proc, 4)
                        row["status"] = "OK"
                        
                        save_all_to_csv(fieldnames, rows)
                        print("[LOG] Zapisano wiersz do CSV.")
                        break
                        
                    elif potwierdzenie == 'p':
                        print("[LOG] Pominięto frazę na żądanie użytkownika.")
                        break 
                        
                    else:
                        print("[LOG] Odrzucono wynik. Powtarzamy tę samą frazę...")
                        print("\n[CZEKAM NA WYPOWIEDŹ] (Naciśnij Ctrl+C aby przerwać)...")
                        last_log_time = time.time() # Reset timera po odrzuceniu wyniku

                else:
                    # Sprawdzenie różnicy czasu - komunikat pojawi się tylko raz na 10 sekund ciszy
                    current_time = time.time()
                    if current_time - last_log_time >= 10.0:
                        print("[LOG] Cisza... Dalej czekam na dźwięk/frazę...")
                        last_log_time = current_time

        print("\n[SUKCES] Wszystkie puste pola zostały sprawdzone i uzupełnione!")

    except KeyboardInterrupt:
        print("\n\n[INFO] Przerwano działanie programu. Aktualny postęp został zachowany w pliku CSV.")