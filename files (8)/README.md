# RV Thermostat v2 - ESP32 + Pico W

A Nest-style smart thermostat for RVs with scheduling, dual temperature zones, and wireless relay control.

## Architecture

```
[ESP32 - Main Controller]        [Pico W - Trigger]
├─ BMP280 (temp/pressure)        ├─ DHT11 (temp/humidity)
├─ DHT11 (humidity)              ├─ Furnace relay
├─ OLED display                  └─ Rooftop AC relay
├─ IR transmitter (Whynter)
├─ Web interface
├─ Thermostat logic
└─ Scheduler (Home/Away/Sleep)
        │
        └──────── WiFi ─────────────┘
```

## Features

- **Dual temperature zones**: Kitchen (ESP32) + Living Room (Pico W)
- **Average temperature control**: Uses average of both sensors
- **Nest-style scheduling**: Home/Away/Sleep modes
- **Weekly programming**: Different schedules for each day
- **Quick mode switching**: Instantly switch to Home/Away/Sleep
- **Hold function**: Temporary override with optional timer
- **Mobile web interface**: Works on any phone/tablet
- **Wireless relay control**: No wires between units

## ESP32 Main Controller

### Wiring

| Component | ESP32 Pin |
|-----------|-----------|
| BMP280 SDA | GPIO 21 |
| BMP280 SCL | GPIO 22 |
| OLED SDA | GPIO 21 (shared I2C) |
| OLED SCL | GPIO 22 (shared I2C) |
| DHT11 Data | GPIO 4 |
| IR LED | GPIO 18 |
| IR Receiver | GPIO 19 |

### Files to Upload

```
esp32_main/
├── config.py      # Settings - EDIT WIFI HERE
├── main.py        # Entry point
├── bmp280.py      # Sensor driver
├── ssd1306.py     # OLED driver
├── scheduler.py   # Time-based control
├── thermostat.py  # Control logic
└── webserver.py   # Web interface
```

### Setup

1. Flash MicroPython to ESP32
2. Edit `config.py`:
   - Set `WIFI_SSID` and `WIFI_PASSWORD`
   - Set `PICO_IP` to your Pico's IP address
   - Adjust `TIMEZONE_OFFSET` for your location
3. Upload all files to ESP32
4. Reset - note the IP address shown

## Pico W Trigger

### Wiring

| Component | Pico Pin |
|-----------|----------|
| DHT11 Data | GPIO 16 |
| Relay IN1 (Furnace) | GPIO 20 |
| Relay IN2 (Rooftop) | GPIO 21 |
| Relay VCC | 5V (VBUS) |
| Relay GND | GND |

### Files to Upload

```
pico_trigger/
└── main.py    # EDIT WIFI CREDENTIALS
```

### Setup

1. Edit `main.py`:
   - Set `WIFI_SSID` and `WIFI_PASSWORD`
2. Upload `main.py` to Pico W
3. Reset - note the IP address
4. Update ESP32's `config.py` with Pico's IP

## Web Interface

Open the ESP32's IP address in your browser.

### Main Screen

- Current time and day
- Average temperature (large display)
- Both zone temperatures and humidity
- Current status (Heating/Cooling/Idle)
- Schedule mode indicator
- Quick mode buttons (Home/Away/Sleep/Resume)
- Heat and cool setpoint adjusters
- System mode (Off/Heat/Cool/Auto)
- Cooling system selector (Rooftop/Portable)

### Schedule Editor

Click "Edit Schedule" to access:

- Enable/disable scheduling
- Set temperatures for Home/Away/Sleep modes
- Edit daily schedules (add/remove time entries)

## Default Schedule

| Day | Schedule |
|-----|----------|
| Mon-Fri | 6am Home → 8am Away → 5pm Home → 10pm Sleep |
| Sat-Sun | 7am Home → 10/11pm Sleep |

## Default Temperatures

| Mode | Heat | Cool |
|------|------|------|
| Home | 70°F | 74°F |
| Away | 62°F | 80°F |
| Sleep | 66°F | 72°F |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Full status JSON |
| `/api/mode` | POST | Set mode (v: 0-3) |
| `/api/heat` | POST | Adjust heat (v: delta) |
| `/api/cool` | POST | Adjust cool (v: delta) |
| `/api/quick` | POST | Quick mode (v: 0-2, h: hours) |
| `/api/resume` | POST | Clear hold |
| `/api/sched_en` | POST | Enable schedule (v: bool) |
| `/api/sched_temps` | POST | Set mode temps |
| `/api/sched_day` | POST | Set day schedule |

## Troubleshooting

### ESP32 can't reach Pico

- Verify both are on same WiFi network
- Check Pico's IP in ESP32's `config.py`
- Test: open Pico's IP directly in browser

### Time not syncing

- Check WiFi connection
- NTP may be blocked - try different `NTP_HOST`
- Time will still work, just wrong timezone

### Schedule not changing temperatures

- Verify schedule is enabled (toggle in Schedule page)
- Check if a Hold is active
- Clear hold with "Resume" button
