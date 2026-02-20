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
- **Main ESP32-S3** (N16R8, 44-pin): /dev/ttyACM0, IP 192.168.71.152
  - 16MB Flash, 8MB PSRAM
  - I2C: SDA=GPIO 8, SCL=GPIO 9
  - Has BME280 sensor and OLED display
  - Runs web UI, thermostat brain, scheduler
- **Remote ESP32-S3** (N16R8, 44-pin): /dev/ttyACM1, IP 192.168.71.153
  - 16MB Flash, 8MB PSRAM
  - USB: QinHeng CH340 — shows as /dev/ttyACM*
  - Serial: 5B3E033335, MAC: 1c:db:d4:ae:a2:1c
  - GPIO 22-25 don't exist on S3; GPIO 26-37 reserved for flash/PSRAM
  - Controls: Furnace relay, Rooftop AC compressor + fan relays, IR transmitter
  - I2C: SDA=GPIO 8, SCL=GPIO 9
  - Relay Furnace: GPIO 38 (active HIGH, 5V module)
  - Relay Compressor: GPIO 39 (active HIGH, 5V module)
  - Relay Fan Low: GPIO 40 (active HIGH, 5V module)
  - Relay Fan High: GPIO 41 (active HIGH, 5V module)
  - DS18B20 Freeze Sensor: GPIO 42 (1-Wire, 4.7K pull-up to 3.3V)
  - GPIO 17, 18 unused (IR replaced by Broadlink RM4 Mini)
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

## Dr. Infrared Heater IR (non-humidifier model)
- **Raw captured** — proprietary protocol (not NEC), codes captured from physical remote
- Power code hardcoded in ir_heater.py, additional buttons can be learned via `/api/heater?learn=<name>`
- API: `/api/heater?power=on|off|toggle|force_off`
- **Dual state tracking**: HeaterController.power_on (IR device state) vs ThermostatController.heater_mode (UI state)
- **Force-off**: `/api/heater?power=force_off` sends IR regardless of tracked state, syncs both states to OFF (fixes out-of-sync IR)

## Relay Wiring Notes
- All 4 relays (GPIO 38-41): Active HIGH module, 5V VCC, jumper on HIGH trigger
  - HIGH trigger required because 3.3V GPIO vs 5V VCC leaves 1.7V across optocoupler, falsely triggering active LOW relays
  - boot.py sets all relay GPIOs LOW (OFF) immediately on startup
- Only Low + High fan speeds (no Medium) to fit existing 5-wire thermostat cable
- Furnace is a standalone unit with its own blower (relay is just contact closure)
- Fan relays are for Dometic Brisk II rooftop AC only

## Dometic Brisk II — Direct 120VAC Wiring (No Control Box)
- **Old Dometic Etratech 3313199.000 control box is REMOVED from circuit**
  - Board had MCU running "RelayControl V4.hex" — not a simple relay board
  - Decoded proprietary digital protocol from Dometic CT thermostat via 4-wire data cable
  - 4-wire connector: +12V from supply, +12V to stat, -12V ground, orange (digital data)
  - Board relays (HF3FF 012-1ZS1): K1 (freeze safety), K2/K3/K4 (switching), K5 (empty, reversing valve)
- **ESP32 HL-52S relays + SSR-25DA switch 120VAC** to Brisk II via 6-pin cable
  - Compressor: GPIO 39 → HL-52S Relay 2 (switches 12VDC) → SSR-25DA DC+ → SSR AC out → bimetal cutout → Pin 1 Blue
  - SSR-25DA (Twtade): 25A/380VAC solid state relay, 3-32VDC input, needs heatsink (~15W @ 12A)
  - SSR AC1 = 120VAC LINE (hot), SSR AC2 = compressor load output
  - HL-52S Relay 2 COM = 12VDC (NOT on 120VAC bus), only triggers SSR at milliamp current
  - Relay 3-4 COM bus = 120VAC LINE (fans only, ~2-3A each — within HL-52S 10A rating)
  - GPIO 40 NO → Pin 4 Red (fan low)
  - GPIO 41 NO → Pin 2 Black (fan high)
  - GPIO 38 = furnace dry contact (separate unit, NOT on 120VAC bus)
  - Pin 5 White (neutral) = pass-through, no relay
  - Pin 6 Green/Yellow (ground) = pass-through, no relay
  - Pin 3 Yellow (reversing valve) = not connected
