# ESP32 Deployment Guide

## Prerequisites
- ESP32 connected via USB
- Thonny IDE installed, OR
- esptool and rshell/ampy installed

## Method 1: Using Thonny IDE (Easiest)

1. **Open Thonny IDE**
2. **Select ESP32 interpreter**:
   - Go to: Tools → Options → Interpreter
   - Select "MicroPython (ESP32)"
   - Choose the correct port (usually /dev/ttyUSB0)

3. **Upload files**:
   - In Thonny, open the Files panel (View → Files)
   - Navigate to `/home/heath/Dev/rv_thermostat/`
   - Right-click each `.py` file → Upload to /
   - Make sure to upload:
     - main.py
     - config.py
     - config_local.py (IMPORTANT!)
     - env.py
     - webserver.py
     - thermostat_remote.py
     - pico_client.py
     - scheduler.py
     - sensor.py
     - display.py
     - bmp280.py
     - ssd1306.py

4. **Verify upload**:
   - In Thonny REPL, type: `import os; os.listdir()`
   - Should show all uploaded files

5. **Restart**:
   - Click the STOP button (red square)
   - Click the Run button, or
   - Type: `import machine; machine.reset()`

## Method 2: Using Command Line (Advanced)

### Install tools (if not already installed):
```bash
source venv/bin/activate
pip install adafruit-ampy
```

### Upload files:
```bash
cd /home/heath/Dev/rv_thermostat
PORT=/dev/ttyUSB0  # Adjust if needed

# Upload all .py files
for file in *.py; do
    echo "Uploading $file..."
    ampy -p $PORT put $file
done

# Verify
ampy -p $PORT ls
```

### Reset ESP32:
```bash
# Method 1: Hard reset
esptool.py --port $PORT run

# Method 2: Soft reset via minicom
minicom -D $PORT -b 115200
# Then press Ctrl+D in the MicroPython REPL
```

## Verification

After deployment, connect to serial console:
```bash
screen /dev/ttyUSB0 115200
# Or
minicom -D /dev/ttyUSB0 -b 115200
```

You should see:
```
[env] Environment: prod
[config] Override: WIFI_SSID = tinkerer
[config] Override: WIFI_PASSWORD = V!ncent16
[config] Override: STATIC_IP = 192.168.71.152
[config] Override: SUBNET_MASK = 255.255.255.0
[config] Override: GATEWAY = 192.168.71.1
[config] Override: DNS_SERVER = 192.168.71.1
Static IP configured: 192.168.71.152
Connecting to tinkerer...
Connected: 192.168.71.152
Sensors: BMP280=True, DHT11=True
Pico remote at 192.168.71.153
Web server started on port 80
Open http://192.168.71.152 in your browser
Thermostat running... Press Ctrl+C to stop
```

## Testing

Once connected, test from your computer:
```bash
cd /home/heath/Dev/rv_thermostat
./test_esp32_web.sh
```

Should show:
- ✓ Network connectivity
- ✓ API responding
- ✓ HTML page accessible

Then open in browser: **http://192.168.71.152/**
