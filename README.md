# RV Thermostat - Dual ESP32 System

A DIY RV thermostat using two ESP32 microcontrollers to control three HVAC systems: furnace, rooftop AC, and Whynter portable AC/heater.

## Architecture

**ESP32 Main (192.168.71.152):**
- System orchestration and scheduling
- BMP280 sensor (temperature/pressure)
- SSD1306 OLED display
- Web interface
- Remote control via HTTP API

**ESP32 Remote (192.168.71.153):**
- HVAC hardware control
- BMP280 sensor (temperature/pressure)
- DHT11 sensor (humidity)
- SSD1306 OLED display
- 2-channel relay module (furnace + rooftop AC)
- IR transmitter/receiver (portable AC control)

## Wiring Diagrams

**ESP32 Main:** [wiring/esp32_main_wiring.svg](wiring/esp32_main_wiring.svg) - BMP280 and OLED connections

**ESP32 Remote:** [wiring/esp32_remote_wiring.svg](wiring/esp32_remote_wiring.svg) - Complete HVAC hardware wiring

Both diagrams include color-coded wiring and detailed hardware notes.

### ESP32 Main Wiring

| Component | Pin | ESP32 GPIO |
|-----------|-----|------------|
| BMP280 SDA | SDA | GPIO 21 |
| BMP280 SCL | SCL | GPIO 22 |
| BMP280 VCC | 3.3V | 3.3V |
| BMP280 GND | GND | GND |
| OLED SDA | SDA | GPIO 21 |
| OLED SCL | SCL | GPIO 22 |
| OLED VCC | 3.3V | 3.3V |
| OLED GND | GND | GND |

### ESP32 Remote Wiring

| Component | Pin | ESP32 GPIO |
|-----------|-----|------------|
| BMP280 SDA | SDA | GPIO 21 |
| BMP280 SCL | SCL | GPIO 22 |
| DHT11 Data | S | GPIO 4 |
| OLED SDA | SDA | GPIO 21 |
| OLED SCL | SCL | GPIO 22 |
| Relay IN1 | - | GPIO 25 (Furnace) |
| Relay IN2 | - | GPIO 26 (Rooftop AC) |
| IR LED | + | GPIO 18 |
| IR Receiver | OUT | GPIO 19 (optional) |

## Installation

### Prerequisites
- MicroPython firmware installed on both ESP32s
- mpremote installed: `pip install mpremote`
- Both ESP32s connected via USB

### ESP32 Main Setup

1. Create `config_local.py` with WiFi credentials:
   ```python
   WIFI_SSID = "YourNetwork"
   WIFI_PASSWORD = "YourPassword"
   ```

2. Deploy to ESP32 Main:
   ```bash
   source venv/bin/activate
   mpremote connect /dev/ttyUSB0 cp *.py :
   mpremote connect /dev/ttyUSB0 reset
   ```

### ESP32 Remote Setup

1. Create `esp32_remote/config_local.py` with WiFi credentials

2. Deploy using the script:
   ```bash
   ./deploy_esp32_remote.sh
   ```

3. Verify connection:
   ```bash
   curl http://192.168.71.153/api/status
   ```

### Testing

Test components:
```python
>>> import test
>>> test.test_all()
   ```

4. Run the thermostat:
   ```python
   >>> import main
   >>> main.main()
   ```

## Files

| File | Purpose |
|------|---------|
| config.py | All settings |
| bmp280.py | BMP280 driver |
| sensor.py | Combined BMP280+DHT11 |
| ssd1306.py | OLED driver |
| display.py | Screen layouts |
| thermostat.py | Control logic |
| webserver.py | Web interface |
| main.py | Entry point |
| test.py | Component tests |

## Web Interface

Open the IP address shown on the OLED in your phone browser.

Features:
- Current temperature, humidity, pressure
- Heat/cool setpoint adjustment
- Mode selection (Off/Heat/Cool/Auto)
- Cooling system selection (Rooftop/Portable)
