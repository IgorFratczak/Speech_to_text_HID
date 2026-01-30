import asyncio
import time
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

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

    def on_write(self, characteristic: BlessGATTCharacteristic, value: bytearray):
        try:
            msg = value.decode("utf-8").strip()
            self.log(f"Odebrano: {msg}")
            if msg.startswith("MODEL:") and self.on_model_change_callback:
                self.on_model_change_callback(msg.split(":")[1])
        except Exception as e:
            print(f"Błąd zapisu: {e}")

    async def start(self, on_model_change_callback):
        self.on_model_change_callback = on_model_change_callback
        await self.server.add_new_service(SERVICE_UUID)
        
        # Tylko Write i Write Without Response - najstabilniejsza opcja
        await self.server.add_new_characteristic(
            SERVICE_UUID, CHAR_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable
        )

        self.server.write_request_func = self.on_write
        await self.server.start()
        if self.debug:
            print("--- SERWER BLE AKTYWNY ---", flush=True)
        while True:
            await asyncio.sleep(1)

def run_hidra_server(debug_mode, callback):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = HidraConfigServer(debug_mode=debug_mode)
    loop.run_until_complete(server.start(callback))