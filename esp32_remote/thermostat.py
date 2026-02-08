# ESP32 Remote - Thermostat Controller
# Handles heating/cooling with fan speed control for Dometic Brisk II rooftop AC
# Furnace: relay contact closure (blue wire)
# Rooftop AC: individual relays for compressor + fan low/med/high

from machine import Pin
import time
import config


class ThermostatController:
    def __init__(self):
        # Setpoints
        self.heat_setpoint = config.DEFAULT_HEAT_SETPOINT
        self.cool_setpoint = config.DEFAULT_COOL_SETPOINT

        # Operating mode
        self.mode = config.MODE_OFF

        # Current readings
        self.current_temp = None
        self.current_humidity = None
        self.current_pressure = None

        # State tracking
        self.heating_active = False
        self.cooling_active = False
        self.fan_only = False
        self.fan_speed = config.FAN_AUTO
        self.whynter_mode = 0  # 0=off, 1=cool
        self.heater_mode = 0  # 0=off, 1=on (IR heater)
        self.last_heat_change = 0
        self.last_cool_change = 0
        self.last_whynter_change = 0
        self.last_heater_change = 0
        self.last_compressor_off = 0  # For short-cycle protection
        self.fan_post_run_until = 0   # Fan post-run timer

        # Fan relay polarity helpers (active HIGH vs active LOW)
        self._fan_on_val = 1 if config.FAN_RELAY_ACTIVE_HIGH else 0
        self._fan_off_val = 0 if config.FAN_RELAY_ACTIVE_HIGH else 1

        # Initialize relay pins
        # Furnace/compressor: active LOW (value=1 = OFF)
        self.relay_furnace = Pin(config.RELAY_FURNACE_PIN, Pin.OUT, value=1)
        self.relay_compressor = Pin(config.RELAY_COMPRESSOR_PIN, Pin.OUT, value=1)
        # Fan relays: active HIGH (value=0 = OFF) due to 5V relay module
        self.relay_fan_low = Pin(config.RELAY_FAN_LOW_PIN, Pin.OUT, value=self._fan_off_val)
        self.relay_fan_high = Pin(config.RELAY_FAN_HIGH_PIN, Pin.OUT, value=self._fan_off_val)

        # IR controllers (set later if available)
        self.whynter = None  # Whynter portable AC (via Broadlink)
        self.heater = None   # Dr. Heater (via Broadlink)

    def set_ir_transmitter(self, whynter_ir):
        """Attach Whynter IR controller"""
        self.whynter = whynter_ir

    def set_heater_controller(self, heater_ctrl):
        """Attach Dr. Heater IR controller"""
        self.heater = heater_ctrl

    def update_readings(self, temp_f, humidity, pressure):
        """Update sensor readings"""
        self.current_temp = temp_f
        self.current_humidity = humidity
        self.current_pressure = pressure

    def set_mode(self, mode):
        """Set operating mode"""
        if mode in config.MODE_NAMES:
            self.mode = mode
            if mode == config.MODE_OFF:
                self._all_off()

    def set_heat_setpoint(self, temp):
        """Set heating setpoint"""
        self.heat_setpoint = max(config.MIN_SETPOINT,
                                  min(config.MAX_SETPOINT, temp))

    def set_cool_setpoint(self, temp):
        """Set cooling setpoint"""
        self.cool_setpoint = max(config.MIN_SETPOINT,
                                  min(config.MAX_SETPOINT, temp))

    def set_fan_speed(self, speed):
        """Set fan speed (0=off, 1=low, 2=med, 3=high, 4=auto)"""
        if speed not in config.FAN_NAMES:
            print(f"Invalid fan speed: {speed}")
            return
        self.fan_speed = speed
        # If fan is currently running, update immediately
        if self.cooling_active or self.fan_only:
            self._set_fan(speed)

    def set_fan_only(self, on):
        """Enable/disable fan-only mode (no compressor)"""
        if on and not self.fan_only:
            self.fan_only = True
            speed = self.fan_speed if self.fan_speed != config.FAN_OFF else config.FAN_LOW
            self._set_fan(speed)
            print(f"Fan-only ON ({config.FAN_NAMES.get(speed, '?')})")
        elif not on and self.fan_only:
            self.fan_only = False
            if not self.cooling_active:
                self._fan_off()
            print("Fan-only OFF")

    def set_whynter_mode(self, mode):
        """Set Whynter portable AC mode (0=off, 1=on/cool)"""
        if mode < 0 or mode > 1:
            print(f"Invalid Whynter mode: {mode}")
            return

        if mode == self.whynter_mode:
            print(f"Whynter already in mode {mode}")
            return

        if not self.whynter:
            print("No Whynter controller available")
            return

        if mode == 0:
            print("Setting Whynter to OFF")
            if not config.DRY_RUN:
                self.whynter.send_off()
        else:
            print("Setting Whynter to COOL mode")
            if not config.DRY_RUN:
                self.whynter.set_mode('cool')

        self.whynter_mode = mode
        self.last_whynter_change = time.time()

    def set_heater_mode(self, mode):
        """Set Dr. Heater mode (0=off, 1=on)"""
        if mode < 0 or mode > 1:
            print(f"Invalid heater mode: {mode}")
            return

        if mode == self.heater_mode:
            print(f"Heater already in mode {mode}")
            return

        if not self.heater:
            print("No heater controller available")
            return

        if not self.heater.has_code('power'):
            print("No heater power IR code learned")
            return

        print(f"Setting heater to {'ON' if mode else 'OFF'}")
        if not config.DRY_RUN:
            if mode == 1:
                self.heater.send_on()
            else:
                self.heater.send_off()

        self.heater_mode = mode
        self.last_heater_change = time.time()

    def _can_change_heat(self):
        """Check if enough time has passed since last furnace state change"""
        return (time.time() - self.last_heat_change) >= config.MIN_CYCLE_TIME

    def _can_change_cool(self):
        """Check if enough time has passed since last A/C state change"""
        return (time.time() - self.last_cool_change) >= config.MIN_CYCLE_TIME

    def _can_start_compressor(self):
        """Check compressor short-cycle protection"""
        return (time.time() - self.last_compressor_off) >= config.COMPRESSOR_MIN_OFF_TIME

    def _can_change_whynter(self):
        """Check if enough time has passed since last Whynter change"""
        return (time.time() - self.last_whynter_change) >= config.MIN_CYCLE_TIME

    # ---- Fan relay control ----

    def _set_fan(self, speed):
        """Activate a single fan speed relay. Only one active at a time."""
        if speed == config.FAN_AUTO:
            speed = self._auto_fan_speed()

        if config.DRY_RUN:
            return

        # Deactivate all fan relays first (mutual exclusion)
        self.relay_fan_low.value(self._fan_off_val)
        self.relay_fan_high.value(self._fan_off_val)

        # Activate the requested speed
        if speed == config.FAN_LOW:
            self.relay_fan_low.value(self._fan_on_val)
        elif speed == config.FAN_HIGH:
            self.relay_fan_high.value(self._fan_on_val)

    def _fan_off(self):
        """Turn off all fan relays"""
        if not config.DRY_RUN:
            self.relay_fan_low.value(self._fan_off_val)
            self.relay_fan_high.value(self._fan_off_val)

    def _auto_fan_speed(self):
        """Determine fan speed based on temp delta from setpoint"""
        if self.current_temp is None:
            return config.FAN_HIGH

        if self.cooling_active:
            delta = self.current_temp - self.cool_setpoint
        elif self.heating_active:
            delta = self.heat_setpoint - self.current_temp
        else:
            delta = 0

        if delta > 3:
            return config.FAN_HIGH
        else:
            return config.FAN_LOW

    # ---- Control loop ----

    def run_control_loop(self):
        """Main control logic - call periodically"""
        if self.current_temp is None:
            return

        if self.mode == config.MODE_OFF:
            # Fan-only is a manual override, preserve it when mode=OFF
            if not self.fan_only:
                self._all_off()
            return

        if self.mode == config.MODE_HEAT:
            self._control_heat()
        elif self.mode == config.MODE_COOL:
            self._control_cool()
        elif self.mode == config.MODE_AUTO:
            self._control_auto()

        # Handle fan post-run (fan continues after compressor stops)
        now = time.time()
        if self.fan_post_run_until > 0 and now >= self.fan_post_run_until:
            if not self.cooling_active and not self.fan_only:
                self._fan_off()
            self.fan_post_run_until = 0

        # Update auto fan speed if actively cooling/heating
        if self.fan_speed == config.FAN_AUTO and (self.cooling_active or self.fan_only):
            self._set_fan(config.FAN_AUTO)

    def _control_heat(self):
        """Heating control with hysteresis"""
        if self.heating_active:
            if self.current_temp >= self.heat_setpoint:
                if self._can_change_heat():
                    self._heat_off()
        else:
            if self.current_temp <= (self.heat_setpoint - config.HYSTERESIS):
                if self._can_change_heat():
                    self._heat_on()

    def _control_cool(self):
        """Cooling control with hysteresis"""
        if self.cooling_active:
            if self.current_temp <= self.cool_setpoint:
                if self._can_change_cool():
                    self._cool_off()
        else:
            if self.current_temp >= (self.cool_setpoint + config.HYSTERESIS):
                if self._can_change_cool() and self._can_start_compressor():
                    self._cool_on()

    def _control_auto(self):
        """Auto mode - heat or cool as needed"""
        # Heating logic (furnace is independent, no delay needed vs A/C)
        if self.current_temp <= (self.heat_setpoint - config.HYSTERESIS):
            if not self.heating_active and self._can_change_heat():
                self._cool_off()
                self._heat_on()
        elif self.current_temp >= self.heat_setpoint and self.heating_active:
            if self._can_change_heat():
                self._heat_off()

        # Cooling logic (compressor has its own short-cycle protection)
        if self.current_temp >= (self.cool_setpoint + config.HYSTERESIS):
            if not self.cooling_active and self._can_change_cool() and self._can_start_compressor():
                self._heat_off()
                self._cool_on()
        elif self.current_temp <= self.cool_setpoint and self.cooling_active:
            if self._can_change_cool():
                self._cool_off()

    # ---- Heat on/off ----

    def _heat_on(self):
        """Turn on furnace and IR heater"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}HEAT ON (temp: {temp_str}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_furnace.value(0)  # Active LOW
        self.heating_active = True
        self.last_heat_change = time.time()
        # Auto-trigger IR heater when furnace turns on
        if self.heater_mode == 0:
            self.set_heater_mode(1)

    def _heat_off(self):
        """Turn off furnace and IR heater"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}HEAT OFF (temp: {temp_str}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_furnace.value(1)  # Inactive HIGH
        self.heating_active = False
        self.last_heat_change = time.time()
        # Auto-turn off IR heater when furnace turns off
        if self.heater_mode == 1:
            self.set_heater_mode(0)

    # ---- Cool on/off ----

    def _cool_on(self):
        """Turn on rooftop AC: fan first, then compressor"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        speed = self.fan_speed if self.fan_speed != config.FAN_OFF else config.FAN_HIGH
        speed_name = config.FAN_NAMES.get(speed, '?')
        print(f"{dry_run}COOL ON (temp: {temp_str}F, setpoint: {self.cool_setpoint}F, fan: {speed_name})")

        # Start fan before compressor
        self._set_fan(speed)

        if not config.DRY_RUN:
            # Fan pre-run delay before compressor
            time.sleep(config.FAN_PRE_RUN)
            self.relay_compressor.value(0)  # Active LOW

        self.cooling_active = True
        self.fan_post_run_until = 0  # Cancel any post-run timer
        self.last_cool_change = time.time()

    def _cool_off(self):
        """Turn off rooftop AC: compressor first, fan continues for post-run"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}COOL OFF (temp: {temp_str}F, setpoint: {self.cool_setpoint}F)")

        if not config.DRY_RUN:
            self.relay_compressor.value(1)  # Compressor off first

        self.cooling_active = False
        self.last_compressor_off = time.time()
        self.last_cool_change = time.time()

        # Fan post-run: keep fan going to extract residual cooling
        if not self.fan_only:
            self.fan_post_run_until = time.time() + config.FAN_POST_RUN

    # ---- All off ----

    def _all_off(self):
        """Turn off all systems"""
        if self.heating_active or self.cooling_active or self.fan_only or self.whynter_mode != 0 or self.heater_mode != 0:
            if not config.DRY_RUN:
                self.relay_furnace.value(1)
                self.relay_compressor.value(1)
                self.relay_fan_low.value(self._fan_off_val)
                self.relay_fan_high.value(self._fan_off_val)
                if self.whynter and self.whynter_mode != 0:
                    self.whynter.send_off()
                if self.heater and self.heater_mode != 0:
                    self.heater.send_off()
            if self.cooling_active:
                self.last_compressor_off = time.time()
            self.heating_active = False
            self.cooling_active = False
            self.fan_only = False
            self.fan_post_run_until = 0
            if self.whynter_mode != 0:
                self.whynter_mode = 0
                self.last_whynter_change = time.time()
            if self.heater_mode != 0:
                self.heater_mode = 0
                self.last_heater_change = time.time()
            self.last_heat_change = time.time()
            self.last_cool_change = time.time()

    def _furnace_relay(self, on):
        """Direct furnace relay control"""
        if not config.DRY_RUN:
            self.relay_furnace.value(0 if on else 1)

    def get_status(self):
        """Get current status as dict"""
        whynter_names = {0: 'Off', 1: 'On'}
        heater_names = {0: 'Off', 1: 'On'}
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
            'fan_speed': self.fan_speed,
            'fan_speed_name': config.FAN_NAMES.get(self.fan_speed, '?'),
            'fan_only': self.fan_only,
            'whynter_mode': self.whynter_mode,
            'whynter_mode_name': whynter_names.get(self.whynter_mode, '?'),
            'heater_mode': self.heater_mode,
            'heater_mode_name': heater_names.get(self.heater_mode, '?'),
            'dry_run': config.DRY_RUN,
            'debug': config.DEBUG
        }
