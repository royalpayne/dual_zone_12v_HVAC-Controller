# Enhanced Whynter IR test - sends code multiple times
# Try this if single transmission doesn't work

import sys
sys.path.insert(0, '/peterhinch_ir')

from machine import Pin
from ir_tx import Player
import time

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
player = Player(pin, freq=38000, verbose=False)

print("\n=== Sending Whynter POWER code ===")
print("Distance: Get within 1-2 feet of A/C unit")
print("Angle: Point LED directly at receiver")
print(f"Code length: {len(power_code)} timings")
print("\nSending 3 times with delays...")

for i in range(3):
    print(f"\n[{i+1}/3] Transmitting...")
    player.play(power_code)
    time.sleep(0.5)  # 500ms between transmissions

print("\n=== Done! ===")
print("Did the A/C respond?")
print("\nIf not, try:")
print("1. Move closer (< 1 foot)")
print("2. Point LED directly at A/C receiver")
print("3. Make sure A/C is plugged in and ready")
