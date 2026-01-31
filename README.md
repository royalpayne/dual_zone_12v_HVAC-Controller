# RV Thermostat - Phase 1

A DIY RV thermostat using Raspberry Pi Pico W with web interface.

## Hardware

**Sensors:**
- BMP280 - Temperature and pressure (I2C)
- DHT11 - Humidity (GPIO 16)

**Display:**
- SSD1306 128x64 OLED (I2C)

**Control:**
- 2-channel relay module (GPIO 20, 21)
- IR LED for portable AC (GPIO 18) - Phase 2
- IR Receiver for learning codes (GPIO 19) - Phase 2

## Wiring

| Component | Pin | Pico GPIO |
|-----------|-----|-----------|
| BMP280 SDA | SDA | GPIO 0 |
| BMP280 SCL | SCL | GPIO 1 |
| BMP280 VCC | 3.3V | 3.3V |
| BMP280 GND | GND | GND |
| BMP280 CSB | - | 3.3V |
| BMP280 SDO | - | GND |
| DHT11 S | Data | GPIO 16 |
| DHT11 + | VCC | 3.3V |
| DHT11 - | GND | GND |
| OLED SDA | SDA | GPIO 0 |
| OLED SCL | SCL | GPIO 1 |
| Relay IN1 | - | GPIO 20 |
| Relay IN2 | - | GPIO 21 |

## Installation

1. Edit `config.py` with your WiFi credentials:
   ```python
   WIFI_SSID = "YourNetwork"
   WIFI_PASSWORD = "YourPassword"
   ```

2. Upload all `.py` files to the Pico using Thonny

3. Test components:
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
