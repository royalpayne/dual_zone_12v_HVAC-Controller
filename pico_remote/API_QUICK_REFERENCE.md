# IR Control API Quick Reference

Replace `PICO_IP` with your Pico's IP address (e.g., 192.168.71.151)

## Initial Setup

### Learn IR Codes (do once)
```bash
curl "http://PICO_IP/api/ir/learn?name=power"
curl "http://PICO_IP/api/ir/learn?name=mode"
curl "http://PICO_IP/api/ir/learn?name=temp_up"
curl "http://PICO_IP/api/ir/learn?name=temp_down"
curl "http://PICO_IP/api/ir/learn?name=fan"
```

### Verify Learned Codes
```bash
curl "http://PICO_IP/api/ir/codes"
```

## Common Operations

### Check Status
```bash
curl "http://PICO_IP/api/ir/status"
```

### Power Control
```bash
curl "http://PICO_IP/api/ir/power?on=1"   # Turn ON
curl "http://PICO_IP/api/ir/power?on=0"   # Turn OFF
```

### Quick Cooling
```bash
curl "http://PICO_IP/api/ir/set_cooling?temp=72&fan=auto"
curl "http://PICO_IP/api/ir/set_cooling?temp=68&fan=high"
```

### Quick Heating
```bash
curl "http://PICO_IP/api/ir/set_heating?temp=72&fan=auto"
curl "http://PICO_IP/api/ir/set_heating?temp=75&fan=low"
```

### Change Temperature Only
```bash
curl "http://PICO_IP/api/ir/temperature?temp=72"
```

### Change Fan Only
```bash
curl "http://PICO_IP/api/ir/fan?speed=high"
curl "http://PICO_IP/api/ir/fan?speed=auto"
```

### Change Mode Only
```bash
curl "http://PICO_IP/api/ir/mode?mode=cool"
curl "http://PICO_IP/api/ir/mode?mode=heat"
curl "http://PICO_IP/api/ir/mode?mode=fan"
curl "http://PICO_IP/api/ir/mode?mode=dehum"
```

## Advanced Control

### Master State Control
```bash
# Full state specification
curl "http://PICO_IP/api/ir/achieve_state?power=1&mode=cool&temp=72&fan=high"

# Partial state (only change what you specify)
curl "http://PICO_IP/api/ir/achieve_state?temp=75"
curl "http://PICO_IP/api/ir/achieve_state?fan=low"
curl "http://PICO_IP/api/ir/achieve_state?power=0"
```

## Python Integration

### Using requests library
```python
import requests

PICO_IP = "192.168.71.151"

# Turn on cooling at 72°F
response = requests.get(f"http://{PICO_IP}/api/ir/set_cooling?temp=72&fan=auto")
print(response.json())

# Check status
status = requests.get(f"http://{PICO_IP}/api/ir/status").json()
print(f"Power: {status['power_on']}, Mode: {status['current_mode']}, Temp: {status['current_temp']}")

# Turn off
requests.get(f"http://{PICO_IP}/api/ir/power?on=0")
```

### Direct in MicroPython
```python
# From the IR module directly
ir = WhynterIR()

# Set cooling mode
ir.set_cooling(72, fan_speed='auto')

# Set heating mode
ir.set_heating(68, fan_speed='low')

# Change just temperature
ir.set_temperature(75)

# Master control
ir.achieve_state(power=True, mode='cool', temp=72, fan='high')
```

## Response Format

All endpoints return JSON:

**Success:**
```json
{
  "ok": true,
  "mode": "cool",
  "temp": 72,
  "fan": "auto"
}
```

**Error:**
```json
{
  "ok": false,
  "error": "No signal captured"
}
```

**Status Response:**
```json
{
  "codes": ["power", "mode", "temp_up", "temp_down", "fan"],
  "data_pin": 17,
  "power_on": true,
  "current_mode": "cool",
  "current_temp": 72,
  "current_fan": "auto",
  "modes": ["cool", "dehum", "fan", "heat"],
  "fan_speeds": ["auto", "low", "med", "high"],
  "temp_range": {"min": 61, "max": 89}
}
```

## Valid Values

- **power**: `1` (on) or `0` (off)
- **mode**: `cool`, `heat`, `fan`, `dehum`
- **temp**: `61` to `89` (Fahrenheit)
- **fan**: `auto`, `low`, `med`, `high`

## Troubleshooting

### No Response
- Check Pico IP address
- Ensure Pico is connected to WiFi
- Verify API server started (check serial output)

### Commands Don't Work
- Verify codes are learned: `curl "http://PICO_IP/api/ir/codes"`
- Re-learn codes if needed
- Check IR LED is pointed at AC unit

### State Out of Sync
- Delete `ir_state.json` on Pico
- Set correct state via API
- Avoid using physical remote
