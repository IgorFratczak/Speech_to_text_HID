# Speech_to_text_HID

  

## Przegląd


**Speech-to-Text HID**  to rozwiązanie sprzętowe zaprojektowane do konwersji słów wypowiadanych w czasie rzeczywistym na sygnały klawiatury USB.

  

Dzięki wykorzystaniu protokołu **HID (Human Interface Device)**, urządzenie jest rozpoznawane przez każdy komputer jako standardowa klawiatura fizyczna. Pozwala to na „pisanie” głosem w dowolnym oprogramowaniu (Word, Excel, przeglądarki internetowe czy terminale) bez konieczności instalowania dodatkowych sterowników lub oprogramowania firm trzecich na komputerze docelowym.

  

## Kluczowe funkcje

  

-   **Transkrypcja w czasie rzeczywistym:** Natychmiastowa konwersja mowy na tekst przy minimalnych opóźnieniach.
    
-   **Plug & Play:** Kompatybilność z systemami Windows, macOS, Linux i Android od razu po podłączeniu.
    
-   **Emulacja sprzętowa:** System wprowadza tekst bezpośrednio w miejscu skupienia kursora, dokładnie tak jak klawiatura mechaniczna.
    
-   **Zero śladów (Zero-Footprint):** Idealne rozwiązanie dla środowisk o ograniczonym dostępie (np. komputery służbowe), gdzie instalacja oprogramowania do rozpoznawania mowy jest zabroniona.

  

## Jak to działa

Projekt opiera się na trzystopniowym procesie przetwarzania:

1.  **Przechwytywanie dźwięku:** Wysokiej jakości mikrofon odbiera sygnał głosowy.
    
2.  **Rozpoznawanie mowy:** Dźwięk jest przetwarzany przez silnik STT (Speech-to-Text) w celu wygenerowania danych tekstowych.
    
3.  **Mapowanie HID:** Tekst jest konwertowany na kody skanowania (scancodes) klawiatury USB i przesyłany do komputera hosta.


## Wymagania sprzętowe

-   **Raspberry Pi 5 - 2/4/8/16GB RAM**
    
-   **Mikrofon z kartą dźwiękową (lub dodatkowa karta dźwiękowa USB)**
    
-   **Kabel USB-A do USB-C z obsługą przesyłania danych i ładowania**
    
-   **Karta MicroSD 32GB**
    
-   **Czytnik kart Micro SD**

  


## Opcjonalnie

-   **Adapter kabla Micro HDMI do HDMI**
    
-   **Zasilacz Raspberry Pi 27W USB-C**

  


## Pierwsze kroki
Poniższa procedura opisuje proces przekształcenia Raspberry Pi w urządzenie typu **USB Gadget**. Wymaga to modyfikacji parametrów jądra (kernel) oraz konfiguracji modułów systemowych.

**Zainstaluj Raspberry Pi OS** na karcie microSD. Podczas instalacji włącz SSH. Jeśli tego nie zrobiłeś, dodaj pusty plik o nazwie `ssh` (bez rozszerzenia) do folderu `boot`.
    
**Uruchom Raspberry Pi** i połącz je z internetem. Zanotuj adres IP urządzenia. Zainstaluj aplikację Xshell lub dodatek Remote - SSH w Visual Studio Code na urządzeniu głównym. Połącz się z adresem IP Raspberry Pi.
    
**Przełącz się na użytkownika root:** `sudo -i`
    
 **Użyj edytora nano, aby edytować:** `/boot/firmware/config.txt`
    
    nano /boot/firmware/config.txt

Na końcu pliku dodaj:

    dtoverlay=dwc2`
    nano /boot/firmware/config.txt

Zakomentuj następujące linie (dodaj `#` na początku każdej z nich):

    #camera_auto_detect=1
    #display_auto_detect=1
    #dtoverlay=vc4-kms-v3d
    #max_framebuffers=2


Po restarcie obsługa Raspberry Pi poprzez interfejs graficzny (HDMI) nie będzie możliwa. Komunikacja odbywać się będzie wyłącznie przez terminal .

