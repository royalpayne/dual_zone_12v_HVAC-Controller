# Whynter ARC-14SH IR Controller
# ================================
# Protocol-based IR control for portable AC/Heatpump
# Sends full state in each 32-bit command via Broadlink RM4 Mini
# Protocol source: ESPHome PR #3641

import time
import json
from broadlink_client import pulses_to_broadlink

# State file for persistence across reboots
IR_STATE_FILE = "ir_state.json"

# Whynter modes
MODES = ['cool', 'dehum', 'fan', 'heat']

# Fan speeds
FAN_SPEEDS = ['auto', 'low', 'med', 'high']

# Temperature range (Fahrenheit)
MIN_TEMP = 61
MAX_TEMP = 89

# IR Protocol timing (microseconds) - ESPHome ARC-14S/ARC-14SH
HEADER_MARK = 8000
HEADER_SPACE = 4000
BIT_MARK = 600
ONE_SPACE = 1600
ZERO_SPACE = 550

# 32-bit command layout
COMMAND_HEADER = 0x12 << 24  # Bits 31-24

# Fan speed (bits 22-20)
_FAN_BITS = {
    'high': 0b001 << 20,
    'med':  0b010 << 20,
    'low':  0b100 << 20,
    'auto': 0b000 << 20,
}

# Mode (bits 19-16)
_MODE_BITS = {
    'fan':   0b0001 << 16,
    'dehum': 0b0010 << 16,
    'heat':  0b0100 << 16,
    'cool':  0b1000 << 16,
}

FAHRENHEIT_BIT = 1 << 10  # Bit 10
POWER_BIT = 1 << 8        # Bit 8


def _reverse_bits(byte_val):
    """Reverse bits of an 8-bit value for temperature encoding"""
    result = 0
    for i in range(8):
        if byte_val & (1 << i):
            result |= 1 << (7 - i)
    return result


def _encode_command(power, mode, fan, temp_f):
    """Build 32-bit Whynter command word"""
    cmd = COMMAND_HEADER
    cmd |= _FAN_BITS.get(fan, 0)
    cmd |= _MODE_BITS.get(mode, _MODE_BITS['cool'])
    cmd |= FAHRENHEIT_BIT
    if power:
        cmd |= POWER_BIT
    cmd |= _reverse_bits(temp_f) & 0xFF
    return cmd


def _command_to_pulses(cmd):
    """Convert 32-bit command to IR pulse timings (microseconds)"""
    pulses = [HEADER_MARK, HEADER_SPACE]
    for i in range(31, -1, -1):
        pulses.append(BIT_MARK)
        if (cmd >> i) & 1:
            pulses.append(ONE_SPACE)
        else:
            pulses.append(ZERO_SPACE)
    pulses.append(BIT_MARK)  # Final mark
    return pulses


