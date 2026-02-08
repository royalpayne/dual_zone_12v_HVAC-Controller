# Dr. Infrared Heater (with Humidifier) - IR Controller
# =====================================================
# Uses captured raw IR data via Broadlink RM4 Mini
# Proprietary protocol (not NEC) - codes captured from physical remote

import time
import json
from broadlink_client import pulses_to_broadlink, broadlink_to_pulses

HEATER_STATE_FILE = "heater_state.json"

# Raw Broadlink IR data captured from physical remote
# Proprietary protocol: ~1200us/370us marks, ~7800us group gaps
_RAW_CODES = {
    'power': bytes.fromhex(
        "2600ba00271509000b4507290cff260f280e0d28280f280e0b2a0c2a270f0b2a"
        "0d280d290cff270f270f0c29270e290d0c2a0c2a270e0c2a0c290d290dfe270e"
        "280e0c2a280d290d0d280e2a260f0c290c290c2a0cff270f270f0c292610260f"
        "0d290d28280e0c2b0b2a0b2a0c000100260f270f0b2a270f26100c280d2a270f"
        "0c2a0a2b0b2b0b000100260f270e0d292610270e0d280d2a270e0c2a0d270d2b"
        "0b000100260f270f0c29270f270f0c290c29270f0c2a0c290c2a0c000d05"
    ),
}


class HeaterController:
    """IR controller for Dr. Infrared Heater (humidifier model) via Broadlink"""

    def __init__(self, broadlink_client):
        self.bl = broadlink_client
        self.power_on = False
        self.extra_codes = {}
        self.load_state()
        self._load_extra_codes()

    def load_state(self):
        """Load current state from file"""
        try:
            with open(HEATER_STATE_FILE, 'r') as f:
                state = json.load(f)
                self.power_on = state.get('power', False)
                print(f"[Heater] State: power={self.power_on}")
        except:
            print("[Heater] No saved state, using defaults")

    def save_state(self):
        """Save current state to file"""
        try:
            with open(HEATER_STATE_FILE, 'w') as f:
                json.dump({'power': self.power_on}, f)
        except Exception as e:
            print(f"[Heater] State save error: {e}")

    def _load_extra_codes(self):
        """Load additional learned codes from file"""
        try:
            with open("heater_codes.json", 'r') as f:
                self.extra_codes = json.load(f)
                if self.extra_codes:
                    print(f"[Heater] Loaded {len(self.extra_codes)} extra codes")
        except:
            self.extra_codes = {}

    def _save_extra_codes(self):
        """Save additional learned codes to file"""
        try:
            with open("heater_codes.json", 'w') as f:
                json.dump(self.extra_codes, f)
        except Exception as e:
            print(f"[Heater] Save error: {e}")

    def _send_raw(self, code_name):
        """Send a raw Broadlink IR code"""
        # Check hardcoded codes first, then extra learned codes
        if code_name in _RAW_CODES:
            data = _RAW_CODES[code_name]
        elif code_name in self.extra_codes:
            timings = self.extra_codes[code_name]
            data = pulses_to_broadlink(timings)
        else:
            print(f"[Heater] Unknown code: {code_name}")
            return False

        try:
            return self.bl.send_data(data)
        except Exception as e:
            print(f"[Heater] Send error: {e}")
            return False

    def capture(self, timeout_ms=10000):
        """Capture IR signal via Broadlink learning mode"""
        print("[Heater] Point remote at Broadlink and press button...")
        try:
            self.bl.ensure_connected()
            self.bl.enter_learning()

            start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
                data = self.bl.check_data()
                if data:
                    timings = broadlink_to_pulses(data)
                    print(f"[Heater] Captured {len(timings)} timing values")
                    return timings
                time.sleep(0.5)

            print("[Heater] Timeout waiting for signal")
            return None
        except Exception as e:
            print(f"[Heater] Capture error: {e}")
            return None

    def learn(self, code_name, timeout_ms=10000):
        """Learn and save an additional IR code"""
        timings = self.capture(timeout_ms)
        if timings:
            self.extra_codes[code_name] = timings
            self._save_extra_codes()
            print(f"[Heater] Learned '{code_name}' ({len(timings)} pulses)")
            return True
        return False

    def send_power(self):
        """Toggle power on/off"""
        print(f"[Heater] Power {'OFF' if self.power_on else 'ON'}")
        if self._send_raw('power'):
            self.power_on = not self.power_on
            self.save_state()
            return True
        return False

    def send_on(self):
        """Turn heater on"""
        if not self.power_on:
            return self.send_power()
        return True

    def send_off(self):
        """Turn heater off"""
        if self.power_on:
            return self.send_power()
        return True

    def has_code(self, code_name):
        """Check if a command is available"""
        return code_name in _RAW_CODES or code_name in self.extra_codes

    def get_codes(self):
        """Get list of available commands"""
        return list(_RAW_CODES.keys()) + list(self.extra_codes.keys())

    def get_status(self):
        """Get status for API"""
        return {
            'protocol': 'raw_captured',
            'power_on': self.power_on,
            'commands': self.get_codes()
        }
