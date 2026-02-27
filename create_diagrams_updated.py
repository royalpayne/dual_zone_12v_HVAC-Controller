#!/usr/bin/env python3
"""
Create all wiring diagrams for RV thermostat project.
- ESP32-S3-N16R8 + 4-Channel Relay Module
- Page size: 11.5 x 8 inches (landscape)
- Orthogonal wire routing only (no diagonals)
- Wire labels BELOW the wire lines with clear spacing
- All wires terminate at their pin/terminal dots
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle


# Page size for all diagrams
PAGE_W = 11.5
PAGE_H = 8


def pin(ax, x, y, color='black', size=8):
    """Draw a connection pin dot"""
    ax.plot(x, y, 'o', color=color, markersize=size, zorder=5)


def wire(ax, *points, color='black', lw=2.5):
    """Draw wire through a series of (x,y) waypoints — all segments orthogonal."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle='round', zorder=3)


def label(ax, x, y, text, color='black', fontsize=8, ha='center', va='top', **kw):
    """Place a label. Default va='top' so text sits below the y coordinate."""
    ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color=color, zorder=6, **kw)


def box(ax, x, y, w, h, edge='#333', face='#f0f0f0', lw=2.5):
    """Draw a rounded box and return it."""
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                       edgecolor=edge, facecolor=face, linewidth=lw, zorder=2)
    ax.add_patch(b)
    return b


def new_page(coord_w, coord_h):
    """Create a new figure at 11.5x8 with given coordinate range."""
    fig, ax = plt.subplots(figsize=(PAGE_W, PAGE_H))
    ax.set_xlim(0, coord_w)
    ax.set_ylim(0, coord_h)
    ax.axis('off')
    return fig, ax


