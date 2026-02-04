# RV Thermostat Project - Claude Memory

## Project Overview
A DIY smart RV thermostat system controlling three HVAC systems (furnace, rooftop AC, and Whynter portable AC/heater) using dual microcontrollers (ESP32 + ESP32).

---

## Architecture

### Hardware Stack

**ESP32 Main Controller**:
- ESP32 microcontroller
- BMP280 sensor (temp/pressure) - to be upgraded to BME280
- SSD1306 OLED 128x64 display
- No relays, no DHT11, no IR hardware

**ESP32 Remote Controller**:
- ESP32 microcontroller
- BMP280 sensor (temp/pressure) - to be upgraded to BME280
- DHT11 sensor (humidity)
- SSD1306 OLED 128x64 display
- 2-channel relay module (active-low)
- 38kHz IR LED transmitter (GPIO 18)
- IR receiver (GPIO 19, optional)

### Software Stack
- **Language**: MicroPython
- **Communication**: HTTP/REST APIs over WiFi
- **Data Persistence**: JSON files (IR codes, schedules)
- **Deployment**: mpremote, esptool

---

## Dual Controller Design

### ESP32 (Main Unit)
- Full system orchestration
- Web server and UI
- Nest-style scheduling
- Sensor monitoring
- Remote control of ESP32 Remote via HTTP API

### ESP32 (Remote Unit)
- Wireless relay control (furnace/rooftop AC)
- IR control of Whynter portable AC
- Local sensors and OLED
- HTTP API server
- Independent operation capability

**Why Two Controllers?**
- Distributed architecture provides redundancy
- Wireless communication allows flexible placement
- Allows modular expansion of system

---

## Key Features

### Climate Control
- **Multi-zone monitoring**: BMP280 sensors on both ESP32s for temperature/pressure
- **Three HVAC systems** (all controlled by Remote ESP32):
  - Furnace (relay on GPIO 25)
  - Rooftop AC (relay on GPIO 26)
  - Whynter ARC-14SH portable AC/heater (IR control on GPIO 18)

### Control Logic
- **Hysteresis**: 1.5°F prevents rapid cycling
- **Short-cycle protection**: 3-minute minimum between state changes
- **Modes**: OFF, HEAT, COOL, AUTO
- **Default setpoints**: Heat 68°F, Cool 75°F
- **Boost mode**: Auto-activates portable AC when temp > setpoint + 10°F

### Scheduling
- Nest-style time-based modes (Home/Away/Sleep)
- Configurable temperature setpoints per mode
- Day/time-based rule engine

### IR Control (Whynter)
- **Learned commands**: power, mode, temp_up, temp_down, fan
- **State tracking**: Maintains AC state in `ir_state.json`
- **Smart control**: Can achieve any target state from any starting point
- **Capabilities**: Set specific temps, fan speeds, heating/cooling modes

---

## Project Structure

```
/home/heath/Dev/rv_thermostat/
├── main.py (ESP32 entry point - 170 lines)
├── config.py, config_dev.py, config_prod.py, env.py
├── thermostat_remote.py (control logic - 240 lines)
├── scheduler.py (time-based scheduling - 145 lines)
├── webserver.py (HTTP API - 265 lines)
├── remote_client.py (ESP32→Remote communication - 94 lines)
├── sensor.py (BMP280 + DHT11 wrapper - 109 lines)
├── display.py (OLED UI - 95 lines)
├── bmp280.py, ssd1306.py (hardware drivers)
├── test.py, test_remote.py (component tests)
├── deploy_esp32_remote.sh, test_thermostat.sh
├── README.md, DEPLOY_MANUAL.md, rv_thermostat_project_summary.md
├── esp32_remote/ (11 files, ~1700 lines)
│   ├── main.py (ESP32 Remote entry point - 165 lines)
│   ├── thermostat.py (local control - 249 lines)
│   ├── ir_whynter.py (IR TX/RX - 540 lines)
│   ├── webserver.py (API server - 322 lines)
│   ├── sensor.py, display.py, config.py
│   ├── API_QUICK_REFERENCE.md
│   ├── IR_SETUP_GUIDE.md
│   └── AUTOMATIC_CONTROL.md
└── wiring/ (hardware diagrams)
```

**Total**: ~53 files, ~4,365 lines of code

---

## Configuration System

### Priority Order (highest to lowest)
1. `config_local.py` - Local overrides (git-ignored, WiFi credentials)
2. `config_dev.py` / `config_prod.py` - Environment-specific
3. `config.py` - Defaults

### Key Settings

**ESP32 Main Config**:
- I2C: GPIO 21 (SDA), GPIO 22 (SCL)
- BMP280: I2C address 0x76
- OLED: I2C address 0x3C
- Static IP: 192.168.71.152
- No DHT11, no relays, no IR