- **6-pin cable carries 120VAC** (NOT 24VAC as originally assumed)
- **14 AWG minimum** for all 120VAC wiring, in proper junction box
- **Freeze protection (dual layer)**:
  - Software: DS18B20 waterproof probe on evaporator coil (GPIO 42, 4.7K pull-up)
    - Cut compressor at 32°F, allow restart at 45°F
  - Hardware: Supco SFPC freeze stat (clamp-on, NC, opens 35°F, closes 50°F) on suction line, in series after SSR AC2 output
- See docs/esp32_remote_relay_splice.svg for wiring diagram

## Broadlink RM4 Mini Sleep Workaround
- Broadlink goes to power-save mode after inactivity, ignoring IR commands
- `broadlink_client.py` retry logic re-authenticates inside the retry loop (not just before it)
- 5-minute keepalive ping (`bl.ping()`) in Remote main loop prevents sleep
- `send_data()` retries 3 times with 1-second delay and re-auth between attempts

## Whynter Boost Logic
- **Threshold boost**: Auto-enables Whynter if temp >= cool_setpoint + BOOST_THRESHOLD (5°F)
- **Stall boost**: Auto-enables Whynter if rooftop AC runs for BOOST_STALL_TIME (10 min) with no temp drop
- **Auto-disable**: Turns off Whynter when temp drops to cool_setpoint + HYSTERESIS (1.5°F)
- **Auto-disable on cool-off**: Whynter shuts off when rooftop AC cycle ends
- IR state only updated on successful Broadlink send (prevents phantom "on" state)

## Sensor Calibration
- BME280 sensors have manufacturing tolerances (~0.7°F between units)
- Calibration offsets in each device's `config_local.py`: TEMP_OFFSET, HUMIDITY_OFFSET, PRESSURE_OFFSET
- Applied in `sensor.py` after raw read, before returning values
- Current offsets: Main +0.38°F, Remote -0.38°F (split-the-difference)

## Auto-Sync (Main → Remote)
- `thermostat_remote.py` auto-syncs mode, heat/cool setpoints to Remote every 60 seconds
- Also syncs immediately on any Kitchen setting change (debounced to 1/sec)
- Handles Remote ESP32 reboots — settings restored within 60 seconds
- Manual SYNC button in web UI still available for immediate force-sync

## Deployment
- Use `mpremote connect /dev/ttyACM0` for Main
- Use `mpremote connect /dev/ttyACM1` for Remote
- Both boards show as ttyACM* (CH340 USB-serial)
- Deploy boot.py LAST to prevent main.py from blocking subsequent file copies
- If main.py is running, interrupt via serial (Ctrl+C) then use `mpremote resume fs cp`
- MicroPython firmware: v1.27.0 SPIRAM-OCT variant for ESP32-S3
- udev rules in `99-esp32-thermostat.rules` create persistent symlinks by USB serial number

### OTA Deployment via WebREPL
- `python3 deploy_ota.py remote|main|both` deploys files over WiFi
- Uses raw WebSocket protocol to ESP32 WebREPL (port 8266)
- Custom implementation (mpremote ws: doesn't support special chars in password)
- Critical: `_handshake()` reads HTTP response 1 byte at a time to avoid consuming WebSocket frames
- Soft reset (`machine.reset()`) after deploy often leaves boards offline — power cycle recommended
- WebREPL password: V!ncent16