# =============================================================================
# DIAGRAM 1: SSR-25DA COMPRESSOR WIRING
# =============================================================================
def create_ssr_diagram():
    fig, ax = new_page(23, 16)

    # Title
    label(ax, 11.5, 15.5, 'SSR-25DA COMPRESSOR WIRING DIAGRAM',
          fontsize=16, weight='bold', va='center')
    label(ax, 11.5, 14.9, 'Relay CH2 (GPIO 5)  →  SSR-25DA  →  120VAC  →  Compressor',
          fontsize=10, color='#666', va='center')

    # --- Row layout: components at y~9 band, left to right ---

    # 1. ESP32 + Relay Module  (left)
    box(ax, 0.5, 7, 3.5, 4.5, '#0066cc', '#e6f3ff')
    label(ax, 2.25, 11.2, 'ESP32-S3-N16R8', fontsize=11, weight='bold', va='center')
    label(ax, 2.25, 10.7, '+ 4-Ch Relay Module', fontsize=9, va='center')

    # Pins on right edge
    pin(ax, 4.0, 10.0, '#ff6600')
    label(ax, 4.2, 10.0, 'CH2 (GPIO 5)', fontsize=8, ha='left', va='center')
    pin(ax, 4.0, 9.0, '#cc0000')
    label(ax, 4.2, 9.0, '12V+', fontsize=8, ha='left', va='center')
    pin(ax, 4.0, 8.0, 'black')
    label(ax, 4.2, 8.0, 'GND', fontsize=8, ha='left', va='center')

    # 2. Relay CH2 block
    box(ax, 6.5, 7, 3.5, 4.5, '#ff6600', '#fff3e0')
    label(ax, 8.25, 11.2, 'Relay CH2 Output', fontsize=11, weight='bold', va='center')
    label(ax, 8.25, 10.7, '(External Relay Module)', fontsize=8, va='center', color='#666')

    # Relay pins
    pin(ax, 6.5, 10.0, '#ff6600')  # IN (left side)
    label(ax, 6.3, 10.0, 'IN', fontsize=8, ha='right', va='center')
    pin(ax, 10.0, 10.0, '#cc0000')  # COM (right side)
    label(ax, 10.2, 10.0, 'COM', fontsize=8, ha='left', va='center')
    pin(ax, 10.0, 9.0, '#cc0000')  # NO
    label(ax, 10.2, 9.0, 'NO', fontsize=8, ha='left', va='center')
    pin(ax, 10.0, 8.0, 'gray')  # NC
    label(ax, 10.2, 8.0, 'NC (unused)', fontsize=8, ha='left', va='center', color='gray')

    # 3. SSR-25DA
    box(ax, 12.5, 7, 3.5, 4.5, '#cc0000', '#fff5f5')
    label(ax, 14.25, 11.2, 'SSR-25DA', fontsize=12, weight='bold', va='center', color='#cc0000')
    label(ax, 14.25, 10.7, 'Solid State Relay', fontsize=9, va='center')
    label(ax, 14.25, 10.2, '3-32VDC → 25A/380VAC', fontsize=8, va='center', color='#666')

    pin(ax, 12.5, 9.5, '#cc0000')  # DC+
    label(ax, 12.3, 9.5, 'DC+', fontsize=8, ha='right', va='center')
    pin(ax, 12.5, 8.5, 'black')  # DC-
    label(ax, 12.3, 8.5, 'DC-', fontsize=8, ha='right', va='center')
    pin(ax, 16.0, 9.5, '#ff0000')  # AC1
    label(ax, 16.2, 9.5, 'AC1 (in)', fontsize=8, ha='left', va='center')
    pin(ax, 16.0, 8.5, '#ff0000')  # AC2
    label(ax, 16.2, 8.5, 'AC2 (out)', fontsize=8, ha='left', va='center')

    # 4. 120VAC Source (top right)
    box(ax, 18.0, 10.0, 4.0, 2.5, '#ff0000', '#ffeeee')
    label(ax, 20.0, 12.2, '120VAC SOURCE', fontsize=12, weight='bold', va='center', color='#ff0000')
    pin(ax, 18.2, 11.0, '#ff0000')
    label(ax, 18.0, 11.0, 'HOT', fontsize=9, ha='right', va='center')
    pin(ax, 21.8, 11.0, '#0066ff')
    label(ax, 22.0, 11.0, 'NEUTRAL', fontsize=9, ha='left', va='center')

    # 5. Load Chain (below 120VAC source)
    box(ax, 18.0, 5.5, 4.0, 3.5, 'black', '#f0f0f0', 2)
    label(ax, 20.0, 8.7, 'LOAD CHAIN', fontsize=11, weight='bold', va='center')
    pin(ax, 20.0, 7.8, '#ff0000')
    label(ax, 20.0, 7.5, 'Supco SFPC', fontsize=8, va='center')
    label(ax, 20.0, 7.1, '(freeze stat: opens 35F)', fontsize=7, va='center', color='#666')
    pin(ax, 20.0, 6.5, '#ff0000')
    label(ax, 20.0, 6.2, 'Bimetal Cutout', fontsize=8, va='center')

    # 6. Compressor (bottom right)
    box(ax, 18.0, 3.0, 4.0, 1.8, 'black', '#f0f0f0')
    label(ax, 20.0, 4.5, 'COMPRESSOR', fontsize=11, weight='bold', va='center')
    label(ax, 20.0, 3.8, 'Pin 1 Blue', fontsize=9, va='center', color='#0000ff')

    # ---- WIRES ----

    # CH2 → Relay IN (straight horizontal at y=10)
    wire(ax, (4.0, 10.0), (6.5, 10.0), color='#ff6600', lw=2.5)
    label(ax, 5.25, 9.1, 'Control Signal', fontsize=8, color='#ff6600')

    # 12V+ → Relay COM: horizontal at y=9, then up to y=10 at relay COM
    wire(ax, (4.0, 9.0), (10.0, 9.0), color='#cc0000', lw=2.5)
    wire(ax, (10.0, 9.0), (10.0, 10.0), color='#cc0000', lw=2.5)
    label(ax, 7.0, 8.1, '12VDC Supply', fontsize=8, color='#cc0000')

    # Relay NO → SSR DC+: horizontal at y=9, then up to 9.5 at SSR
    wire(ax, (10.0, 9.0), (11.5, 9.0), color='#cc0000', lw=2.5)
    wire(ax, (11.5, 9.0), (11.5, 9.5), color='#cc0000', lw=2.5)
    wire(ax, (11.5, 9.5), (12.5, 9.5), color='#cc0000', lw=2.5)
    label(ax, 11.0, 8.1, '12V Trigger', fontsize=8, color='#cc0000')

    # GND → SSR DC-: down to y=6, across, up to SSR DC-
    wire(ax, (4.0, 8.0), (4.0, 6.0), color='black', lw=2.5)
    wire(ax, (4.0, 6.0), (12.0, 6.0), color='black', lw=2.5)
    wire(ax, (12.0, 6.0), (12.0, 8.5), color='black', lw=2.5)
    wire(ax, (12.0, 8.5), (12.5, 8.5), color='black', lw=2.5)
    label(ax, 8.0, 5.1, 'GND', fontsize=8)

    # 120VAC HOT → SSR AC1: straight horizontal at y=11, down to AC1
    wire(ax, (18.2, 11.0), (17.0, 11.0), color='#ff0000', lw=3.5)
    wire(ax, (17.0, 11.0), (17.0, 9.5), color='#ff0000', lw=3.5)
    wire(ax, (17.0, 9.5), (16.0, 9.5), color='#ff0000', lw=3.5)
    label(ax, 17.6, 10.5, '120VAC HOT', fontsize=9, color='#ff0000', weight='bold', ha='left')

    # SSR AC2 → Load Chain: horizontal to x=20, down to load chain
    wire(ax, (16.0, 8.5), (17.5, 8.5), color='#ff0000', lw=3.5)
    wire(ax, (17.5, 8.5), (17.5, 7.8), color='#ff0000', lw=3.5)
    wire(ax, (17.5, 7.8), (20.0, 7.8), color='#ff0000', lw=3.5)
    label(ax, 18.5, 7.0, '120VAC Switched', fontsize=8, color='#ff0000', weight='bold')

    # Through load chain
    wire(ax, (20.0, 7.8), (20.0, 6.5), color='#ff0000', lw=3.5)

    # Load chain → Compressor
    wire(ax, (20.0, 6.5), (20.0, 4.8), color='#ff0000', lw=3.5)

    # Neutral return: compressor → right edge → up → 120VAC NEU
    wire(ax, (20.0, 3.0), (20.0, 2.5), color='#0066ff', lw=3.5)
    wire(ax, (20.0, 2.5), (22.5, 2.5), color='#0066ff', lw=3.5)
    wire(ax, (22.5, 2.5), (22.5, 11.0), color='#0066ff', lw=3.5)
    wire(ax, (22.5, 11.0), (21.8, 11.0), color='#0066ff', lw=3.5)
    label(ax, 22.7, 7.0, 'NEUTRAL RETURN', fontsize=8, color='#0066ff',
          rotation=90, ha='left', va='center')

    # ---- Safety Notes ----
    box(ax, 0.5, 0.5, 11.0, 5.0, '#ff0000', '#fff5f5', 2)
    label(ax, 6.0, 5.2, 'SAFETY NOTES', fontsize=12, weight='bold', color='#ff0000', va='center')
    notes = [
        "KEY POINTS:",
        "  CH2 relay NO terminal switches 12VDC milliamp trigger to SSR DC+",
        "  SSR-25DA switches high-current 120VAC to compressor load",
        "  SSR needs heatsink (~15W dissipation @ 12A compressor load)",
        "  Supco SFPC: normally closed, opens at 35F, recloses at 50F",
        "  Bimetal cutout: thermal overload protection, in series",
        "  All 120VAC wiring: 14 AWG minimum, in junction box per NEC",
        "  CH1/CH3/CH4 switch 120VAC directly (2-3A fan loads, 10A relay rating)",
    ]
    y = 4.7
    for n in notes:
        w = 'bold' if n.startswith("KEY") else 'normal'
        label(ax, 0.8, y, n, fontsize=8, weight=w, ha='left', va='center')
        y -= 0.5

    plt.tight_layout()
    plt.savefig('docs/ssr_wiring_pro.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('docs/ssr_wiring_pro.svg', dpi=300, bbox_inches='tight')
    print("Created ssr_wiring_pro.pdf and .svg")
    plt.close()


# =============================================================================
# DIAGRAM 2: I2C / OLED + BME280 WIRING
# =============================================================================
def create_i2c_diagram():
    fig, ax = new_page(23, 16)

    label(ax, 11.5, 15.5, 'OLED & BME280 I2C WIRING DIAGRAM',
          fontsize=16, weight='bold', va='center')
    label(ax, 11.5, 14.9, '3-Meter Cable: ESP32-S3 Module  →  Thermostat Location',
          fontsize=10, color='#666', va='center')

    # --- LEFT: ESP32 Module ---
    box(ax, 0.5, 6.0, 4.0, 6.0, '#0066cc', '#e6f3ff', 3)
    label(ax, 2.5, 11.7, 'ESP32-S3-N16R8', fontsize=12, weight='bold', va='center')
    label(ax, 2.5, 11.2, '+ 4-Ch Relay Module', fontsize=9, va='center', color='#666')
    label(ax, 2.5, 10.7, '44-Pin Dev Board', fontsize=8, va='center', color='#888')

    # Power info
    box(ax, 1.0, 6.3, 3.0, 1.2, '#ff6600', '#fff3e0', 1.5)
    label(ax, 2.5, 7.2, 'Power: 5V USB-C', fontsize=8, weight='bold', va='center')
    label(ax, 2.5, 6.7, 'Onboard 3.3V regulator', fontsize=7, va='center', color='#666')

    # Output pins (right side) — wide spacing for labels
    px = 4.5
    pin(ax, px, 10.0, '#ff0000')
    label(ax, px + 0.2, 10.0, '3.3V', fontsize=9, ha='left', va='center')
    pin(ax, px, 9.2, 'black')
    label(ax, px + 0.2, 9.2, 'GND', fontsize=9, ha='left', va='center')
    pin(ax, px, 8.4, '#00aa00')
    label(ax, px + 0.2, 8.4, 'GPIO 8 (SDA)', fontsize=9, ha='left', va='center')
    pin(ax, px, 7.6, '#0066ff')
    label(ax, px + 0.2, 7.6, 'GPIO 9 (SCL)', fontsize=9, ha='left', va='center')

    # --- MIDDLE: 3-Meter Cable ---
    cx1 = 6.5
    cx2 = 13.5
    cmid = (cx1 + cx2) / 2

    # Cable background
    ax.fill_between([cx1, cx2], [7.2, 7.2], [10.4, 10.4], color='#f5f5f5', zorder=0)
    ax.plot([cx1, cx2], [10.4, 10.4], color='#ccc', lw=1, ls='--', zorder=1)
    ax.plot([cx1, cx2], [7.2, 7.2], color='#ccc', lw=1, ls='--', zorder=1)
    label(ax, cmid, 11.0, '3-METER CABLE RUN', fontsize=13, weight='bold', va='center')
    label(ax, cmid, 10.6, '18 AWG Thermostat Wire (4 conductors)', fontsize=9, va='center')

    # Four horizontal wires with labels BELOW each wire
    wires_data = [
        (10.0, '#ff0000', '3.3V (red wire)'),
        (9.2,  'black',   'GND (black wire)'),
        (8.4,  '#00aa00', 'SDA (green wire)'),
        (7.6,  '#0066ff', 'SCL (blue wire)'),
    ]
    for wy, wc, wl in wires_data:
        wire(ax, (px, wy), (14.0, wy), color=wc, lw=2.5)
        label(ax, cmid, wy - 0.55, wl, fontsize=8, color=wc)

    # --- RIGHT: Thermostat Location ---
    box(ax, 13.5, 3.5, 9.0, 10.5, '#ff6600', '#fff8f0', 3)
    label(ax, 18.0, 13.7, 'THERMOSTAT LOCATION', fontsize=13, weight='bold', va='center')
    label(ax, 18.0, 13.2, '(Former Dometic Stat Position)', fontsize=9, va='center', color='#666')

    # Bus bar — vertical at x=14.5
    bus_x = 14.5
    wire(ax, (bus_x, 7.6), (bus_x, 10.0), color='#888', lw=5)
    label(ax, bus_x, 10.3, 'BUS', fontsize=7, weight='bold', color='#888', va='center')

    # Bus arrival dots
    for wy, wc, _ in wires_data:
        pin(ax, bus_x, wy, wc, 10)

    # ---- OLED (upper device) ----
    box(ax, 17.0, 9.0, 4.5, 3.2, '#444', '#2a2a4a', 2)
    screen = Rectangle((17.3, 10.3), 3.9, 1.2, facecolor='#000', edgecolor='#555', lw=1, zorder=3)
    ax.add_patch(screen)
    label(ax, 19.25, 10.9, '128x64', fontsize=9, color='#00ff00', va='center')
    label(ax, 19.25, 9.8, 'SSD1306 OLED', fontsize=10, weight='bold', color='white', va='center')
    label(ax, 19.25, 9.3, 'I2C: 0x3C', fontsize=8, color='#ccc', va='center')

    # OLED pins on LEFT edge
    oled_px = 17.0
    oled_pins = [(12.0, '#ff0000', 'VCC'), (11.6, 'black', 'GND'),
                 (11.2, '#00aa00', 'SDA'), (10.8, '#0066ff', 'SCL')]
    for py, pc, pl in oled_pins:
        pin(ax, oled_px, py, pc, 6)
        label(ax, oled_px - 0.15, py, pl, fontsize=7, ha='right', va='center')

    # ---- BME280 (lower device) ----
    box(ax, 17.0, 4.5, 4.5, 3.2, '#444', '#4a4a6a', 2)
    label(ax, 19.25, 7.3, 'BME280', fontsize=12, weight='bold', color='white', va='center')
    label(ax, 19.25, 6.7, 'Temp / Humidity / Pressure', fontsize=8, color='#aaa', va='center')
    label(ax, 19.25, 6.2, 'I2C: 0x76', fontsize=8, color='#ccc', va='center')

    # BME pins on LEFT edge
    bme_pins = [(7.5, '#ff0000', 'VCC'), (7.1, 'black', 'GND'),
                (6.7, '#00aa00', 'SDA'), (6.3, '#0066ff', 'SCL')]
    for py, pc, pl in bme_pins:
        pin(ax, oled_px, py, pc, 6)
        label(ax, oled_px - 0.15, py, pl, fontsize=7, ha='right', va='center')

    # ---- Bus to OLED wiring (vertical risers at unique x, then horizontal to pin) ----
    # Each signal gets its own x column to avoid overlaps
    riser = {  # signal: riser_x
        '3v3': 15.2,
        'gnd': 15.6,
        'sda': 16.0,
        'scl': 16.4,
    }

    # 3.3V → OLED VCC
    wire(ax, (bus_x, 10.0), (riser['3v3'], 10.0), color='#ff0000', lw=2)
    wire(ax, (riser['3v3'], 10.0), (riser['3v3'], 12.0), color='#ff0000', lw=2)
    wire(ax, (riser['3v3'], 12.0), (oled_px, 12.0), color='#ff0000', lw=2)

    # GND → OLED GND
    wire(ax, (bus_x, 9.2), (riser['gnd'], 9.2), color='black', lw=2)
    wire(ax, (riser['gnd'], 9.2), (riser['gnd'], 11.6), color='black', lw=2)
    wire(ax, (riser['gnd'], 11.6), (oled_px, 11.6), color='black', lw=2)

    # SDA → OLED SDA
    wire(ax, (bus_x, 8.4), (riser['sda'], 8.4), color='#00aa00', lw=2)
    wire(ax, (riser['sda'], 8.4), (riser['sda'], 11.2), color='#00aa00', lw=2)
    wire(ax, (riser['sda'], 11.2), (oled_px, 11.2), color='#00aa00', lw=2)

    # SCL → OLED SCL
    wire(ax, (bus_x, 7.6), (riser['scl'], 7.6), color='#0066ff', lw=2)
    wire(ax, (riser['scl'], 7.6), (riser['scl'], 10.8), color='#0066ff', lw=2)
    wire(ax, (riser['scl'], 10.8), (oled_px, 10.8), color='#0066ff', lw=2)

    # ---- Bus to BME280 wiring (risers go DOWN from bus) ----
    # 3.3V → BME VCC
    wire(ax, (riser['3v3'], 10.0), (riser['3v3'], 7.5), color='#ff0000', lw=2)
    wire(ax, (riser['3v3'], 7.5), (oled_px, 7.5), color='#ff0000', lw=2)

    # GND → BME GND
    wire(ax, (riser['gnd'], 9.2), (riser['gnd'], 7.1), color='black', lw=2)
    wire(ax, (riser['gnd'], 7.1), (oled_px, 7.1), color='black', lw=2)

    # SDA → BME SDA
    wire(ax, (riser['sda'], 8.4), (riser['sda'], 6.7), color='#00aa00', lw=2)
    wire(ax, (riser['sda'], 6.7), (oled_px, 6.7), color='#00aa00', lw=2)

    # SCL → BME SCL
    wire(ax, (riser['scl'], 7.6), (riser['scl'], 6.3), color='#0066ff', lw=2)
    wire(ax, (riser['scl'], 6.3), (oled_px, 6.3), color='#0066ff', lw=2)

    # ---- Notes ----
    box(ax, 0.5, 0.5, 9.0, 4.5, '#0066cc', '#f0f8ff', 2)
    label(ax, 5.0, 4.7, 'TECHNICAL NOTES', fontsize=11, weight='bold', va='center')
    notes = [
        "GROUNDING:",
        "  Safe to tie OLED/BME280 GND to 12VDC ground",
        "  All grounds are common reference (0V)",
        "  I2C requires shared ground for proper signaling",
        "",
        "I2C BUS:",
        "  400 kHz (can reduce to 100 kHz for long cable)",
        "  Internal pull-ups on ESP32-S3",
        "  GPIO 8 = SDA, GPIO 9 = SCL",
        "",
        "WARNING: OLED/BME280 VCC = 3.3V ONLY (not 12V!)",
    ]
    y = 4.2
    for n in notes:
        if n == "":
            y -= 0.15
            continue
        w = 'bold' if n.endswith(":") or n.startswith("WARNING") else 'normal'
        c = '#ff6600' if n.startswith("WARNING") else 'black'
        label(ax, 0.8, y, n, fontsize=8, weight=w, ha='left', va='center', color=c)
        y -= 0.35

    plt.tight_layout()
    plt.savefig('docs/oled_bme280_wiring_pro.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('docs/oled_bme280_wiring_pro.svg', dpi=300, bbox_inches='tight')
    print("Created oled_bme280_wiring_pro.pdf and .svg")
    plt.close()


# =============================================================================
# DIAGRAM 3: ESP32-S3 MAIN CONTROLLER WIRING
# =============================================================================
def create_esp32_main_wiring():
    fig, ax = new_page(20, 14)

    label(ax, 10, 13.5, 'ESP32-S3 MAIN CONTROLLER WIRING',
          fontsize=16, weight='bold', va='center')
    label(ax, 10, 13.0, 'IP: 192.168.71.152  |  /dev/esp32_main',
          fontsize=10, color='#666', va='center')

    # --- Power Supply (top) ---
    box(ax, 11.0, 10.5, 7.0, 1.8, '#FF9800', '#fff3e0', 2)
    label(ax, 14.5, 12.0, 'Power Supply', fontsize=11, weight='bold', va='center')
    label(ax, 14.5, 11.5, '12V DC → Buck Converter → 5V', fontsize=9, va='center')
    label(ax, 14.5, 11.0, '5V → ESP32 VIN | Onboard 3.3V reg', fontsize=8, va='center', color='#888')

    # --- ESP32 (right side) ---
    box(ax, 11.0, 4.0, 4.5, 5.5, '#333', '#1a1a2e', 2.5)
    usb = Rectangle((12.5, 9.4), 1.5, 0.2, facecolor='#555', edgecolor='#777', lw=1, zorder=3)
    ax.add_patch(usb)
    label(ax, 13.25, 9.5, 'USB-C', fontsize=6, color='white', va='center')
    label(ax, 13.25, 9.0, 'ESP32-S3', fontsize=13, weight='bold', color='white', va='center')
    label(ax, 13.25, 8.5, 'Main Controller', fontsize=9, color='#aaa', va='center')

    # ESP32 pins (LEFT side) — well spaced
    esp_x = 11.0
    esp_pins = [
        (7.5, '#4CAF50', '3.3V'),
        (6.8, 'black',   'GND'),
        (6.1, '#2196F3', 'GPIO 8 (SDA)'),
        (5.4, '#2196F3', 'GPIO 9 (SCL)'),
    ]
    for py, pc, pl in esp_pins:
        pin(ax, esp_x, py, pc, 9)
        label(ax, esp_x + 0.2, py, pl, fontsize=8, ha='left', va='center',
              color=pc if pc != 'black' else '#333', weight='bold')

    # 5V/VIN pin (right side)
    pin(ax, 15.5, 7.5, '#f44336', 9)
    label(ax, 15.7, 7.5, '5V/VIN', fontsize=8, ha='left', va='center',
          weight='bold', color='#f44336')

    # 5V wire from power supply
    wire(ax, (14.5, 10.5), (14.5, 7.8), color='#f44336', lw=2.5)
    wire(ax, (14.5, 7.8), (14.5, 7.5), color='#f44336', lw=2.5)
    wire(ax, (14.5, 7.5), (15.5, 7.5), color='#f44336', lw=2.5)
    label(ax, 15.0, 9.5, '5V', fontsize=8, color='#f44336', ha='left', va='center')

    # --- BME280 (top left) ---
    box(ax, 0.5, 7.5, 4.5, 3.0, '#666', '#4a4a6a', 2)
    label(ax, 2.75, 10.2, 'BME280', fontsize=12, weight='bold', color='white', va='center')
    label(ax, 2.75, 9.6, 'Temp / Humidity / Pressure', fontsize=8, color='#aaa', va='center')
    label(ax, 2.75, 9.1, 'Addr: 0x76', fontsize=7, color='#ccc', va='center')

    # BME pins (right side)
    bme_x = 5.0
    bme_pins = [(8.8, '#4CAF50', 'VCC'), (8.4, 'black', 'GND'),
                (8.0, '#2196F3', 'SDA'), (7.6, '#2196F3', 'SCL')]
    for py, pc, pl in bme_pins:
        pin(ax, bme_x, py, pc, 7)
        label(ax, bme_x + 0.15, py, pl, fontsize=7, ha='left', va='center')

    # --- OLED (bottom left) ---
    box(ax, 0.5, 3.5, 4.5, 3.2, '#666', '#1a1a4a', 2)
    screen = Rectangle((0.7, 4.5), 4.1, 1.4, facecolor='#000', edgecolor='#444', lw=1, zorder=3)
    ax.add_patch(screen)
    label(ax, 2.75, 5.2, '128x64', fontsize=9, color='#00ff00', va='center')
    label(ax, 2.75, 4.1, 'SSD1306 OLED', fontsize=9, weight='bold', color='white', va='center')
    label(ax, 2.75, 3.7, 'Addr: 0x3C', fontsize=7, color='#ccc', va='center')

    # OLED pins (right side)
    oled_pins = [(6.4, '#4CAF50', 'VCC'), (6.0, 'black', 'GND'),
                 (5.6, '#2196F3', 'SDA'), (5.2, '#2196F3', 'SCL')]
    for py, pc, pl in oled_pins:
        pin(ax, bme_x, py, pc, 7)
        label(ax, bme_x + 0.15, py, pl, fontsize=7, ha='left', va='center')

    # --- Bus bars (vertical columns between devices and ESP32) ---
    # 4 vertical columns at distinct x positions
    bx = {'3v3': 7.0, 'gnd': 7.8, 'sda': 8.6, 'scl': 9.4}

    # Draw bus bars as vertical lines spanning from OLED bottom to BME top
    wire(ax, (bx['3v3'], 5.2), (bx['3v3'], 8.8), color='#4CAF50', lw=3)
    wire(ax, (bx['gnd'], 5.2), (bx['gnd'], 8.4), color='black', lw=3)
    wire(ax, (bx['sda'], 5.2), (bx['sda'], 8.0), color='#2196F3', lw=3)
    wire(ax, (bx['scl'], 5.2), (bx['scl'], 7.6), color='#2196F3', lw=3)

    # Labels at top of each bus — placed well above wire endpoints
    label(ax, bx['3v3'], 9.5, '3.3V', fontsize=7, color='#4CAF50', weight='bold', va='bottom')
    label(ax, bx['gnd'], 9.1, 'GND', fontsize=7, weight='bold', va='bottom')
    label(ax, bx['sda'], 8.7, 'SDA', fontsize=7, color='#2196F3', weight='bold', va='bottom')
    label(ax, bx['scl'], 8.3, 'SCL', fontsize=7, color='#2196F3', weight='bold', va='bottom')

    # BME → bus (horizontal)
    wire(ax, (bme_x, 8.8), (bx['3v3'], 8.8), color='#4CAF50', lw=2)
    wire(ax, (bme_x, 8.4), (bx['gnd'], 8.4), color='black', lw=2)
    wire(ax, (bme_x, 8.0), (bx['sda'], 8.0), color='#2196F3', lw=2)
    wire(ax, (bme_x, 7.6), (bx['scl'], 7.6), color='#2196F3', lw=2)

    # OLED → bus (horizontal)
    wire(ax, (bme_x, 6.4), (bx['3v3'], 6.4), color='#4CAF50', lw=2)
    wire(ax, (bme_x, 6.0), (bx['gnd'], 6.0), color='black', lw=2)
    wire(ax, (bme_x, 5.6), (bx['sda'], 5.6), color='#2196F3', lw=2)
    wire(ax, (bme_x, 5.2), (bx['scl'], 5.2), color='#2196F3', lw=2)

    # Bus → ESP32 (horizontal)
    wire(ax, (bx['3v3'], 7.5), (esp_x, 7.5), color='#4CAF50', lw=2)
    wire(ax, (bx['gnd'], 6.8), (esp_x, 6.8), color='black', lw=2)
    wire(ax, (bx['sda'], 6.1), (esp_x, 6.1), color='#2196F3', lw=2)
    wire(ax, (bx['scl'], 5.4), (esp_x, 5.4), color='#2196F3', lw=2)

    # --- Legend ---
    box(ax, 11.0, 1.0, 7.0, 2.5, '#ddd', '#f8f8f8', 1.5)
    label(ax, 14.5, 3.2, 'Wire Legend', fontsize=11, weight='bold', va='center')
    items = [
        (2.7, '#2196F3', 'I2C SDA (GPIO 8) + SCL (GPIO 9)'),
        (2.2, '#4CAF50', '3.3V Power'),
        (1.7, '#f44336', '5V (Buck Converter → VIN)'),
        (1.2, 'black',   'Ground'),
    ]
    for iy, ic, il in items:
        wire(ax, (11.3, iy), (12.0, iy), color=ic, lw=2.5)
        label(ax, 12.3, iy, il, fontsize=9, ha='left', va='center')

    # Notes
    label(ax, 10, 0.4, 'BME280: 0x76  |  SSD1306: 0x3C  |  I2C 400 kHz  |  Both share SDA/SCL bus',
          fontsize=9, color='#888', va='center')

    plt.tight_layout()
    plt.savefig('docs/esp32_main_wiring_pro.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('docs/esp32_main_wiring_pro.svg', dpi=300, bbox_inches='tight')
    print("Created esp32_main_wiring_pro.pdf and .svg")
    plt.close()


# =============================================================================
# DIAGRAM 4: COMPREHENSIVE RELAY SPLICE
# =============================================================================
def create_relay_splice_comprehensive():
    fig, ax = new_page(28, 20)

    label(ax, 14, 19.5, 'ESP32-S3-N16R8 — DIRECT 120VAC WIRING TO DOMETIC BRISK II',
          fontsize=18, weight='bold', va='center')
    label(ax, 14, 18.9, 'SSR-25DA for Compressor  |  Relay Channels for Fans + Furnace  |  Dual Freeze Protection',
          fontsize=11, color='#666', va='center')

    # =====================================================
    # LEFT: ESP32 + Relay Module
    # =====================================================
    box(ax, 0.5, 7.0, 6.0, 11.0, '#0066cc', '#e6f3ff', 3)
    label(ax, 3.5, 17.7, 'ESP32-S3-N16R8 + 4-CH RELAY', fontsize=13, weight='bold', va='center')
    label(ax, 3.5, 17.2, '44-Pin Dev Board  |  5V USB-C', fontsize=9, va='center', color='#666')
    label(ax, 3.5, 16.7, 'Relay: 10A, Active HIGH (jumper)', fontsize=8, va='center', color='#888')

    # Channel pins — right side of box
    ch_x = 6.5
    channels = [
        (16.0, 'CH1 (GPIO 4): Furnace',       '#ff6600'),
        (15.2, 'CH2 (GPIO 5): Compressor→SSR', '#cc0000'),
        (14.4, 'CH3 (GPIO 6): Fan Low',       '#ff0000'),
        (13.6, 'CH4 (GPIO 15): Fan High',     '#333333'),
    ]
    for cy, cl, cc in channels:
        pin(ax, ch_x, cy, cc, 9)
        label(ax, ch_x - 0.2, cy, cl, fontsize=9, ha='right', va='center', color=cc)

    # Other pins
    pin(ax, ch_x, 12.8, '#9900cc', 7)
    label(ax, ch_x - 0.2, 12.8, 'Reset Btn: GPIO 2', fontsize=8, ha='right', va='center', color='#9900cc')
    pin(ax, ch_x, 12.0, '#00cc00', 7)
    label(ax, ch_x - 0.2, 12.0, 'RGB LED: GPIO 48', fontsize=8, ha='right', va='center', color='#00cc00')
    pin(ax, ch_x, 11.0, '#2196F3', 7)
    label(ax, ch_x - 0.2, 11.0, 'I2C: GPIO 41/40', fontsize=8, ha='right', va='center', color='#2196F3')
    pin(ax, ch_x, 10.2, '#00cccc', 7)
    label(ax, ch_x - 0.2, 10.2, 'DS18B20: GPIO 42', fontsize=8, ha='right', va='center', color='#00cccc')
    pin(ax, ch_x, 9.4, 'black', 7)
    label(ax, ch_x - 0.2, 9.4, 'GND', fontsize=8, ha='right', va='center')
    pin(ax, ch_x, 8.6, '#cc0000', 7)
    label(ax, ch_x - 0.2, 8.6, '12V+', fontsize=8, ha='right', va='center', color='#cc0000')
    pin(ax, ch_x, 7.8, '#ff0000', 7)
    label(ax, ch_x - 0.2, 7.8, '3.3V', fontsize=8, ha='right', va='center', color='#ff0000')

    # =====================================================
    # TOP CENTER: SSR-25DA
    # =====================================================
    box(ax, 9.0, 15.5, 5.0, 3.0, '#cc0000', '#ffebee', 3)
    label(ax, 11.5, 18.2, 'SSR-25DA', fontsize=14, weight='bold', va='center', color='#cc0000')
    label(ax, 11.5, 17.6, 'Solid State Relay', fontsize=10, va='center')
    label(ax, 11.5, 17.1, '3-32VDC → 25A/380VAC', fontsize=9, va='center', color='#666')

    pin(ax, 9.0, 16.8, '#cc0000', 9)
    label(ax, 8.8, 16.8, 'DC+', fontsize=9, ha='right', va='center')
    pin(ax, 9.0, 16.0, 'black', 9)
    label(ax, 8.8, 16.0, 'DC-', fontsize=9, ha='right', va='center')
    pin(ax, 14.0, 16.8, '#ff0000', 9)
    label(ax, 14.2, 16.8, 'AC1 (in)', fontsize=9, ha='left', va='center')
    pin(ax, 14.0, 16.0, '#ff0000', 9)
    label(ax, 14.2, 16.0, 'AC2 (out)', fontsize=9, ha='left', va='center')

    # =====================================================
    # TOP RIGHT: 120VAC Source
    # =====================================================
    box(ax, 21.0, 16.0, 6.0, 2.5, '#ff0000', '#ffebee', 3)
    label(ax, 24.0, 18.2, '120VAC SOURCE', fontsize=14, weight='bold', va='center', color='#ff0000')
    pin(ax, 21.5, 17.0, '#ff0000', 10)
    label(ax, 21.3, 17.0, 'HOT', fontsize=10, ha='right', va='center')
    pin(ax, 26.5, 17.0, '#0066ff', 10)
    label(ax, 26.7, 17.0, 'NEUTRAL', fontsize=10, ha='left', va='center')

    # =====================================================
    # MIDDLE RIGHT: Load Chain
    # =====================================================
    box(ax, 16.0, 13.0, 5.0, 3.5, 'black', '#f0f0f0', 2.5)
    label(ax, 18.5, 16.2, 'LOAD CHAIN', fontsize=12, weight='bold', va='center')
    pin(ax, 18.5, 15.3, '#ff0000', 9)
    label(ax, 18.5, 15.0, 'Supco SFPC (freeze stat)', fontsize=8, va='center')
    label(ax, 18.5, 14.6, 'NC: opens 35F, closes 50F', fontsize=7, va='center', color='#666')
    pin(ax, 18.5, 14.0, '#ff0000', 9)
    label(ax, 18.5, 13.7, 'Bimetal Cutout', fontsize=8, va='center')

    # =====================================================
    # RIGHT: 6-Pin Dometic Cable
    # =====================================================
    box(ax, 21.0, 7.0, 6.5, 8.0, '#4CAF50', '#e8f5e9', 2.5)
    label(ax, 24.25, 14.7, '6-PIN DOMETIC CABLE', fontsize=13, weight='bold', va='center', color='#4CAF50')
    label(ax, 24.25, 14.2, 'to Brisk II Rooftop AC', fontsize=10, va='center')
    label(ax, 24.25, 13.7, '(14 AWG minimum)', fontsize=8, va='center', color='#666')

    cp_x = 21.5
    cable_pins = [
        (13.0, 'Pin 1: Blue (Compressor)',  '#0000ff'),
        (12.2, 'Pin 2: Black (Fan Hi)',     '#333333'),
        (11.4, 'Pin 3: Yellow (unused)',    '#cccc00'),
        (10.6, 'Pin 4: Red (Fan Lo)',       '#ff0000'),
        (9.8,  'Pin 5: White (Neutral)',    '#aaa'),
        (9.0,  'Pin 6: Green (Ground)',     '#00aa00'),
    ]
    for cy, cl, cc in cable_pins:
        pin(ax, cp_x, cy, cc, 10)
        label(ax, cp_x + 0.2, cy, cl, fontsize=9, ha='left', va='center')

    # =====================================================
    # WIRING — All orthogonal, clean routing
    # =====================================================

    # --- CH2 → SSR DC+ ---
    # Right from CH2, up to SSR DC+
    wire(ax, (ch_x, 15.2), (7.8, 15.2), color='#cc0000', lw=2.5)
    wire(ax, (7.8, 15.2), (7.8, 16.8), color='#cc0000', lw=2.5)
    wire(ax, (7.8, 16.8), (9.0, 16.8), color='#cc0000', lw=2.5)
    label(ax, 7.4, 16.2, 'CH2', fontsize=7, color='#cc0000', ha='left', va='center')

    # --- GND → SSR DC- ---
    # From GND pin, right to x=7.5, up to SSR DC-
    wire(ax, (ch_x, 9.4), (7.5, 9.4), color='black', lw=2.5)
    wire(ax, (7.5, 9.4), (7.5, 16.0), color='black', lw=2.5)
    wire(ax, (7.5, 16.0), (9.0, 16.0), color='black', lw=2.5)
    label(ax, 7.1, 12.5, 'GND', fontsize=7, ha='right', va='center')

    # --- 120VAC HOT → SSR AC1 ---
    # Straight horizontal along y=17
    wire(ax, (21.5, 17.0), (15.0, 17.0), color='#ff0000', lw=3.5)
    wire(ax, (15.0, 17.0), (15.0, 16.8), color='#ff0000', lw=3.5)
    wire(ax, (15.0, 16.8), (14.0, 16.8), color='#ff0000', lw=3.5)
    label(ax, 18.0, 17.5, '120VAC HOT', fontsize=10, color='#ff0000', weight='bold', va='bottom')

    # --- SSR AC2 → Load Chain ---
    wire(ax, (14.0, 16.0), (15.5, 16.0), color='#ff0000', lw=3.5)
    wire(ax, (15.5, 16.0), (15.5, 15.3), color='#ff0000', lw=3.5)
    wire(ax, (15.5, 15.3), (18.5, 15.3), color='#ff0000', lw=3.5)
    label(ax, 17.0, 15.8, '120VAC Switched', fontsize=8, color='#ff0000', weight='bold', va='bottom')

    # Through load chain
    wire(ax, (18.5, 15.3), (18.5, 14.0), color='#ff0000', lw=3.5)

    # Load chain → Cable Pin 1 (Compressor)
    wire(ax, (18.5, 14.0), (18.5, 13.0), color='#0000ff', lw=3.5)
    wire(ax, (18.5, 13.0), (21.5, 13.0), color='#0000ff', lw=3.5)

    # --- NEUTRAL bus ---
    # From 120VAC NEU down right side to Cable Pin 5
    wire(ax, (26.5, 17.0), (27.5, 17.0), color='#0066ff', lw=3.5)
    wire(ax, (27.5, 17.0), (27.5, 9.8), color='#0066ff', lw=3.5)
    wire(ax, (27.5, 9.8), (21.5, 9.8), color='#0066ff', lw=3.5)
    label(ax, 27.7, 13.0, 'NEUTRAL', fontsize=9, color='#0066ff', rotation=90, ha='left', va='center')

    # --- Fan Low: CH3 → Cable Pin 4 ---
    # Route AROUND Load Chain box: horizontal to x=15.7, down, then right to pin
    wire(ax, (ch_x, 14.4), (15.7, 14.4), color='#ff0000', lw=2.5)
    wire(ax, (15.7, 14.4), (15.7, 10.6), color='#ff0000', lw=2.5)
    wire(ax, (15.7, 10.6), (21.5, 10.6), color='#ff0000', lw=2.5)
    label(ax, 18.5, 10.0, 'Fan Lo (CH3 → Pin 4)', fontsize=7, color='#ff0000')

    # --- Fan High: CH4 → Cable Pin 2 ---
    # Route AROUND Load Chain box: horizontal to x=15.2, down, then right to pin
    wire(ax, (ch_x, 13.6), (15.2, 13.6), color='#333', lw=2.5)
    wire(ax, (15.2, 13.6), (15.2, 12.2), color='#333', lw=2.5)
    wire(ax, (15.2, 12.2), (21.5, 12.2), color='#333', lw=2.5)
    label(ax, 18.5, 11.6, 'Fan Hi (CH4 → Pin 2)', fontsize=7, color='#333')

    # --- CH1 → Furnace ---
    # From CH1 pin straight DOWN (at x=6.5) to furnace box
    # Route LEFT of the module box to avoid crossing other channel pins
    wire(ax, (ch_x, 16.0), (8.0, 16.0), color='#ff6600', lw=2.5)
    wire(ax, (8.0, 16.0), (8.0, 5.5), color='#ff6600', lw=2.5)
    wire(ax, (8.0, 5.5), (5.5, 5.5), color='#ff6600', lw=2.5)
    label(ax, 8.3, 11.0, 'CH1 NO', fontsize=9, color='#ff6600', rotation=90, ha='left', va='center')

    # =====================================================
    # BOTTOM LEFT: Furnace
    # =====================================================
    box(ax, 0.5, 4.0, 6.0, 2.5, '#ff6600', '#fff3e0', 2)
    label(ax, 3.5, 6.2, 'FURNACE', fontsize=12, weight='bold', va='center')
    label(ax, 3.5, 5.7, '(Dry Contact Closure)', fontsize=9, va='center')
    label(ax, 3.5, 5.2, 'Separate unit with own blower', fontsize=8, va='center', color='#666')
    pin(ax, 2.0, 4.5, '#ff6600', 9)
    label(ax, 2.0, 4.2, 'T1', fontsize=8, va='center')
    pin(ax, 5.5, 4.5, '#ff6600', 9)
    label(ax, 5.5, 4.2, 'T2', fontsize=8, va='center')
    # Wire arrives at T2 from above
    wire(ax, (5.5, 5.5), (5.5, 4.5), color='#ff6600', lw=2.5)

    # =====================================================
    # BOTTOM CENTER: DS18B20 (3-lead: VCC, Data, GND)
    # =====================================================
    box(ax, 9.0, 4.0, 8.0, 2.5, '#00cccc', '#e0f7fa', 2)
    label(ax, 12.5, 6.2, 'DS18B20 FREEZE SENSOR', fontsize=11, weight='bold', va='center', color='#00cccc')
    label(ax, 12.5, 5.7, 'Waterproof probe on evaporator coil', fontsize=8, va='center', color='#666')
    label(ax, 12.5, 5.2, 'Software: Cut compressor @ 32F, restart @ 45F', fontsize=8, va='center', color='#cc0000')
    label(ax, 12.5, 4.5, '4.7K\u03A9 pull-up: Data \u2192 3.3V', fontsize=7, va='center', color='#666')

    # DS18B20 pins on left edge (3 leads)
    ds_px = 9.0
    pin(ax, ds_px, 5.8, '#ff0000', 7)
    label(ax, ds_px + 0.15, 5.8, 'VCC', fontsize=7, ha='left', va='center', color='#ff0000')
    pin(ax, ds_px, 5.3, '#00cccc', 7)
    label(ax, ds_px + 0.15, 5.3, 'Data', fontsize=7, ha='left', va='center', color='#00cccc')
    pin(ax, ds_px, 4.8, 'black', 7)
    label(ax, ds_px + 0.15, 4.8, 'GND', fontsize=7, ha='left', va='center')

    # --- DS18B20 wiring: 3 leads from ESP32 ---
    # VCC (3.3V): from 3.3V pin, right to riser, down to sensor VCC
    wire(ax, (ch_x, 7.8), (8.7, 7.8), color='#ff0000', lw=2)
    wire(ax, (8.7, 7.8), (8.7, 5.8), color='#ff0000', lw=2)
    wire(ax, (8.7, 5.8), (ds_px, 5.8), color='#ff0000', lw=2)

    # Data (GPIO 15): from GPIO 15 pin, right to riser, down to sensor Data
    wire(ax, (ch_x, 10.2), (8.5, 10.2), color='#00cccc', lw=2)
    wire(ax, (8.5, 10.2), (8.5, 5.3), color='#00cccc', lw=2)
    wire(ax, (8.5, 5.3), (ds_px, 5.3), color='#00cccc', lw=2)

    # GND: branch from GND bus at junction, right to riser, down to sensor GND
    pin(ax, 7.5, 9.4, 'black', 5)  # junction dot for GND branch
    wire(ax, (7.5, 9.4), (8.3, 9.4), color='black', lw=2)
    wire(ax, (8.3, 9.4), (8.3, 4.8), color='black', lw=2)
    wire(ax, (8.3, 4.8), (ds_px, 4.8), color='black', lw=2)

    # =====================================================
    # BOTTOM: Safety Notes + Specs
    # =====================================================
    box(ax, 0.5, 0.3, 13.0, 3.2, '#ff0000', '#fff5f5', 2.5)
    label(ax, 7.0, 3.2, 'SAFETY CRITICAL — 120VAC WIRING', fontsize=11, weight='bold',
          va='center', color='#ff0000')
    notes = [
        "  CH2 relay NO switches 12VDC milliamp trigger to SSR DC+",
        "  SSR-25DA switches 120VAC to compressor (heatsink required ~15W @ 12A)",
        "  CH3/CH4 switch 120VAC directly to fans (2-3A, 10A relay rating)",
        "  CH1 = dry contact for furnace (separate unit)",
        "  Dual freeze protection: DS18B20 software (32F) + Supco SFPC hardware (35F)",
        "  All 120VAC wiring: 14 AWG minimum, proper junction box per NEC",
    ]
    y = 2.8
    for n in notes:
        label(ax, 0.8, y, n, fontsize=8, ha='left', va='center')
        y -= 0.38

    box(ax, 14.0, 0.3, 13.5, 3.2, '#0066cc', '#f0f8ff', 2)
    label(ax, 20.75, 3.2, 'COMPONENT SPECIFICATIONS', fontsize=11, weight='bold',
          va='center', color='#0066cc')
    specs = [
        "ESP32-S3-N16R8 + 4-CHANNEL RELAY MODULE:",
        "  ESP32: 16MB Flash, 8MB PSRAM | 5V USB-C",
        "  Relay: 10A per channel, Active HIGH (4 channels)",
        "GPIO ASSIGNMENTS:",
        "  CH1=GPIO4  CH2=GPIO5  CH3=GPIO6  CH4=GPIO15",
        "  I2C: SDA=GPIO41, SCL=GPIO40 | 1-Wire: GPIO42",
        "  RGB LED: GPIO48 | Reset Button: GPIO2 (NO to GND)",
    ]
    y = 2.8
    for s in specs:
        w = 'bold' if s.endswith(":") else 'normal'
        label(ax, 14.3, y, s, fontsize=8, ha='left', va='center', weight=w)
        y -= 0.38

    plt.tight_layout()
    plt.savefig('docs/esp32_remote_relay_splice_pro.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('docs/esp32_remote_relay_splice_pro.svg', dpi=300, bbox_inches='tight')
    print("Created esp32_remote_relay_splice_pro.pdf and .svg")
    plt.close()


# =============================================================================
if __name__ == '__main__':
    print("\nCreating wiring diagrams (11.5x8 pages, orthogonal routing)...")
    print("=" * 60)
    create_ssr_diagram()
    create_i2c_diagram()
    create_esp32_main_wiring()
    create_relay_splice_comprehensive()
    print("=" * 60)
    print("All diagrams created in docs/")
