# boot.py - ESP32 Auto-start
# This file runs automatically on boot and starts main.py

import time
from machine import Pin

print("ESP32 boot.py starting...")

# Set relay GPIOs to OFF immediately to prevent activation during boot
# Waveshare ESP32-S3-Relay-6CH: All relays are active HIGH (LOW = OFF)
# CH1 (GPIO 1) = Furnace, CH2 (GPIO 2) = Compressor
# CH3 (GPIO 41) = Fan Low, CH4 (GPIO 42) = Fan High
for gpio in (1, 2, 41, 42):
    Pin(gpio, Pin.OUT, value=0)

time.sleep(1)  # Give hardware time to initialize

try:
    import main
    main.main()
except Exception as e:
    print(f"Error starting main: {e}")
    import sys
    sys.print_exception(e)
