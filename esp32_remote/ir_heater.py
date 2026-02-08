# Dr. Heater Infrared Heater - IR Controller
# ============================================
# Power on/off control via Broadlink RM4 Mini
# Stores codes in heater_codes.json, state in heater_state.json

import time
import json
from broadlink_client import pulses_to_broadlink, broadlink_to_pulses

HEATER_CODES_FILE = "heater_codes.json"
HEATER_STATE_FILE = "heater_state.json"


class HeaterController:
    """IR controller for Dr. Heater infrared heater"""

    def __init__(self, broadlink_client):
        self.bl = broadlink_client

        self.codes = {}
        self.power_on = False
        self.load_codes()
        self.load_state()
        self._migrate_legacy_codes()

    def _migrate_legacy_codes(self):
        """Migrate heater_power from old ir_codes.json if present"""
        if 'power' in self.codes:
            return  # Already have a power code

        try:
            with open('ir_codes.json', 'r') as f:
                old_codes = json.load(f)
            if 'heater_power' in old_codes:
                self.codes['power'] = old_codes['heater_power']
                self.save_codes()
                # Remove from old file
                del old_codes['heater_power']
                with open('ir_codes.json', 'w') as f:
                    json.dump(old_codes, f)
                print("[Heater] Migrated heater_power from ir_codes.json")
        except:
            pass

    def load_codes(self):
        """Load IR codes from file"""
        try:
            with open(HEATER_CODES_FILE, 'r') as f:
                self.codes = json.load(f)
                print(f"[Heater] Loaded {len(self.codes)} codes")
        except:
            self.codes = {}

    def save_codes(self):
        """Save IR codes to file"""
        try:
            with open(HEATER_CODES_FILE, 'w') as f:
                json.dump(self.codes, f)
        except Exception as e:
            print(f"[Heater] Save error: {e}")

    def load_state(self):
        """Load current state from file"""
        try:
            with open(HEATER_STATE_FILE, 'r') as f:
                state = json.load(f)
                self.power_on = state.get('power', False)
        except:
            pass

    def save_state(self):
        """Save current state to file"""
        try:
            with open(HEATER_STATE_FILE, 'w') as f:
                json.dump({'power': self.power_on}, f)
        except Exception as e:
            print(f"[Heater] State save error: {e}")

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
        """Learn and save an IR code"""
        timings = self.capture(timeout_ms)
        if timings:
            self.codes[code_name] = timings
            self.save_codes()
            print(f"[Heater] Learned '{code_name}' ({len(timings)} pulses)")
            return True
        return False

    def send(self, code_name):
        """Send a learned IR code via Broadlink"""
        if code_name not in self.codes:
            print(f"[Heater] Unknown code: {code_name}")
            return False

        timings = self.codes[code_name]
        print(f"[Heater] Sending '{code_name}'")
        try:
            bl_data = pulses_to_broadlink(timings)
            return self.bl.send_data(bl_data)
        except Exception as e:
            print(f"[Heater] Send error: {e}")
            return False

    def send_power(self):
        """Toggle power on/off"""
        if self.send('power'):
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
        """Check if a code has been learned"""
        return code_name in self.codes

    def get_codes(self):
        """Get list of learned code names"""
        return list(self.codes.keys())

    def delete_code(self, code_name):
        """Delete a learned code"""
        if code_name in self.codes:
            del self.codes[code_name]
            self.save_codes()
            return True
        return False

    def get_status(self):
        """Get status for API"""
        return {
            'codes': self.get_codes(),
            'power_on': self.power_on
        }
