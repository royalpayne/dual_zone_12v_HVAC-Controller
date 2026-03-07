# Nest-Style Scheduler
# ====================
# Time-based scheduling with Home/Away/Sleep modes

import json
import time
import config

# Default schedule file
SCHEDULE_FILE = "schedule.json"

# Preset modes
MODE_HOME = "home"
MODE_AWAY = "away"
MODE_SLEEP = "sleep"

# Default mode temperatures (heat, cool) and humidity threshold
DEFAULT_PRESETS = {
    MODE_HOME: {"heat": 70, "cool": 74, "humidity": 55},
    MODE_AWAY: {"heat": 62, "cool": 80, "humidity": 70},
    MODE_SLEEP: {"heat": 66, "cool": 72, "humidity": 55}
}

# Default schedule (weekday Mon-Fri, weekend Sat-Sun)
DEFAULT_SCHEDULE = {
    "weekday": [
        {"time": "06:00", "mode": MODE_HOME},
        {"time": "08:00", "mode": MODE_AWAY},
        {"time": "17:00", "mode": MODE_HOME},
        {"time": "22:00", "mode": MODE_SLEEP}
    ],
    "weekend": [
        {"time": "08:00", "mode": MODE_HOME},
        {"time": "23:00", "mode": MODE_SLEEP}
    ]
}

DAY_TYPES = ["weekday", "weekend"]


def _is_us_dst(month, mday, wday):
    """Check if US Daylight Saving Time is active.
    DST: 2nd Sunday of March through 1st Sunday of November.
    wday: 0=Monday, 6=Sunday (MicroPython convention)."""
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
    # March: DST starts 2nd Sunday (day 8-14 that's a Sunday)
    if month == 3:
        days_since_sun = (wday + 1) % 7  # Sun=0, Mon=1, ..., Sat=6
        last_sun = mday - days_since_sun
        return last_sun >= 8  # 2nd Sunday is day 8-14
    # November: DST ends 1st Sunday (day 1-7 that's a Sunday)
    if month == 11:
        days_since_sun = (wday + 1) % 7
        last_sun = mday - days_since_sun
        return last_sun < 1  # Before 1st Sunday


class Scheduler:
    def __init__(self, thermostat):
        self.thermostat = thermostat
        self.enabled = False
        self.current_mode = MODE_HOME
        self.hold_until = None  # Temporary hold override
        self.presets = dict(DEFAULT_PRESETS)
        self.schedule = dict(DEFAULT_SCHEDULE)
        self.last_check_minute = -1
        self.load()

    def load(self):
        """Load schedule from file"""
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                self.enabled = data.get("enabled", False)
                self.presets = data.get("presets", dict(DEFAULT_PRESETS))
                self.schedule = data.get("schedule", dict(DEFAULT_SCHEDULE))
                print(f"[scheduler] Loaded schedule, enabled={self.enabled}")
        except:
            print("[scheduler] No saved schedule, using defaults")

    def save(self):
        """Save schedule to file"""
        try:
            data = {
                "enabled": self.enabled,
                "presets": self.presets,
                "schedule": self.schedule
            }
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump(data, f)
            print("[scheduler] Schedule saved")
        except Exception as e:
            print(f"[scheduler] Save error: {e}")

    def set_enabled(self, enabled):
        """Enable/disable scheduler"""
        self.enabled = enabled
        self.save()

    def set_preset(self, mode, heat, cool, humidity=None):
        """Set temperatures for a preset mode (preserves humidity if not given)"""
        if mode in self.presets:
            old_hum = self.presets[mode].get("humidity", 55)
            self.presets[mode] = {"heat": heat, "cool": cool, "humidity": humidity if humidity is not None else old_hum}
            self.save()
            if mode == self.current_mode:
                self._apply_mode(mode)

    def set_hold(self, mode, hours=0):
        """Hold a mode temporarily (0 = cancel hold)"""
        if hours > 0:
            self.hold_until = time.time() + (hours * 3600)
            self.current_mode = mode
            self._apply_mode(mode)
        else:
            self.hold_until = None

    def set_schedule_entry(self, day_type, entries):
        """Set schedule for weekday or weekend"""
        if day_type in DAY_TYPES:
            self.schedule[day_type] = entries
            self.save()

    def get_status(self):
        """Get scheduler status"""
        return {
            "enabled": self.enabled,
            "current_mode": self.current_mode,
            "hold_until": self.hold_until,
            "presets": self.presets,
            "schedule": self.schedule
        }

    def run(self):
        """Check schedule and apply mode - call periodically"""
        if not self.enabled:
            return

        # Check if hold is still active
        if self.hold_until:
            if time.time() >= self.hold_until:
                self.hold_until = None
            else:
                return  # Still holding

        # Get current local time (RTC is UTC, apply timezone + DST)
        try:
            offset = config.TIMEZONE_OFFSET
            # Auto-detect US DST (2nd Sunday Mar 2am → 1st Sunday Nov 2am)
            utc = time.localtime()
            month, mday, wday = utc[1], utc[2], utc[6]  # wday: 0=Mon, 6=Sun
            if _is_us_dst(month, mday, wday):
                offset += 1
            t = time.localtime(time.time() + offset * 3600)
            current_minute = t[3] * 60 + t[4]  # hours * 60 + minutes
            weekday_num = t[6]  # 0=Monday, 6=Sunday
            # Determine if weekday (Mon-Fri: 0-4) or weekend (Sat-Sun: 5-6)
            day_type = "weekday" if weekday_num < 5 else "weekend"
        except:
            return

        # Only check once per minute
        if current_minute == self.last_check_minute:
            return
        self.last_check_minute = current_minute

        # Find current mode based on schedule
        day_schedule = self.schedule.get(day_type, [])
        new_mode = self.current_mode

        for entry in day_schedule:
            entry_time = entry.get("time", "00:00")
            h, m = map(int, entry_time.split(":"))
            entry_minute = h * 60 + m
            if current_minute >= entry_minute:
                new_mode = entry.get("mode", MODE_HOME)

        # Apply if changed
        if new_mode != self.current_mode:
            print(f"[scheduler] Mode change: {self.current_mode} -> {new_mode}")
            self.current_mode = new_mode
            self._apply_mode(new_mode)

    def _apply_mode(self, mode):
        """Apply preset temperatures and humidity to thermostat"""
        preset = self.presets.get(mode, self.presets[MODE_HOME])
        self.thermostat.set_heat_setpoint(preset["heat"])
        self.thermostat.set_cool_setpoint(preset["cool"])
        if "humidity" in preset:
            self.thermostat.set_humidity_setpoint(preset["humidity"])
        print(f"[scheduler] Applied {mode}: heat={preset['heat']}, cool={preset['cool']}, humidity={preset.get('humidity', '?')}")
