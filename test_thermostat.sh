#!/bin/bash
# Test RV Thermostat System
# Usage: ./test_thermostat.sh <ESP32_IP>

ESP32_IP=${1:-"192.168.71.152"}  # ESP32 static IP
PICO_IP="192.168.71.153"         # Pico W static IP

echo "========================================="
echo "RV Thermostat System Test"
echo "========================================="
echo ""
echo "ESP32 Main Controller: $ESP32_IP"
echo "Pico IR Remote: $PICO_IP"
echo ""

echo "--- ESP32 Status ---"
curl -s "http://$ESP32_IP/api/status" | python3 -m json.tool

echo ""
echo "--- Setting Cooling Mode (75°F) ---"
curl -s "http://$ESP32_IP/api/mode?mode=2" | python3 -m json.tool
curl -s "http://$ESP32_IP/api/cool_setpoint?temp=75" | python3 -m json.tool

echo ""
echo "--- Pico IR Status ---"
curl -s "http://$PICO_IP/api/ir/status" | python3 -m json.tool

echo ""
echo "========================================="
echo "System configured for cooling at 75°F"
echo "Boost mode will activate if temp > 85°F"
echo "========================================="
