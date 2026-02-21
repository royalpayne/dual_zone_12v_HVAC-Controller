# RV Thermostat Wiring Diagrams

All diagrams created using matplotlib for professional quality at 300 DPI.
**UPDATED:** Now featuring Waveshare ESP32-S3-Relay-6CH integrated module.

## Current Wiring Diagrams (Professional Quality - Updated Feb 2026)

### Main Components

**Hardware Update:**
- **Waveshare ESP32-S3-Relay-6CH**: Integrated ESP32-S3 + 6 relay channels
- **IP65 Waterproof Enclosure**: 6.3"×4.33"×3.54"
- **Power**: 7-36V DC (or 5V USB-C)
- **Relay Rating**: 10A @ 250VAC/30VDC per channel

### ESP32 Controllers

1. **esp32_main_wiring_pro.pdf** (45 KB)
   - ESP32-S3 Main Controller (IP 192.168.71.152)
   - I2C connections to BME280 sensor and SSD1306 OLED
   - Power supply: 12V DC → Buck Converter → 5V → ESP32 VIN
   - I2C addresses: BME280 (0x76), OLED (0x3C)
   - GPIO 8 (SDA), GPIO 9 (SCL)
   - **Unchanged** - separate ESP32 board

### Remote HVAC Control

2. **esp32_remote_relay_splice_pro.pdf** (60 KB)
   - **MOST IMPORTANT** - Complete system wiring diagram
   - Waveshare ESP32-S3-Relay-6CH module
   - GPIO assignments:
     * CH1 (GPIO 1): Furnace relay
     * CH2 (GPIO 2): Compressor (triggers SSR-25DA)
     * CH3 (GPIO 41): Fan Low
     * CH4 (GPIO 42): Fan High
     * CH5/CH6 (GPIO 45/46): Available for expansion
   - I2C: GPIO 8 (SDA), GPIO 9 (SCL) - 3m cable to remote OLED/BME280
   - DS18B20 freeze sensor: GPIO 10 (1-Wire, changed from GPIO 42)
   - SSR-25DA for compressor switching (12VDC trigger → 120VAC load)
   - Supco SFPC hardware freeze stat + DS18B20 software freeze protection
   - 6-pin Dometic cable to Brisk II rooftop AC
   - IP65 waterproof enclosure specs
   - All safety critical wiring notes

### Component-Specific Diagrams

3. **ssr_wiring_pro.pdf** (48 KB)
   - Detailed SSR-25DA compressor control wiring
   - Shows Waveshare CH2 relay triggering SSR
   - Separation between 12VDC control and 120VAC load
   - Safety device chain: SSR → Supco SFPC → Bimetal → Compressor
   - Heatsink requirements (~15W @ 12A load)
   - Neutral return path

4. **oled_bme280_wiring_pro.pdf** (57 KB)
   - 3-meter I2C cable run using 18 AWG thermostat wire
   - From Waveshare module to thermostat location
   - 4-wire connection: 3.3V, GND, SDA (GPIO 8), SCL (GPIO 9)
   - OLED (0x3C) and BME280 (0x76) in parallel at thermostat location
   - Grounding: Safe to tie GND to 12VDC ground (required for I2C)
   - I2C frequency: 400 kHz (can reduce to 100 kHz if needed)
   - **WARNING:** Do NOT connect VCC to 12V (only 3.3V!)

## GPIO Pin Reference

**Waveshare ESP32-S3-Relay-6CH:**
- Relay CH1: GPIO 1 (Furnace)
- Relay CH2: GPIO 2 (Compressor → SSR)
- Relay CH3: GPIO 41 (Fan Low)
- Relay CH4: GPIO 42 (Fan High)
- Relay CH5: GPIO 45 (Available)
- Relay CH6: GPIO 46 (Available)
- I2C SDA: GPIO 8
- I2C SCL: GPIO 9
- DS18B20 (1-Wire): GPIO 10
- RS485 TX/RX: GPIO 17/18
- Buzzer: GPIO 21
- RGB LED (WS2812): GPIO 38
- Boot Button: GPIO 0

**Reserved (Do Not Use):**
- GPIO 22-25: Don't exist on ESP32-S3
- GPIO 26-37: Reserved for Flash/PSRAM

## Legacy Documents

5. **esp32_dometic_wiring_instructions.pdf** (18 KB)
   - Original wiring instructions (pre-Waveshare module)

## Archived Files

All original SVG diagrams have been moved to `archive_svg/` for reference.
The new professional PDF diagrams are the authoritative source.

## Diagram Features

- **Wire label positioning**: All labels positioned BELOW wires for clarity
- **Color coding**:
  - Red/Orange: Power (120VAC hot, 12VDC, 5V, 3.3V)
  - Blue: Neutral (120VAC), I2C signals (SDA/SCL)
  - Green: Ground, SDA (I2C)
  - Black: Ground
  - Cyan: 1-Wire (DS18B20)
  - Purple: Special functions

- **Critical safety information** highlighted in red boxes
- **Component specifications** included in detail
- **300 DPI resolution** for clear printing
- **Vector graphics** scale cleanly when zoomed

## Viewing

Open any PDF in a standard PDF viewer (Adobe Reader, Evince, Preview, Chrome, etc.)
All diagrams are vector-based and will scale cleanly when zoomed.

## Change Log

**February 2026:**
- Updated to Waveshare ESP32-S3-Relay-6CH integrated module
- Replaced separate ESP32 + HL-52S relay setup
- Updated GPIO pin assignments
- DS18B20 moved from GPIO 42 to GPIO 10
- Added IP65 enclosure specifications (6.3"×4.33"×3.54")
- Fixed wire label positioning (now below lines)
