# Scheduler - Time-based temperature control
# Supports Home/Away/Sleep modes with weekly programming

import time
import ntptime
import json
import config

class Scheduler:
    def __init__(self):
        # Schedule temps: {mode: (heat, cool)}
        self.schedule_temps = dict(config.SCHEDULE_TEMPS)
        
        # Weekly schedule
        self.weekly_schedule = dict(config.DEFAULT_SCHEDULE)
        
        # State
        self.current_mode = config.SCHEDULE_HOME
        self.schedule_enabled = True
        self.time_synced = False
        self.last_sync = 0
        
        # Hold (temporary override)
        self.hold_active = False
        self.hold_until = None
        self.hold_heat = None
        self.hold_cool = None
    
    def sync_time(self):
        """Sync with NTP server"""
        try:
            ntptime.host = config.NTP_HOST
            ntptime.settime()
            self.time_synced = True
            self.last_sync = time.time()
            print("Time synced")
            return True
        except Exception as e:
            print(f"NTP error: {e}")
            return False
    
    def get_local_time(self):
        """Get local time with timezone"""
        return time.localtime(time.time() + config.TIMEZONE_OFFSET * 3600)
    
    def get_time_str(self):
        """Format: 12:30 PM"""
        t = self.get_local_time()
        h, m = t[3], t[4]
        ap = "AM" if h < 12 else "PM"
        h = h % 12 or 12
        return f"{h}:{m:02d} {ap}"
    
    def get_day_str(self):
        """Get day name"""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return days[self.get_local_time()[6]]
    
    def get_current_mode(self):
        """Get scheduled mode for current time"""
        if not self.schedule_enabled:
            return config.SCHEDULE_HOME
        
        t = self.get_local_time()
        day = t[6]
        now_mins = t[3] * 60 + t[4]
        
        schedule = self.weekly_schedule.get(day, [])
        if not schedule:
            return config.SCHEDULE_HOME
        
        mode = schedule[0][2]
        for h, m, smode in schedule:
            if now_mins >= h * 60 + m:
                mode = smode
        return mode
    
    def update(self):
        """Update scheduler - call every minute"""
        # Resync every 6 hours
        if time.time() - self.last_sync > 21600:
            self.sync_time()
        
        # Check hold expiry
        if self.hold_active and self.hold_until:
            if time.time() >= self.hold_until:
                self.clear_hold()
        
        self.current_mode = self.get_current_mode()
    
    def get_setpoints(self):
        """Get current heat/cool setpoints"""
        if self.hold_active:
            return self.hold_heat, self.hold_cool
        
        if not self.schedule_enabled:
            return config.DEFAULT_HEAT_SETPOINT, config.DEFAULT_COOL_SETPOINT
        
        temps = self.schedule_temps.get(self.current_mode)
        return temps if temps else (config.DEFAULT_HEAT_SETPOINT, config.DEFAULT_COOL_SETPOINT)
    
    def set_hold(self, heat, cool, hours=None):
        """Set temporary hold"""
        self.hold_active = True
        self.hold_heat = heat
        self.hold_cool = cool
        self.hold_until = time.time() + hours * 3600 if hours else None
        print(f"Hold: H={heat} C={cool} hrs={hours}")
    
    def clear_hold(self):
        """Resume schedule"""
        self.hold_active = False
        self.hold_until = None
        self.hold_heat = None
        self.hold_cool = None
        print("Hold cleared")
    
    def set_quick_mode(self, mode, hours=2):
        """Quick switch to Home/Away/Sleep"""
        if mode in self.schedule_temps:
            h, c = self.schedule_temps[mode]
            self.set_hold(h, c, hours)
    
    def set_schedule_temps(self, mode, heat, cool):
        """Update temps for a mode"""
        self.schedule_temps[mode] = (heat, cool)
    
    def set_schedule_entry(self, day, entries):
        """Set schedule for a day: [(hour, min, mode), ...]"""
        self.weekly_schedule[day] = entries
    
    def get_next_change(self):
        """Get minutes until next schedule change"""
        if not self.schedule_enabled:
            return None, None
        
        t = self.get_local_time()
        day = t[6]
        now_mins = t[3] * 60 + t[4]
        
        # Check today
        for h, m, mode in self.weekly_schedule.get(day, []):
            entry_mins = h * 60 + m
            if entry_mins > now_mins:
                return entry_mins - now_mins, config.SCHEDULE_MODE_NAMES.get(mode)
        
        # Next is tomorrow
        tomorrow = (day + 1) % 7
        sched = self.weekly_schedule.get(tomorrow, [])
        if sched:
            h, m, mode = sched[0]
            mins = (1440 - now_mins) + h * 60 + m
            return mins, config.SCHEDULE_MODE_NAMES.get(mode)
        
        return None, None
    
    def get_status(self):
        """Get status dict for API"""
        heat, cool = self.get_setpoints()
        hold_mins = None
        if self.hold_active and self.hold_until:
            remaining = self.hold_until - time.time()
            if remaining > 0:
                hold_mins = int(remaining / 60)
        
        next_mins, next_mode = self.get_next_change()
        
        return {
            'time': self.get_time_str(),
            'day': self.get_day_str(),
            'synced': self.time_synced,
            'sched_on': self.schedule_enabled,
            'sched_mode': self.current_mode,
            'sched_name': config.SCHEDULE_MODE_NAMES.get(self.current_mode, "?"),
            'hold': self.hold_active,
            'hold_mins': hold_mins,
            'heat_sp': heat,
            'cool_sp': cool,
            'next_mins': next_mins,
            'next_mode': next_mode,
            'temps': {
                'home': self.schedule_temps.get(config.SCHEDULE_HOME),
                'away': self.schedule_temps.get(config.SCHEDULE_AWAY),
                'sleep': self.schedule_temps.get(config.SCHEDULE_SLEEP)
            }
        }
    
    def save(self):
        """Save settings to flash"""
        data = {
            'temps': self.schedule_temps,
            'schedule': self.weekly_schedule,
            'enabled': self.schedule_enabled
        }
        try:
            with open('schedule.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def load(self):
        """Load settings from flash"""
        try:
            with open('schedule.json', 'r') as f:
                data = json.load(f)
                self.schedule_temps = data.get('temps', self.schedule_temps)
                self.weekly_schedule = data.get('schedule', self.weekly_schedule)
                self.schedule_enabled = data.get('enabled', True)
        except:
            pass
