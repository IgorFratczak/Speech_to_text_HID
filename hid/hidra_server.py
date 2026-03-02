import asyncio
import time
import os
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)
import Debug from hid.debug as DEBUG
SERVICE_UUID = "A1B2C3D4-E5F6-4890-81D2-13B4C5D6E7F8"
CHAR_UUID    = "B1B2C3D4-E5F6-4890-81D2-13B4C5D6E7F8"

class HidraConfigServer:
    def __init__(self):
        self.server = BlessServer(name="Hidra")
        self.on_model_change_callback = None

    def debug_log(self, message):
        if DEBUG.debug_status():
            print(f"[BLE][{time.strftime('%H:%M:%S')}]  {message}", flush=True)

    def save_wifi_credentials(self, ssid, password):
        """
        Fizyczna próba przełączenia WiFi za pomocą nmcli.
        """
        self.debug_log(f"Uruchamiam procedurę zmiany WiFi na: {ssid}...")
        
        cmd = f'sudo nmcli device wifi connect "{ssid}" password "{password}"'
        
        try: 
            result = os.system(cmd)
            
            if result == 0:
                self.debug_log(f"SUKCES: Połączono z siecią {ssid}!")
            else:
                self.debug_log(f"BŁĄD: Nie udało się połączyć z {ssid}. Kod błędu: {result}")
        except Exception as e:
            self.debug_log(f"Wyjątek podczas próby zmiany WiFi: {e}")

    def on_write(self, characteristic: BlessGATTCharacteristic, value: bytearray):
        try:
            msg = value.decode("utf-8").strip()
            self.debug_log(f"Odebrano dane: {msg}")

            if msg.startswith("MODEL:") and self.on_model_change_callback:
                model_name = msg.split(":")[1]
                self.debug_log(f"Zlecenie zmiany modelu na: {model_name}")
                self.on_model_change_callback(model_name)

            elif msg.startswith("WIFI:"):
                parts = msg.split(":")
                if len(parts) >= 3:
                    ssid = parts[1]
                    password = parts[2]
                    self.save_wifi_credentials(ssid, password)
                else:
                    self.debug_log("Błąd: Niekompletne dane WiFi (wymagany format WIFI:SSID:HASLO)")

        except Exception as e:
            self.debug_log(f"Błąd podczas przetwarzania zapisu: {e}")

    async def start(self, on_model_change_callback):
        self.on_model_change_callback = on_model_change_callback
        
        self.debug_log("Inicjalizacja usług GATT...")
        await self.server.add_new_service(SERVICE_UUID)
        
        await self.server.add_new_characteristic(
            SERVICE_UUID, CHAR_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable
        )

        self.server.write_request_func = self.on_write
        
        self.debug_log("Uruchamianie serwera BLE...")
        await self.server.start()
        
        self.debug_log("Serwer BLE uruchomiony i gotowy do odbierania danych.")
        self.debug_log(f"Udostępnianie konfiguracji modelu oraz WiFi na UUID: {CHAR_UUID}")
        
        while True:
            await asyncio.sleep(1)

def run_hidra_server(callback):
    """
    Funkcja startowa wywoływana z głównego skryptu (main.py)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = HidraConfigServer()
    try:
        loop.run_until_complete(server.start(callback))
    except KeyboardInterrupt:
        server.debug_log("Zatrzymywanie serwera...")
      