**ESP32 Remote Config**:
- I2C: GPIO 21 (SDA), GPIO 22 (SCL)
- BMP280: I2C address 0x76
- OLED: I2C address 0x3C
- DHT11: GPIO 4 (humidity sensor)
- Furnace relay: GPIO 25
- Rooftop AC relay: GPIO 26
- IR LED: GPIO 18 (transmitter)
- IR Receiver: GPIO 19 (optional)
- Static IP: 192.168.71.153
- Boost threshold: 10°F

**Control Parameters**:
- Hysteresis: 1.5°F
- Min cycle time: 180 seconds
- Sensor read interval: 5 seconds
- DHT11 rate limit: 2+ seconds

---

## Main Program Flow

### ESP32 Startup
```
main()
├── Initialize I2C, OLED, sensors
├── Connect to WiFi
├── Create RemoteClient
├── Initialize RemoteThermostatController
├── Initialize Scheduler
├── Start ThermostatWebServer (port 80)
└── Loop (every 100ms):
    ├── Handle web requests
    └── Every 5s: read sensors → update thermostat → run scheduler → update OLED
```

### ESP32 Remote Startup
```
main()
├── Initialize I2C, OLED, sensors
├── Connect to WiFi (ESP32-specific init sequence)
├── Initialize WhynterIR (load ir_codes.json)
├── Create ThermostatController
├── Start RemoteAPI server (port 80)
└── Loop (every 100ms):
    ├── Handle API requests
    └── Every 5s: read sensors → update thermostat → control relays → update OLED
```

### Control Loop
```
run_control_loop()
├── Read current temperature
├── MODE_OFF → turn off all systems
├── MODE_HEAT → heat_on if temp < setpoint-1.5°F, heat_off if temp ≥ setpoint
├── MODE_COOL → cool_on if temp > setpoint+1.5°F, cool_off if temp ≤ setpoint
├── MODE_AUTO → smart deadband control
├── Check boost: if temp > setpoint+10°F → activate portable AC
└── Enforce 3-minute minimum between state changes
```

---

## API Endpoints

### ESP32 API
- `GET /api/status` - Thermostat status
- `POST /api/mode` - Set mode (off/heat/cool/auto)
- `POST /api/heat_setpoint` - Set heat setpoint
- `POST /api/cool_setpoint` - Set cool setpoint
- `POST /api/schedule/*` - Manage schedules
- `POST /api/remote/*` - Control ESP32 Remote
- `GET /` - Web UI

### ESP32 Remote API
- `GET /api/status` - Thermostat + IR status
- `POST /api/mode`, `/api/heat_setpoint`, `/api/cool_setpoint` - Local thermostat
- `POST /api/relay/furnace`, `/api/relay/rooftop` - Direct relay control
- `POST /api/ir/learn` - Capture IR code (button: power/mode/temp_up/temp_down/fan)
- `POST /api/ir/power` - Toggle AC power
- `POST /api/ir/mode` - Cycle mode (cool/heat/fan/dehumidify)
- `POST /api/ir/temperature` - Adjust temp (direction: up/down, steps: 1-10)
- `POST /api/ir/fan` - Cycle fan speed (low/med/high/auto)
- `POST /api/ir/set_cooling` - Set cooling mode + temp + fan
- `POST /api/ir/set_heating` - Set heating mode + temp + fan
- `POST /api/ir/achieve_state` - Master state control (power/mode/temp/fan)

---

## Deployment

### ESP32 Remote Deployment
```bash
cd /home/heath/Dev/rv_thermostat
./deploy_esp32_remote.sh
```

**Manual alternative**:
```bash
source venv/bin/activate
cd esp32_remote
mpremote connect /dev/ttyUSB0 cp *.py :
mpremote connect /dev/ttyUSB0 rm boot.py
mpremote connect /dev/ttyUSB0 reset
```

### Testing
```bash
./test_thermostat.sh  # System integration test
python test.py        # Component tests (I2C, sensors, OLED, relays)
python test_remote.py   # ESP32 Remote diagnostics
```

---

## Notable Code Patterns

1. **Graceful degradation**: System continues working even if sensors fail
2. **Rate limiting**: Prevents sensor over-polling (DHT11 2s minimum)
3. **JSON persistence**: IR codes and schedules survive reboots
4. **Hysteresis control**: Prevents chattering relays
5. **Short-cycle protection**: Protects HVAC equipment
6. **State tracking**: IR controller knows exact AC state without feedback

---

## Documentation Files

1. **README.md** - Phase 1 overview, hardware specs, installation
2. **rv_thermostat_project_summary.md** - Comprehensive architecture doc
3. **DEPLOY_MANUAL.md** - Deployment instructions
4. **esp32_remote/AUTOMATIC_CONTROL.md** - IR control capabilities
5. **esp32_remote/API_QUICK_REFERENCE.md** - API reference
6. **esp32_remote/IR_SETUP_GUIDE.md** - Whynter IR setup guide

---

## Developer Context

### Preferences
- Practical working solutions over theory
- Step-by-step guidance with specific details
- Hardware wiring comfortable, software architecture needs help
- Detailed iterative feedback appreciated

### Outstanding Work
- IR signal capture timing issues (Whynter remote learning)
- Complete web UI dashboard
- Advanced scheduling rules
- Full ESP32 Main↔Remote synchronization

