# boot.py - ESP32 Auto-start
# This file runs automatically on boot and starts main.py

import time

print("ESP32 boot.py starting...")
time.sleep(1)  # Give hardware time to initialize

try:
    import main
    main.main()
except Exception as e:
    print(f"Error starting main: {e}")
    import sys
    sys.print_exception(e)
