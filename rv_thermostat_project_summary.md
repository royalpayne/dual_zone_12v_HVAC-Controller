# RV Smart Thermostat & Weather Station Project Summary

## Project Overview

Custom DIY RV thermostat and weather station system to supplement an existing multi-zone HVAC setup. The RV has:
- **Propane furnace** (relay-controlled)
- **Rooftop AC** (relay-controlled)
- **Whynter Portable Air Conditioner/Heater** (model ARC-14SH, IR-controlled)

The goal is to add smart control capabilities using relays wired in parallel for the furnace and rooftop AC, while controlling the portable unit via infrared transmission. Features include web-based control, scheduling, and multi-zone temperature management.

---

## Architecture

### Dual-Microcontroller Design
Due to memory limitations when adding Nest-style scheduling features on a single Pico W, the system uses:

| Controller | Location | Responsibilities |
|------------|----------|------------------|
| **ESP32** | Kitchen (main) | Full scheduling, web interface, sensors, IR transmission for Whynter |
| **Pico W** | Living Room | Wireless trigger unit, relay control, additional temperature readings |

### Communication
- ESP32 acts as main controller
- Pico W communicates wirelessly with ESP32
- Web interface served from ESP32

---

## Hardware Components

### Sensors
- **BMP280** - Temperature and pressure (note: received counterfeit BME280 that was actually BMP280, no humidity)
- **DHT11** - Temperature and humidity (added to compensate for BMP280 lacking humidity)

### Control
- **Relays** - Wired in parallel with existing thermostat for furnace and rooftop AC
- **IR LED circuit** - Uses 2N2222 transistor for controlling Whynter portable AC
- **IR Receiver module** - For capturing Whynter remote codes (in progress)

### Development Hardware
- Raspberry Pi Pico W
- ESP32
- Elegoo electronics kit (includes 2N2222 transistors, resistors, etc.)

---

## Software Stack

- **Language**: MicroPython
- **IDE**: Thonny (previously), transitioning to VS Code
- **Code Structure**: Modular files:
  - `config.py` - Configuration settings
  - Hardware drivers (sensor modules)
  - `display.py` - Display management
  - `thermostat.py` - Thermostat logic
  - `webserver.py` - Web server functionality

---

## Current Status (Phase 1 Complete)

### Working Features
- ✅ Basic thermostat functionality on Pico W
- ✅ Web interface with mobile-friendly controls
- ✅ Dual temperature zones
- ✅ BMP280 + DHT11 sensor integration
- ✅ IR LED circuit tested and working with 2N2222 transistor

### In Progress
- 🔄 IR signal capture from Whynter remote (encountered timing issues)
- 🔄 ESP32-based scheduling system
- 🔄 Programmable Home/Away/Sleep modes
- 🔄 Time-based temperature control

---

## Key Learnings & Notes

1. **Counterfeit sensors**: Verify component authenticity - received fake BME280 (was actually BMP280)
2. **Memory limitations**: Pico W ran out of memory with complex scheduling + web interface, hence dual-MCU architecture
3. **IR debugging**: Initial IR capture attempts had timing issues that need investigation

---

## Preferences

- Prefers practical, working solutions over theoretical explanations
- Appreciates step-by-step guidance with specific pin assignments and code examples
- Comfortable with hardware wiring and basic programming
- Needs assistance with complex software architecture and web development
- Provides detailed feedback for iterative improvements

---

## Next Steps

1. Debug IR receiver timing issues for Whynter remote capture
2. Implement captured IR codes for Whynter control
3. Complete ESP32 scheduling system with web UI
4. Integrate ESP32 ↔ Pico W wireless communication
5. Final integration and testing
