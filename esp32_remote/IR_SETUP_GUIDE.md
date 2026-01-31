# Whynter IR Setup & Usage Guide

## Overview
The IR module provides complete automatic control of the Whynter portable AC/heat pump unit. All settings (mode, temperature, fan speed) are tracked and can be controlled programmatically.

## Initial Setup: Learning IR Codes

Before automatic control works, you need to learn the IR codes from your remote control.

### Required Buttons to Learn

1. **power** - Power on/off button
2. **mode** - Mode cycle button (cool → dehum → fan → heat)
3. **temp_up** - Increase temperature
4. **temp_down** - Decrease temperature
5. **fan** - Fan speed cycle button (auto → low → med → high)

### Learning Process

Point the Whynter remote at the IR receiver and use the API:

```bash
# Learn each button (10 second timeout to press button)
curl "http://REMOTE_IP/api/ir/learn?name=power"
curl "http://REMOTE_IP/api/ir/learn?name=mode"
curl "http://REMOTE_IP/api/ir/learn?name=temp_up"
curl "http://REMOTE_IP/api/ir/learn?name=temp_down"
curl "http://REMOTE_IP/api/ir/learn?name=fan"
```

**Process for each:**
1. Send the API request
2. Wait for "[IR] Point remote at receiver and press button..." message
3. Press and hold the button on the remote for 1-2 seconds
4. Wait for confirmation "[IR] Learned 'button_name'"

### Verify Learned Codes

```bash
curl "http://REMOTE_IP/api/ir/codes"
```

Should return: `{"codes": ["power", "mode", "temp_up", "temp_down", "fan"]}`

## API Endpoints for Automatic Control

### Basic Controls

**Get IR Status**
```bash
curl "http://REMOTE_IP/api/ir/status"
```
Returns current state: power, mode, temp, fan speed, and available codes.

**Power Control**
```bash
curl "http://REMOTE_IP/api/ir/power?on=1"  # Turn on
curl "http://REMOTE_IP/api/ir/power?on=0"  # Turn off
```

**Set Mode** (cool/heat/fan/dehum)
```bash
curl "http://REMOTE_IP/api/ir/mode?mode=cool"
curl "http://REMOTE_IP/api/ir/mode?mode=heat"
```

**Set Temperature** (61-89°F)
```bash
curl "http://REMOTE_IP/api/ir/temperature?temp=72"
```

**Set Fan Speed** (auto/low/med/high)
```bash
curl "http://REMOTE_IP/api/ir/fan?speed=low"
```

### Advanced: Combined Controls

**Set Cooling Mode** (mode + temp + fan in one call)
```bash
curl "http://REMOTE_IP/api/ir/set_cooling?temp=72&fan=auto"
```

**Set Heating Mode** (mode + temp + fan in one call)
```bash
curl "http://REMOTE_IP/api/ir/set_heating?temp=68&fan=low"
```

**Achieve Specific State** (master control - set any combination)
```bash
# Turn on cooling at 72°F with high fan
curl "http://REMOTE_IP/api/ir/achieve_state?power=1&mode=cool&temp=72&fan=high"

# Turn off
curl "http://REMOTE_IP/api/ir/achieve_state?power=0"

# Change just temperature (leave everything else as-is)
curl "http://REMOTE_IP/api/ir/achieve_state?temp=75"
```

## State Tracking

The system tracks the current AC state in `ir_state.json`:
- **power**: On/off status
- **mode**: Current mode (cool/heat/fan/dehum)
- **temp**: Current temperature setpoint (61-89°F)
- **fan**: Current fan speed (auto/low/med/high)

This state persists across reboots, so the system always knows the AC's current settings.

## Automatic Operation

The thermostat controller can now use these methods for boost mode:

### Example: Activate Boost Cooling
```python
# In thermostat controller when temp exceeds setpoint + BOOST_THRESHOLD
ir.set_cooling(target_temp=65, fan_speed='high')
```

### Example: Deactivate Boost
```python
ir.send_off()
```

### Example: Smart Heating
```python
# Turn on heat at specific temp
ir.set_heating(target_temp=70, fan_speed='auto')
```

## Troubleshooting

**IR codes not working?**
- Re-learn the codes with fresh batteries in remote
- Ensure IR LED is positioned correctly
- Check IR_LED_PIN in config.py matches hardware

**Temperature/fan control not working?**
- Verify `temp_up`, `temp_down`, and `fan` buttons are learned
- Check that unit is powered on before adjusting settings
- Ensure `ir_state.json` reflects actual unit state

**State out of sync?**
- Manually using the remote will desync the tracked state
- Delete `ir_state.json` and re-learn the state
- Or use `achieve_state()` which works regardless of current state

## Hardware Notes

- **IR LED Pin**: GPIO 17 (default, see config.py)
- **Carrier Frequency**: 38kHz
- **Single Pin**: Same pin used for TX and RX (automatically switched)
- **Range**: Typically 5-10 feet, point LED directly at AC unit
