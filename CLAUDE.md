# RV Thermostat Project Notes

## ESP32 Devices
- **Main ESP32-S3** (N16R8, 44-pin): /dev/ttyACM0, IP 192.168.71.152
  - 16MB Flash, 8MB PSRAM
  - I2C: SDA=GPIO 8, SCL=GPIO 9
  - Has BME280 sensor and OLED display
  - Runs web UI, thermostat brain, scheduler
- **Remote: Waveshare ESP32-S3-Relay-6CH**: /dev/ttyACM1, IP 192.168.71.153
  - ESP32-S3-WROOM-1U-N16 (16MB Flash, NO PSRAM)
  - DIN-rail enclosed, 7-36V DC input or 5V USB-C
  - 6 built-in relays (10A @ 250VAC per channel, active HIGH)
  - 40-pin expansion header (inside case) for sensor GPIOs
  - USB: QinHeng CH340 — shows as /dev/ttyACM*
  - Controls: Furnace relay, Rooftop AC compressor + fan relays
  - **Relay CH1**: GPIO 1 — Furnace (dry contact closure)
  - **Relay CH2**: GPIO 2 — Compressor (triggers SSR-25DA via 12VDC)
  - **Relay CH3**: GPIO 41 — Rooftop AC fan low speed
  - **Relay CH4**: GPIO 42 — Rooftop AC fan high speed
  - **Relay CH5**: GPIO 45 — Expansion (dehumidifier, disabled)
  - **Relay CH6**: GPIO 46 — Expansion (vent fan, disabled)
  - I2C: SDA=GPIO 8, SCL=GPIO 9 (expansion header Pin 32/34)
  - DS18B20 Freeze Sensor: GPIO 10 (expansion header, 4.7K pull-up to 3.3V)
  - RGB LED: GPIO 38 (WS2812B, onboard)
  - Buzzer: GPIO 21 (passive, onboard)
  - RS485: GPIO 17 TX, GPIO 18 RX (hardwired to transceiver, future use)
  - Has BME280 sensor and OLED display (via expansion header I2C)
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

## Emergency Shutdown
- **Force All Off**: `/api/force_all_off` unconditionally shuts down all systems
  - Turns off all relays (furnace, compressor, fans)
  - Force-sends IR off to Whynter and heater (ignores tracked state)
  - Resets all state variables to OFF
  - Accessible via red "FORCE ALL OFF" button in web UI
  - Fixes out-of-sync IR devices when mode changes fail to turn off equipment

## Relay Wiring Notes — Waveshare ESP32-S3-Relay-6CH
- 6 built-in relays (10A @ 250VAC, 1NO+1NC per channel), active HIGH
  - boot.py sets CH1-CH4 GPIOs (1, 2, 41, 42) LOW (OFF) immediately on startup
- Only Low + High fan speeds (no Medium) to fit existing 5-wire thermostat cable
- Furnace is a standalone unit with its own blower (relay is just contact closure)
- Fan relays are for Dometic Brisk II rooftop AC only

## Dometic Brisk II — Direct 120VAC Wiring (No Control Box)
- **Old Dometic Etratech 3313199.000 control box is REMOVED from circuit**
  - Board had MCU running "RelayControl V4.hex" — not a simple relay board
  - Decoded proprietary digital protocol from Dometic CT thermostat via 4-wire data cable
  - 4-wire connector: +12V from supply, +12V to stat, -12V ground, orange (digital data)
  - Board relays (HF3FF 012-1ZS1): K1 (freeze safety), K2/K3/K4 (switching), K5 (empty, reversing valve)
- **Waveshare relays + SSR-25DA switch 120VAC** to Brisk II via 6-pin cable
  - Compressor: CH2 (GPIO 2) → switches 12VDC → SSR-25DA DC+ → SSR AC out → bimetal cutout → Pin 1 Blue
  - SSR-25DA (Twtade): 25A/380VAC solid state relay, 3-32VDC input, needs heatsink (~15W @ 12A)
  - SSR AC1 = 120VAC LINE (hot), SSR AC2 = compressor load output
  - CH2 COM = 12VDC (NOT on 120VAC bus), only triggers SSR at milliamp current
  - CH3/CH4 COM bus = 120VAC LINE (fans only, ~2-3A each — within 10A relay rating)
  - CH3 (GPIO 41) NO → Pin 4 Red (fan low)
  - CH4 (GPIO 42) NO → Pin 2 Black (fan high)
  - CH1 (GPIO 1) = furnace dry contact (separate unit, NOT on 120VAC bus)
  - Pin 5 White (neutral) = pass-through, no relay
  - Pin 6 Green/Yellow (ground) = pass-through, no relay
  - Pin 3 Yellow (reversing valve) = not connected
