# Remote Thermostat Controller (ESP32)
# =====================================
# Controls remote device's relays/IR remotely via API
# ESP32 is the brain, remote ESP32 is the actuator

import time
import config


class RemoteThermostatController:
    """ESP32 thermostat that controls Pico remotely"""

    def __init__(self, pico_client):
        self.pico = pico_client

        # Setpoints
        self.heat_setpoint = config.DEFAULT_HEAT_SETPOINT
        self.cool_setpoint = config.DEFAULT_COOL_SETPOINT

        # Operating mode
        self.mode = config.MODE_OFF

        # Cooling system selection
        self.cool_system = config.COOL_SYSTEM_ROOFTOP

        # Current readings (local ESP32 sensors)
        self.current_temp = None
        self.current_humidity = None
        self.current_pressure = None

        # State tracking
        self.heating_active = False
        self.cooling_active = False
        self.last_state_change = 0
        self.last_pico_sync = 0

    def update_readings(self, temp_f, humidity, pressure):
        """Update local sensor readings"""
        self.current_temp = temp_f
        self.current_humidity = humidity
        self.current_pressure = pressure

    def set_mode(self, mode):
        """Set operating mode"""
        if mode in config.MODE_NAMES:
            self.mode = mode
            # Sync to Pico
            self._sync_to_pico()
            if mode == config.MODE_OFF:
                self._all_off()

    def set_heat_setpoint(self, temp):
        """Set heating setpoint"""
        self.heat_setpoint = max(config.MIN_SETPOINT,
                                  min(config.MAX_SETPOINT, temp))
        self._sync_to_pico()

    def set_cool_setpoint(self, temp):
        """Set cooling setpoint"""
        self.cool_setpoint = max(config.MIN_SETPOINT,
                                  min(config.MAX_SETPOINT, temp))
        self._sync_to_pico()

    def set_cool_system(self, system):
        """Set which cooling system to use"""
        if system in config.COOL_SYSTEM_NAMES:
            self.cool_system = system

    def _can_change_state(self):
        """Check if enough time has passed since last state change"""
        return (time.time() - self.last_state_change) >= config.MIN_CYCLE_TIME

    def _sync_to_pico(self):
        """Sync settings to Pico (debounced)"""
        now = time.time()
        if now - self.last_pico_sync < 1:  # Don't sync more than once per second
            return
        self.last_pico_sync = now

        try:
            self.pico.set_mode(self.mode)
            self.pico.set_heat_setpoint(int(self.heat_setpoint))
            self.pico.set_cool_setpoint(int(self.cool_setpoint))
        except Exception as e:
            print(f"Pico sync error: {e}")

    def run_control_loop(self):
        """Main control logic - monitors and sends commands to Pico"""
        if self.current_temp is None:
            return

        if self.mode == config.MODE_OFF:
            if self.heating_active or self.cooling_active:
                self._all_off()
            return

        if self.mode == config.MODE_HEAT:
            self._control_heat()
        elif self.mode == config.MODE_COOL:
            self._control_cool()
        elif self.mode == config.MODE_AUTO:
            self._control_auto()

    def _control_heat(self):
        """Heating control with hysteresis"""
        if self.heating_active:
            if self.current_temp >= self.heat_setpoint:
                if self._can_change_state():
                    self._heat_off()
        else:
            if self.current_temp <= (self.heat_setpoint - config.HYSTERESIS):
                if self._can_change_state():
                    self._heat_on()

    def _control_cool(self):
        """Cooling control with hysteresis"""
        if self.cooling_active:
            if self.current_temp <= self.cool_setpoint:
                if self._can_change_state():
                    self._cool_off()
        else:
            if self.current_temp >= (self.cool_setpoint + config.HYSTERESIS):
                if self._can_change_state():
                    self._cool_on()

    def _control_auto(self):
        """Auto mode - heat or cool as needed"""
        if self.current_temp <= (self.heat_setpoint - config.HYSTERESIS):
            if not self.heating_active and self._can_change_state():
                self._cool_off()
                self._heat_on()
        elif self.current_temp >= self.heat_setpoint and self.heating_active:
            if self._can_change_state():
                self._heat_off()

        if self.current_temp >= (self.cool_setpoint + config.HYSTERESIS):
            if not self.cooling_active and self._can_change_state():
                self._heat_off()
                self._cool_on()
        elif self.current_temp <= self.cool_setpoint and self.cooling_active:
            if self._can_change_state():
                self._cool_off()

    def _heat_on(self):
        """Turn on heating via Pico"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}HEAT ON (temp: {self.current_temp:.1f}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            try:
                self.remote.set_furnace(True)
            except Exception as e:
                print(f"Remote furnace error: {e}")
        self.heating_active = True
        self.last_state_change = time.time()

    def _heat_off(self):
        """Turn off heating via Pico"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}HEAT OFF (temp: {self.current_temp:.1f}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            try:
                self.remote.set_furnace(False)
            except Exception as e:
                print(f"Remote furnace error: {e}")
        self.heating_active = False
        self.last_state_change = time.time()

    def _cool_on(self):
        """Turn on cooling via Pico"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}COOL ON (temp: {self.current_temp:.1f}F, setpoint: {self.cool_setpoint}F)")
        if not config.DRY_RUN:
            try:
                self.remote.set_rooftop(True)
            except Exception as e:
                print(f"Remote rooftop error: {e}")
        self.cooling_active = True
        self.last_state_change = time.time()

    def _cool_off(self):
        """Turn off cooling via Pico"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}COOL OFF (temp: {self.current_temp:.1f}F, setpoint: {self.cool_setpoint}F)")
        if not config.DRY_RUN:
            try:
                self.remote.set_rooftop(False)
            except Exception as e:
                print(f"Remote rooftop error: {e}")
        self.cooling_active = False
        self.last_state_change = time.time()

    def _all_off(self):
        """Turn off all systems via Pico"""
        if self.heating_active or self.cooling_active:
            if not config.DRY_RUN:
                try:
                    self.remote.set_furnace(False)
                    self.remote.set_rooftop(False)
                except Exception as e:
                    print(f"Remote all-off error: {e}")
            self.heating_active = False
            self.cooling_active = False
            self.last_state_change = time.time()

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
            'cool_system': self.cool_system,
            'cool_system_name': config.COOL_SYSTEM_NAMES.get(self.cool_system, "?"),
            'env': get_env(),
            'dry_run': config.DRY_RUN,
            'debug': config.DEBUG
        }