Aby zapisać plik, naciśnij `Ctrl + X`, następnie `Y`, aby potwierdzić i `Enter`, aby wyjść.

**Edytuj plik** `/boot/firmware/cmdline.txt`
    
    nano /boot/firmware/cmdline.txt

Na końcu pliku (w tej samej linii) dodaj:

    modules-load=dwc2

**Edytuj plik** `/etc/modules`
    

    nano /etc/modules

Na końcu pliku dodaj:

    libcomposite

 **Zrestartuj RPi. Po restarcie powinno wejść w tryb USB gadget.**
    

    reboot

Aby potwierdzić, uruchom komendę:

    ls /sys/class/udc

Jeśli wynik wygląda jak `1000480000.usb`, RPi działa poprawnie w trybie gadget.

  


## Tworzenie interfejsów HID

Ostatnim krokiem konfiguracji jest zdefiniowanie deskryptorów USB oraz utworzenie interfejsów HID dla urządzenia typu "gadget".

W konsoli RPi utwórz nowy plik skryptu `.sh`:

    nano /home/hid.sh

Wklej do niego następującą zawartość :

    #!/bin/bash
    cd /sys/kernel/config/usb_gadget/
    sudo mkdir -p hidg
    cd hidg
    
    sudo bash -c 'echo "0x1d6b" > idVendor'  
    sudo bash -c 'echo "0x0104" > idProduct' # Multifunction Composite Gadget
    sudo bash -c 'echo "0x0100" > bcdDevice' # Version 1.0.0
    sudo bash -c 'echo "0x0200" > bcdUSB'    # USB2
    
    sudo mkdir -p strings/0x409
    sudo bash -c 'echo "SN0001" > strings/0x409/serialnumber'
    sudo bash -c 'echo "HIDRA_LABS" > strings/0x409/manufacturer'
    sudo bash -c 'echo "HIDRA_Keyboard_Interface" > strings/0x409/product'
    
    sudo mkdir -p configs/c.1
    sudo bash -c 'echo "0x80" > configs/c.1/bmAttributes'
    sudo bash -c 'echo "250" > configs/c.1/MaxPower'
    
    
    sudo mkdir -p functions/hid.usb0
    sudo bash -c 'echo 1 > functions/hid.usb0/protocol'    
    sudo bash -c 'echo 1 > functions/hid.usb0/subclass'    
    sudo bash -c 'echo 8 > functions/hid.usb0/report_length'
    
    sudo bash -c 'echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc'
    
    sudo ln -s functions/hid.usb0 configs/c.1/
    
    sudo bash -c 'ls /sys/class/udc > UDC'
Następnie należy uruchomić skrypt:

    sh /home/hid.sh


  Po tym etapie dodane zostanie wykryte urządzenie HID do urządzenia host.



# Weryfikacja i Testowanie Interfejsów HID

Po pomyślnej konfiguracji deskryptorów USB, należy przeprowadzić walidację komunikacji między Raspberry Pi, a systemem host. Proces ten potwierdza poprawność emulacji fizycznej klawiatury.

### Pobranie repozytorium

W celu uzyskania dostępu do projektu, sklonuj repozytorium projektu:

    git clone https://github.com/IgorFratczak/Speach_to_text_HID.git
    cd Speech_to_text_HID

### Uruchomienie testów diagnostycznych

Do weryfikacji warstwy sprzętowej służy dedykowany test jednostkowy. Skrypt ten omija silnik rozpoznawania mowy i wysyła bezpośrednie pakiety danych do sterownika jądra `/dev/hidg0`.

Uruchom test przy użyciu interpretera wewnątrz środowiska wirtualnego:

    sudo ./venv/bin/python3 -m test.unit.test_gadget_mode

### Procedura weryfikacji

Aby poprawnie zinterpretować wynik testu, postępuj zgodnie z poniższymi krokami:

1.  **Aktywacja kursora:** Na komputerze hosta otwórz dowolny edytor tekstu i upewnij się, że okno jest aktywne.
    
