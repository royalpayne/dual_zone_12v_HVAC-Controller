#!/usr/bin/env python3
"""Generate ESP32-to-Dometic Control Box wiring instruction PDF."""

from fpdf import FPDF

class WiringPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'ESP32 RV Thermostat - Dometic Control Box Wiring Instructions', align='C', new_x="LMARGIN", new_y="NEXT")
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
        x = self.get_x()
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
        self.rect(10, y, 190, 14, style='DF')
        self.set_xy(14, y + 2)
        self.multi_cell(182, 5, text)
        self.ln(6)

    def info_box(self, text):
        self.set_fill_color(235, 245, 255)
        self.set_draw_color(50, 100, 180)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 60, 120)
        y = self.get_y()
        # Calculate height needed
        lines = len(text) / 85 + text.count('\n')
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
        for i, (cell, w) in enumerate(zip(cells, widths)):
            self.cell(w, 7, cell, border=1, fill=fill, align='C' if bold else 'L')
        self.ln()


def build_pdf():
    pdf = WiringPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ─── Title ───
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(20, 20, 60)
    pdf.cell(0, 12, 'ESP32 Remote Relay Wiring', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Direct Coil Drive on Dometic Etratech 3313199.000 Control Board', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ─── Overview ───
    pdf.section_title('Overview')
    pdf.body_text(
        'This document describes how to wire the ESP32-S3 Remote relay module to the '
        'Dometic Etratech control board (P/N 3313199.000) by driving the onboard relay '
        'coils directly. The ESP32 replaces the Dometic CT thermostat as the sole '
        'controller while keeping the control board\'s 120VAC switching and K1 freeze '
        'sensor protection intact.'
    )

    pdf.warning_box(
        'WARNING: The Etratech board carries 120VAC on LINE/NEUTRAL and relay contacts. '
        'Disconnect shore power before working on this board. Only handle 12VDC signals.'
    )

    # ─── Architecture ───
    pdf.section_title('System Architecture')
    pdf.body_text(
        'The Etratech control board receives 120VAC shore power and has an onboard power '
        'supply that generates 12VDC for the control logic and relay coils. The board has '
        'a microcontroller running "RelayControl V4.hex" firmware that normally decodes '
        'digital commands from the Dometic CT thermostat via a 4-wire data cable.'
    )
    pdf.body_text(
        'By disconnecting the Dometic thermostat and driving the relay coils directly '
        'with the ESP32 relay module, we bypass the MCU while keeping all 120VAC switching '
        'safely inside the control board.'
    )

    pdf.sub_title('Signal Path')
    pdf.body_text(
        'ESP32 GPIO closes HL-52S relay  -->  Coil drive pin connected to GND  -->  '
        '12VDC flows through relay coil  -->  Control board relay (K2/K3/K4) energizes  '
        '-->  120VAC switched to AC unit via 6-pin connector'
    )

    pdf.sub_title('Freeze Protection (K1)')
    pdf.body_text(
        'Relay K1 is wired as a Normally Closed safety interlock in the compressor circuit. '
        'When the evaporator freeze sensor (connected at J4 "Outdoor Sensor") detects icing, '
        'K1 energizes and its NC contact opens, cutting the compressor regardless of what '
        'the ESP32 is doing. This is hardware-level protection independent of any software.'
    )

    # ─── Board Reference ───
    pdf.add_page()
    pdf.section_title('Board Component Reference')

    pdf.sub_title('Relays')
    w = [25, 45, 50, 70]
    pdf.table_row(['Relay', 'Type', 'Coil', 'Function'], w, bold=True, fill=True)
    pdf.table_row(['K1', 'HF3FF 012-1ZS1', '12VDC', 'Freeze safety (NC to compressor)'], w)
    pdf.table_row(['K2', 'HF3FF 012-1ZS1', '12VDC', 'Switching relay -> 6-pin output'], w)
    pdf.table_row(['K3', 'HF3FF 012-1ZS1', '12VDC', 'Switching relay -> 6-pin output'], w)
    pdf.table_row(['K4', 'HF3FF 012-1ZS1', '12VDC', 'Switching relay -> 6-pin output'], w)
    pdf.table_row(['K5', '(empty pads)', '-', 'Reversing valve (not populated)'], w)
    pdf.ln(4)

    pdf.sub_title('Relay Specifications (HF3FF 012-1ZS1)')
    pdf.bullet('Coil voltage: 12VDC')
    pdf.bullet('Coil resistance: ~280-400 ohms')
    pdf.bullet('Contact rating: 12A @ 125VAC / 10A @ 250VAC')
    pdf.bullet('Contact configuration: SPDT (1 Form C: COM, NO, NC)')
    pdf.ln(2)

    pdf.sub_title('Y-Terminal Pads (Bottom Edge of Board)')
    w2 = [25, 55, 55, 55]
    pdf.table_row(['Pad', 'Label', 'Drives', 'Status'], w2, bold=True, fill=True)
    pdf.table_row(['Y8', 'FAN LO', 'K2, K3, or K4 (TBD)', 'Active - use'], w2)
    pdf.table_row(['Y9', 'FAN HI', 'K2, K3, or K4 (TBD)', 'Active - use'], w2)
    pdf.table_row(['Y5', 'REV VALVE', 'K5 (empty)', 'Unused'], w2)
    pdf.table_row(['Y10', '(none)', 'K5 (empty)', 'Unused'], w2)
    pdf.ln(4)

    pdf.sub_title('Connectors & Other Labels')
    pdf.bullet('J2 - Upper connector (thermostat data interface)')
    pdf.bullet('J4 - "Outdoor Sensor" / Freeze sensor input')
    pdf.bullet('LINE / NEUTRAL - 120VAC shore power input')
    pdf.bullet('FURNACE - Labeled pads (upper right) for furnace contact closure')
    pdf.bullet('C10 - Capacitor (not a connection point)')
    pdf.bullet('VDR1 - Varistor (surge protection)')
    pdf.bullet('F1 - Fuse')
    pdf.ln(2)

    pdf.sub_title('4-Wire Thermostat Connector (Disconnect This)')
    w3 = [60, 130]
    pdf.table_row(['Wire', 'Purpose'], w3, bold=True, fill=True)
    pdf.table_row(['+12V from supply', '12VDC input from RV battery/converter'], w3)
    pdf.table_row(['+12V to stat', '12VDC output to Dometic CT thermostat'], w3)
    pdf.table_row(['-12V supply/stat', 'Shared ground'], w3)
    pdf.table_row(['Orange (unlabeled)', 'Digital data line (proprietary protocol)'], w3)
    pdf.ln(2)
    pdf.info_box('Leave this connector disconnected. The ESP32 replaces the Dometic CT thermostat. The MCU on the board will be idle with no thermostat connected.')

    # ─── Procedure ───
    pdf.add_page()
    pdf.section_title('Wiring Procedure')

    pdf.warning_box(
        'DISCONNECT SHORE POWER before Steps 1 and 3. '
        'Step 2 requires the board to be powered - use extreme caution around 120VAC traces.'
    )

    # Step 1
    pdf.sub_title('Step 1: Identify Coil Pins on K2, K3, K4')
    pdf.body_text('Board must be UNPOWERED and removed so you can access the solder side.')
    pdf.bullet('Set multimeter to resistance mode (ohms).')
    pdf.bullet(
        'For each relay (K2, K3, K4), probe pairs of the 5 solder joints on the '
        'back of the board.'
    )
    pdf.bullet(
        'The two pins showing approximately 280-400 ohms are the COIL pins. '
        'The contact pins will show 0 ohms (NC=closed) or OL/infinity (NO=open).'
    )
    pdf.bullet(
        'Mark both coil pins for each relay with a marker or tape. '
        'You now know which 2 of the 5 pins are the coil.'
    )
    pdf.ln(2)

    # Step 2
    pdf.sub_title('Step 2: Identify the Drive Side of Each Coil')
    pdf.body_text(
        'Board must be POWERED for this step. Reinstall the board temporarily, '
        'connect shore power, but do NOT connect the thermostat.'
    )
    pdf.warning_box('120VAC is present on the board. Only touch the coil pins you identified with multimeter probes.')
    pdf.bullet('Set multimeter to DC voltage mode.')
    pdf.bullet(
        'Measure each coil pin (identified in Step 1) relative to the board\'s '
        'ground (-12V). Use the ground wire from the 4-wire thermostat connector '
        'as your ground reference point.'
    )
    pdf.bullet(
        'For each relay, one coil pin will read approximately +12VDC. '
        'This is the power rail side - do NOT solder to this pin.'
    )
    pdf.bullet(
        'The OTHER coil pin will read approximately 0V. '
        'This is the DRIVE SIDE - mark this pin. This is where you will solder your wire.'
    )
    pdf.bullet('Repeat for all three relays (K2, K3, K4). Disconnect shore power when done.')
    pdf.ln(2)

    # Step 3
    pdf.sub_title('Step 3: Identify Which Relay Drives Which Function')
    pdf.body_text(
        'Board must be UNPOWERED. You need access to both the solder side and '
        'the junction box where the 6-pin cable wires terminate with wire nuts.'
    )
    pdf.bullet('Set multimeter to continuity mode (beep).')
    pdf.bullet(
        'Remove the wire nut from the BLUE wire (compressor). Touch one probe to '
        'the bare blue wire end. Touch the other probe to the CONTACT pins '
        '(not coil pins) of each relay on the solder side. The relay that beeps '
        'is the COMPRESSOR relay. (Continuity goes through K1 NC which is closed '
        'when unpowered.)'
    )
    pdf.bullet(
        'Repeat with the BLACK wire (fan high) to identify the FAN HIGH relay.'
    )
    pdf.bullet(
        'Repeat with the RED wire (fan low) to identify the FAN LOW relay.'
    )
    pdf.bullet(
        'Record your findings - you now know which relay (K2, K3, or K4) '
        'drives each function.'
    )
    pdf.ln(2)

    # Step 4
    pdf.add_page()
    pdf.sub_title('Step 4: Solder Wires to the Board')
    pdf.body_text('Board must be UNPOWERED and removed.')
    pdf.bullet(
        'Solder a 22 AWG wire to the DRIVE-SIDE coil pin (from Step 2) of each relay:'
    )
    pdf.bullet('    - Compressor relay drive pin', indent=20)
    pdf.bullet('    - Fan high relay drive pin', indent=20)
    pdf.bullet('    - Fan low relay drive pin', indent=20)
    pdf.bullet(
        'Solder a 4th wire to a GROUND point on the board. The -12V trace or a '
        'ground pad near the thermostat connector are good options.'
    )
    pdf.bullet(
        'Optionally: solder a 5th wire to the FURNACE pads on the board '
        '(upper right area) for furnace contact closure control.'
    )
    pdf.bullet(
        'Route all wires out of the control box enclosure through an appropriate '
        'strain relief or grommet. Use heat shrink on solder joints.'
    )
    pdf.ln(2)

    # Step 5
    pdf.sub_title('Step 5: Wire to ESP32 Relay Module')
    pdf.body_text(
        'Connect the wires from the Etratech board to the ESP32 HL-52S relay module:'
    )
    pdf.ln(2)

    w4 = [55, 45, 55, 35]
    pdf.table_row(['ESP32 Relay', 'GPIO', 'Etratech Wire', 'Function'], w4, bold=True, fill=True)
    pdf.table_row(['All relay COM', '(bus)', 'Board GND (-12V)', 'Common ground'], w4)
    pdf.table_row(['Relay 2 NO', 'GPIO 39', 'Comp relay drive', 'Compressor'], w4)
    pdf.table_row(['Relay 3 NO', 'GPIO 40', 'Fan lo relay drive', 'Fan Low'], w4)
    pdf.table_row(['Relay 4 NO', 'GPIO 41', 'Fan hi relay drive', 'Fan High'], w4)
    pdf.table_row(['Relay 1 NO', 'GPIO 38', 'FURNACE pads', 'Furnace'], w4)
    pdf.ln(4)

    pdf.sub_title('How It Works')
    pdf.bullet(
        'When ESP32 sets GPIO 39 HIGH, the HL-52S relay closes, connecting the '
        'compressor relay coil drive pin to ground.'
    )
    pdf.bullet(
        '12VDC from the board\'s power rail flows through the relay coil to ground, '
        'energizing the relay.'
    )
    pdf.bullet(
        'The control board relay closes its contacts, switching 120VAC through to '
        'the compressor contactor via the 6-pin cable.'
    )
    pdf.bullet(
        'K1 freeze safety relay remains in the compressor circuit - if the freeze '
        'sensor trips, K1 opens and cuts the compressor regardless of ESP32 state.'
    )
    pdf.ln(2)

    # ─── 6-Pin Cable Reference ───
    pdf.add_page()
    pdf.section_title('6-Pin Output Cable Reference')
    pdf.body_text('This cable runs from the control box to the Dometic Brisk II rooftop AC unit.')

    w5 = [15, 30, 45, 50, 50]
    pdf.table_row(['Pin', 'Color', 'Function', 'Control Board', '120VAC Load'], w5, bold=True, fill=True)
    pdf.table_row(['1', 'Blue', 'Compressor', 'K?? -> K1 NC', 'Comp contactor'], w5)
    pdf.table_row(['2', 'Black', 'Fan High', 'K??', 'Fan motor high'], w5)
    pdf.table_row(['3', 'Yellow', 'Rev Valve', 'K5 (empty)', 'Not connected'], w5)
    pdf.table_row(['4', 'Red', 'Fan Low', 'K??', 'Fan motor low'], w5)
    pdf.table_row(['5', 'White', 'Common', 'Neutral bus', '120VAC return'], w5)
    pdf.table_row(['6', 'Grn/Ylw', 'Chassis Gnd', 'Direct', 'Safety ground'], w5)
    pdf.ln(4)

    pdf.info_box(
        'NOTE: The 6-pin cable carries 120VAC, NOT 24VAC as previously documented. '
        'The control board relays (HF3FF, 12A/125VAC) switch 120VAC from the LINE '
        'input directly to the AC unit. Do not splice into this cable with the '
        'ESP32 relay module.'
    )

    # ─── Failsafe ───
    pdf.section_title('Failsafe Behavior')

    w6 = [60, 130]
    pdf.table_row(['Condition', 'Result'], w6, bold=True, fill=True)
    pdf.table_row(['ESP32 power loss', 'All HL-52S relays open -> all coils de-energized -> HVAC OFF'], w6)
    pdf.table_row(['Shore power loss', 'Control board dead, no 120VAC -> HVAC OFF'], w6)
    pdf.table_row(['Evaporator freeze', 'K1 opens NC contact -> compressor cut (hardware)'], w6)
    pdf.table_row(['ESP32 + thermostat off', 'MCU idle, ESP32 relays open -> all HVAC OFF'], w6)
    pdf.ln(4)

    pdf.warning_box(
        'There is NO backup thermostat. If the ESP32 loses power or crashes, '
        'all HVAC stops. The system is fail-safe (everything OFF) but not fail-operational.'
    )

    # ─── ESP32 Remote Reference ───
    pdf.section_title('ESP32-S3 Remote Reference')
    pdf.body_text('ESP32-S3 N16R8 (40-pin) at IP 192.168.71.153')

    w7 = [30, 50, 60, 50]
    pdf.table_row(['GPIO', 'Relay', 'Etratech Target', 'Function'], w7, bold=True, fill=True)
    pdf.table_row(['38', 'Relay 1 NO', 'FURNACE pads', 'Furnace call'], w7)
    pdf.table_row(['39', 'Relay 2 NO', 'Comp coil drive', 'Compressor'], w7)
    pdf.table_row(['40', 'Relay 3 NO', 'Fan lo coil drive', 'Fan low speed'], w7)
    pdf.table_row(['41', 'Relay 4 NO', 'Fan hi coil drive', 'Fan high speed'], w7)
    pdf.table_row(['17', '-', '-', 'IR RX (VS1838B)'], w7)
    pdf.table_row(['18', '-', '-', 'IR TX (2N2222 driver)'], w7)
    pdf.table_row(['8', '-', '-', 'I2C SDA (BME280/OLED)'], w7)
    pdf.table_row(['9', '-', '-', 'I2C SCL (BME280/OLED)'], w7)
    pdf.ln(4)

    pdf.sub_title('Relay Module: HL-52S 4-Channel')
    pdf.bullet('Active HIGH trigger (jumper set to HIGH)')
    pdf.bullet('5V VCC from buck converter')
    pdf.bullet('Relay contacts: 10A @ 250VAC (not used for 120VAC in this design)')
    pdf.bullet('Relay coil drive: Optocoupler isolated, 3.3V GPIO compatible')
    pdf.bullet('boot.py sets all relay GPIOs LOW (OFF) on startup')

    # ─── Checklist ───
    pdf.add_page()
    pdf.section_title('Pre-Installation Checklist')

    pdf.sub_title('Tools Required')
    pdf.bullet('Digital multimeter with continuity, resistance, and DC voltage modes')
    pdf.bullet('Soldering iron with fine tip')
    pdf.bullet('22 AWG hookup wire (4-5 pieces, ~12 inches each)')
    pdf.bullet('Heat shrink tubing')
    pdf.bullet('Wire strippers')
    pdf.bullet('Marker or tape for labeling')
    pdf.bullet('Strain relief grommet for control box enclosure')
    pdf.ln(2)

    pdf.sub_title('Materials')
    pdf.bullet('ESP32-S3 Remote with HL-52S relay module (already assembled)')
    pdf.bullet('5V buck converter (already powering relay module and IR LEDs)')
    pdf.bullet('Wago 221-412 connectors (optional, for furnace wiring)')
    pdf.ln(2)

    pdf.sub_title('Verification Checklist')
    pdf.set_font('Helvetica', '', 10)
    checks = [
        'Shore power DISCONNECTED before opening control box',
        'Coil pins identified on K2, K3, K4 (resistance test)',
        'Drive side identified on each coil (voltage test)',
        'Relay-to-function mapping confirmed (continuity test)',
        'Wires soldered to drive-side coil pins with heat shrink',
        'Ground wire soldered to board GND',
        'Wires routed through strain relief',
        'ESP32 relay COM bus connected to board GND',
        'ESP32 relay NO contacts connected to correct coil drive pins',
        'Furnace relay connected to FURNACE pads',
        '4-wire thermostat connector LEFT DISCONNECTED',
        'All wire nuts on 6-pin cable securely reinstalled',
        'Control box cover reinstalled',
        'Shore power reconnected',
        'ESP32 tested: each relay activates correct function',
        'Freeze sensor tested: compressor cuts when sensor triggered',
    ]
    for check in checks:
        pdf.bullet(f'[ ]  {check}')

    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, 'Generated for RV Thermostat Project - github.com/heath (ESP32 MicroPython)', align='C')

    return pdf


if __name__ == '__main__':
    pdf = build_pdf()
    output = '/home/heath/Dev/rv_thermostat/docs/esp32_dometic_wiring_instructions.pdf'
    pdf.output(output)
    print(f'PDF saved to: {output}')
