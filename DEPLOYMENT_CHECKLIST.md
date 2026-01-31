# Deployment Checklist

## Summary
Both ESP32 and Pico W need updated config files to use static IPs:
- ESP32: 192.168.71.152
- Pico W: 192.168.71.153

## Current Status
- ✅ Code updated with static IP support
- ✅ config_local.py files created with WiFi credentials and static IPs
- ⏳ Pico W running with OLD config (192.168.71.151)
- ⏳ ESP32 not deployed yet

---

## Quick Deployment Steps

### Pico W (Currently at 192.168.71.151)

**Option A: Via USB (Recommended)**
1. Unplug Pico USB cable
2. Hold BOOTSEL button on Pico
3. Plug in USB while holding BOOTSEL
4. Pico mounts as USB drive
5. Copy new config:
   ```bash
   cp /home/heath/Dev/rv_thermostat/pico_remote/config_local.py /media/$USER/RPI-RP2/
   ```
6. Eject and reset

**Option B: Full Redeployment**
1. Disconnect Pico from power
2. Reconnect while holding BOOTSEL
3. Run: `./deploy_pico_remote.sh`
4. Reset Pico

**Expected Result**: Pico connects at 192.168.71.153

---

### ESP32

**Using Thonny IDE** (See DEPLOY_ESP32.md for details):
1. Open Thonny
2. Select ESP32 interpreter (Tools → Options)
3. Upload all .py files (especially config_local.py!)
4. Reset ESP32
5. Check serial output

**Expected Result**: ESP32 connects at 192.168.71.152

---

## Verification

### Test Pico W:
```bash
ping 192.168.71.153
curl http://192.168.71.153/api/status
```

### Test ESP32:
```bash
./test_esp32_web.sh
```

### Open Web Interface:
Open browser to: **http://192.168.71.152/**

---

## Troubleshooting

### Pico shows old IP (192.168.71.151)
→ config_local.py not uploaded, redeploy

### ESP32 not connecting
→ Check serial output, verify WiFi credentials

### Can ping but web page doesn't load
→ Check if web server started in serial output
→ Try: `curl http://192.168.71.152/` to see raw response
→ Clear browser cache / try incognito mode

### Files Prepared:
- ✅ /home/heath/Dev/rv_thermostat/config_local.py
- ✅ /home/heath/Dev/rv_thermostat/pico_remote/config_local.py
- ✅ Static IP code in main.py (both devices)
- ✅ Test scripts ready
