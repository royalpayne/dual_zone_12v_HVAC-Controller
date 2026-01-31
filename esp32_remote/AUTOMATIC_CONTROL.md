# Automatic Control Implementation Summary

## Overview
The IR module has been enhanced with comprehensive automatic control capabilities. The system can now autonomously manage all Whynter AC settings including mode, temperature, and fan speed.

## What Was Added

### 1. Complete State Tracking
**File: [ir_whynter.py](pico_remote/ir_whynter.py)**

The system now tracks:
- `power_on` - Power state (True/False)
- `current_mode` - Operating mode (cool/heat/fan/dehum)
- `current_temp` - Temperature setpoint (61-89°F)
- `current_fan` - Fan speed (auto/low/med/high)

All state persists in `ir_state.json` across reboots.

### 2. Temperature Control Methods

```python
# Set specific temperature (automatically presses temp_up/temp_down as needed)
ir.set_temperature(72)  # Sets to 72°F

# Smart mode + temp setting
ir.set_cooling(72, fan_speed='auto')  # Cool mode at 72°F
ir.set_heating(68, fan_speed='low')   # Heat mode at 68°F
```

### 3. Fan Speed Control

```python
# Set specific fan speed (automatically cycles through speeds)
ir.set_fan_speed('high')  # Options: auto, low, med, high
```

### 4. Master Control Method

```python
# Achieve any state from any starting state
ir.achieve_state(
    power=True,      # Turn on
    mode='cool',     # Set cooling mode
    temp=72,         # Set to 72°F
    fan='high'       # High fan speed
)

# Turn off completely
ir.achieve_state(power=False)

# Change just temperature (leave everything else as-is)
ir.achieve_state(temp=75)
```

### 5. Enhanced Boost Mode
**File: [thermostat.py](pico_remote/thermostat.py:202)**

Boost mode now uses intelligent settings:

**Heating Boost:**
- Sets mode to HEAT
- Sets temperature to `heat_setpoint + 5°F` (max 85°F)
- Sets fan to HIGH for maximum output

**Cooling Boost:**
- Sets mode to COOL
- Sets temperature to `cool_setpoint - 5°F` (min 65°F)
- Sets fan to HIGH for maximum output

This makes the portable unit work much harder than the old simple "turn on heat/cool" approach.

## API Endpoints Added

### Temperature Control
```bash
# Set temperature
GET /api/ir/temperature?temp=72

# Query current temp
GET /api/ir/temperature
```

### Fan Speed Control
```bash
# Set fan speed
GET /api/ir/fan?speed=high

# Query current fan
GET /api/ir/fan
```

### Combined Operations
```bash
# Set cooling mode with temp and fan in one call
GET /api/ir/set_cooling?temp=72&fan=auto

# Set heating mode with temp and fan
GET /api/ir/set_heating?temp=68&fan=low

# Master control - set any combination
GET /api/ir/achieve_state?power=1&mode=cool&temp=72&fan=high
GET /api/ir/achieve_state?temp=75  # Just change temp
GET /api/ir/achieve_state?power=0  # Just turn off
```

## How Automatic Operation Works

### Initial Setup (One Time)

1. **Learn IR Codes** from the Whynter remote:
   - `power` - Power button
   - `mode` - Mode cycle button
   - `temp_up` - Temperature increase
   - `temp_down` - Temperature decrease
   - `fan` - Fan speed cycle

2. **Set Initial State** in code or via API:
   ```python
   # Tell system what state the AC is currently in
   ir.current_temp = 72
   ir.current_fan = 'auto'
   ir.current_mode = 'cool'
   ir.power_on = False
   ir.save_state()
   ```

### Automatic Boost Operation Example

**Scenario:** Room is 85°F, cooling setpoint is 75°F, BOOST_THRESHOLD is 10°F

1. Normal rooftop AC activates (room above 75°F + hysteresis)
2. Room is still 10°F above setpoint → boost mode triggers
3. System calls `ir.set_cooling(70, 'high')` which:
   - Sends `power` command to turn on
   - Cycles `mode` button to reach 'cool' mode
   - Presses `temp_down` multiple times to reach 70°F
   - Cycles `fan` button to reach 'high' speed