2.  **Transmisja danych:** Po uruchomieniu skryptu, Raspberry Pi wyśle sekwencję kodów klawiszy.
    
3.  **Oczekiwany rezultat:** W aktywnym oknie edytora powinien pojawić się automatycznie wpisany tekst testowy.
 

# Instalacja wymaganych bibliotek

Poniższe kroki są niezbędne do prawidłowego przygotowania środowiska uruchomieniowego projektu. Należy wykonać je kolejno w terminalu:

    python3 -m venv venv
    sudo apt update
    sudo apt install libportaudio2
    ./venv/bin/pip install sounddevice
    ./venv/bin/pip install evdev
    ./venv/bin/pip install pyudev
    ./venv/bin/pip install SpeechRecognition
    ./venv/bin/pip install vosk
    ./venv/bin/pip install bless
    wget https://alphacephei.com/vosk/models/vosk-model-small-pl-0.22.zip
    unzip vosk-model-small-pl-0.22.zip
    mv vosk-model-small-pl-0.22 model
    rm vosk-model-small-pl-0.22.zip
    sudo apt install portaudio19-dev
    ./venv/bin/pip install pyaudio

Po poprawnym zainstalowaniu bibliotek, aplikacje można uruchomić za pomocą komendy:

    sudo ./venv/bin/python3 -m main

  ## Konfiguracja autostartu 

Aby projekt uruchamiał się automatycznie po włączeniu zasilania, należy skonfigurować usługę systemową.
Utwórz nowy plik konfiguracyjny dla systemd:

    sudo nano /etc/systemd/system/hid_project.service

Wklej do niego poniższą zawartość (w linijce  `ExecStart=/bin/bash` należy zmienić ścieżkę na właściwą) :


    [Unit]
    Description=HIDRA Speech-to-Text HID Device
    After=network.target
    
    [Service]
    Type=simple
    ExecStart=/bin/bash /home/igor/Desktop/Speech_to_text_HID/run_hid.sh
    Restart=always
    RestartSec=5
    User=root
    
    [Install]
    WantedBy=multi-user.target 

Zmień ścieżkę w pliku `run_hid.sh` na adres projektu.
  Następnie należy wykonać kolejno komendy:

      sudo systemctl daemon-reload
      sudo systemctl enable hid_project.service
      sudo systemctl start hid_project.service
Po tym etapie, system Rpi będzie automatycznie włączam aplikację po włączeniu.

## Przydatne komendy do zarządzania usługą

Poniżej znajduje się lista komend niezbędnych do administracji, diagnostyki oraz sterowania procesem autostartu aplikacji.

### 1. Zarządzanie procesem systemowym

**Przeładowanie konfiguracji**

`sudo systemctl daemon-reload`

**Włączenie autostartu**

`sudo systemctl enable hid_project.service`

**Wyłączenie autostartu**

`sudo systemctl disable hid_project.service`

**Restart usługi**

`sudo systemctl restart hid_project.service`

**Zatrzymanie usługi**

`sudo systemctl stop hid_project.service`

**Sprawdzenie statusu**

`sudo systemctl status hid_project.service`

### 2. Diagnostyka (Czarna Skrzynka)

Jeśli system nie zachowuje się poprawnie, użyj poniższej komendy, aby przejrzeć ostatnie 50 wpisów w logach systemowych bez konieczności przewijania:

```
journalctl -u hid_project.service -n 50 --no-pager
```

### 3. Całkowite zatrzymanie procesów

W przypadku konieczności nagłego przerwania działania wszystkich procesów Python oraz usługi:


```
# Zatrzymanie usługi systemowej
sudo systemctl stop hid_project.service

# Wymuszenie zamknięcia wszystkich aktywnych procesów Python
sudo pkill -9 python3

```

### 4. Monitorowanie procesów

Aby sprawdzić, jakie procesy Python są aktualnie uruchomione w systemie i jakie zasoby zużywają:


```
ps aux | grep python
```




