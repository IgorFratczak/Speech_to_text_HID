import asyncio
import os
import subprocess
import time
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

# UUID MUSZĄ BYĆ IDENTYCZNE JAK W ANDROIDZIE
SERVICE_UUID = "A1B2C3D4-E5F6-4890-81D2-13B4C5D6E7F8"
CHAR_UUID    = "B1B2C3D4-E5F6-4890-81D2-13B4C5D6E7F8"

def apply_wifi(ssid, password):
    print(f"--- PRÓBA ZMIANY WIFI NA: {ssid} ---", flush=True)
    
    # nmcli spróbuje się połączyć. Jeśli ma już profil o tej nazwie, nadpisze go.
    cmd = f'sudo nmcli dev wifi connect "{ssid}" password "{password}"'
    
    try:
        # Timeout 25s, aby dać czas na DHCP, ale nie zablokować skryptu na amen
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25)
        
        if process.returncode == 0:
            print(f"SUKCES: Połączono z {ssid}!", flush=True)
            # Pobieramy nowe IP, żeby wiedzieć gdzie się połączyć przez SSH
            ip_cmd = "hostname -I | cut -d' ' -f1"
            new_ip = subprocess.check_output(ip_cmd, shell=True).decode().strip()
            print(f"NOWY ADRES IP: {new_ip}", flush=True)
        else:
            print(f"BŁĄD: Nie udało się połączyć. Log: {process.stderr}", flush=True)
            
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Sieć nie odpowiedziała na czas.", flush=True)
async def run():
    server = BlessServer(name="Hidra-Pi")
    loop = asyncio.get_event_loop() # Pobieramy pętlę tutaj

    def on_write(characteristic: BlessGATTCharacteristic, value: bytearray):
        print(f"BŁYSK! Odebrano bajty: {list(value)}", flush=True)
        try:
            msg = value.decode("utf-8")
            print(f"Tekst: {msg}", flush=True)

            if msg.startswith("WIFI:"):
                parts = msg.split(":")
                if len(parts) >= 3:
                    ssid = parts[1]
                    password = parts[2]
                    print(f"Zlecono zmianę WiFi na {ssid}...", flush=True)
                    # Używamy pętli bezpośrednio, aby uruchomić funkcję w tle
                    loop.run_in_executor(None, apply_wifi, ssid, password)

            elif msg.startswith("MODEL:"):
                model = msg.split(":")[1]
                print(f"Zmieniam model na: {model}", flush=True)

        except Exception as e:
            print(f"Błąd w on_write: {e}", flush=True)

    # Reszta bez zmian
    await server.add_new_service(SERVICE_UUID)
    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_UUID,
        GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
        None,
        GATTAttributePermissions.writeable
    )

    server.write_request_func = on_write
    await server.start()
    print("SERWER HIDRA GOTOWY!", flush=True)
    
    while True:
        await asyncio.sleep(1)
if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nZamykanie serwera przez użytkownika...")
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")