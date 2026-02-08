# RV Thermostat Project Notes

## Hardware Notes
- User's phone has an IR filter - cannot see IR LEDs through phone camera
- IR LED circuit uses 2N2222 NPN transistor driver with GPIO 18
- 5V buck converter powers IR LEDs and HL-52S relay module
- Circuit: base resistor (1K-10K) + LED current limiting resistor (50 ohm recommended but currently omitted)
- IR range ~1 foot - position ESP32 Remote within 1 foot of heater
- IR LED polarity: longer leg = anode (toward 5V), shorter leg = cathode (toward transistor collector)
- NOTE: Currently running without current limiting resistor for max brightness; may shorten LED lifespan

## ESP32 Devices
- **Main ESP32-S3** (N16R8, 40-pin): /dev/ttyACM0, IP 192.168.71.152
  - 16MB Flash, 8MB PSRAM
  - I2C: SDA=GPIO 8, SCL=GPIO 9
  - Has BME280 sensor and OLED display
  - Runs web UI, thermostat brain, scheduler
- **Remote ESP32-S3** (N16R8, 40-pin): /dev/ttyACM1, IP 192.168.71.153
  - 16MB Flash, 8MB PSRAM
  - USB: QinHeng CH340 — shows as /dev/ttyACM*
  - Serial: 5B41036349, MAC: 1c:db:d4:ad:d2:64
  - GPIO 22-25 don't exist on S3; GPIO 26-37 reserved for flash/PSRAM
  - Controls: Furnace relay, Rooftop AC compressor + fan relays, IR transmitter
  - I2C: SDA=GPIO 8, SCL=GPIO 9
  - Relay Furnace: GPIO 38 (active LOW, separate module)
  - Relay Compressor: GPIO 39 (active LOW, separate module)
  - Relay Fan Low: GPIO 40 (active HIGH, 5V module)
  - Relay Fan High: GPIO 42 (active HIGH, 5V module)
  - GPIO 41 unused (medium speed removed to fit 5-wire thermostat cable)
  - IR TX: GPIO 18 (via 2N2222 transistor driver)
  - IR RX: GPIO 17 (VS1838B)
  - Has BME280 sensor and OLED display
- **Broadlink RM4 Mini**: IP 192.168.71.155, MAC e8:70:72:ab:f9:25
  - Device type: 0x520c (rm4mini)
  - WiFi IR blaster for Whynter + Dr. Heater
  - Requires "unlock device" in Broadlink app for local API access
  - python-broadlink library available on PC for testing

## Whynter ARC-14SH IR Protocol
- **Protocol-based** — no learned codes needed, full state sent in each 32-bit command
- Source: ESPHome PR #3641
- Carrier: 38kHz
- Header: 8000us mark, 4000us space
- Bits: 600us mark + 1600us (1) / 550us (0) space, 32 bits MSB first
- Final: 600us mark
- 32-bit command layout:
  - Bits 31-24: 0x12 (command header)
  - Bits 22-20: Fan speed (001=high, 010=med, 100=low, 000=auto)
  - Bits 19-16: Mode (0001=fan, 0010=dehum, 0100=heat, 1000=cool)
  - Bit 10: Fahrenheit flag
  - Bit 8: Power (1=on, 0=off)
  - Bits 7-0: Temperature (bit-reversed byte)
- API: `/api/whynter?power=on|off`, `?mode=cool|heat|dehum|fan`, `?temp=61-89`, `?fan=auto|low|med|high`

## Relay Wiring Notes
- Furnace/compressor (GPIO 38-39): Active LOW module, 5V VCC, works with 3.3V GPIO
- Fan speed (GPIO 40, 42): Active HIGH module (jumper on HIGH trigger), 5V VCC
  - Only Low + High speeds (no Medium) to fit existing 5-wire thermostat cable
  - Must use HIGH trigger because 3.3V GPIO HIGH vs 5V VCC leaves 1.7V across optocoupler, falsely triggering active LOW relays
  - 10K pull-up resistors on GPIO 40, 42 to 3.3V (prevents boot-time activation)
  - boot.py sets fan GPIOs LOW (OFF) immediately on startup
- Furnace is a standalone unit with its own blower (relay is just contact closure)
- Fan relays are for Dometic Brisk II rooftop AC only

## Dometic Brisk II / Control Box
- **Control Box**: P/N 3313199.000 (Etratech), analog relay board with K3/K4/K5 relays
- **Thermostat**: Dometic CT (Comfort Touch) digital, communicates via data cable to control box
- **6-pin connector** from control box to AC unit (output side):
  - Pin 1: Blue = Compressor
  - Pin 2: Black = Fan High
  - Pin 3: Yellow = Unused (reversing valve, no heat pump)
  - Pin 4: Red = Fan Low
  - Pin 5: White = Common (24V return)
  - Pin 6: Green/Yellow = Chassis ground
- **Furnace**: Separate screw terminals on control box (not through 6-pin connector)
- **Freeze sensor**: Connected to control box, provides evaporator freeze protection
- **Parallel wiring**: ESP32 relay NO contacts T-splice at 6-pin connector output
  - Only 4 wires need splicing: White (common), Blue (comp), Black (fan hi), Red (fan lo)
  - Yellow and ground untouched
  - Control box freeze protection remains active for both Dometic and ESP32-initiated cooling
  - See docs/parallel_thermostat_wiring.svg for diagram

## Deployment
- Use `mpremote connect /dev/ttyACM0` for Main
- Use `mpremote connect /dev/ttyACM1` for Remote
- Both boards show as ttyACM* (CH340 USB-serial)
- Deploy boot.py LAST to prevent main.py from blocking subsequent file copies
- If main.py is running, interrupt via serial (Ctrl+C) then use `mpremote resume fs cp`
- MicroPython firmware: v1.27.0 SPIRAM-OCT variant for ESP32-S3
- udev rules in `99-esp32-thermostat.rules` create persistent symlinks by USB serial number
