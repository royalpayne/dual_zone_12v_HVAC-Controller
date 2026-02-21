#!/usr/bin/env python3
"""
Create all wiring diagrams with updated components:
- Waveshare ESP32-S3-Relay-6CH
- IP65 waterproof enclosure (6.3"x4.33"x3.54")
- Correct GPIO assignments
- Wire labels positioned BELOW lines
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

def create_ssr_diagram():
    """SSR-25DA Compressor Wiring - Updated"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(7, 9.5, 'SSR-25DA COMPRESSOR WIRING DIAGRAM',
            ha='center', fontsize=18, weight='bold')
    ax.text(7, 9.1, 'Waveshare ESP32-S3-Relay-6CH → SSR-25DA → Compressor',
            ha='center', fontsize=12)

    # Waveshare Module Box
    ws_box = FancyBboxPatch((0.2, 5), 2.8, 3, boxstyle="round,pad=0.1",
                            edgecolor='#0066cc', facecolor='#e6f3ff', linewidth=2.5)
    ax.add_patch(ws_box)
    ax.text(1.6, 7.7, 'Waveshare', ha='center', fontsize=11, weight='bold')
    ax.text(1.6, 7.45, 'ESP32-S3-Relay-6CH', ha='center', fontsize=10)

    # Module pins
    ax.plot(3.0, 7.2, 'o', color='#ff6600', markersize=8)
    ax.text(3.2, 7.2, 'CH2 (GPIO 2)', va='center', fontsize=9)

    ax.plot(3.0, 6.5, 'o', color='black', markersize=8)
    ax.text(3.2, 6.5, 'GND', va='center', fontsize=9)

    ax.plot(3.0, 5.8, 'o', color='#cc0000', markersize=8)
    ax.text(3.2, 5.8, '12V+', va='center', fontsize=9)

    # Relay output terminals
    relay_box = FancyBboxPatch((4, 5), 3, 3, boxstyle="round,pad=0.1",
                               edgecolor='#ff6600', facecolor='#fff3e0', linewidth=2.5)
    ax.add_patch(relay_box)
    ax.text(5.5, 7.7, 'Relay CH2 Output', ha='center', fontsize=11, weight='bold')
    ax.text(5.5, 7.4, '(Compressor Control)', ha='center', fontsize=9, style='italic')

    # Relay terminals
    ax.plot(4.0, 7, 'o', color='#ff6600', markersize=8)
    ax.text(3.8, 7, 'IN', ha='right', va='center', fontsize=9)

    ax.plot(7.0, 7, 'o', color='#cc0000', markersize=8)
    ax.text(7.2, 7, 'COM (12V)', va='center', fontsize=9)

    ax.plot(7.0, 6.3, 'o', color='#cc0000', markersize=8)
    ax.text(7.2, 6.3, 'NO', va='center', fontsize=9)

    ax.plot(7.0, 5.6, 'o', color='gray', markersize=8)
    ax.text(7.2, 5.6, 'NC (unused)', va='center', fontsize=9, color='gray')

    # Wires: Waveshare to Relay input
    ax.plot([3.0, 4.0], [7.2, 7], color='#ff6600', linewidth=2.5)
    ax.text(3.5, 6.9, 'Control', fontsize=8, color='#ff6600')  # BELOW line

    # 12V to COM
    ax.plot([3.0, 7.0], [5.8, 7], color='#cc0000', linewidth=2.5)
    ax.text(5, 6.2, '12VDC', fontsize=8, color='#cc0000')  # BELOW line

    # SSR-25DA
    ssr_box = FancyBboxPatch((8, 5), 2.5, 3, boxstyle="round,pad=0.1",
                             edgecolor='#cc0000', facecolor='#fff5f5', linewidth=2.5)
    ax.add_patch(ssr_box)
    ax.text(9.25, 7.7, 'SSR-25DA', ha='center', fontsize=11, weight='bold')
    ax.text(9.25, 7.4, 'Solid State Relay', ha='center', fontsize=9)
    ax.text(9.25, 7.1, '3-32VDC → 25A/380VAC', ha='center', fontsize=8, style='italic')

    # SSR DC pins (left)
    ax.plot(8, 6.6, 'o', color='#cc0000', markersize=8)
    ax.text(7.8, 6.6, 'DC+', ha='right', va='center', fontsize=9)

    ax.plot(8, 5.9, 'o', color='black', markersize=8)
    ax.text(7.8, 5.9, 'DC-', ha='right', va='center', fontsize=9)

    # SSR AC pins (right)
    ax.plot(10.5, 6.6, 'o', color='#ff0000', markersize=8)
    ax.text(10.7, 6.6, 'AC1 (in)', va='center', fontsize=9)

    ax.plot(10.5, 5.9, 'o', color='#ff0000', markersize=8)
    ax.text(10.7, 5.9, 'AC2 (out)', va='center', fontsize=9)

    # Wires: Relay to SSR
    ax.plot([7.0, 8], [6.3, 6.6], color='#cc0000', linewidth=2.5)
    ax.text(7.5, 6.2, '12V Trigger', fontsize=8, color='#cc0000')  # BELOW line

    # Ground wire (route below)
    ax.plot([3.0, 3.0, 8, 8], [6.5, 4.5, 4.5, 5.9], color='black', linewidth=2.5)
    ax.text(5.5, 4.2, 'GND', ha='center', fontsize=8)  # BELOW line

    # 120VAC Source
    vac_box = FancyBboxPatch((11.5, 6.5), 2, 1.5, boxstyle="round,pad=0.1",
                             edgecolor='#ff0000', facecolor='#ffeeee', linewidth=2.5)
    ax.add_patch(vac_box)
    ax.text(12.5, 7.8, '120VAC SOURCE', ha='center', fontsize=11, weight='bold', color='#ff0000')

    ax.plot(11.7, 7.5, 'o', color='#ff0000', markersize=8)
    ax.text(11.5, 7.5, 'HOT', ha='right', va='center', fontsize=9)

    ax.plot(11.7, 7, 'o', color='#0000ff', markersize=8)
    ax.text(11.5, 7, 'NEUTRAL', ha='right', va='center', fontsize=9)

    # Wire: 120VAC HOT to SSR AC1
    ax.plot([11.7, 11, 11, 10.5], [7.5, 7.5, 6.6, 6.6], color='#ff0000', linewidth=3)
    ax.text(10.9, 7.1, '⚠ 120VAC\nHOT', ha='center', fontsize=8, color='#ff0000', weight='bold')

    # Load Chain
    load_box = FancyBboxPatch((11.5, 2.5), 2, 2.5, boxstyle="round,pad=0.1",
                              edgecolor='black', facecolor='#f0f0f0', linewidth=2)
    ax.add_patch(load_box)
    ax.text(12.5, 4.8, 'LOAD CHAIN', ha='center', fontsize=10, weight='bold')

    ax.plot(12.5, 4.2, 'o', color='#ff0000', markersize=8)
    ax.text(12.5, 4.4, 'Supco SFPC', ha='center', fontsize=8)
    ax.text(12.5, 4, '(freeze stat)', ha='center', fontsize=7, style='italic')

    ax.plot(12.5, 3.2, 'o', color='#ff0000', markersize=8)
    ax.text(12.5, 3, 'Bimetal\nCutout', ha='center', fontsize=8)

    # Wire: SSR AC2 to Load Chain
    ax.plot([10.5, 11, 11, 12.5], [5.9, 5.9, 4.2, 4.2], color='#ff0000', linewidth=3)
    ax.text(10.9, 5, '⚠ 120VAC\nSWITCHED', ha='center', fontsize=8, color='#ff0000', weight='bold')

    # Wire through load chain
    ax.plot([12.5, 12.5], [4.2, 3.2], color='#ff0000', linewidth=3)

    # Compressor
    comp_box = FancyBboxPatch((11.5, 0.8), 2, 1.2, boxstyle="round,pad=0.1",
                              edgecolor='black', facecolor='#f0f0f0', linewidth=2.5)
    ax.add_patch(comp_box)
    ax.text(12.5, 1.8, 'COMPRESSOR', ha='center', fontsize=10, weight='bold')
    ax.plot(12.5, 1.2, 'o', color='#ff0000', markersize=8)
    ax.text(12.5, 1, 'Pin 1 Blue', ha='center', fontsize=8)

    # Wire: Load chain to compressor
    ax.plot([12.5, 12.5], [3.2, 1.2], color='#ff0000', linewidth=3)

    # Wire: Compressor to NEUTRAL (return)
    ax.plot([12.5, 12.5, 13.5, 13.5, 11.7], [1.2, 0.5, 0.5, 7, 7], color='#0000ff', linewidth=3)
    ax.text(13.7, 3.5, 'NEUTRAL\nRETURN', ha='left', fontsize=8, color='#0000ff', rotation=90, va='center')

    # Safety notes box
    notes_box = FancyBboxPatch((0.2, 0.3), 7, 3.8, boxstyle="round,pad=0.1",
                               edgecolor='#ff0000', facecolor='#fff5f5', linewidth=2.5, linestyle='--')
    ax.add_patch(notes_box)
    ax.text(3.7, 3.9, '⚠ SAFETY CRITICAL WIRING ⚠', ha='center', fontsize=11, weight='bold', color='#ff0000')

    notes = [
        "KEY POINTS:",
        "• Waveshare CH2 relay NO terminal switches 12VDC to SSR DC+",
        "• Relay switches milliamp trigger current to SSR",
        "• SSR switches high-current 120VAC to compressor",
        "• SSR needs heatsink (~15W @ 12A compressor load)",
        "• Supco SFPC: NC contact, opens 35°F, closes 50°F",
        "• Bimetal cutout: thermal overload protection",
        "• All 120VAC wiring must be 14 AWG minimum",
        "• Install in proper junction box per NEC",
        "• Other relays (CH1/3/4) switch 120VAC directly",
        "  (~2-3A fan loads, 10A relay rating)"
    ]

    y_pos = 3.5
    for note in notes:
        if note.startswith("KEY"):
            ax.text(0.4, y_pos, note, fontsize=9, weight='bold')
        else:
            ax.text(0.4, y_pos, note, fontsize=8)
        y_pos -= 0.3

    plt.tight_layout()
    plt.savefig('docs/ssr_wiring_pro.pdf', dpi=300, bbox_inches='tight')
    print("✓ Created ssr_wiring_pro.pdf")
    plt.close()