4. Portable AC now runs at 70°F on high fan alongside rooftop AC
5. When room temp drops below setpoint + threshold → boost deactivates
6. System calls `ir.send_off()` to turn off portable unit

## Required IR Codes for Full Functionality

| Code Name   | Purpose | Required For |
|------------|---------|--------------|
| `power` | Power on/off | All operations |
| `mode` | Cycle through modes | Mode selection |
| `temp_up` | Increase temperature | Temperature control |
| `temp_down` | Decrease temperature | Temperature control |
| `fan` | Cycle fan speeds | Fan speed control |

**Note:** The system will work without `temp_up`, `temp_down`, or `fan` codes, but automatic temperature and fan control won't be available.

## State Synchronization

**Important:** The system tracks state based on IR commands sent. If you manually use the Whynter remote, the tracked state will be out of sync.

**Solutions:**
1. **Only use API/automatic control** - Don't use physical remote
2. **Reset state file** - Delete `ir_state.json` and set correct state
3. **Use achieve_state()** - It works regardless of actual AC state (may cause extra button presses)

## Configuration Options

**File: [config.py](pico_remote/config.py:22)**

```python
# Boost activation threshold
BOOST_THRESHOLD = 10  # Activate boost when temp differs by 10°F

# Short-cycle protection
MIN_CYCLE_TIME = 180  # 3 minutes between state changes

# Temperature limits (enforced by IR module)
MIN_TEMP = 61  # Minimum AC temp
MAX_TEMP = 89  # Maximum AC temp
```

## Testing the Implementation

### Test Basic Controls
```bash
# Check status
curl "http://REMOTE_IP/api/ir/status"

# Test temperature
curl "http://REMOTE_IP/api/ir/temperature?temp=72"

# Test fan
curl "http://REMOTE_IP/api/ir/fan?speed=high"
```

### Test Automatic Operation
```bash
# Simulate boost cooling
curl "http://REMOTE_IP/api/ir/set_cooling?temp=65&fan=high"

# Check result
curl "http://REMOTE_IP/api/ir/status"

# Turn off
curl "http://REMOTE_IP/api/ir/power?on=0"
```

### Test State Achievement
```bash
# Complex state change
curl "http://REMOTE_IP/api/ir/achieve_state?power=1&mode=heat&temp=72&fan=low"

# Verify
curl "http://REMOTE_IP/api/ir/status"
```

## Files Modified

1. **[ir_whynter.py](pico_remote/ir_whynter.py)** - Core IR control with automatic features
   - Added temperature and fan tracking
   - Added `set_temperature()`, `set_fan_speed()` methods
   - Added `set_cooling()`, `set_heating()` convenience methods
   - Added `achieve_state()` master control method
   - Enhanced state persistence

2. **[webserver.py](pico_remote/webserver.py)** - API endpoints
   - Added `/api/ir/temperature` endpoint
   - Added `/api/ir/fan` endpoint
   - Added `/api/ir/set_cooling` endpoint
   - Added `/api/ir/set_heating` endpoint
   - Added `/api/ir/achieve_state` master endpoint

3. **[thermostat.py](pico_remote/thermostat.py:202)** - Enhanced boost mode
   - Modified `_boost_on()` to use intelligent temp/fan settings
   - Heating boost: setpoint+5°F on high fan
   - Cooling boost: setpoint-5°F on high fan

## Benefits of New Implementation

✅ **Precise Control** - Set exact temperature and fan speed, not just mode
✅ **State Tracking** - System always knows current AC settings
✅ **Automatic Operation** - No manual intervention needed
✅ **Persistent State** - Survives reboots
✅ **Boost Optimization** - Portable unit works harder for faster results
✅ **API Flexibility** - Control any setting via simple HTTP calls
✅ **Graceful Degradation** - Works even if some codes aren't learned

## Next Steps

1. ✅ Learn all 5 IR codes using the remote
2. ✅ Test each control function via API
3. ✅ Verify state tracking persists across reboot
4. ✅ Test automatic boost mode activation
5. ✅ Monitor for state sync issues during normal operation
