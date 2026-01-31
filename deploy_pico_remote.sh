#!/bin/bash
# Deploy updated code to ESP32 Remote
# This uploads all necessary files for the IR control functionality

set -e

echo "========================================="
echo "Deploying ESP32 Remote Code"
echo "========================================="

# Activate virtual environment if needed
if [ -d "venv" ]; then
    source venv/bin/activate
fi

cd pico_remote

echo ""
echo "Step 1: Checking connection to ESP32..."
mpremote connect /dev/ttyUSB0 exec "print('Connected to ESP32')" || {
    echo "Failed to connect on /dev/ttyUSB0, trying /dev/ttyACM0..."
    DEVICE=/dev/ttyACM0
    mpremote connect $DEVICE exec "print('Connected to ESP32')" || {
        echo "ERROR: Could not connect to ESP32 on any device"
        exit 1
    }
} && DEVICE=/dev/ttyUSB0

echo "✓ Connected on $DEVICE"

echo ""
echo "Step 2: Uploading core files..."

# Upload all Python files
FILES=(
    "boot.py"
    "main.py"
    "config.py"
    "ir_whynter.py"
    "webserver.py"
    "thermostat.py"
    "sensor.py"
    "display.py"
    "bmp280.py"
    "ssd1306.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  Uploading $file..."
        mpremote connect $DEVICE cp "$file" :
    else
        echo "  Warning: $file not found, skipping"
    fi
done

echo ""
echo "Step 3: Checking for config_local.py..."
if [ -f "config_local.py" ]; then
    echo "  Uploading config_local.py (WiFi credentials)..."
    mpremote connect $DEVICE cp config_local.py :
else
    echo "  Warning: config_local.py not found"
    echo "  Make sure WiFi credentials are set in config.py"
fi

echo ""
echo "Step 4: Listing uploaded files..."
mpremote connect $DEVICE ls

echo ""
echo "Step 5: Resetting ESP32..."
mpremote connect $DEVICE reset

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Wait ~10 seconds for ESP32 to boot and connect to WiFi"
echo "2. Check serial output: mpremote connect $DEVICE"
echo "3. Look for the IP address in the boot messages"
echo "4. Test API: curl http://192.168.71.153/api/status"
echo ""