def create_i2c_diagram():
    """OLED/BME280 I2C Wiring - Updated"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(7, 9.5, 'OLED & BME280 I2C WIRING DIAGRAM',
            ha='center', fontsize=18, weight='bold')
    ax.text(7, 9.1, '3-Meter Run: Waveshare Module → Thermostat Location',
            ha='center', fontsize=12)

    # Waveshare Module Box
    ws_box = FancyBboxPatch((0.5, 4), 3, 4, boxstyle="round,pad=0.1",
                            edgecolor='#0066cc', facecolor='#e6f3ff', linewidth=3)
    ax.add_patch(ws_box)
    ax.text(2, 7.7, 'WAVESHARE MODULE', ha='center', fontsize=12, weight='bold')
    ax.text(2, 7.4, 'ESP32-S3-Relay-6CH', ha='center', fontsize=9, style='italic')
    ax.text(2, 7.1, 'IP65 Enclosure', ha='center', fontsize=8, color='#666')
    ax.text(2, 6.85, '6.3"×4.33"×3.54"', ha='center', fontsize=8, color='#666')

    # Module I2C pins
    ax.plot(3.5, 6.2, 'o', color='#ff0000', markersize=10)
    ax.text(3.7, 6.2, '3.3V', va='center', fontsize=9)

    ax.plot(3.5, 5.9, 'o', color='black', markersize=10)
    ax.text(3.7, 5.9, 'GND', va='center', fontsize=9)

    ax.plot(3.5, 5.6, 'o', color='#00cc00', markersize=10)
    ax.text(3.7, 5.6, 'GPIO 8 (SDA)', va='center', fontsize=9)

    ax.plot(3.5, 5.3, 'o', color='#0066ff', markersize=10)
    ax.text(3.7, 5.3, 'GPIO 9 (SCL)', va='center', fontsize=9)

    # Power supply info
    pwr_box = FancyBboxPatch((0.8, 4.3), 2.4, 0.9, boxstyle="round,pad=0.05",
                             edgecolor='#ff6600', facecolor='#fff3e0', linewidth=1.5)
    ax.add_patch(pwr_box)
    ax.text(2, 5, 'Power: 7-36V DC', ha='center', fontsize=9, weight='bold')
    ax.text(2, 4.7, 'Onboard 3.3V reg', ha='center', fontsize=7, style='italic', color='#666')
    ax.text(2, 4.45, '(or 5V USB-C)', ha='center', fontsize=7, style='italic', color='#666')

    # 3-Meter Cable Run
    ax.plot([4, 9.5], [6.5, 6.5], linewidth=6, color='#666666', linestyle='--', solid_capstyle='round')
    ax.text(6.75, 7, '3-METER CABLE RUN', ha='center', fontsize=12, weight='bold')
    ax.text(6.75, 6.7, '18 AWG Thermostat Wire (4 conductors)', ha='center', fontsize=9)

    # Cable wires
    ax.plot([3.5, 9.5], [6.2, 6.2], color='#ff0000', linewidth=3)
    ax.text(6.75, 6.05, '3.3V (red)', ha='center', fontsize=8, color='#ff0000')  # BELOW line

    ax.plot([3.5, 9.5], [5.9, 5.9], color='black', linewidth=3)
    ax.text(6.75, 5.75, 'GND (black)', ha='center', fontsize=8)  # BELOW line

    ax.plot([3.5, 9.5], [5.6, 5.6], color='#00cc00', linewidth=3)
    ax.text(6.75, 5.45, 'SDA (green)', ha='center', fontsize=8, color='#00cc00')  # BELOW line

    ax.plot([3.5, 9.5], [5.3, 5.3], color='#0066ff', linewidth=3)
    ax.text(6.75, 5.15, 'SCL (blue)', ha='center', fontsize=8, color='#0066ff')  # BELOW line

    # Thermostat Location
    therm_box = FancyBboxPatch((9, 3), 4.5, 5, boxstyle="round,pad=0.1",
                               edgecolor='#ff6600', facecolor='#fff5e6', linewidth=3)
    ax.add_patch(therm_box)
    ax.text(11.25, 7.7, 'THERMOSTAT LOCATION', ha='center', fontsize=12, weight='bold')
    ax.text(11.25, 7.4, '(Former Dometic Stat Position)', ha='center', fontsize=9, style='italic')

    # 12V supply at thermostat (optional)
    v12_box = FancyBboxPatch((9.5, 6.7), 1.5, 0.8, boxstyle="round,pad=0.05",
                             edgecolor='#666', facecolor='#f0f0f0', linewidth=1.5)
    ax.add_patch(v12_box)
    ax.text(10.25, 7.3, '12V Supply', ha='center', fontsize=9, weight='bold')
    ax.text(10.25, 7.1, '(Available)', ha='center', fontsize=7, style='italic')
    ax.plot(9.7, 6.9, 'o', color='#cc0000', markersize=8)
    ax.text(9.9, 6.9, '12V+', va='center', fontsize=8)
    ax.plot(10.7, 6.9, 'o', color='black', markersize=8)
    ax.text(10.9, 6.9, 'GND', va='center', fontsize=8)

    # Ground connection
    ax.plot([9.5, 10.7], [5.9, 6.9], color='black', linewidth=3.5)
    ax.text(10, 6.3, '← Common\nGround OK', fontsize=8, color='#0066cc', weight='bold')

    # Connection bus points
    ax.plot(9.5, 6.2, 'o', color='#ff0000', markersize=12)
    ax.plot(9.5, 5.9, 'o', color='black', markersize=12)
    ax.plot(9.5, 5.6, 'o', color='#00cc00', markersize=12)
    ax.plot(9.5, 5.3, 'o', color='#0066ff', markersize=12)

    # OLED Display
    oled_box = FancyBboxPatch((9.5, 4.2), 1.5, 1.3, boxstyle="round,pad=0.05",
                              edgecolor='black', facecolor='#f0f0f0', linewidth=2)
    ax.add_patch(oled_box)
    ax.text(10.25, 5.3, 'OLED', ha='center', fontsize=10, weight='bold')
    ax.text(10.25, 5.05, 'SSD1306', ha='center', fontsize=8)
    ax.text(10.25, 4.85, '128x64', ha='center', fontsize=8)
    ax.text(10.25, 4.6, 'I2C: 0x3C', ha='center', fontsize=7, style='italic', color='#666')

    ax.plot(9.7, 4.3, 'o', color='#ff0000', markersize=6)
    ax.text(9.5, 4.3, 'VCC', ha='right', va='center', fontsize=7)
    ax.plot(10, 4.3, 'o', color='black', markersize=6)
    ax.text(10, 4.15, 'GND', ha='center', fontsize=7)
    ax.plot(10.5, 4.3, 'o', color='#00cc00', markersize=6)
    ax.text(10.5, 4.15, 'SDA', ha='center', fontsize=7)
    ax.plot(10.8, 4.3, 'o', color='#0066ff', markersize=6)
    ax.text(10.8, 4.15, 'SCL', ha='center', fontsize=7)

    # BME280 Sensor
    bme_box = FancyBboxPatch((11.5, 4.2), 1.5, 1.3, boxstyle="round,pad=0.05",
                             edgecolor='black', facecolor='#f0f0f0', linewidth=2)
    ax.add_patch(bme_box)
    ax.text(12.25, 5.3, 'BME280', ha='center', fontsize=10, weight='bold')
    ax.text(12.25, 5.05, 'Temp/Hum/', ha='center', fontsize=8)
    ax.text(12.25, 4.85, 'Pressure', ha='center', fontsize=8)
    ax.text(12.25, 4.6, 'I2C: 0x76', ha='center', fontsize=7, style='italic', color='#666')

    ax.plot(11.7, 4.3, 'o', color='#ff0000', markersize=6)
    ax.text(11.5, 4.3, 'VCC', ha='right', va='center', fontsize=7)
    ax.plot(12, 4.3, 'o', color='black', markersize=6)
    ax.text(12, 4.15, 'GND', ha='center', fontsize=7)
    ax.plot(12.5, 4.3, 'o', color='#00cc00', markersize=6)
    ax.text(12.5, 4.15, 'SDA', ha='center', fontsize=7)
    ax.plot(12.8, 4.3, 'o', color='#0066ff', markersize=6)
    ax.text(12.8, 4.15, 'SCL', ha='center', fontsize=7)

    # Wiring at thermostat location
    # 3.3V bus
    ax.plot([9.5, 9.7], [6.2, 4.3], color='#ff0000', linewidth=2)
    ax.plot([9.5, 11.7], [6.2, 4.3], color='#ff0000', linewidth=2)

    # GND bus
    ax.plot([9.5, 10], [5.9, 4.3], color='black', linewidth=2)
    ax.plot([9.5, 12], [5.9, 4.3], color='black', linewidth=2)

    # SDA bus
    ax.plot([9.5, 10.5], [5.6, 4.3], color='#00cc00', linewidth=2)
    ax.plot([9.5, 12.5], [5.6, 4.3], color='#00cc00', linewidth=2)

    # SCL bus
    ax.plot([9.5, 10.8], [5.3, 4.3], color='#0066ff', linewidth=2)
    ax.plot([9.5, 12.8], [5.3, 4.3], color='#0066ff', linewidth=2)

    # I2C specs box
    spec_box = FancyBboxPatch((9.5, 3.2), 3.5, 0.8, boxstyle="round,pad=0.05",
                              edgecolor='#666', facecolor='white', linewidth=1.5)
    ax.add_patch(spec_box)
    ax.text(11.25, 3.8, 'I2C BUS SPECS', ha='center', fontsize=9, weight='bold')
    ax.text(9.7, 3.6, '• Frequency: 400 kHz (can reduce to 100 kHz)', fontsize=7)
    ax.text(9.7, 3.45, '• Pull-ups: Internal (ESP32-S3)', fontsize=7)
    ax.text(9.7, 3.3, '• GPIO 8 (SDA), GPIO 9 (SCL)', fontsize=7)

    # Technical notes
    notes_box = FancyBboxPatch((0.5, 0.3), 6, 2.8, boxstyle="round,pad=0.1",
                               edgecolor='#0066cc', facecolor='#f0f8ff', linewidth=2.5)
    ax.add_patch(notes_box)
    ax.text(3.5, 2.9, 'TECHNICAL NOTES', ha='center', fontsize=11, weight='bold')

    notes = [
        "GROUNDING:",
        "✓ Safe to tie OLED/BME280 GND to 12VDC ground",
        "✓ All grounds are common reference (0V)",
        "✓ Waveshare module powered by 7-36V DC (or 5V USB-C)",
        "✓ I2C requires shared ground for proper signaling",
        "✓ No voltage conflict (power rail ≠ ground rail)"
    ]

    y_pos = 2.5
    for note in notes:
        if note.startswith("GROUND"):
            ax.text(0.7, y_pos, note, fontsize=9, weight='bold')
        else:
            ax.text(0.7, y_pos, note, fontsize=8)
        y_pos -= 0.35

    # Warning box
    warn_box = FancyBboxPatch((0.5, 0.5), 6, 0.5, boxstyle="round,pad=0.05",
                              edgecolor='#ff6600', facecolor='#fff9e6', linewidth=2.5)
    ax.add_patch(warn_box)
    ax.text(3.5, 0.75, '⚠ Do NOT connect OLED/BME280 VCC to 12V - Only 3.3V!',
            ha='center', fontsize=9, weight='bold', color='#ff6600')

    plt.tight_layout()
    plt.savefig('docs/oled_bme280_wiring_pro.pdf', dpi=300, bbox_inches='tight')
    print("✓ Created oled_bme280_wiring_pro.pdf")
    plt.close()


def create_esp32_main_wiring():
    """ESP32-S3 Main Controller Wiring - Unchanged"""
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title
    ax.text(6, 8.5, 'ESP32-S3 MAIN CONTROLLER WIRING',
            ha='center', fontsize=16, weight='bold')
    ax.text(6, 8.2, 'IP: 192.168.71.152 | Serial: 5B41038621 | /dev/esp32_main',
            ha='center', fontsize=10, color='#666')

    # Power Supply Box
    pwr_box = FancyBboxPatch((7.5, 6.5), 4, 1.5, boxstyle="round,pad=0.1",
                             edgecolor='#FF9800', facecolor='#fff3e0', linewidth=2)
    ax.add_patch(pwr_box)
    ax.text(9.5, 7.8, 'Power Supply', ha='center', fontsize=11, weight='bold')
    ax.text(9.5, 7.5, '12V DC → Buck Conv → 5V', ha='center', fontsize=9)
    ax.text(9.5, 7.2, '5V → ESP32 VIN', ha='center', fontsize=9)
    ax.text(9.5, 6.9, 'Onboard: 5V → 3.3V', ha='center', fontsize=8, style='italic', color='#888')

    # ESP32 Board
    esp_box = FancyBboxPatch((4.5, 3.5), 3, 4, boxstyle="round,pad=0.1",
                             edgecolor='#333', facecolor='#1a1a2e', linewidth=2.5)
    ax.add_patch(esp_box)
    ax.text(6, 7.2, 'ESP32-S3', ha='center', fontsize=12, weight='bold', color='white')
    ax.text(6, 6.9, 'Main Controller', ha='center', fontsize=9, color='#aaa')

    # USB Port
    usb = Rectangle((5.5, 7.45), 1, 0.2, facecolor='#555', edgecolor='#777', linewidth=1)
    ax.add_patch(usb)
    ax.text(6, 7.55, 'USB-C', ha='center', va='center', fontsize=7, color='white')

    # ESP32 Left pins
    ax.plot(4.5, 6.7, 'o', color='#4CAF50', markersize=10)
    ax.text(4.3, 6.7, '3.3V', ha='right', va='center', fontsize=9, weight='bold')

    ax.plot(4.5, 6.2, 'o', color='black', markersize=10)
    ax.text(4.3, 6.2, 'GND', ha='right', va='center', fontsize=9, weight='bold')

    ax.plot(4.5, 5.5, 'o', color='#2196F3', markersize=10)
    ax.text(4.3, 5.5, 'GPIO 8', ha='right', va='center', fontsize=9, weight='bold', color='#2196F3')

    ax.plot(4.5, 4.9, 'o', color='#2196F3', markersize=10)
    ax.text(4.3, 4.9, 'GPIO 9', ha='right', va='center', fontsize=9, weight='bold', color='#2196F3')

    # ESP32 Right pin
    ax.plot(7.5, 6.7, 'o', color='#f44336', markersize=10)
    ax.text(7.7, 6.7, '5V/VIN', va='center', fontsize=9, weight='bold', color='#f44336')

    # BME280 Sensor
    bme_box = FancyBboxPatch((0.5, 5), 2.5, 1.5, boxstyle="round,pad=0.1",
                             edgecolor='#666', facecolor='#4a4a6a', linewidth=2)
    ax.add_patch(bme_box)
    ax.text(1.75, 6.2, 'BME280', ha='center', fontsize=10, weight='bold', color='white')
    ax.text(1.75, 5.9, 'Temp/Humidity', ha='center', fontsize=8, color='#aaa')
    ax.text(1.75, 5.6, 'Pressure', ha='center', fontsize=8, color='#aaa')
    ax.text(1.75, 5.3, 'Addr: 0x76', ha='center', fontsize=7, color='#ccc', style='italic')

    # BME280 pins
    ax.plot(3, 6.1, 'o', color='#4CAF50', markersize=8)
    ax.text(3.15, 6.1, 'VCC', va='center', fontsize=8)
    ax.plot(3, 5.85, 'o', color='black', markersize=8)
    ax.text(3.15, 5.85, 'GND', va='center', fontsize=8)
    ax.plot(3, 5.6, 'o', color='#2196F3', markersize=8)
    ax.text(3.15, 5.6, 'SDA', va='center', fontsize=8, color='#2196F3')
    ax.plot(3, 5.35, 'o', color='#2196F3', markersize=8)
    ax.text(3.15, 5.35, 'SCL', va='center', fontsize=8, color='#2196F3')

    # OLED Display
    oled_box = FancyBboxPatch((0.5, 3), 2.5, 1.6, boxstyle="round,pad=0.1",
                              edgecolor='#666', facecolor='#1a1a4a', linewidth=2)
    ax.add_patch(oled_box)
    # Screen
    screen = Rectangle((0.7, 3.5), 2.1, 0.8, facecolor='#000', edgecolor='#444', linewidth=1)
    ax.add_patch(screen)
    ax.text(1.75, 3.9, '128x64', ha='center', va='center', fontsize=9, color='#00ff00')
    ax.text(1.75, 3.3, 'SSD1306 OLED', ha='center', fontsize=9, weight='bold', color='white')
    ax.text(1.75, 3.1, 'Addr: 0x3C', ha='center', fontsize=7, color='#ccc', style='italic')

    # OLED pins
    ax.plot(3, 4.3, 'o', color='#4CAF50', markersize=8)
    ax.text(3.15, 4.3, 'VCC', va='center', fontsize=8)
    ax.plot(3, 4.05, 'o', color='black', markersize=8)
    ax.text(3.15, 4.05, 'GND', va='center', fontsize=8)
    ax.plot(3, 3.8, 'o', color='#2196F3', markersize=8)
    ax.text(3.15, 3.8, 'SDA', va='center', fontsize=8, color='#2196F3')
    ax.plot(3, 3.55, 'o', color='#2196F3', markersize=8)
    ax.text(3.15, 3.55, 'SCL', va='center', fontsize=8, color='#2196F3')

    # Wiring - 3.3V bus
    ax.plot([4.5, 3.8], [6.7, 6.7], color='#4CAF50', linewidth=2.5)
    ax.plot([3.8, 3.8, 3], [6.7, 6.1, 6.1], color='#4CAF50', linewidth=2.5)
    ax.plot([3.8, 3.8, 3], [6.7, 4.3, 4.3], color='#4CAF50', linewidth=2.5)

    # GND bus
    ax.plot([4.5, 3.5], [6.2, 6.2], color='black', linewidth=2.5)
    ax.plot([3.5, 3.5, 3], [6.2, 5.85, 5.85], color='black', linewidth=2.5)
    ax.plot([3.5, 3.5, 3], [6.2, 4.05, 4.05], color='black', linewidth=2.5)

    # SDA bus (GPIO 8)
    ax.plot([4.5, 3.7], [5.5, 5.5], color='#2196F3', linewidth=2.5)
    ax.plot([3.7, 3.7, 3], [5.5, 5.6, 5.6], color='#2196F3', linewidth=2.5)
    ax.plot([3.7, 3.7, 3], [5.5, 3.8, 3.8], color='#2196F3', linewidth=2.5)

    # SCL bus (GPIO 9)
    ax.plot([4.5, 3.6], [4.9, 4.9], color='#2196F3', linewidth=2.5)
    ax.plot([3.6, 3.6, 3], [4.9, 5.35, 5.35], color='#2196F3', linewidth=2.5)
    ax.plot([3.6, 3.6, 3], [4.9, 3.55, 3.55], color='#2196F3', linewidth=2.5)

    # 5V from power supply
    ax.plot([9.5, 9.5, 7.5], [6.5, 6.7, 6.7], color='#f44336', linewidth=2.5)

    # Legend Box
    legend_box = FancyBboxPatch((7.5, 3.5), 4, 2.5, boxstyle="round,pad=0.1",
                                edgecolor='#ddd', facecolor='#f5f5f5', linewidth=1.5)
    ax.add_patch(legend_box)
    ax.text(9.5, 5.8, 'Pin Assignments', ha='center', fontsize=11, weight='bold')

    # Legend items
    ax.plot([7.8, 8.3], [5.5, 5.5], color='#2196F3', linewidth=2.5)
    ax.text(8.5, 5.5, 'I2C SDA (GPIO 8)', va='center', fontsize=9)

    ax.plot([7.8, 8.3], [5.2, 5.2], color='#2196F3', linewidth=2.5)
    ax.text(8.5, 5.2, 'I2C SCL (GPIO 9)', va='center', fontsize=9)

    ax.plot([7.8, 8.3], [4.9, 4.9], color='#4CAF50', linewidth=2.5)
    ax.text(8.5, 4.9, '3.3V Power', va='center', fontsize=9)

    ax.plot([7.8, 8.3], [4.6, 4.6], color='#f44336', linewidth=2.5)
    ax.text(8.5, 4.6, '5V (Buck Conv)', va='center', fontsize=9)

    ax.plot([7.8, 8.3], [4.3, 4.3], color='black', linewidth=2.5)
    ax.text(8.5, 4.3, 'Ground', va='center', fontsize=9)

    # I2C Addresses
    i2c_box = FancyBboxPatch((7.5, 0.8), 4, 1, boxstyle="round,pad=0.1",
                             edgecolor='#2196F3', facecolor='#e3f2fd', linewidth=1.5)
    ax.add_patch(i2c_box)
    ax.text(9.5, 1.6, 'I2C Addresses', ha='center', fontsize=10, weight='bold')
    ax.text(7.7, 1.3, 'BME280: 0x76', fontsize=9)
    ax.text(7.7, 1.0, 'SSD1306: 0x3C', fontsize=9)

    # Notes
    ax.text(6, 0.5, 'Both I2C devices share the same SDA/SCL bus', ha='center', fontsize=9, color='#666')
    ax.text(6, 0.2, 'Power: 12V DC → Buck Converter (5V) → ESP32 VIN', ha='center', fontsize=9, color='#666')

    plt.tight_layout()
    plt.savefig('docs/esp32_main_wiring_pro.pdf', dpi=300, bbox_inches='tight')
    print("✓ Created esp32_main_wiring_pro.pdf")
    plt.close()


if __name__ == '__main__':
    print("\nCreating updated professional wiring diagrams...")
    print("=" * 60)
    print("Component updates:")
    print("  • Waveshare ESP32-S3-Relay-6CH (replaces ESP32 + HL-52S)")
    print("  • IP65 waterproof enclosure (6.3\"×4.33\"×3.54\")")
    print("  • Updated GPIO assignments")
    print("  • Wire labels positioned BELOW lines")
    print("=" * 60)

    create_ssr_diagram()
    create_i2c_diagram()
    create_esp32_main_wiring()

    print("=" * 60)
    print("Diagrams created successfully!")
    print("\nNext: Create comprehensive relay splice diagram...")


def create_relay_splice_comprehensive():
    """Comprehensive Waveshare Module to Dometic Brisk II Wiring"""
    fig, ax = plt.subplots(figsize=(18, 14))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 14)
    ax.axis('off')

    # Title
    ax.text(9, 13.5, 'WAVESHARE ESP32-S3 — DIRECT 120VAC WIRING TO DOMETIC BRISK II',
            ha='center', fontsize=20, weight='bold')
    ax.text(9, 13.1, 'SSR-25DA for Compressor | Relay Channels for Fans + Furnace | Dual Freeze Protection',
            ha='center', fontsize=12, color='#666')

    # Waveshare Module Box (Left)
    ws_box = FancyBboxPatch((0.5, 8), 4.5, 4.5, boxstyle="round,pad=0.1",
                            edgecolor='#0066cc', facecolor='#e6f3ff', linewidth=3)
    ax.add_patch(ws_box)
    ax.text(2.75, 12.2, 'WAVESHARE ESP32-S3-RELAY-6CH', ha='center', fontsize=13, weight='bold')
    ax.text(2.75, 11.9, 'Industrial 6-Channel Relay Module', ha='center', fontsize=10)
    ax.text(2.75, 11.6, 'IP65 Waterproof Enclosure (6.3"×4.33"×3.54")', ha='center', fontsize=9, color='#666')

    # Power specs
    ax.text(2.75, 11.2, 'Power: 7-36V DC (or 5V USB-C)', ha='center', fontsize=8, style='italic')
    ax.text(2.75, 10.95, 'Relay Rating: 10A @ 250VAC / 30VDC', ha='center', fontsize=8, style='italic')

    # GPIO assignments
    relay_channels = [
        (5, 10.5, 'CH1 (GPIO 1): Furnace', '#ff6600'),
        (5, 10.1, 'CH2 (GPIO 2): Compressor→SSR', '#cc0000'),
        (5, 9.7, 'CH3 (GPIO 41): Fan Low', '#ff6600'),
        (5, 9.3, 'CH4 (GPIO 42): Fan High', '#ff6600'),
        (5, 8.9, 'CH5 (GPIO 45): Available', '#999'),
        (5, 8.5, 'CH6 (GPIO 46): Available', '#999'),
    ]

    for x, y, label, color in relay_channels:
        ax.plot(x, y, 'o', color=color, markersize=9)
        ax.text(x+0.15, y, label, va='center', fontsize=9, color=color)

    # I2C and 1-Wire
    ax.plot(5, 10.9, 'o', color='#2196F3', markersize=8)
    ax.text(5.15, 10.9, 'I2C: GPIO 8 (SDA), GPIO 9 (SCL)', va='center', fontsize=8, color='#2196F3')

    ax.plot(5, 8.2, 'o', color='#00cccc', markersize=8)
    ax.text(5.15, 8.2, 'DS18B20: GPIO 10 (1-Wire)', va='center', fontsize=8, color='#00cccc')

    # SSR-25DA (Middle-Top)
    ssr_box = FancyBboxPatch((6, 9.5), 3, 2.5, boxstyle="round,pad=0.1",
                             edgecolor='#cc0000', facecolor='#ffebee', linewidth=3)
    ax.add_patch(ssr_box)
    ax.text(7.5, 11.8, 'SSR-25DA', ha='center', fontsize=12, weight='bold', color='#cc0000')
    ax.text(7.5, 11.5, 'Solid State Relay', ha='center', fontsize=10)
    ax.text(7.5, 11.25, '3-32VDC → 25A/380VAC', ha='center', fontsize=9, style='italic')

    # SSR pins
    ax.plot(6, 10.7, 'o', color='#cc0000', markersize=9)
    ax.text(5.8, 10.7, 'DC+', ha='right', va='center', fontsize=9)
    ax.plot(6, 10.2, 'o', color='black', markersize=9)
    ax.text(5.8, 10.2, 'DC-', ha='right', va='center', fontsize=9)
    
    ax.plot(9, 10.7, 'o', color='#ff0000', markersize=9)
    ax.text(9.2, 10.7, 'AC1 (in)', va='center', fontsize=9)
    ax.plot(9, 10.2, 'o', color='#ff0000', markersize=9)
    ax.text(9.2, 10.2, 'AC2 (out)', va='center', fontsize=9)

    # Wire: CH2 to SSR DC+
    ax.plot([5, 6], [10.1, 10.7], color='#cc0000', linewidth=2.5)
    ax.text(5.5, 10.2, '12V Trigger', fontsize=8, color='#cc0000')  # BELOW line

    # Ground to SSR DC-
    ax.plot([2.75, 2.75, 6], [8, 7, 7], color='black', linewidth=2.5)
    ax.plot([6, 6], [7, 10.2], color='black', linewidth=2.5)
    ax.text(4, 6.85, 'GND', ha='center', fontsize=8)  # BELOW line

    # 120VAC Source (Top Right)
    vac_box = FancyBboxPatch((14.5, 10.5), 3, 2, boxstyle="round,pad=0.1",
                             edgecolor='#ff0000', facecolor='#ffebee', linewidth=3)
    ax.add_patch(vac_box)
    ax.text(16, 12.3, '120VAC SOURCE', ha='center', fontsize=13, weight='bold', color='#ff0000')
    
    ax.plot(14.7, 11.8, 'o', color='#ff0000', markersize=10)
    ax.text(14.5, 11.8, 'HOT', ha='right', va='center', fontsize=10)
    ax.plot(14.7, 11.2, 'o', color='#0066ff', markersize=10)
    ax.text(14.5, 11.2, 'NEUTRAL', ha='right', va='center', fontsize=10)

    # Wire: 120VAC HOT to SSR AC1
    ax.plot([14.7, 13, 13, 9], [11.8, 11.8, 10.7, 10.7], color='#ff0000', linewidth=3.5)
    ax.text(11, 11.2, '⚠ 120VAC HOT', ha='center', fontsize=9, color='#ff0000', weight='bold')

    # Load Chain (Middle)
    load_box = FancyBboxPatch((10, 8.5), 3, 2, boxstyle="round,pad=0.1",
                              edgecolor='black', facecolor='#f0f0f0', linewidth=2.5)
    ax.add_patch(load_box)
    ax.text(11.5, 10.3, 'LOAD CHAIN', ha='center', fontsize=11, weight='bold')
    
    ax.plot(11.5, 9.7, 'o', color='#ff0000', markersize=9)
    ax.text(11.5, 9.9, 'Supco SFPC', ha='center', fontsize=9)
    ax.text(11.5, 9.5, '(freeze stat)', ha='center', fontsize=7, style='italic', color='#666')
    
    ax.plot(11.5, 9, 'o', color='#ff0000', markersize=9)
    ax.text(11.5, 8.8, 'Bimetal Cutout', ha='center', fontsize=9)

    # Wire: SSR AC2 to Load Chain
    ax.plot([9, 11.5], [10.2, 9.7], color='#ff0000', linewidth=3.5)
    ax.text(10.2, 9.7, '⚠ 120VAC SWITCHED', fontsize=8, color='#ff0000', weight='bold')  # BELOW line

    # Wire through load chain
    ax.plot([11.5, 11.5], [9.7, 9], color='#ff0000', linewidth=3.5)

    # 6-Pin Dometic Cable
    cable_box = FancyBboxPatch((14.5, 5), 3, 4.5, boxstyle="round,pad=0.1",
                               edgecolor='#4CAF50', facecolor='#e8f5e9', linewidth=2.5)
    ax.add_patch(cable_box)
    ax.text(16, 9.3, '6-PIN DOMETIC CABLE', ha='center', fontsize=12, weight='bold', color='#4CAF50')
    ax.text(16, 9, 'to Brisk II Rooftop AC', ha='center', fontsize=10)
    ax.text(16, 8.7, '(14 AWG minimum)', ha='center', fontsize=8, style='italic')

    # Cable pins
    cable_pins = [
        (14.7, 8.3, 'Pin 1: Blue (Compressor)', '#0000ff'),
        (14.7, 7.9, 'Pin 2: Black (Fan Hi)', '#333'),
        (14.7, 7.5, 'Pin 3: Yellow (unused)', '#cccc00'),
        (14.7, 7.1, 'Pin 4: Red (Fan Lo)', '#ff0000'),
        (14.7, 6.7, 'Pin 5: White (Neutral)', '#ccc'),
        (14.7, 6.3, 'Pin 6: Green (Ground)', '#00cc00'),
    ]
    
    for x, y, label, color in cable_pins:
        ax.plot(x, y, 'o', color=color, markersize=10)
        ax.text(x+0.15, y, label, va='center', fontsize=9)

    # Compressor (Bottom Right)
    comp_box = FancyBboxPatch((14.5, 3), 3, 1.5, boxstyle="round,pad=0.1",
                              edgecolor='black', facecolor='#f0f0f0', linewidth=2.5)
    ax.add_patch(comp_box)
    ax.text(16, 4.3, 'COMPRESSOR', ha='center', fontsize=12, weight='bold')
    ax.plot(16, 3.5, 'o', color='#0000ff', markersize=9)
    ax.text(16, 3.3, 'Pin 1 Blue', ha='center', fontsize=9)

    # Wire: Load chain to compressor
    ax.plot([11.5, 11.5, 14.7], [9, 8.3, 8.3], color='#0000ff', linewidth=3.5)
    ax.plot([14.7, 16], [8.3, 3.5], color='#0000ff', linewidth=3.5)

    # Wire: Compressor to NEUTRAL
    ax.plot([16, 16, 14.7], [3.5, 2.5, 2.5], color='#0066ff', linewidth=3.5)
    ax.plot([14.7, 14.7], [2.5, 6.7], color='#0066ff', linewidth=3.5)
    ax.plot([14.7, 14.7], [6.7, 11.2], color='#0066ff', linewidth=3.5)

    # Fan relays to cable (simplified)
    # Fan Low (CH3 → Pin 4 Red)
    ax.plot([5, 14.7], [9.7, 7.1], color='#ff0000', linewidth=2.5)
    ax.text(9, 8.2, 'Fan Low', fontsize=8, color='#ff0000')  # BELOW line

    # Fan High (CH4 → Pin 2 Black)
    ax.plot([5, 14.7], [9.3, 7.9], color='#333', linewidth=2.5)
    ax.text(9, 8.5, 'Fan High', fontsize=8)  # BELOW line

    # Furnace (CH1 - dry contact)
    furn_box = FancyBboxPatch((0.5, 5.5), 4.5, 2, boxstyle="round,pad=0.1",
                              edgecolor='#ff6600', facecolor='#fff3e0', linewidth=2)
    ax.add_patch(furn_box)
    ax.text(2.75, 7.3, 'FURNACE', ha='center', fontsize=11, weight='bold')
    ax.text(2.75, 7, '(Dry Contact Closure)', ha='center', fontsize=9)
    ax.text(2.75, 6.7, 'Separate unit with own blower', ha='center', fontsize=8, style='italic', color='#666')
    
    ax.plot([5, 5, 3.5], [10.5, 6.5, 6.5], color='#ff6600', linewidth=2.5)
    ax.text(4, 6.3, 'CH1 NO', fontsize=8, color='#ff6600')  # BELOW line
    ax.plot(3.5, 6.5, 'o', color='#ff6600', markersize=8)
    ax.plot(2, 6.5, 'o', color='#ff6600', markersize=8)
    ax.text(2.75, 6.3, 'Furnace terminals', ha='center', fontsize=7)

    # DS18B20 Freeze Sensor
    ds_box = FancyBboxPatch((0.5, 3), 4.5, 2, boxstyle="round,pad=0.1",
                            edgecolor='#00cccc', facecolor='#e0f7fa', linewidth=2)
    ax.add_patch(ds_box)
    ax.text(2.75, 4.8, 'DS18B20 FREEZE SENSOR', ha='center', fontsize=11, weight='bold', color='#00cccc')
    ax.text(2.75, 4.5, '1-Wire, GPIO 10, 4.7K pullup to 3.3V', ha='center', fontsize=9)
    ax.text(2.75, 4.25, 'Waterproof probe on evaporator coil', ha='center', fontsize=8, style='italic', color='#666')
    ax.text(2.75, 3.95, 'Cut compressor @ 32°F, restart @ 45°F', ha='center', fontsize=8, color='#cc0000')
    ax.text(2.75, 3.7, 'Software protection (primary)', ha='center', fontsize=7, style='italic')
    
    ax.plot([5, 5, 2.75], [8.2, 4.4, 4.4], color='#00cccc', linewidth=2)
    ax.text(3.5, 4.25, 'GPIO 10', fontsize=8, color='#00cccc')  # BELOW line

    # Safety Notes Box (Bottom Left)
    safety_box = FancyBboxPatch((0.5, 0.3), 9, 2.3, boxstyle="round,pad=0.1",
                                edgecolor='#ff0000', facecolor='#fff5f5', linewidth=3, linestyle='--')
    ax.add_patch(safety_box)
    ax.text(5, 2.4, '⚠ SAFETY CRITICAL - 120VAC WIRING ⚠', ha='center', fontsize=12, weight='bold', color='#ff0000')

    safety_notes = [
        "CRITICAL POINTS:",
        "• Waveshare CH2 relay NO terminal switches 12VDC to SSR DC+ (milliamp trigger current)",
        "• SSR-25DA switches high-current 120VAC to compressor (needs heatsink ~15W @ 12A load)",
        "• CH1/CH3/CH4 relays switch 120VAC directly to fans/furnace (2-3A loads, 10A relay rating)",
        "• Supco SFPC hardware freeze stat: NC contact, opens 35°F, closes 50°F (in series after SSR)",
        "• DS18B20 software freeze protection: Cut @ 32°F, restart @ 45°F (dual layer protection)",
        "• All 120VAC wiring: 14 AWG minimum, install in proper junction box per NEC",
        "• Old Dometic control box REMOVED from circuit — direct ESP32 control",
    ]

    y_pos = 2.1
    for note in safety_notes:
        if note.startswith("CRITICAL"):
            ax.text(0.7, y_pos, note, fontsize=9, weight='bold')
            y_pos -= 0.23
        else:
            ax.text(0.7, y_pos, note, fontsize=8)
            y_pos -= 0.22

    # Component Specs Box (Bottom Right)
    spec_box = FancyBboxPatch((10, 0.3), 7.5, 2.3, boxstyle="round,pad=0.1",
                              edgecolor='#0066cc', facecolor='#f0f8ff', linewidth=2)
    ax.add_patch(spec_box)
    ax.text(13.75, 2.4, 'COMPONENT SPECIFICATIONS', ha='center', fontsize=11, weight='bold', color='#0066cc')

    specs = [
        "WAVESHARE ESP32-S3-RELAY-6CH:",
        "  • Power: 7-36V DC (or 5V USB-C) | Enclosure: IP65 waterproof (6.3\"×4.33\"×3.54\")",
        "  • Relay Rating: 10A @ 250VAC/30VDC per channel (6 channels total)",
        "  • Optocoupler + digital + power isolation for safety | Onboard RS485 interface",
        "",
        "GPIO ASSIGNMENTS:",
        "  • Relays: CH1=GPIO1, CH2=GPIO2, CH3=GPIO41, CH4=GPIO42, CH5=GPIO45, CH6=GPIO46",
        "  • I2C: SDA=GPIO8, SCL=GPIO9 (to remote OLED/BME280 via 3m cable)",
        "  • 1-Wire: GPIO10 (DS18B20 freeze sensor with 4.7K pullup)",
        "  • RS485: TX=GPIO17, RX=GPIO18 | Buzzer: GPIO21 | RGB LED: GPIO38",
    ]

    y_pos = 2.1
    for spec in specs:
        if spec == "":
            y_pos -= 0.15
        elif spec.endswith(":"):
            ax.text(10.2, y_pos, spec, fontsize=9, weight='bold')
            y_pos -= 0.2
        else:
            ax.text(10.2, y_pos, spec, fontsize=7.5)
            y_pos -= 0.18

    plt.tight_layout()
    plt.savefig('docs/esp32_remote_relay_splice_pro.pdf', dpi=300, bbox_inches='tight')
    print("✓ Created esp32_remote_relay_splice_pro.pdf")
    plt.close()


if __name__ == '__main__':
    print("\nCreating updated professional wiring diagrams...")
    print("=" * 60)
    print("Component updates:")
    print("  • Waveshare ESP32-S3-Relay-6CH (replaces ESP32 + HL-52S)")
    print("  • IP65 waterproof enclosure (6.3\"×4.33\"×3.54\")")
    print("  • Updated GPIO assignments")
    print("  • Wire labels positioned BELOW lines")
    print("=" * 60)

    create_ssr_diagram()
    create_i2c_diagram()
    create_esp32_main_wiring()
    create_relay_splice_comprehensive()

    print("=" * 60)
    print("All diagrams created successfully!")
