# boot.py - ESP32 Auto-start
# This file runs automatically on boot and starts main.py

import time
from machine import Pin

print("ESP32 boot.py starting...")

# Set relay GPIOs to OFF immediately to prevent activation during boot
# Furnace/compressor (38, 39): active LOW → HIGH = OFF
for gpio in (38, 39):
    Pin(gpio, Pin.OUT, value=1)
# Fan relays (40, 42): active HIGH → LOW = OFF
for gpio in (40, 42):
    Pin(gpio, Pin.OUT, value=0)

time.sleep(1)  # Give hardware time to initialize

try:
    import main
    main.main()
except Exception as e:
    print(f"Error starting main: {e}")
    import sys
    sys.print_exception(e)
