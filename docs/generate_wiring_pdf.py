#!/usr/bin/env python3
"""Generate ESP32 Direct 120VAC Wiring Instruction PDF.

SSR-40DA approach: ESP32-S3-N16R8 with external 4-channel relay module.
Relay CH2 switches 12VDC to trigger an SSR-40DA solid state relay for the
compressor. CH3/CH4 switch 120VAC directly for fans. The Dometic Etratech
control box is eliminated.
"""

from fpdf import FPDF


class WiringPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'ESP32-S3-N16R8 + 4-Channel Relay - SSR-40DA Wiring Instructions',
                  align='C', new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 30, 80)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=10):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.cell(indent, 5.5, '')
        self.cell(4, 5.5, '-')
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def warning_box(self, text):
        self.set_fill_color(255, 240, 240)
        self.set_draw_color(200, 50, 50)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(180, 0, 0)
        y = self.get_y()
        lines = len(text) / 80 + text.count('\n')
        h = max(14, (lines + 1) * 5.5 + 4)
        self.rect(10, y, 190, h, style='DF')
        self.set_xy(14, y + 2)
        self.multi_cell(182, 5.5, text)
        self.set_y(y + h + 4)

    def info_box(self, text):
        self.set_fill_color(235, 245, 255)
        self.set_draw_color(50, 100, 180)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 60, 120)
        y = self.get_y()
        lines = len(text) / 80 + text.count('\n')
        h = max(14, (lines + 1) * 5.5 + 4)
        self.rect(10, y, 190, h, style='DF')
        self.set_xy(14, y + 2)
        self.multi_cell(182, 5.5, text)
        self.set_y(y + h + 4)

    def table_row(self, cells, widths, bold=False, fill=False):
        self.set_font('Helvetica', 'B' if bold else '', 9)
        if fill:
            self.set_fill_color(220, 230, 245)
        self.set_text_color(0, 0, 0)
        for cell, w in zip(cells, widths):
            self.cell(w, 7, cell, border=1, fill=fill, align='C' if bold else 'L')
        self.ln()


