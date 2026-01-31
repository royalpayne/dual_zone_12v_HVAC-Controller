# Manual Deployment Guide for Pico Remote

## Quick Upload - Copy/Paste Commands

Run these commands one at a time from the `rv_thermostat` directory:

```bash
# Activate venv
source venv/bin/activate

# Go to pico_remote directory
cd pico_remote

# Upload each file (one at a time)
mpremote cp ir_whynter.py :ir_whynter.py
mpremote cp webserver.py :webserver.py
mpremote cp thermostat.py :thermostat.py
mpremote cp main.py :main.py
mpremote cp config.py :config.py
mpremote cp sensor.py :sensor.py
mpremote cp display.py :display.py
mpremote cp bmp280.py :bmp280.py
mpremote cp ssd1306.py :ssd1306.py

# Upload config_local.py if it exists
mpremote cp config_local.py :config_local.py 2>/dev/null || echo "No config_local.py - using defaults"

# Reset the Pico
mpremote reset

# Monitor serial output to see IP address
mpremote
```

## Alternative: Using Thonny IDE

1. Open Thonny IDE
2. Connect to Pico (bottom right corner - select "MicroPython (Raspberry Pi Pico)" device)
3. In the Files pane, navigate to `pico_remote/` folder on your computer
4. Select all `.py` files
5. Right-click → "Upload to /"
6. Press the reset button on Pico or run `import machine; machine.reset()`
7. Watch the Shell pane for boot messages with IP address

## After Upload

1. Watch the serial console - you should see:
   ```
   Pico Remote starting...
   Connecting to YOUR_WIFI_SSID...
   Connected: 192.168.71.XXX
   API server listening on port 80
   ```

2. Note the IP address

3. Test the connection:
   ```bash
   curl "http://PICO_IP/api/ir/status"
   ```

## If Still No Connection

- Check WiFi credentials in config.py or config_local.py
- Make sure Pico is on same network as your computer
- Check router DHCP client list for Pico's IP
- Try pressing reset button on Pico after upload
