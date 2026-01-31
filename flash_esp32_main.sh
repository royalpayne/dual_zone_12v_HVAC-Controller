#!/bin/bash
# Flash MicroPython firmware to ESP32 Main
# Usage: ./flash_esp32_main.sh [device]
# Example: ./flash_esp32_main.sh /dev/ttyUSB0

set -e

DEVICE=${1:-/dev/ttyUSB0}
FIRMWARE="ESP32_GENERIC-20240222-v1.22.2.bin"

echo "========================================="
echo "Flashing ESP32 Main Controller"
echo "Device: $DEVICE"
echo "========================================="

# Check if firmware file exists
if [ ! -f "$FIRMWARE" ]; then
    echo "Firmware file not found: $FIRMWARE"
    echo "Downloading MicroPython firmware..."
    wget -O "$FIRMWARE" https://micropython.org/resources/firmware/ESP32_GENERIC-20240222-v1.22.2.bin
fi

echo ""
echo "Step 1: Erasing flash..."
esptool.py --chip esp32 --port $DEVICE erase_flash

echo ""
echo "Step 2: Flashing MicroPython firmware..."
esptool.py --chip esp32 --port $DEVICE --baud 460800 write_flash -z 0x1000 $FIRMWARE

echo ""
echo "========================================="
echo "Flash Complete!"
echo "========================================="
echo ""
echo "ESP32 should reboot automatically."
echo "Next step: Deploy the thermostat code"
echo ""