- **6-pin cable carries 120VAC** (NOT 24VAC as originally assumed)
- **14 AWG minimum** for all 120VAC wiring, in proper junction box
- **Freeze protection (dual layer)**:
  - Software: DS18B20 waterproof probe on evaporator coil (GPIO 10 via expansion header, 4.7K pull-up to 3.3V)
    - Cut compressor at 32°F, allow restart at 45°F
  - Hardware: Supco SFPC freeze stat (clamp-on, NC, opens 35°F, closes 50°F) on suction line, in series after SSR AC2 output
- See wiring diagrams in docs/ (PDF + SVG)

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
- Web UI has AUTO-SYNC ZONES toggle (ON/OFF) to enable/disable sync
- `sync_enabled` flag gates both immediate sync and 60-second periodic sync
- Toggle ON immediately syncs current Kitchen settings to Living Room

## Deployment
- Use `mpremote connect /dev/ttyACM0` for Main
- Use `mpremote connect /dev/ttyACM1` for Remote
- Both boards show as ttyACM* (CH340 USB-serial)
- Deploy boot.py LAST to prevent main.py from blocking subsequent file copies
- If main.py is running, interrupt via serial (Ctrl+C) then use `mpremote resume fs cp`
- MicroPython firmware: v1.27.0 for ESP32-S3
  - Main: SPIRAM-OCT variant (has 8MB PSRAM)
  - Remote (Waveshare): Standard variant (no PSRAM)
- udev rules in `99-esp32-thermostat.rules` create persistent symlinks by USB serial number

### OTA Deployment via WebREPL
- `python3 deploy_ota.py remote|main|both` deploys files over WiFi + auto-restarts
- `python3 deploy_ota.py restart remote|main|both` restarts without uploading
- `python3 deploy_ota.py main file1.py file2.py` deploys specific files + restarts
- `--no-restart` flag skips restart (just uploads files)
- Uses raw WebSocket protocol to ESP32 WebREPL (port 8266)
- Custom implementation (mpremote ws: doesn't support special chars in password)
- Critical: `_handshake()` reads HTTP response 1 byte at a time to avoid consuming WebSocket frames
- **Warm restart** (no power cycle needed):
  - Sends Ctrl+C via WebREPL to interrupt running main.py
  - Executes `_restart.py` helper which purges cached user modules from `sys.modules`
  - Re-runs `main.py` via `exec()` — WiFi + WebREPL stay up the entire time
  - `connect_wifi()` detects WiFi already connected and skips re-init
  - HTTP verification confirms board is back online after restart
- **Hardware resets still fail** via WebREPL (machine.reset/soft_reset/deepsleep all kill WiFi)
  - ESP32-S3 + MicroPython v1.27.0: network stack doesn't reinitialize after programmatic reset
  - Warm restart avoids this by never tearing down WiFi
- WebREPL password: V!ncent16

## Wiring Diagrams
- Generated by `create_diagrams_updated.py` using matplotlib
- Outputs both PDF and SVG to `docs/` directory
- 4 diagrams, each 11.5x8 inch landscape, 300 DPI:
  - `ssr_wiring_pro` — SSR-25DA compressor wiring (Waveshare CH2 → SSR → Load Chain → Compressor)
  - `oled_bme280_wiring_pro` — I2C cable run from Waveshare expansion header to OLED + BME280 at thermostat location
  - `esp32_main_wiring_pro` — Main ESP32-S3 board wiring with BME280, OLED, bus bars
  - `esp32_remote_relay_splice_pro` — Comprehensive relay splice showing all 120VAC wiring, fan routing, DS18B20 3-lead sensor
- Design rules: orthogonal (Manhattan-style) wire routing only, wire labels below lines with clear spacing, colored wires per signal type
- Run `python3 create_diagrams_updated.py` to regenerate all diagrams
- Old SVG diagrams archived in `docs/archive_svg/`
