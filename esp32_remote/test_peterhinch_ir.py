# Test IR transmission using peterhinch library with proper RMT carrier
# This uses ESP32 hardware to generate 38kHz modulated signal

import sys
sys.path.insert(0, '/peterhinch_ir')

from machine import Pin
from ir_tx import Player

# Whynter power code captured from remote
power_code = [
    9075, 4568,  # Leader
    625, 548, 624, 544, 571, 598, 567, 1742,
    545, 650, 541, 623, 572, 1748, 603, 575,
    571, 598, 567, 1742, 545, 650, 541, 1748,
    603, 575, 571, 598, 567, 1742, 545, 1748,
    603, 1748, 571, 598, 567, 1742, 545, 650,
    541, 1748, 603, 1748, 571, 1748, 567, 1742,
    545, 650, 541, 1748, 603, 575, 571, 598,
    567, 1742, 545, 650, 541, 623, 572, 1748, 577
]

print("Initializing IR Player on GPIO 18...")
pin = Pin(18, Pin.OUT)
player = Player(pin, freq=38000, verbose=True)

print("\nSending Whynter POWER code with 38kHz carrier...")
print(f"Code has {len(power_code)} timing values")
player.play(power_code)

print("\nDone! Check if Whynter responded.")