class WhynterIR:
    """Protocol-based IR controller for Whynter ARC-14SH via Broadlink"""

    def __init__(self, broadlink_client):
        self.bl = broadlink_client

        # Track current state
        self.current_mode = 'cool'
        self.power_on = False
        self.current_temp = 72
        self.current_fan = 'auto'
        self.load_state()

    def load_state(self):
        """Load current AC state from file"""
        try:
            with open(IR_STATE_FILE, 'r') as f:
                state = json.load(f)
                self.current_mode = state.get('mode', 'cool')
                self.power_on = state.get('power', False)
                self.current_temp = state.get('temp', 72)
                self.current_fan = state.get('fan', 'auto')
                print(f"[IR] State: power={self.power_on}, mode={self.current_mode}, temp={self.current_temp}, fan={self.current_fan}")
        except:
            print("[IR] No saved state, using defaults")

    def save_state(self):
        """Save current AC state to file"""
        try:
            state = {
                'mode': self.current_mode,
                'power': self.power_on,
                'temp': self.current_temp,
                'fan': self.current_fan
            }
            with open(IR_STATE_FILE, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"[IR] State save error: {e}")

    def _send_command(self, power, mode=None, fan=None, temp=None):
        """Build and send an IR command with current or overridden state"""
        mode = mode or self.current_mode
        fan = fan or self.current_fan
        temp = temp if temp is not None else self.current_temp

        cmd = _encode_command(power, mode, fan, temp)
        pulses = _command_to_pulses(cmd)
        bl_data = pulses_to_broadlink(pulses)

        try:
            result = self.bl.send_data(bl_data)
            if result:
                self.power_on = power
                self.current_mode = mode
                self.current_fan = fan
                self.current_temp = temp
                self.save_state()
            return result
        except Exception as e:
            print(f"[IR] Send error: {e}")
            return False

    def send_off(self):
        """Turn off the Whynter"""
        print("[IR] Whynter OFF")
        return self._send_command(power=False)

    def send_on(self):
        """Turn on the Whynter (to current mode/temp/fan)"""
        if self.power_on:
            return True
        print(f"[IR] Whynter ON ({self.current_mode}, {self.current_temp}F, {self.current_fan})")
        return self._send_command(power=True)

    def set_mode(self, target_mode):
        """Set to a specific mode (cool/dehum/fan/heat) and turn on"""
        if target_mode not in MODES:
            print(f"[IR] Invalid mode: {target_mode}")
            return False
        print(f"[IR] Whynter {target_mode} mode")
        return self._send_command(power=True, mode=target_mode)

    def send_cool_on(self):
        """Turn on in cooling mode"""
        return self.set_mode('cool')

    def send_heat_on(self):
        """Turn on in heating mode"""
        return self.set_mode('heat')

    def send_dehum_on(self):
        """Turn on in dehumidifier mode"""
        return self.set_mode('dehum')

    def send_fan_on(self):
        """Turn on in fan-only mode"""
        return self.set_mode('fan')

    def set_temperature(self, target_temp):
        """Set temperature (sends full state command)"""
        if target_temp < MIN_TEMP or target_temp > MAX_TEMP:
            print(f"[IR] Temp {target_temp} out of range ({MIN_TEMP}-{MAX_TEMP})")
            return False
        print(f"[IR] Set temp {target_temp}F")
        return self._send_command(power=True, temp=target_temp)

    def set_fan_speed(self, target_fan):
        """Set fan speed (auto/low/med/high)"""
        if target_fan not in FAN_SPEEDS:
            print(f"[IR] Invalid fan speed: {target_fan}")
            return False
        print(f"[IR] Set fan {target_fan}")
        return self._send_command(power=True, fan=target_fan)

    def set_cooling(self, target_temp, fan_speed='auto'):
        """Set to cooling mode at specific temperature and fan speed"""
        print(f"[IR] Cooling: {target_temp}F, fan={fan_speed}")
        return self._send_command(power=True, mode='cool', temp=target_temp, fan=fan_speed)

    def set_heating(self, target_temp, fan_speed='auto'):
        """Set to heating mode at specific temperature and fan speed"""
        print(f"[IR] Heating: {target_temp}F, fan={fan_speed}")
        return self._send_command(power=True, mode='heat', temp=target_temp, fan=fan_speed)

    def achieve_state(self, power=None, mode=None, temp=None, fan=None):
        """Set the Whynter to an exact state in a single command"""
        if power is False:
            return self.send_off()
        p = power if power is not None else self.power_on
        return self._send_command(power=p, mode=mode, temp=temp, fan=fan)

    def get_codes(self):
        """Get list of available commands (protocol-based, always available)"""
        return ['power', 'cool', 'heat', 'dehum', 'fan', 'temp', 'fan_speed']

    def get_status(self):
        """Get IR status for API"""
        return {
            'protocol': 'whynter_arc14sh',
            'power_on': self.power_on,
            'current_mode': self.current_mode,
            'current_temp': self.current_temp,
            'current_fan': self.current_fan,
            'modes': MODES,
            'fan_speeds': FAN_SPEEDS,
            'temp_range': {'min': MIN_TEMP, 'max': MAX_TEMP}
        }