---

## Quick Reference

### Static IP Addresses
- ESP32 Main: 192.168.71.152 (configured in config.py)
- ESP32 Remote: 192.168.71.153 (configured in esp32_remote/config.py)
- Gateway: 192.168.71.1
- Subnet: 255.255.255.0

### WiFi Credentials
Stored in `config_local.py` (git-ignored):
```python
WIFI_SSID = "your_ssid"
WIFI_PASSWORD = "your_password"
```

### Common Commands
```bash
# Test I2C devices
python test.py test_i2c_scan

# Check ESP32 status
curl http://192.168.71.152/api/status

# Check ESP32 Remote status
curl http://192.168.71.153/api/status

# Set cooling mode to 72°F (on ESP32 Remote)
curl -X POST http://192.168.71.153/api/cool_setpoint -d '{"setpoint": 72}'
curl -X POST http://192.168.71.153/api/mode -d '{"mode": "cool"}'

# Learn IR code
curl -X POST http://192.168.71.153/api/ir/learn -d '{"button": "power"}'

# Control Whynter AC
curl -X POST http://192.168.71.153/api/ir/set_cooling -d '{"temperature": 68, "fan": "high"}'
```

---

## Git Status (as of last check)

**Current branch**: master
**Modified files**: PartsBuilder project files (outside rv_thermostat)
**RV Thermostat**: Clean working directory

---

## IR Testing Log (2026-02-03)

### Current Hardware Configuration
- **ESP32**: ESP32-S3 (upgraded from regular ESP32)
- **IR LED**: 940nm, GPIO 18
- **Resistor**: 100Ω (GPIO 18 → resistor → LED anode, cathode → GND)
- **LED Status**: ✅ VERIFIED WORKING (visible on phone camera)
- **Library**: peterhinch IR library (in /peterhinch_ir/)
- **Carrier Frequency**: 38 kHz

### Test Scripts
1. `/esp32_remote/test_peterhinch_ir.py` - Single transmission
2. `/esp32_remote/test_whynter_repeat.py` - 3x repetition with delays
3. `/arduino_ir/arduino_ir.ino` - Arduino alternative

### Whynter Power Code (Captured)
```python
power_code = [
    9075, 4568,  # Leader (NEC-like protocol)
    625, 548, 624, 544, 571, 598, 567, 1742,
    545, 650, 541, 623, 572, 1748, 603, 575,
    571, 598, 567, 1742, 545, 650, 541, 1748,
    603, 575, 571, 598, 567, 1742, 545, 1748,
    603, 1748, 571, 598, 567, 1742, 545, 650,
    541, 1748, 603, 1748, 571, 1748, 567, 1742,
    545, 650, 541, 1748, 603, 575, 571, 598,
    567, 1742, 545, 650, 541, 623, 572, 1748, 577
]
```

### Testing Checklist
- ✅ IR LED wired correctly (100Ω resistor)
- ✅ IR LED emitting light (visible on phone camera)
- ✅ Code uploads and runs
- ✅ IR transmission successful (3x transmissions sent)
- ❓ A/C unit responding to IR signals - **AWAITING USER FEEDBACK**

### Test Results (2026-02-03 22:31-23:30)

**✅ PROBLEM SOLVED! A/C NOW RESPONDS!**

**Root Cause**: LED brightness insufficient with 50% PWM duty cycle
**Solution**: Increase PWM duty cycle to 75% (duty=768 instead of 512)

**Tests Performed**:
1. RMT-based transmission (50% duty) - No response
2. Freshly captured IR code - No response
3. Raw PWM transmission (50% duty) - No response
4. Multiple frequencies (36-40kHz) - No response
5. Fixed disconnected wiring - Circuit working
6. Increased duty cycle to 75% - ✅ **SUCCESS!**

### Working Configuration

**Hardware**: GPIO 18 → 100Ω resistor → IR LED (940nm) → GND

**Software**:
```python
PWM(Pin(18), freq=38000, duty=768)  # 75% duty cycle (768/1024)
```

**Captured Code** (confirmed working):
```python
[9000, 4603, 525, 629, 548, 628, 526, 650, 527, 1759, 541, 655, 521, 681,
 523, 1755, 572, 631, 528, 648, 522, 634, 519, 655, 544, 1757, 546, 634,
 545, 1782, 522, 732, 445, 658, 544, 1755, 549, 628, 522, 635, 541, 634,
 520, 658, 545, 1782, 519, 657, 547, 1757, 520, 658, 519, 657, 520, 1783,
 518, 637, 542, 636, 541, 659, 519, 1782, 656, 523, 520]
```

**Test Script**: `/esp32_remote/test_whynter_working.py`

**Alternative Solutions**:
- Use smaller resistor (68Ω or 47Ω) with 50% duty cycle
- Use multiple IR LEDs in parallel for more output power

---

*Last updated: 2026-02-03 - IR transmission WORKING*
*Previous session: ab1610c*
