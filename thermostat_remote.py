# Remote Thermostat Controller (ESP32)
# =====================================
# Main ESP32 sends sensor readings + settings to Remote ESP32.
# Remote ESP32 handles all relay control using worst-case temp across zones.
# Main polls Remote for actual relay state (heating/cooling active).

import time
import config


class RemoteThermostatController:
    """ESP32 thermostat that sends readings to Remote ESP32 for multi-zone control"""

    def __init__(self, remote_client):
        self.remote = remote_client

        # Setpoints
        self.heat_setpoint = config.DEFAULT_HEAT_SETPOINT
        self.cool_setpoint = config.DEFAULT_COOL_SETPOINT

        # Operating mode
        self.mode = config.DEFAULT_MODE

        # Humidity setpoint (synced to Remote for auto-dehumidification)
        self.humidity_setpoint = 55

        # Current readings (local ESP32 sensors)
        self.current_temp = None
        self.current_humidity = None
        self.current_pressure = None

        # State tracking (updated from Remote's status)
        self.heating_active = False
        self.cooling_active = False
        self.last_remote_sync = 0
        self.last_temp_send = 0
        self.sync_enabled = True  # Auto-sync Kitchen → Living Room

    def update_readings(self, temp_f, humidity, pressure):
        """Update local sensor readings"""
        self.current_temp = temp_f
        self.current_humidity = humidity
        self.current_pressure = pressure

    def set_mode(self, mode):
        """Set operating mode"""
        if mode in config.MODE_NAMES:
            self.mode = mode
            # Sync to Remote
            self._sync_to_remote()
            if mode == config.MODE_OFF:
                self._all_off()

    def set_heat_setpoint(self, temp):
        """Set heating setpoint"""
        self.heat_setpoint = max(config.MIN_SETPOINT,
                                  min(config.MAX_SETPOINT, temp))
        self._sync_to_remote()

    def set_cool_setpoint(self, temp):
        """Set cooling setpoint"""
        self.cool_setpoint = max(config.MIN_SETPOINT,
                                  min(config.MAX_SETPOINT, temp))
        self._sync_to_remote()

    def set_humidity_setpoint(self, value):
        """Set humidity setpoint for auto-dehumidification"""
        self.humidity_setpoint = max(30, min(80, value))
        self._sync_to_remote()

    def set_schedule_mode(self, mode):
        """Sync scheduler mode to remote ESP32 so it can disable dehum during sleep"""
        try:
            if self.remote and hasattr(self.remote, 'set_schedule_mode'):
                self.remote.set_schedule_mode(mode)
        except Exception as e:
            print(f"Remote schedule_mode sync error: {e}")

    def set_sync_enabled(self, enabled):
        """Enable/disable auto-sync of Kitchen settings to Living Room"""
        self.sync_enabled = enabled
        print(f"Auto-sync {'ON' if enabled else 'OFF'}")
        if enabled:
            self._sync_to_remote()

    def _sync_to_remote(self):
        """Sync settings to Remote (debounced)"""
        if not self.sync_enabled:
            return
        now = time.time()
        if now - self.last_remote_sync < 1:  # Don't sync more than once per second
            return
        self.last_remote_sync = now

        try:
            self.remote.set_mode(self.mode)
            self.remote.set_heat_setpoint(int(self.heat_setpoint))
            self.remote.set_cool_setpoint(int(self.cool_setpoint))
            self.remote.set_humidity_setpoint(int(self.humidity_setpoint))
        except Exception as e:
            print(f"Remote sync error: {e}")

    def run_control_loop(self):
        """Send kitchen temp to Remote and poll relay state.
        Remote uses worst-case temp across zones for all relay decisions."""
        if self.current_temp is None:
            return

        now = time.time()

        # Send kitchen temperature to Remote every 15 seconds
        # Response includes full status — update heating/cooling state from it
        if now - self.last_temp_send >= 15:
            try:
                status = self.remote.set_remote_temp(self.current_temp)
                if status:
                    self.heating_active = status.get('heating_active', False)
                    self.cooling_active = status.get('cooling_active', False)
            except Exception as e:
                print(f"Remote temp send error: {e}")
            self.last_temp_send = now

        # Periodic re-sync to Remote (handles Remote reboots)
        if now - self.last_remote_sync >= 60:
            self._sync_to_remote()

        # MODE_OFF: ensure Remote is off
        if self.mode == config.MODE_OFF:
            if self.heating_active or self.cooling_active:
                self._all_off()

    def _all_off(self):
        """Turn off all systems via Remote"""
        try:
            self.remote.set_furnace(False)
            self.remote.set_mode(config.MODE_OFF)
        except Exception as e:
            print(f"Remote all-off error: {e}")
        self.heating_active = False
        self.cooling_active = False

    def get_status(self):
        """Get current status as dict"""
        from env import get_env
        return {
            'temp': self.current_temp,
            'humidity': self.current_humidity,
            'pressure': self.current_pressure,
            'mode': self.mode,
            'mode_name': config.MODE_NAMES.get(self.mode, "?"),
            'heat_setpoint': self.heat_setpoint,
            'cool_setpoint': self.cool_setpoint,
            'heating_active': self.heating_active,
            'cooling_active': self.cooling_active,
            'sync_enabled': self.sync_enabled,
            'env': get_env(),
            'dry_run': config.DRY_RUN,
            'debug': config.DEBUG
        }
