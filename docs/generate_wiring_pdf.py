#!/usr/bin/env python3
"""Generate ESP32 Direct 120VAC Wiring Instruction PDF.

SSR-25DA approach: ESP32 HL-52S Relay 2 switches 12VDC to trigger an SSR-25DA
solid state relay for the compressor. HL-52S Relays 3-4 switch 120VAC directly
for fans. The Dometic Etratech control box is eliminated.
"""

from fpdf import FPDF


class WiringPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'ESP32 RV Thermostat - SSR-25DA + HL-52S Wiring Instructions',
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
    pdf.cell(0, 12, 'ESP32 Wiring: SSR-25DA + HL-52S', align='C',
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Dometic Brisk II Direct Wiring (No Control Box)',
             align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # =================================================================
    # Section 1: Overview
    # =================================================================
    pdf.section_title('1. Overview')
    pdf.body_text(
        'This document describes how to wire the ESP32-S3 Remote to control the '
        'Dometic Brisk II rooftop AC unit. The Dometic Etratech control box '
        '(P/N 3313199.000) is eliminated. The ESP32 controls all loads via two '
        'switching stages:'
    )
    pdf.bullet(
        'SSR-25DA solid state relay for the compressor (25A capacity, handles '
        '~12A running current and inrush)')
    pdf.bullet(
        'HL-52S relay module for fans (10A contacts, adequate for ~2-3A fan motors) '
        'and furnace (dry contact)')
    pdf.body_text(
        'The HL-52S Relay 2 does NOT switch 120VAC for the compressor. Instead, '
        'it switches 12VDC from the RV battery to the SSR-25DA DC input, which '
        'then switches 120VAC to the compressor. This keeps all high-current '
        'switching on the SSR while the HL-52S handles only milliamp-level '
        '12VDC trigger current.'
    )

    pdf.warning_box(
        'WARNING: This system switches 120VAC through the SSR-25DA and HL-52S '
        'relay contacts. All 120VAC wiring must be in a proper junction box with '
        '14 AWG wire (minimum for 15A circuit). The SSR-25DA must be mounted on '
        'a heatsink. Disconnect shore power before all wiring work.')

    # =================================================================
    # Section 2: System Architecture
    # =================================================================
    pdf.section_title('2. System Architecture')

    pdf.sub_title('Compressor Signal Path')
    pdf.body_text(
        'ESP32 GPIO 39 HIGH -> HL-52S Relay 2 closes -> 12VDC from RV battery '
        'reaches SSR-25DA DC+ input -> SSR turns ON -> 120VAC LINE flows through '
        'SSR AC output -> Supco SFPC freeze stat (NC) -> 6-pin Blue wire -> '
        'Compressor motor')
    pdf.info_box(
        'The SSR-25DA handles the full compressor load current (25A rating vs '
        '~12A running). The HL-52S Relay 2 only switches 12VDC at milliamps to '
        'trigger the SSR. This eliminates relay contact wear and welding risk.')

    pdf.sub_title('Fan Signal Path')
    pdf.body_text(
        'ESP32 GPIO 40/41 HIGH -> HL-52S Relay 3/4 closes -> 120VAC LINE flows '
        'directly through relay NO contact -> 6-pin Red/Black wire -> Fan motor. '
        'Fan motors draw ~2-3A, well within the HL-52S 10A contact rating.')

    pdf.sub_title('Freeze Protection (Dual-Layer)')
    pdf.body_text(
        'With the Etratech control box removed, the built-in K1 freeze relay is '
        'gone. Freeze protection is now provided by two independent layers:')
    pdf.bullet(
        'SOFTWARE: DS18B20 waterproof probe on the evaporator coil, connected to '
        'ESP32 GPIO 42. When evaporator temp drops below 32F, the ESP32 cuts the '
        'compressor (GPIO 39 LOW). Held off until evaporator recovers to 45F.')
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

    pdf.sub_title('SSR-25DA Solid State Relay')
    w_ssr = [40, 150]
    pdf.table_row(['Spec', 'Value'], w_ssr, bold=True, fill=True)
    pdf.table_row(['Model', 'Twtade SSR-25DA'], w_ssr)
    pdf.table_row(['Output', '24-380VAC, 25A'], w_ssr)
    pdf.table_row(['Input', '3-32VDC (triggered with 12VDC from RV battery)'], w_ssr)
    pdf.table_row(['Heatsink', 'Required (~15W dissipation at 12A load)'], w_ssr)
    pdf.ln(2)
    pdf.body_text('Terminal assignments:')
    pdf.bullet('DC+ (pin 3): 12VDC from HL-52S Relay 2 NO output')
    pdf.bullet('DC- (pin 4): 12VDC GND (RV battery negative)')
    pdf.bullet('AC1 (pin 1): 120VAC LINE (hot) input')
    pdf.bullet('AC2 (pin 2): Output to freeze stat -> 6-pin Blue wire')
    pdf.ln(2)

    pdf.info_box(
        'Why not trigger the SSR directly from 3.3V GPIO? The SSR-25DA needs '
        '~5mA minimum to trigger reliably. At 3.3V through its internal resistor '
        'and LED, only ~1.5mA is available. Using the HL-52S relay to switch 12VDC '
        'provides ~15mA -- well above the minimum threshold.')

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

    pdf.sub_title('HL-52S 4-Channel Relay Module')
    w_hl = [40, 150]
    pdf.table_row(['Spec', 'Value'], w_hl, bold=True, fill=True)
    pdf.table_row(['Trigger', 'Active HIGH (jumper set to HIGH)'], w_hl)
    pdf.table_row(['VCC', '5V from buck converter'], w_hl)
    pdf.table_row(['Contacts', '10A @ 250VAC per relay (SRD-05VDC-SL-C)'], w_hl)
    pdf.table_row(['Isolation', 'Optocoupler, 3.3V GPIO compatible'], w_hl)
    pdf.ln(4)

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
    pdf.table_row(['2', 'Black', 'Fan High', 'HL-52S Relay 4 NO -> Black'], w5)
    pdf.table_row(['3', 'Yellow', 'Rev Valve', 'Not connected (no heat pump)'], w5)
    pdf.table_row(['4', 'Red', 'Fan Low', 'HL-52S Relay 3 NO -> Red'], w5)
    pdf.table_row(['5', 'White', 'Neutral', 'Pass-through to AC unit'], w5)
    pdf.table_row(['6', 'Grn/Ylw', 'Chassis Gnd', 'Pass-through to AC unit'], w5)
    pdf.ln(4)

    pdf.sub_title('HL-52S Relay Connections')

    w4 = [40, 30, 55, 65]
    pdf.table_row(['Relay', 'GPIO', 'Switches', 'Connection'], w4, bold=True, fill=True)
    pdf.table_row(['Relay 1', 'GPIO 38', 'Dry contact', 'Furnace call (no voltage)'], w4)
    pdf.table_row(['Relay 2', 'GPIO 39', '12VDC', 'SSR DC+ trigger (from RV battery)'], w4)
    pdf.table_row(['Relay 3', 'GPIO 40', '120VAC', 'Fan Low (direct to Red)'], w4)
    pdf.table_row(['Relay 4', 'GPIO 41', '120VAC', 'Fan High (direct to Black)'], w4)
    pdf.ln(2)

    pdf.warning_box(
        'Relay 2 (Compressor) is NOT on the 120VAC bus. Its COM connects to RV '
        '+12VDC, and its NO connects to SSR DC+. The SSR handles 120VAC switching. '
        'Relay 1 (Furnace) is a dry contact. Only Relays 3 and 4 carry 120VAC.')

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
    pdf.sub_title('Step 2: Mount and Wire the SSR-25DA')
    pdf.bullet(
        'Mount the SSR-25DA on a metal heatsink (aluminum, at least 4"x4"). '
        'Use thermal paste between SSR and heatsink. Mount heatsink inside or '
        'adjacent to the junction box with adequate airflow.')
    pdf.bullet(
        'AC1 (pin 1): Connect with 14 AWG wire to 120VAC LINE (hot). Use a '
        'Wago 221-412 or wire nut to branch LINE to both the SSR AC1 and the '
        'Relay 3/4 COM bus.')
    pdf.bullet(
        'AC2 (pin 2): Connect with 14 AWG wire to the Supco SFPC freeze stat '
        'input terminal. The freeze stat output connects to the 6-pin Blue wire.')
    pdf.bullet(
        'DC+ (pin 3): Connect with 18-22 AWG wire to HL-52S Relay 2 NO terminal.')
    pdf.bullet(
        'DC- (pin 4): Connect with 18-22 AWG wire to RV 12VDC GND (battery '
        'negative / chassis ground).')
    pdf.ln(2)

    # Step 3
    pdf.sub_title('Step 3: Wire 120VAC Bus to Relay 3/4 COM')
    pdf.bullet(
        'Create a 120VAC LINE bus to Relay 3 COM and Relay 4 COM. Use 14 AWG '
        'wire and Wago connectors or wire nuts to branch from the same LINE '
        'wire feeding SSR AC1.')
    pdf.bullet(
        'Relay 3 NO (GPIO 40) -> 14 AWG -> 6-pin Red wire (Fan Low)')
    pdf.bullet(
        'Relay 4 NO (GPIO 41) -> 14 AWG -> 6-pin Black wire (Fan High)')
    pdf.ln(2)

    # Step 4
    pdf.sub_title('Step 4: Wire 12VDC to Relay 2 COM')
    pdf.bullet(
        'Connect RV +12VDC (house battery / converter) to Relay 2 COM terminal. '
        'Use 18-22 AWG wire. This is the SSR trigger source.')
    pdf.bullet(
        'Relay 2 NO connects to SSR DC+ (already done in Step 2).')
    pdf.bullet(
        'When GPIO 39 goes HIGH, Relay 2 closes, 12VDC reaches SSR DC+, and '
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
    pdf.sub_title('Step 6: Wire Furnace (Relay 1)')
    pdf.bullet(
        'Connect furnace call wires to Relay 1 COM and NO terminals. This is '
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
    pdf.bullet('Wire: Red to 3.3V, Black to GND, Yellow/White data to GPIO 42.')
    pdf.bullet(
        'Solder a 4.7K ohm pull-up resistor between GPIO 42 and 3.3V, as '
        'close to the ESP32 as practical.')
    pdf.bullet('Route sensor cable away from 120VAC wires to avoid noise.')

    # =================================================================
    # Section 6: Freeze Protection Details
    # =================================================================
    pdf.add_page()
    pdf.section_title('6. Freeze Protection Details')

    pdf.sub_title('Software Layer (DS18B20)')
    w_th = [95, 95]
    pdf.table_row(['Condition', 'Action'], w_th, bold=True, fill=True)
    pdf.table_row(['Evap temp < 32F', 'Cut compressor (GPIO 39 LOW)'], w_th)
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
    # Section 7: Failsafe Behavior
    # =================================================================
    pdf.section_title('7. Failsafe Behavior')

    pdf.body_text(
        'The system is fail-safe: any single point of failure results in HVAC OFF. '
        'The SSR-25DA and HL-52S relays are normally open, so power loss to the '
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
    pdf.table_row(['HL-52S relay welded', 'Only that one fan load stays on'], w6)
    pdf.table_row(['120VAC bus fault', 'Breaker trips -> all loads OFF'], w6)
    pdf.ln(4)

    pdf.warning_box(
        'There is NO backup thermostat. If the ESP32 loses power or crashes, all '
        'HVAC stops until the ESP32 recovers. The system is fail-safe (everything '
        'OFF) but not fail-operational.')

    # =================================================================
    # Section 8: ESP32-S3 Remote GPIO Reference
    # =================================================================
    pdf.add_page()
    pdf.section_title('8. ESP32-S3 Remote GPIO Reference')
    pdf.body_text('ESP32-S3 N16R8 (40-pin) at IP 192.168.71.153')

    w7 = [30, 50, 55, 55]
    pdf.table_row(['GPIO', 'Function', 'Relay/Device', 'Load'], w7, bold=True, fill=True)
    pdf.table_row(['38', 'Furnace', 'Relay 1 NO/COM', 'Dry contact closure'], w7)
    pdf.table_row(['39', 'Compressor', 'Relay 2 -> SSR', '12VDC trigger -> SSR 120VAC'], w7)
    pdf.table_row(['40', 'Fan Low', 'Relay 3 NO', '120VAC -> Red'], w7)
    pdf.table_row(['41', 'Fan High', 'Relay 4 NO', '120VAC -> Black'], w7)
    pdf.table_row(['42', 'Freeze Sensor', 'DS18B20', '1-Wire, 4.7K pull-up to 3.3V'], w7)
    pdf.table_row(['8', 'I2C SDA', 'BME280 / OLED', 'Sensor + display'], w7)
    pdf.table_row(['9', 'I2C SCL', 'BME280 / OLED', 'Sensor + display'], w7)
    pdf.ln(4)

    pdf.sub_title('Power Architecture')
    pdf.bullet(
        'Control side: RV 12VDC battery system (always available with battery). '
        'Powers ESP32 (via USB or regulator), relay module VCC, SSR trigger.')
    pdf.bullet(
        'Load side: 120VAC shore power through SSR and relay contacts. '
        'Completely isolated from control side via optocouplers.')
    pdf.bullet('boot.py sets all relay GPIOs LOW (OFF) immediately on startup.')

    # =================================================================
    # Section 9: Pre-Installation Checklist
    # =================================================================
    pdf.add_page()
    pdf.section_title('9. Pre-Installation Checklist')

    pdf.sub_title('Tools Required')
    pdf.bullet('Digital multimeter with continuity and AC voltage modes')
    pdf.bullet('Non-contact voltage tester (NCVT)')
    pdf.bullet('Wire strippers rated for 14 AWG and 18-22 AWG')
    pdf.bullet('Crimping tool for ring/spade terminals (if used)')
    pdf.bullet('Screwdriver set (flat and Phillips) for relay/SSR screw terminals')
    pdf.bullet('Soldering iron (for DS18B20 pull-up resistor)')
    pdf.bullet('Heat shrink tubing and heat gun')
    pdf.bullet('Cable ties and/or aluminum tape (for sensor mounting)')
    pdf.ln(2)

    pdf.sub_title('Materials')
    pdf.bullet('ESP32-S3 Remote with HL-52S relay module (already assembled)')
    pdf.bullet('Twtade SSR-25DA solid state relay')
    pdf.bullet('Aluminum heatsink for SSR (at least 4"x4")')
    pdf.bullet('Thermal paste (for SSR-to-heatsink and DS18B20 mounting)')
    pdf.bullet('5V buck converter (already powering relay module and IR LEDs)')
    pdf.bullet('Supco SFPC freeze protection control (clamp-on)')
    pdf.bullet('DS18B20 waterproof temperature sensor (stainless steel probe)')
    pdf.bullet('4.7K ohm resistor (1/4W, for DS18B20 pull-up)')
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
        'SSR-25DA mounted on heatsink with thermal paste',
        'SSR AC1 (pin 1) connected to 120VAC LINE (14 AWG)',
        'SSR AC2 (pin 2) -> Supco SFPC -> 6-pin Blue (compressor)',
        'SSR DC+ (pin 3) connected to HL-52S Relay 2 NO',
        'SSR DC- (pin 4) connected to RV 12VDC GND',
        'Relay 2 COM connected to RV +12VDC (NOT 120VAC)',
        '120VAC LINE bus connected to Relay 3/4 COM only (14 AWG)',
        'Relay 3 NO (GPIO 40) -> 6-pin Red (fan low)',
        'Relay 4 NO (GPIO 41) -> 6-pin Black (fan high)',
        'Relay 1 (GPIO 38) wired as dry contact for furnace ONLY',
        'Relay 1 NOT connected to 120VAC or 12VDC bus',
        'Neutral (White) passes through directly -- NOT switched',
        'Ground (Green/Yellow) passes through directly -- NOT switched',
        'Yellow wire (reversing valve) capped with wire nut',
        'Supco SFPC clamped on suction line near evaporator',
        'Supco SFPC verified NC (closed) at room temperature',
        'DS18B20 wired to GPIO 42 with 4.7K pull-up to 3.3V',
        'DS18B20 probe mounted on evaporator coil with thermal paste',
        'All 120VAC connections inside junction box',
        'All wire nuts / Wago connectors tight and secure',
        'Junction box closed and cable clamps installed',
        'Shore power reconnected',
        'ESP32 boot verified: all relays OFF on startup',
        'Each relay tested individually from web UI',
        'SSR trigger verified: GPIO 39 HIGH -> compressor runs',
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
