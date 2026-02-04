# Whynter ARC-14SH IR Controller
# ================================
# IR send/receive for portable AC/Heatpump control
# Supports learning IR codes from the original remote
# Uses single data pin for both TX and RX

from machine import Pin, PWM
from esp32 import RMT
import time
import json
import config

# File to store learned IR codes
IR_CODES_FILE = "ir_codes.json"
IR_STATE_FILE = "ir_state.json"

# Whynter mode cycle order (pressing MODE button cycles through these)
MODES = ['cool', 'dehum', 'fan', 'heat']

# Fan speed cycle order (pressing FAN button cycles through these)
FAN_SPEEDS = ['auto', 'low', 'med', 'high']

# Temperature range for Whynter units
MIN_TEMP = 61  # Fahrenheit
MAX_TEMP = 89  # Fahrenheit


class WhynterIR:
    """IR transmitter/receiver for Whynter portable AC"""

    CARRIER_FREQ = 38000  # 38kHz carrier

    def __init__(self, tx_pin=None, rx_pin=None):
        # Separate pins for TX and RX modules
        if tx_pin is None:
            tx_pin = config.IR_LED_PIN
        if rx_pin is None:
            rx_pin = config.IR_RECEIVER_PIN

        self.tx_pin_num = tx_pin
        self.rx_pin_num = rx_pin

        # Initialize TX pin (for transmitting to Whynter)
        self.tx_pin = Pin(tx_pin, Pin.OUT)
        self.tx_pin.value(0)

        # Initialize RMT for hardware-timed IR transmission
        # RMT(channel, pin, clock_div, tx_carrier=(freq, duty_percent, level))
        # duty_percent=50 provides good brightness with transistor driver
        self.rmt = RMT(0, pin=self.tx_pin, clock_div=80, tx_carrier=(self.CARRIER_FREQ, 50, 1))

        # Initialize RX pin (for learning from remote)
        self.rx_pin = Pin(rx_pin, Pin.IN)

        self.pwm = None

        # Learned codes storage
        self.codes = {}
        self.load_codes()

        # Track current portable AC state
        self.current_mode = 'cool'  # Default assumption
        self.power_on = False
        self.current_temp = 72  # Default temp setpoint
        self.current_fan = 'auto'  # Default fan speed
        self.load_state()

    def load_codes(self):
        """Load IR codes from file"""
        try:
            with open(IR_CODES_FILE, 'r') as f:
                self.codes = json.load(f)
                print(f"[IR] Loaded {len(self.codes)} codes")
        except:
            print("[IR] No saved codes, starting fresh")
            self.codes = {}

    def save_codes(self):
        """Save IR codes to file"""
        try:
            with open(IR_CODES_FILE, 'w') as f:
                json.dump(self.codes, f)
            print(f"[IR] Saved {len(self.codes)} codes")
        except Exception as e:
            print(f"[IR] Save error: {e}")

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
            print("[IR] No saved state, assuming defaults")

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


    def _send_raw(self, timings):
        """Send raw timing sequence [mark, space, mark, space, ...] using RMT hardware.
        Uses ESP32's RMT peripheral for precise timing with 38kHz carrier."""
        if not timings or len(timings) < 4:
            print("[IR] No valid timings to send")
            return False

        # Use ESP32 RMT for hardware-timed transmission
        # RMT provides precise timing and automatic carrier generation
        try:
            self.rmt.write_pulses(tuple(timings))
            return True
        except Exception as e:
            print(f"[IR] Transmission error: {e}")
            return False

    def capture(self, timeout_ms=10000):
        """Capture IR signal from remote control using RX pin"""
        print("[IR] Point remote at receiver and press button...")

        timings = []
        last_change = time.ticks_us()
        last_value = self.rx_pin.value()
        start = time.ticks_ms()

        # Wait for first transition (signal start)
        while self.rx_pin.value() == last_value:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                print("[IR] Timeout waiting for signal")
                return None

        # Record start
        last_change = time.ticks_us()
        last_value = self.rx_pin.value()

        # Capture transitions
        while True:
            current = self.rx_pin.value()
            now = time.ticks_us()

            if current != last_value:
                duration = time.ticks_diff(now, last_change)
                timings.append(duration)
                last_change = now
                last_value = current

            # End capture after gap (no transitions for 50ms)
            gap = time.ticks_diff(now, last_change)
            if gap > 50000 and len(timings) > 10:
                break

            # Timeout
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                break

        if len(timings) < 10:
            print("[IR] No valid signal captured")
            return None

        print(f"[IR] Captured {len(timings)} timing values")
        return timings

    def learn(self, code_name, timeout_ms=10000):
        """Learn and save an IR code"""
        timings = self.capture(timeout_ms)
        if timings:
            self.codes[code_name] = timings
            self.save_codes()
            print(f"[IR] Learned '{code_name}' ({len(timings)} pulses)")
            return True
        return False

    def send(self, code_name):
        """Send a learned IR code"""
        if code_name not in self.codes:
            print(f"[IR] Unknown code: {code_name}")
            return False

        timings = self.codes[code_name]
        print(f"[IR] Sending '{code_name}'")
        return self._send_raw(timings)

    def send_off(self):
        """Send power off command"""
        if self.send('power'):
            self.power_on = False
            self.save_state()
            return True
        return False

    def send_on(self):
        """Turn on (to current mode)"""
        if not self.power_on:
            if self.send('power'):
                self.power_on = True
                self.save_state()
                return True
            return False
        return True  # Already on

    def set_mode(self, target_mode):
        """Cycle to a specific mode (cool/dehum/fan/heat)"""
        if target_mode not in MODES:
            print(f"[IR] Invalid mode: {target_mode}")
            return False

        if 'mode' not in self.codes:
            print("[IR] Mode button not learned - learn 'mode' first")
            return False

        # Turn on first if off - unit restores last mode used
        if not self.power_on:
            if not self.send_on():
                return False
            time.sleep(0.5)

        # Calculate how many presses needed to reach target
        current_idx = MODES.index(self.current_mode)
        target_idx = MODES.index(target_mode)
        presses = (target_idx - current_idx) % len(MODES)

        if presses == 0:
            print(f"[IR] Already in {target_mode} mode")
            return True

        print(f"[IR] Cycling from {self.current_mode} to {target_mode} ({presses} presses)")

        for i in range(presses):
            self.send('mode')
            time.sleep(0.3)  # Wait between presses

        self.current_mode = target_mode
        self.save_state()
        return True

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
        """Set temperature to specific value"""
        if target_temp < MIN_TEMP or target_temp > MAX_TEMP:
            print(f"[IR] Temp {target_temp} out of range ({MIN_TEMP}-{MAX_TEMP})")
            return False

        if 'temp_up' not in self.codes or 'temp_down' not in self.codes:
            print("[IR] Temperature buttons not learned - learn 'temp_up' and 'temp_down' first")
            return False

        # Turn on first if off
        if not self.power_on:
            if not self.send_on():
                return False
            time.sleep(0.5)

        # Calculate how many button presses needed
        diff = target_temp - self.current_temp

        if diff == 0:
            print(f"[IR] Already at {target_temp}°F")
            return True

        button = 'temp_up' if diff > 0 else 'temp_down'
        presses = abs(diff)

        print(f"[IR] Setting temp from {self.current_temp}°F to {target_temp}°F ({presses} presses)")

        for i in range(presses):
            self.send(button)
            time.sleep(0.3)  # Wait between presses

        self.current_temp = target_temp
        self.save_state()
        return True

    def set_fan_speed(self, target_fan):
        """Set fan speed (auto, low, med, high)"""
        if target_fan not in FAN_SPEEDS:
            print(f"[IR] Invalid fan speed: {target_fan}")
            return False

        if 'fan' not in self.codes:
            print("[IR] Fan button not learned - learn 'fan' first")
            return False

        # Turn on first if off
        if not self.power_on:
            if not self.send_on():
                return False
            time.sleep(0.5)

        # Calculate how many presses needed to reach target
        current_idx = FAN_SPEEDS.index(self.current_fan)
        target_idx = FAN_SPEEDS.index(target_fan)
        presses = (target_idx - current_idx) % len(FAN_SPEEDS)

        if presses == 0:
            print(f"[IR] Already at {target_fan} fan speed")
            return True

        print(f"[IR] Setting fan from {self.current_fan} to {target_fan} ({presses} presses)")

        for i in range(presses):
            self.send('fan')
            time.sleep(0.3)  # Wait between presses

        self.current_fan = target_fan
        self.save_state()
        return True

    def set_cooling(self, target_temp, fan_speed='auto'):
        """Set to cooling mode at specific temperature and fan speed"""
        print(f"[IR] Setting cooling: {target_temp}°F, fan={fan_speed}")

        # Set mode first
        if not self.set_mode('cool'):
            return False
        time.sleep(0.5)

        # Set temperature
        if not self.set_temperature(target_temp):
            return False
        time.sleep(0.5)

        # Set fan speed
        if not self.set_fan_speed(fan_speed):
            return False

        print(f"[IR] Cooling configured: {target_temp}°F, {fan_speed} fan")
        return True

    def set_heating(self, target_temp, fan_speed='auto'):
        """Set to heating mode at specific temperature and fan speed"""
        print(f"[IR] Setting heating: {target_temp}°F, fan={fan_speed}")

        # Set mode first
        if not self.set_mode('heat'):
            return False
        time.sleep(0.5)

        # Set temperature
        if not self.set_temperature(target_temp):
            return False
        time.sleep(0.5)

        # Set fan speed
        if not self.set_fan_speed(fan_speed):
            return False

        print(f"[IR] Heating configured: {target_temp}°F, {fan_speed} fan")
        return True

    def achieve_state(self, power=None, mode=None, temp=None, fan=None):
        """
        Achieve a specific state regardless of current state.
        This is the master control method for automatic operation.

        Args:
            power: True/False or None to leave unchanged
            mode: 'cool'/'heat'/'fan'/'dehum' or None
            temp: Target temperature or None
            fan: Target fan speed or None
        """
        print(f"[IR] Achieving state: power={power}, mode={mode}, temp={temp}, fan={fan}")

        # Handle power off
        if power is False:
            return self.send_off()

        # Handle power on
        if power is True and not self.power_on:
            if not self.send_on():
                return False
            time.sleep(0.5)

        # Set mode if specified
        if mode is not None and mode != self.current_mode:
            if not self.set_mode(mode):
                return False
            time.sleep(0.5)

        # Set temperature if specified
        if temp is not None and temp != self.current_temp:
            if not self.set_temperature(temp):
                return False
            time.sleep(0.5)

        # Set fan speed if specified
        if fan is not None and fan != self.current_fan:
            if not self.set_fan_speed(fan):
                return False

        print(f"[IR] State achieved successfully")
        return True

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
        """Get IR status for API"""
        return {
            'codes': self.get_codes(),
            'tx_pin': self.tx_pin_num,
            'rx_pin': self.rx_pin_num,
            'power_on': self.power_on,
            'current_mode': self.current_mode,
            'current_temp': self.current_temp,
            'current_fan': self.current_fan,
            'modes': MODES,
            'fan_speeds': FAN_SPEEDS,
            'temp_range': {'min': MIN_TEMP, 'max': MAX_TEMP}
        }
