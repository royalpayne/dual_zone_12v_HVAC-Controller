# RV Thermostat - Dual ESP32-S3 HVAC Control System

A DIY RV thermostat using two ESP32-S3 microcontrollers to control three HVAC systems: propane furnace, Dometic Brisk II rooftop AC, and Whynter ARC-14SH portable AC/heater.

## Architecture

**Main ESP32-S3** (Kitchen, 192.168.71.152):
- System orchestration and scheduling
- BME280 sensor (temperature/humidity/pressure)
- SSD1306 OLED display
- Web interface with dual-zone control
- Auto-syncs settings to Remote

**Remote: Waveshare ESP32-S3-Relay-6CH** (Living Room, 192.168.71.153):
- HVAC hardware control via 6 built-in 10A relays
- BME280 sensor (temperature/humidity/pressure)
- SSD1306 OLED display
- DS18B20 evaporator freeze sensor
- Whynter + Dr. Heater IR control via Broadlink RM4 Mini

**Broadlink RM4 Mini** (192.168.71.155):
- WiFi IR blaster for Whynter portable AC and Dr. Infrared Heater
- Protocol-based Whynter commands (no learned codes needed)
- Raw captured codes for Dr. Heater

## Relay Wiring (Waveshare Remote)

| Channel | GPIO | Function |
|---------|------|----------|
| CH1 | 1 | Furnace (dry contact closure) |
| CH2 | 2 | Compressor (triggers SSR-25DA) |
| CH3 | 41 | Rooftop AC fan low speed |
| CH4 | 42 | Rooftop AC fan high speed |
| CH5 | 45 | Expansion (dehumidifier, disabled) |
| CH6 | 46 | Expansion (vent fan, disabled) |

## Sensor Wiring (via expansion header)

| Component | GPIO | Header Pin |
|-----------|------|------------|
| BME280 SDA | 8 | Pin 32 |
| BME280 SCL | 9 | Pin 34 |
| DS18B20 data | 10 | — (4.7K pull-up to 3.3V) |
| 3.3V | — | Pin 36 |
| GND | — | Pin 3/8/13 |

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
- **Remote (Waveshare)**: ESP32-S3 Standard v1.27.0 (no PSRAM)
