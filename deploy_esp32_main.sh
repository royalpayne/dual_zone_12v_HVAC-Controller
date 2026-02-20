#!/bin/bash
# Deploy code to ESP32 Main Controller
# This uploads all necessary files for the main thermostat controller

set -e

DEVICE=${1:-/dev/ttyACM0}

echo "========================================="
echo "Deploying ESP32 Main Code"
echo "Device: $DEVICE"
echo "========================================="

# Activate virtual environment if needed
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo ""
echo "Step 1: Detecting device..."
if [ -e "$DEVICE" ]; then
    echo "✓ Found ESP32 on $DEVICE"
else
    echo "ERROR: Device not found: $DEVICE"
    exit 1
fi

echo ""
echo "Step 2: Uploading core files..."

# Core Python files for ESP32 Main
FILES=(
    "main.py"
    "config.py"
    "env.py"
    "thermostat_remote.py"
    "scheduler.py"
    "webserver.py"
    "remote_client.py"
    "sensor.py"
    "display.py"
    "bme280.py"
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
    echo "  ⚠ Warning: config_local.py not found"
    echo "  You need to create config_local.py with your WiFi credentials:"
    echo ""
    echo "    WIFI_SSID = \"your_network_name\""
    echo "    WIFI_PASSWORD = \"your_password\""
    echo ""
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
echo "3. Look for the IP address in the boot messages (should be 192.168.71.152)"
echo "4. Test API: curl http://192.168.71.152/api/status"
echo "5. Test BME280: Check if it reports temperature + humidity + pressure"
echo ""
