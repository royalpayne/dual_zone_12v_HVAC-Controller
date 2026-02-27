# boot.py - ESP32 Auto-start
# This file runs automatically on boot and starts main.py

import time
from machine import Pin

print("ESP32 boot.py starting...")

# Set relay GPIOs to OFF immediately to prevent activation during boot
# 4-Channel Relay Module: Active LOW (HIGH = OFF, LOW = ON)
# GPIO 4 = Furnace, GPIO 5 = Compressor, GPIO 6 = Fan Low, GPIO 15 = Fan High
for gpio in (4, 5, 6, 15):
    Pin(gpio, Pin.OUT, value=0)

time.sleep(1)  # Give hardware time to initialize

try:
    import main
    main.main()
except Exception as e:
    print(f"Error starting main: {e}")
    import sys
    sys.print_exception(e)
