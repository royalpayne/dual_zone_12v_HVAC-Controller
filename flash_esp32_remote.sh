#!/bin/bash
# Flash MicroPython firmware to ESP32 Remote
# Usage: ./flash_esp32_remote.sh [device]
# Example: ./flash_esp32_remote.sh /dev/ttyUSB1

set -e

DEVICE=${1:-/dev/ttyUSB1}
FIRMWARE="ESP32_GENERIC-20240222-v1.22.2.bin"

echo "========================================="
echo "Flashing ESP32 Remote Controller"
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
echo "Next step: Deploy the remote code"
echo ""
