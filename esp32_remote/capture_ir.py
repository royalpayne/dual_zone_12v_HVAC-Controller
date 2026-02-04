# Capture IR code from Whynter remote
# Point remote at IR receiver on GPIO 19 and press button

import sys
sys.path.insert(0, '/')

from machine import Pin
from ir_rx.acquire import IR_GET

print("\n=== IR Code Capture ===")
print("IR Receiver on GPIO 19")
print("\nInstructions:")
print("1. Point your Whynter remote at the IR receiver")
print("2. Press and hold the POWER button")
print("3. Wait for code to be captured and displayed")
print("\nStarting capture in 3 seconds...")
print("(Press Ctrl+C to cancel)\n")

import time
time.sleep(3)

# Start capture on GPIO 19
pin = Pin(19, Pin.IN)
irg = IR_GET(pin)
print('Waiting for IR data...')
data = irg.acquire()

print("\n=== CAPTURED CODE ===")
print("Copy this code:")
print(data)
print("\n=== DONE ===")
