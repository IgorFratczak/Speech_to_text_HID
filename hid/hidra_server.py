import asyncio
import time
import os
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

# UUID muszą być identyczne jak w aplikacji na Androidzie
SERVICE_UUID = "A1B2C3D4-E5F6-4890-81D2-13B4C5D6E7F8"
CHAR_UUID    = "B1B2C3D4-E5F6-4890-81D2-13B4C5D6E7F8"

class HidraConfigServer:
    def __init__(self, debug_mode=True):
        self.debug = debug_mode
        self.server = BlessServer(name="Hidra-Pi")
        self.on_model_change_callback = None

    def log(self, message):
        if self.debug:
            print(f"[{time.strftime('%H:%M:%S')}] [BLE] {message}", flush=True)

    def save_wifi_credentials(self, ssid, password):
        """
        Fizyczna próba przełączenia WiFi za pomocą nmcli.
        """
        self.log(f"Uruchamiam procedurę zmiany WiFi na: {ssid}...")
        
        # Komenda nmcli do połączenia z nową siecią
        # --wait 10 sprawia, że nmcli poczeka 10 sekund na wynik połączenia
        cmd = f'sudo nmcli device wifi connect "{ssid}" password "{password}"'
        
        try:
            # Uruchamiamy komendę w systemie
            result = os.system(cmd)
            
            if result == 0:
                self.log(f"SUKCES: Połączono z siecią {ssid}!")
            else:
                self.log(f"BŁĄD: Nie udało się połączyć z {ssid}. Kod błędu: {result}")
        except Exception as e:
            self.log(f"Wyjątek podczas próby zmiany WiFi: {e}")

    def on_write(self, characteristic: BlessGATTCharacteristic, value: bytearray):
        try:
            msg = value.decode("utf-8").strip()
            self.log(f"Odebrano dane: {msg}")

            # Obsługa zmiany modelu (MODEL:NAZWA)
            if msg.startswith("MODEL:") and self.on_model_change_callback:
                model_name = msg.split(":")[1]
                self.log(f"Zlecenie zmiany modelu na: {model_name}")
                self.on_model_change_callback(model_name)

            # Obsługa konfiguracji WiFi (WIFI:SSID:PASSWORD)
            elif msg.startswith("WIFI:"):
                parts = msg.split(":")
                if len(parts) >= 3:
                    ssid = parts[1]
                    password = parts[2]
                    self.save_wifi_credentials(ssid, password)
                else:
                    self.log("Błąd: Niekompletne dane WiFi (wymagany format WIFI:SSID:HASLO)")

        except Exception as e:
            self.log(f"Błąd podczas przetwarzania zapisu: {e}")

    async def start(self, on_model_change_callback):
        self.on_model_change_callback = on_model_change_callback
        
        self.log("Inicjalizacja usług GATT...")
        await self.server.add_new_service(SERVICE_UUID)
        
        # Konfiguracja charakterystyki: Zapisywanie z potwierdzeniem i bez
        await self.server.add_new_characteristic(
            SERVICE_UUID, CHAR_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable
        )

        self.server.write_request_func = self.on_write
        
        self.log("Uruchamianie serwera BLE...")
        await self.server.start()
        
        if self.debug:
            print("--- SERWER HIDRA-PI AKTYWNY (BLE) ---", flush=True)
            print(f"Udostępnianie modelu oraz konfiguracji WiFi na UUID: {CHAR_UUID}")
        
        # Pętla utrzymująca serwer przy życiu
        while True:
            await asyncio.sleep(1)

def run_hidra_server(debug_mode, callback):
    """
    Funkcja startowa wywoływana z głównego skryptu (main.py)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = HidraConfigServer(debug_mode=debug_mode)
    try:
        loop.run_until_complete(server.start(callback))
    except KeyboardInterrupt:
        print("\nZamykanie serwera BLE...")