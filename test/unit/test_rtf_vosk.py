import csv
import json
import os
import re
import sys
import time
import wave
import psutil
from vosk import Model, KaldiRecognizer, SetLogLevel
""" Testy rozpoznawania mowy z użyciem Vosk z użyciem zestawu danych WAV i odpowiadających plików TXT. Wyniki są zapisywane do pliku CSV z metrykami RTF i WER. """
# Path Configuration
DATASET_DIR = "../test_data/paczka_1000"       
MODEL_PATH = "model"               # Directory containing the Vosk model
OUTPUT_CSV = "vosk_benchmark.csv"  # Output CSV report path

# Attempt to load text post-processing function if available
try:
    from hid.speech_recognizer import process_raw_speech
except ImportError:
    def process_raw_speech(text):
        return text

def normalize_text(text: str) -> str:
    """Czyszczenie tekstu z interpunkcji, wielkich liter i podwójnych spacji."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_wer(reference: str, hypothesis: str) -> float:
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)

    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()

    if not ref_words and not hyp_words:
        return 0.0
    if not ref_words:
        return 100.0

    r_len = len(ref_words)
    h_len = len(hyp_words)

    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]

    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                substitution = dp[i - 1][j - 1] + 1
                insertion = dp[i][j - 1] + 1
                deletion = dp[i - 1][j] + 1
                dp[i][j] = min(substitution, insertion, deletion)

    return (dp[r_len][h_len] / float(r_len)) * 100.0

def get_cpu_temp() -> float:
    """Reads Raspberry Pi CPU temperature in degrees Celsius."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read()) / 1000.0
    except Exception:
        return 0.0

def run_benchmark():
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Vosk model directory not found at path '{MODEL_PATH}'")
        sys.exit(1)

    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset directory not found at path '{DATASET_DIR}'")
        sys.exit(1)

    SetLogLevel(-1)
    print("Loading Vosk model...")
    model = Model(MODEL_PATH)

    wav_files = sorted([f for f in os.listdir(DATASET_DIR) if f.endswith('.wav')])
    total_files = len(wav_files)
    
    if total_files == 0:
        print(f"No .wav files found in '{DATASET_DIR}'. Exiting.")
        sys.exit(1)

    print(f"Found {total_files} samples to process.")
    print(f"Processing and saving results to {OUTPUT_CSV}...\n")

    csv_headers = [
        "filename", 
        "audio_duration_s", 
        "inference_time_s", 
        "rtf", 
        "wer", 
        "reference_text", 
        "predicted_text",
        "cpu_percent", 
        "cpu_temp_c"
    ]

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_headers)

        total_audio_time = 0.0
        total_proc_time = 0.0
        wer_list = []

        for idx, wav_filename in enumerate(wav_files, start=1):
            base_name = os.path.splitext(wav_filename)[0]
            txt_filename = base_name + ".txt"
            wav_path = os.path.join(DATASET_DIR, wav_filename)
            txt_path = os.path.join(DATASET_DIR, txt_filename)

            reference_text = ""
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    reference_text = f.read().strip()

            try:
                with wave.open(wav_path, "rb") as wf:
                    sample_rate = wf.getframerate()
                    n_frames = wf.getnframes()
                    audio_duration = n_frames / float(sample_rate)
                    raw_bytes = wf.readframes(n_frames)
            except Exception as e:
                print(f"[{idx}/{total_files}] Skipping {wav_filename} (Failed to read audio): {e}")
                continue

            cpu_before = psutil.cpu_percent(interval=None)
            t0 = time.perf_counter()

            recognizer = KaldiRecognizer(model, sample_rate)
            recognizer.AcceptWaveform(raw_bytes)
            result = json.loads(recognizer.FinalResult())
            
            t1 = time.perf_counter()
            cpu_after = psutil.cpu_percent(interval=None)
            cpu_temp = get_cpu_temp()

            inference_time = t1 - t0
            rtf = inference_time / audio_duration if audio_duration > 0 else 0.0

            raw_predicted = result.get("text", "").strip()
            predicted_text = process_raw_speech(raw_predicted)

            wer = calculate_wer(reference_text, predicted_text)

            total_audio_time += audio_duration
            total_proc_time += inference_time
            wer_list.append(wer)

            writer.writerow([
                wav_filename,
                f"{audio_duration:.3f}",
                f"{inference_time:.3f}",
                f"{rtf:.4f}",
                f"{wer:.4f}",
                reference_text,
                predicted_text,
                f"{cpu_after:.1f}",
                f"{cpu_temp:.1f}"
            ])

            print(f"[{idx}/{total_files}] {wav_filename} | Duration: {audio_duration:.2f}s | Infer: {inference_time:.2f}s | RTF: {rtf:.3f} | WER: {wer:.2f}%")

    avg_rtf = total_proc_time / total_audio_time if total_audio_time > 0 else 0.0
    avg_wer = sum(wer_list) / len(wer_list) if wer_list else 0.0

    print("\n================ BENCHMARK SUMMARY ================")
    print(f"Samples Processed : {len(wer_list)}")
    print(f"Total Audio Time  : {total_audio_time:.2f} s")
    print(f"Total Infer Time  : {total_proc_time:.2f} s")
    print(f"Overall Average RTF: {avg_rtf:.4f}")
    print(f"Overall Average WER: {avg_wer:.2f}%")
    print(f"Detailed CSV Report saved to: {OUTPUT_CSV}")
    print("===================================================\n")

if __name__ == "__main__":
    run_benchmark()