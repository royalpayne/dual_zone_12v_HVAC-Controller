#!/bin/bash
# Test ESP32 Web Server
# =====================

ESP32_IP="192.168.71.152"

echo "========================================="
echo "ESP32 Web Server Diagnostic Test"
echo "========================================="
echo ""

echo "1. Testing network connectivity..."
if ping -c 2 -W 2 $ESP32_IP > /dev/null 2>&1; then
    echo "   ✓ ESP32 is reachable at $ESP32_IP"
else
    echo "   ✗ Cannot ping $ESP32_IP"
    echo "   - Check if ESP32 is powered on"
    echo "   - Verify WiFi connection"
    echo "   - Check if you're on the same network"
    exit 1
fi

echo ""
echo "2. Testing API endpoint..."
if curl -s --max-time 3 "http://$ESP32_IP/api/status" > /dev/null 2>&1; then
    echo "   ✓ API is responding"
    echo ""
    echo "   API Status Response:"
    curl -s "http://$ESP32_IP/api/status" | python3 -m json.tool
else
    echo "   ✗ API not responding"
    echo "   - Web server may not be started"
    echo "   - Check serial console for errors"
    exit 1
fi

echo ""
echo "3. Testing HTML page..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$ESP32_IP/")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ HTML page returns HTTP 200"
    echo ""
    echo "   First 500 characters of response:"
    curl -s "http://$ESP32_IP/" | head -c 500
    echo ""
    echo ""
    echo "   ✓ Web page should be accessible at: http://$ESP32_IP/"
else
    echo "   ✗ HTML page returns HTTP $HTTP_CODE"
fi

echo ""
echo "========================================="
echo "Diagnostic complete!"
echo "========================================="
echo ""
echo "If all tests passed, try accessing in your browser:"
echo "  http://$ESP32_IP/"
echo ""
echo "If browser doesn't work, try:"
echo "  - Hard refresh (Ctrl+F5)"
echo "  - Incognito/private window"
echo "  - Different browser"
