# RV Thermostat - Dual ESP32-S3 HVAC Control System

A DIY RV thermostat using two ESP32-S3 microcontrollers to control three HVAC systems: propane furnace, Dometic Brisk II rooftop AC, and Whynter ARC-14SH portable AC/heater.

## Architecture

**Main ESP32-S3** (Kitchen, 192.168.71.152):
- System orchestration and scheduling
- BME280 sensor (temperature/humidity/pressure)
- SSD1306 OLED display
- Web interface with dual-zone control
- Auto-syncs settings to Remote

**Remote ESP32-S3 N16R8** (Living Room, 192.168.71.153):
- HVAC hardware control via external 4-channel relay module
- BME280 sensor (temperature/humidity/pressure)
- SSD1306 OLED display
- DS18B20 evaporator freeze sensor
- Whynter + Dr. Heater IR control via Broadlink RM4 Mini

**Broadlink RM4 Mini** (192.168.71.155):
- WiFi IR blaster for Whynter portable AC and Dr. Infrared Heater
- Protocol-based Whynter commands (no learned codes needed)
- Raw captured codes for Dr. Heater

## Relay Wiring (4-Channel Module, Active HIGH)

| Relay | GPIO | Function |
|-------|------|----------|
| 1 | 4 | Furnace (dry contact closure) |
| 2 | 5 | Compressor (triggers SSR-25DA) |
| 3 | 6 | Rooftop AC fan low speed |
| 4 | 15 | Rooftop AC fan high speed |

## Sensor Wiring

| Component | GPIO | Notes |
|-----------|------|-------|
| BME280 SDA | 41 | I2C bus |
| BME280 SCL | 40 | I2C bus |
| DS18B20 data | 42 | 4.7K pull-up to 3.3V |
| RGB LED | 48 | WS2812 NeoPixel (onboard) |

## Deployment

### OTA (preferred)
```bash
python3 deploy_ota.py remote          # Deploy + restart Remote
python3 deploy_ota.py main            # Deploy + restart Main
python3 deploy_ota.py both            # Deploy + restart both
python3 deploy_ota.py restart remote  # Restart only
```

### USB Serial
```bash
mpremote connect /dev/ttyACM0 cp *.py :         # Main
mpremote connect /dev/ttyACM1 cp *.py :         # Remote
```

## Web Interface

Open the IP address shown on the OLED in your browser.

Features:
- Current temperature, humidity, pressure (both zones)
- Heat/cool setpoint adjustment
- Mode selection (Off/Heat/Cool/Auto)
- Whynter portable AC boost control
- Dr. Infrared Heater control
- Auto-sync toggle (Kitchen → Living Room)
- Force All Off emergency shutdown

## API Endpoints

### Main ESP32 (Kitchen)
- `GET /api/status` — Thermostat status
- `POST /api/mode` — Set mode (off/heat/cool/auto)
- `POST /api/heat_setpoint` — Set heat setpoint
- `POST /api/cool_setpoint` — Set cool setpoint
- `POST /api/sync_enabled` — Toggle auto-sync

### Remote ESP32 (Living Room)
- `GET /api/status` — Thermostat + sensor status
- `POST /api/mode` — Set mode
- `GET /api/whynter?power=on|off` — Whynter control
- `GET /api/heater?power=on|off` — Heater control
- `GET /api/force_all_off` — Emergency shutdown

## MicroPython Firmware

- **Main**: ESP32-S3 SPIRAM-OCT v1.27.0 (has 8MB PSRAM)
- **Remote (N16R8)**: ESP32-S3 SPIRAM-OCT v1.27.0 (has 8MB PSRAM)