def build_pdf():
    pdf = WiringPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Title ---
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(20, 20, 60)
    pdf.cell(0, 12, 'ESP32-S3-N16R8 + 4-Channel Relay Module', align='C',
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Dometic Brisk II Direct Wiring (No Control Box)',
             align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, 'SSR-40DA Compressor + Direct Fan Relay Switching',
             align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # =================================================================
    # Section 1: Overview
    # =================================================================
    pdf.section_title('1. Overview')
    pdf.body_text(
        'This document describes how to wire the ESP32-S3-N16R8 dev board with '
        'an external 4-channel relay module to control the Dometic Brisk II '
        'rooftop AC unit. The Dometic Etratech control box (P/N 3313199.000) '
        'is eliminated. The relay module has 4 channels (10A each, active HIGH '
        'via jumper) and controls all loads via two switching stages:'
    )
    pdf.bullet(
        'SSR-40DA solid state relay for the compressor (25A capacity, handles '
        '~12A running current and inrush). Triggered by CH2 relay via 12VDC.')
    pdf.bullet(
        'Relay CH3/CH4 for fans (10A contacts, adequate for ~2-3A fan motors). '
        'These switch 120VAC directly.')
    pdf.bullet(
        'Relay CH1 for furnace (dry contact closure to standalone unit with '
        'its own blower).')
    pdf.body_text(
        'CH2 does NOT switch 120VAC for the compressor. Instead, it switches '
        '12VDC from the RV battery to the SSR-40DA DC input, which then '
        'switches 120VAC to the compressor. This keeps all high-current '
        'switching on the SSR while CH2 handles only milliamp-level 12VDC '
        'trigger current.'
    )

    pdf.warning_box(
        'WARNING: This system switches 120VAC through the SSR-40DA and '
        'relay module contacts. All 120VAC wiring must be in a proper '
        'junction box with 14 AWG wire (minimum for 15A circuit). The '
        'SSR-40DA must be mounted on a heatsink. Disconnect shore power '
        'before all wiring work.')

    # =================================================================
    # Section 2: System Architecture
    # =================================================================
    pdf.section_title('2. System Architecture')

    pdf.sub_title('Compressor Signal Path')
    pdf.body_text(
        'ESP32 GPIO 5 HIGH -> Relay CH2 closes -> 12VDC from RV '
        'battery reaches SSR-40DA DC+ input -> SSR turns ON -> 120VAC LINE '
        'flows through SSR AC output -> Supco SFPC freeze stat (NC) -> '
        '6-pin Blue wire -> Compressor motor')
    pdf.info_box(
        'The SSR-40DA handles the full compressor load current (25A rating vs '
        '~12A running). The CH2 relay only switches 12VDC at milliamps to '
        'trigger the SSR. This eliminates relay contact wear and welding risk.')

    pdf.sub_title('Fan Signal Path')
    pdf.body_text(
        'ESP32 GPIO 6/15 HIGH -> Relay CH3/CH4 closes -> 120VAC '
        'LINE flows directly through relay NO contact -> 6-pin Red/Black wire '
        '-> Fan motor. Fan motors draw ~2-3A, well within the relay 10A '
        'contact rating.')

    pdf.sub_title('Freeze Protection (Dual-Layer)')
    pdf.body_text(
        'With the Etratech control box removed, the built-in K1 freeze relay is '
        'gone. Freeze protection is now provided by two independent layers:')
    pdf.bullet(
        'SOFTWARE: DS18B20 waterproof probe on the evaporator coil, connected to '
        'ESP32 GPIO 42. When evaporator temp drops below 32F, the ESP32 cuts '
        'the compressor (GPIO 5 LOW). Held off until evaporator recovers to 45F.')
    pdf.bullet(
        'HARDWARE BACKUP: Supco SFPC freeze protection control. Clamp-on device '
        'that snaps onto the suction line. Normally closed, opens at 35F, closes '
        'at 50F. Wired in series between SSR AC2 output and the 6-pin Blue wire. '
        'Independent of ESP32 -- passive, unpowered, fail-safe.')

    # =================================================================
    # Section 3: Component Reference
    # =================================================================
    pdf.add_page()
    pdf.section_title('3. Component Reference')

    pdf.sub_title('ESP32-S3-N16R8 Dev Board')
    w_ws = [40, 150]
    pdf.table_row(['Spec', 'Value'], w_ws, bold=True, fill=True)
    pdf.table_row(['MCU', 'ESP32-S3-N16R8 (16MB Flash, 8MB PSRAM)'], w_ws)
    pdf.table_row(['Form Factor', '44-pin dev board with USB-C'], w_ws)
    pdf.table_row(['Power', '5V USB-C or 3.3V/5V pin'], w_ws)
    pdf.table_row(['Onboard', 'WS2812 NeoPixel RGB LED (GPIO 48)'], w_ws)
    pdf.ln(2)

    pdf.sub_title('4-Channel Relay Module (External)')
    w_rm = [40, 150]
    pdf.table_row(['Spec', 'Value'], w_rm, bold=True, fill=True)
    pdf.table_row(['Channels', '4 channels, 10A @ 250VAC per channel'], w_rm)
    pdf.table_row(['Trigger', 'Active HIGH (set via jumper)'], w_rm)
    pdf.table_row(['Input', '3.3V/5V logic compatible'], w_rm)
    pdf.ln(2)
    pdf.body_text('Relay channel assignments:')
    pdf.bullet('CH1 (GPIO 4): Furnace dry contact closure')
    pdf.bullet('CH2 (GPIO 5): Compressor -- switches 12VDC to SSR-40DA DC+ trigger')
    pdf.bullet('CH3 (GPIO 6): Fan Low -- switches 120VAC directly')
    pdf.bullet('CH4 (GPIO 15): Fan High -- switches 120VAC directly')
    pdf.ln(2)

    pdf.sub_title('SSR-40DA Solid State Relay')
    w_ssr = [40, 150]
    pdf.table_row(['Spec', 'Value'], w_ssr, bold=True, fill=True)
    pdf.table_row(['Model', 'Twtade SSR-40DA'], w_ssr)
    pdf.table_row(['Output', '24-380VAC, 40A'], w_ssr)
    pdf.table_row(['Input', '3-32VDC (triggered with 12VDC from RV battery)'], w_ssr)
    pdf.table_row(['Heatsink', 'Required (~15W dissipation at 12A load)'], w_ssr)
    pdf.ln(2)
    pdf.body_text('Terminal assignments:')
    pdf.bullet('DC+ (pin 3): 12VDC from relay module CH2 NO output')
    pdf.bullet('DC- (pin 4): 12VDC GND (RV battery negative)')
    pdf.bullet('AC1 (pin 1): 120VAC LINE (hot) input')
    pdf.bullet('AC2 (pin 2): Output to freeze stat -> 6-pin Blue wire')
    pdf.ln(2)

    pdf.info_box(
        'Why not trigger the SSR directly from 3.3V GPIO? The SSR-40DA needs '
        '~5mA minimum to trigger reliably. At 3.3V through its internal resistor '
        'and LED, only ~1.5mA is available. Using the relay module CH2 to '
        'switch 12VDC provides ~15mA -- well above the minimum threshold.')

    pdf.sub_title('Supco SFPC Freeze Protection Control')
    w_sfpc = [40, 150]
    pdf.table_row(['Spec', 'Value'], w_sfpc, bold=True, fill=True)
    pdf.table_row(['Model', 'Supco SFPC'], w_sfpc)
    pdf.table_row(['Type', 'Clamp-on, snaps onto suction line (up to 7/8" OD)'], w_sfpc)
    pdf.table_row(['Contacts', 'SPST NC, opens at 35F, closes at 50F'], w_sfpc)
    pdf.table_row(['Rating', '10A @ 120V, 5A @ 240V'], w_sfpc)
    pdf.table_row(['Install', 'On suction line just outside evaporator coil'], w_sfpc)
    pdf.ln(2)
    pdf.body_text(
        'Alternative: Honeywell FPC (opens at 38F, closes at 48F). Either '
        'device works. The Supco SFPC has a wider differential (15F) which '
        'reduces nuisance trips.')

    # =================================================================
    # Section 4: Wiring Reference
    # =================================================================
    pdf.add_page()
    pdf.section_title('4. Wiring Reference')

    pdf.sub_title('6-Pin Cable (AC Unit Side)')
    pdf.body_text(
        'This cable runs from the junction box up to the Dometic Brisk II rooftop '
        'unit. All load wires carry 120VAC when their respective relay/SSR is ON.')

    w5 = [15, 35, 50, 90]
    pdf.table_row(['Pin', 'Color', 'Function', 'Connection'], w5, bold=True, fill=True)
    pdf.table_row(['1', 'Blue', 'Compressor', 'SSR AC2 -> freeze stat -> Blue'], w5)
    pdf.table_row(['2', 'Black', 'Fan High', 'CH4 (GPIO 15) NO -> Black'], w5)
    pdf.table_row(['3', 'Yellow', 'Rev Valve', 'Not connected (no heat pump)'], w5)
    pdf.table_row(['4', 'Red', 'Fan Low', 'CH3 (GPIO 6) NO -> Red'], w5)
    pdf.table_row(['5', 'White', 'Neutral', 'Pass-through to AC unit'], w5)
    pdf.table_row(['6', 'Grn/Ylw', 'Chassis Gnd', 'Pass-through to AC unit'], w5)
    pdf.ln(4)

    pdf.sub_title('Relay Module Connections')

    w4 = [40, 30, 55, 65]
    pdf.table_row(['Channel', 'GPIO', 'Switches', 'Connection'], w4, bold=True, fill=True)
    pdf.table_row(['CH1', 'GPIO 4', 'Dry contact', 'Furnace call (no voltage)'], w4)
    pdf.table_row(['CH2', 'GPIO 5', '12VDC', 'SSR DC+ trigger (from RV battery)'], w4)
    pdf.table_row(['CH3', 'GPIO 6', '120VAC', 'Fan Low (direct to Red)'], w4)
    pdf.table_row(['CH4', 'GPIO 15', '120VAC', 'Fan High (direct to Black)'], w4)
    pdf.ln(2)

    pdf.warning_box(
        'CH2 (Compressor) is NOT on the 120VAC bus. Its COM connects to RV '
        '+12VDC, and its NO connects to SSR DC+. The SSR handles 120VAC '
        'switching. CH1 (Furnace) is a dry contact. Only CH3 and CH4 carry '
        '120VAC.')

    # =================================================================
    # Section 5: Wiring Procedure
    # =================================================================
    pdf.add_page()
    pdf.section_title('5. Wiring Procedure')

    pdf.warning_box(
        'DISCONNECT SHORE POWER before all wiring. Verify with a non-contact '
        'voltage tester. All 120VAC connections must be inside a junction box.')

    # Step 1
    pdf.sub_title('Step 1: Remove the Etratech Control Box')
    pdf.bullet('Disconnect shore power and verify no voltage is present.')
    pdf.bullet('Disconnect the 6-pin cable from the control box output side.')
    pdf.bullet('Disconnect 120VAC LINE and NEUTRAL from the control box input side.')
    pdf.bullet('Disconnect furnace wires from the control box FURNACE terminals.')
    pdf.bullet('Disconnect freeze sensor wires from J4 (no longer used by control box).')
    pdf.bullet('Remove the Etratech control box entirely.')
    pdf.ln(2)

    # Step 2
    pdf.sub_title('Step 2: Mount and Wire the SSR-40DA')
    pdf.bullet(
        'Mount the SSR-40DA on a metal heatsink (aluminum, at least 4"x4"). '
        'Use thermal paste between SSR and heatsink. Mount heatsink inside or '
        'adjacent to the junction box with adequate airflow.')
    pdf.bullet(
        'AC1 (pin 1): Connect with 14 AWG wire to 120VAC LINE (hot). Use a '
        'Wago 221-412 or wire nut to branch LINE to both the SSR AC1 and the '
        'CH3/CH4 COM bus.')
    pdf.bullet(
        'AC2 (pin 2): Connect with 14 AWG wire to the Supco SFPC freeze stat '
        'input terminal. The freeze stat output connects to the 6-pin Blue wire.')
    pdf.bullet(
        'DC+ (pin 3): Connect with 18-22 AWG wire to relay module CH2 NO '
        'screw terminal.')
    pdf.bullet(
        'DC- (pin 4): Connect with 18-22 AWG wire to RV 12VDC GND (battery '
        'negative / chassis ground).')
    pdf.ln(2)

    # Step 3
    pdf.sub_title('Step 3: Wire 120VAC Bus to CH3/CH4 COM')
    pdf.bullet(
        'Create a 120VAC LINE bus to CH3 COM and CH4 COM screw terminals. Use '
        '14 AWG wire and Wago connectors or wire nuts to branch from the same '
        'LINE wire feeding SSR AC1.')
    pdf.bullet(
        'CH3 NO (GPIO 6) -> 14 AWG -> 6-pin Red wire (Fan Low)')
    pdf.bullet(
        'CH4 NO (GPIO 15) -> 14 AWG -> 6-pin Black wire (Fan High)')
    pdf.ln(2)

    # Step 4
    pdf.sub_title('Step 4: Wire 12VDC to CH2 COM')
    pdf.bullet(
        'Connect RV +12VDC (house battery / converter) to CH2 COM screw '
        'terminal. Use 18-22 AWG wire. This is the SSR trigger source.')
    pdf.bullet(
        'CH2 NO connects to SSR DC+ (already done in Step 2).')
    pdf.bullet(
        'When GPIO 5 goes HIGH, CH2 closes, 12VDC reaches SSR DC+, and '
        'the SSR turns on 120VAC to the compressor.')
    pdf.ln(2)

    # Step 5
    pdf.sub_title('Step 5: Wire Neutral and Ground Pass-Through')
    pdf.bullet(
        'Route NEUTRAL (white) directly through the junction box to the 6-pin '
        'White wire. Not switched by any relay.')
    pdf.bullet(
        'Route GROUND (green/yellow) directly through to the 6-pin Green/Yellow '
        'wire. Connect ground to the junction box and any metal enclosures.')
    pdf.bullet(
        'Cap the Yellow wire (Pin 3, reversing valve) with a wire nut.')
    pdf.ln(2)

    # Step 6
    pdf.sub_title('Step 6: Wire Furnace (CH1)')
    pdf.bullet(
        'Connect furnace call wires to CH1 COM and NO screw terminals. This is '
        'a dry contact closure -- no 120VAC, no 12VDC on these terminals.')
    pdf.ln(2)

    # Step 7
    pdf.sub_title('Step 7: Install Supco SFPC Freeze Stat')
    pdf.bullet(
        'Snap the Supco SFPC clamp onto the suction line just outside the '
        'evaporator coil. No thermal paste needed -- the clamp provides '
        'direct contact with the copper tubing.')
    pdf.bullet(
        'Wire in series: SSR AC2 output -> freeze stat -> 6-pin Blue wire. '
        'Use 14 AWG wire and appropriate connectors.')
    pdf.bullet(
        'Verify NC (closed) at room temperature with a continuity test.')
    pdf.ln(2)

    # Step 8
    pdf.sub_title('Step 8: Install DS18B20 Freeze Sensor')
    pdf.bullet(
        'Mount the waterproof DS18B20 probe on the evaporator coil in contact '
        'with copper tubing or aluminum fins. Use thermal paste and secure '
        'with cable tie or aluminum tape.')
    pdf.bullet(
        'Wire to ESP32-S3-N16R8 dev board: Red to 3.3V pin, Black to GND, '
        'Yellow/White data to GPIO 42.')
    pdf.bullet(
        'Solder a 4.7K ohm pull-up resistor between GPIO 42 and 3.3V, as '
        'close to the dev board as practical.')
    pdf.bullet('Route sensor cable away from 120VAC wires to avoid noise.')

    # =================================================================
    # Section 6: I2C Sensor + OLED Wiring
    # =================================================================
    pdf.add_page()
    pdf.section_title('6. I2C Sensor and Display Wiring')

    pdf.body_text(
        'The BME280 temperature/humidity/pressure sensor and SSD1306 OLED '
        'display are mounted at the thermostat location (former Dometic stat '
        'position) and connected to the ESP32-S3-N16R8 via a 3-meter I2C '
        'cable run.')

    pdf.sub_title('ESP32-S3-N16R8 Pin Connections')
    w_i2c = [40, 40, 55, 55]
    pdf.table_row(['Signal', 'GPIO', 'Dev Board Pin', 'Wire Color'], w_i2c, bold=True, fill=True)
    pdf.table_row(['SDA', 'GPIO 41', 'GPIO 41', 'Green'], w_i2c)
    pdf.table_row(['SCL', 'GPIO 40', 'GPIO 40', 'Blue'], w_i2c)
    pdf.table_row(['3.3V', '--', '3V3', 'Red'], w_i2c)
    pdf.table_row(['GND', '--', 'GND', 'Black'], w_i2c)
    pdf.ln(2)

    pdf.sub_title('I2C Devices (Shared Bus)')
    w_dev = [60, 40, 90]
    pdf.table_row(['Device', 'Address', 'Function'], w_dev, bold=True, fill=True)
    pdf.table_row(['BME280', '0x76', 'Temperature, humidity, pressure'], w_dev)
    pdf.table_row(['SSD1306 OLED', '0x3C', '128x64 pixel display'], w_dev)
    pdf.ln(2)

    pdf.info_box(
        'Both devices share the same I2C bus (SDA + SCL). Use 18 AWG '
        '4-conductor thermostat wire for the 3-meter cable run. I2C bus '
        'speed: 400 kHz (can reduce to 100 kHz if cable causes issues). '
        'WARNING: OLED and BME280 VCC = 3.3V ONLY (not 5V or 12V!).')

    # =================================================================
    # Section 7: Freeze Protection Details
    # =================================================================
    pdf.section_title('7. Freeze Protection Details')

    pdf.sub_title('Software Layer (DS18B20)')
    w_th = [95, 95]
    pdf.table_row(['Condition', 'Action'], w_th, bold=True, fill=True)
    pdf.table_row(['Evap temp < 32F', 'Cut compressor (GPIO 5 LOW)'], w_th)
    pdf.table_row(['Evap temp >= 45F', 'Allow compressor to resume'], w_th)
    pdf.table_row(['DS18B20 not found', 'Software freeze protection disabled'], w_th)
    pdf.table_row(['Check interval', 'Every 5 seconds'], w_th)
    pdf.ln(4)

    pdf.sub_title('Hardware Layer (Supco SFPC)')
    w_hw = [95, 95]
    pdf.table_row(['Condition', 'Action'], w_hw, bold=True, fill=True)
    pdf.table_row(['Suction line < 35F', 'Switch opens, compressor circuit broken'], w_hw)
    pdf.table_row(['Suction line > 50F', 'Switch closes, circuit restored'], w_hw)
    pdf.table_row(['No power needed', 'Passive NC switch, always active'], w_hw)
    pdf.ln(4)

    pdf.info_box(
        'The two layers are independent. The DS18B20 software layer acts first '
        '(32F threshold). The Supco SFPC hardware layer is backup (35F threshold). '
        'Even with a total ESP32 failure, the SFPC physically breaks the '
        'compressor circuit if the suction line reaches 35F.')

    # =================================================================
    # Section 8: Failsafe Behavior
    # =================================================================
    pdf.section_title('8. Failsafe Behavior')

    pdf.body_text(
        'The system is fail-safe: any single point of failure results in HVAC OFF. '
        'The relay module and SSR-40DA are normally open, so power loss to the '
        'ESP32 disconnects all loads.')

    w6 = [60, 130]
    pdf.table_row(['Condition', 'Result'], w6, bold=True, fill=True)
    pdf.table_row(['ESP32 power loss', 'All relays open -> SSR off -> all loads OFF'], w6)
    pdf.table_row(['ESP32 software crash', 'boot.py sets GPIOs LOW on reboot -> all OFF'], w6)
    pdf.table_row(['Shore power loss', 'No 120VAC available -> all loads OFF'], w6)
    pdf.table_row(['12VDC battery loss', 'SSR DC+ has no trigger -> compressor OFF'], w6)
    pdf.table_row(['DS18B20 reads < 32F', 'Software cuts compressor, recovery at 45F'], w6)
    pdf.table_row(['SFPC trips (< 35F)', 'Hardware breaks compressor circuit'], w6)
    pdf.table_row(['SSR failure (open)', 'Compressor stays OFF (safe direction)'], w6)
    pdf.table_row(['Relay welded shut', 'Only that one fan load stays on'], w6)
    pdf.table_row(['120VAC bus fault', 'Breaker trips -> all loads OFF'], w6)
    pdf.ln(4)

    pdf.warning_box(
        'There is NO backup thermostat. If the ESP32 loses power or crashes, all '
        'HVAC stops until the ESP32 recovers. The system is fail-safe (everything '
        'OFF) but not fail-operational.')

    # =================================================================
    # Section 9: ESP32-S3-N16R8 GPIO Reference
    # =================================================================
    pdf.add_page()
    pdf.section_title('9. ESP32-S3-N16R8 GPIO Reference')
    pdf.body_text('IP: 192.168.71.153 | 44-pin dev board | 5V USB-C')

    w7 = [30, 50, 55, 55]
    pdf.table_row(['GPIO', 'Function', 'Channel/Device', 'Load'], w7, bold=True, fill=True)
    pdf.table_row(['4', 'Furnace', 'CH1 NO/COM', 'Dry contact closure'], w7)
    pdf.table_row(['5', 'Compressor', 'CH2 -> SSR', '12VDC trigger -> SSR 120VAC'], w7)
    pdf.table_row(['6', 'Fan Low', 'CH3 NO', '120VAC -> Pin 4 Red'], w7)
    pdf.table_row(['15', 'Fan High', 'CH4 NO', '120VAC -> Pin 2 Black'], w7)
    pdf.table_row(['41', 'I2C SDA', 'Dev board', 'BME280 + OLED'], w7)
    pdf.table_row(['40', 'I2C SCL', 'Dev board', 'BME280 + OLED'], w7)
    pdf.table_row(['42', 'Freeze Sensor', 'Dev board', '1-Wire DS18B20, 4.7K pull-up'], w7)
    pdf.table_row(['48', 'RGB LED', 'Onboard', 'WS2812 NeoPixel status indicator'], w7)
    pdf.ln(4)

    pdf.sub_title('Power Architecture')
    pdf.bullet(
        'Control side: RV 12VDC battery system (always available with battery). '
        'Powers ESP32 (via 5V regulator) and SSR trigger via CH2.')
    pdf.bullet(
        'Load side: 120VAC shore power through SSR and relay contacts. '
        'Completely isolated from control side via relay contacts.')
    pdf.bullet('boot.py sets CH1-CH4 GPIOs (4, 5, 6, 15) LOW (OFF) on startup.')

    # =================================================================
    # Section 10: Pre-Installation Checklist
    # =================================================================
    pdf.add_page()
    pdf.section_title('10. Pre-Installation Checklist')

    pdf.sub_title('Tools Required')
    pdf.bullet('Digital multimeter with continuity and AC voltage modes')
    pdf.bullet('Non-contact voltage tester (NCVT)')
    pdf.bullet('Wire strippers rated for 14 AWG and 18-22 AWG')
    pdf.bullet('Crimping tool for ring/spade terminals (if used)')
    pdf.bullet('Small screwdriver for relay module screw terminals and SSR terminals')
    pdf.bullet('Soldering iron (for DS18B20 pull-up resistor)')
    pdf.bullet('Heat shrink tubing and heat gun')
    pdf.bullet('Cable ties and/or aluminum tape (for sensor mounting)')
    pdf.ln(2)

    pdf.sub_title('Materials')
    pdf.bullet('ESP32-S3-N16R8 dev board + 4-channel relay module')
    pdf.bullet('Twtade SSR-40DA solid state relay')
    pdf.bullet('Aluminum heatsink for SSR (at least 4"x4")')
    pdf.bullet('Thermal paste (for SSR-to-heatsink and DS18B20 mounting)')
    pdf.bullet('Supco SFPC freeze protection control (clamp-on)')
    pdf.bullet('DS18B20 waterproof temperature sensor (stainless steel probe)')
    pdf.bullet('4.7K ohm resistor (1/4W, for DS18B20 pull-up)')
    pdf.bullet('BME280 sensor breakout board')
    pdf.bullet('SSD1306 OLED display (128x64, I2C)')
    pdf.bullet('18 AWG 4-conductor thermostat wire (~3 meters for I2C run)')
    pdf.bullet('14 AWG stranded copper wire (THHN or equivalent), 3-4 feet')
    pdf.bullet('18-22 AWG wire for 12VDC SSR trigger connections')
    pdf.bullet('Wire nuts (14 AWG rated) or Wago 221-412/415 connectors')
    pdf.bullet('Junction box (metal or PVC, sized for conductor count)')
    pdf.bullet('Cable clamps / strain reliefs for junction box knockouts')
    pdf.ln(2)

    pdf.sub_title('Verification Checklist')
    checks = [
        'Shore power DISCONNECTED and verified with NCVT',
        'Etratech control box fully removed from circuit',
        'SSR-40DA mounted on heatsink with thermal paste',
        'SSR AC1 (pin 1) connected to 120VAC LINE (14 AWG)',
        'SSR AC2 (pin 2) -> Supco SFPC -> 6-pin Blue (compressor)',
        'SSR DC+ (pin 3) connected to relay module CH2 NO terminal',
        'SSR DC- (pin 4) connected to RV 12VDC GND',
        'CH2 COM connected to RV +12VDC (NOT 120VAC)',
        '120VAC LINE bus connected to CH3/CH4 COM only (14 AWG)',
        'CH3 NO (GPIO 6) -> 6-pin Red (fan low)',
        'CH4 NO (GPIO 15) -> 6-pin Black (fan high)',
        'CH1 (GPIO 4) wired as dry contact for furnace ONLY',
        'CH1 NOT connected to 120VAC or 12VDC bus',
        'Neutral (White) passes through directly -- NOT switched',
        'Ground (Green/Yellow) passes through directly -- NOT switched',
        'Yellow wire (reversing valve) capped with wire nut',
        'Supco SFPC clamped on suction line near evaporator',
        'Supco SFPC verified NC (closed) at room temperature',
        'DS18B20 wired to GPIO 42 with 4.7K pull-up to 3.3V',
        'DS18B20 probe mounted on evaporator coil with thermal paste',
        'I2C cable: SDA=GPIO 41, SCL=GPIO 40, 3.3V, GND',
        'BME280 and OLED responding on I2C bus',
        'All 120VAC connections inside junction box',
        'All wire nuts / Wago connectors tight and secure',
        'Junction box closed and cable clamps installed',
        'Shore power reconnected',
        'ESP32 boot verified: all relays OFF on startup',
        'Each relay tested individually from web UI',
        'SSR trigger verified: GPIO 5 HIGH -> compressor runs',
        'DS18B20 reading verified in web UI (reasonable temperature)',
        'Freeze protection tested: sensor below 32F -> compressor cuts',
    ]
    for check in checks:
        pdf.bullet(f'[ ]  {check}')

    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, 'Generated for RV Thermostat Project - ESP32 MicroPython',
             align='C')

    return pdf


if __name__ == '__main__':
    pdf = build_pdf()
    output = '/home/heath/Dev/rv_thermostat/docs/esp32_dometic_wiring_instructions.pdf'
    pdf.output(output)
    print(f'PDF saved to: {output}')
