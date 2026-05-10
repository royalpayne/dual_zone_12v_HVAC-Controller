# ESP32 Remote - Thermostat Controller
# Handles heating/cooling with fan speed control for Dometic Brisk II rooftop AC
# Furnace: relay contact closure (dry contact)
# Rooftop AC: 4-ch relay module switches 120VAC directly to compressor + fan (no Dometic control box)
# Freeze protection: DS18B20 on evaporator coil + bimetal thermal cutout (hardware backup)

from machine import Pin
import time
import config
from rgb_led import RGBStatusLED


class ThermostatController:
    def __init__(self):
        # Setpoints
        self.heat_setpoint = config.DEFAULT_HEAT_SETPOINT
        self.cool_setpoint = config.DEFAULT_COOL_SETPOINT

        # Operating mode
        self.mode = config.MODE_OFF

        # Current readings (BME280)
        self.current_temp = None
        self.current_humidity = None
        self.current_pressure = None

        # Broadlink HTS2 sensor readings
        self.bl_temp = None
        self.bl_humidity = None

        # State tracking
        self.heating_active = False
        self.cooling_active = False
        self.fan_only = False
        self.fan_speed = config.FAN_AUTO
        self.whynter_mode = 0  # 0=off, 1=cool
        self.dehum_active = False  # True when Whynter running for dehumidification
        self.dehum_trigger_time = 0   # When humidity first exceeded setpoint (sustained check)
        self.dehum_start_time = 0     # When dehum actually started (min run time)
        self.dehum_stop_time = 0      # When dehum stopped (min off time)
        self.humidity_setpoint = config.HUMIDITY_SETPOINT
        self.schedule_mode = 'home'  # 'home', 'away', 'sleep' — synced from main unit
        self.heater_mode = 0  # 0=off, 1=on (IR heater)
        self.last_heat_change = 0
        self.last_cool_change = 0
        self.last_whynter_change = 0
        self.last_heater_change = 0
        self.last_compressor_off = 0  # For short-cycle protection
        self.fan_post_run_until = 0   # Fan post-run timer
        self.cooling_start_time = 0   # When rooftop AC started cooling
        self.cooling_start_temp = None  # Temp when rooftop AC started
        self.boost_off_time = 0        # When Whynter boost last turned off (cooldown)
        self.boost_active = False         # True when Whynter running specifically for cooling boost

        # Multi-zone: Main ESP32 sends its temperature for either-area control
        self.remote_temp = None        # Main ESP32 temperature reading (°F)
        self.remote_temp_time = 0      # Timestamp of last remote temp update

        # Evaporator freeze protection (DS18B20 sensor)
        self.evap_temp = None          # Evaporator coil temperature (°F)
        self.freeze_lockout = False    # True = compressor locked out due to freeze

        # Relay polarity: Active LOW (0=ON, 1=OFF) or Active HIGH (1=ON, 0=OFF)
        self._relay_invert = getattr(config, 'RELAY_ACTIVE_LOW', False)
        off_val = 1 if self._relay_invert else 0
        self.relay_furnace = Pin(config.RELAY_FURNACE_PIN, Pin.OUT, value=off_val)
        self.relay_compressor = Pin(config.RELAY_COMPRESSOR_PIN, Pin.OUT, value=off_val)
        self.relay_fan_low = Pin(config.RELAY_FAN_LOW_PIN, Pin.OUT, value=off_val)
        self.relay_fan_high = Pin(config.RELAY_FAN_HIGH_PIN, Pin.OUT, value=off_val)

        # IR controllers (set later if available)
        self.whynter = None  # Whynter portable AC (via Broadlink)
        self.heater = None   # Dr. Heater (via Broadlink)

        # RGB LED for status indication
        try:
            self.rgb_led = RGBStatusLED()
            print("RGB LED initialized")
        except Exception as e:
            print(f"RGB LED init failed: {e}")
            self.rgb_led = None

    def _relay_on(self, pin):
        """Set relay ON (handles Active LOW inversion)"""
        pin.value(0 if self._relay_invert else 1)

    def _relay_off(self, pin):
        """Set relay OFF (handles Active LOW inversion)"""
        pin.value(1 if self._relay_invert else 0)

    def _relay_is_on(self, pin):
        """Check if relay is ON (handles Active LOW inversion)"""
        return pin.value() == (0 if self._relay_invert else 1)

    def set_ir_transmitter(self, whynter_ir):
        """Attach Whynter IR controller"""
        self.whynter = whynter_ir

    def set_heater_controller(self, heater_ctrl):
        """Attach Dr. Heater IR controller"""
        self.heater = heater_ctrl

    def update_readings(self, temp_f, humidity, pressure):
        """Update BME280 sensor readings. Falls back to remote (kitchen) temp if local sensor is unavailable."""
        if temp_f is not None:
            self.current_temp = temp_f
        elif self.remote_temp is not None:
            # Local sensor dead — use kitchen temp as fallback so control loop keeps working
            self.current_temp = self.remote_temp
            print(f"Sensor fallback: using kitchen temp {self.remote_temp:.1f}F")
        else:
            self.current_temp = None
        self.current_humidity = humidity  # humidity stays None if sensor dead
        self.current_pressure = pressure

    def update_evap_temp(self, temp_f):
        """Update evaporator coil temperature from DS18B20 freeze sensor."""
        self.evap_temp = temp_f
        if temp_f is None:
            return
        # Freeze detected: immediately cut compressor
        if temp_f <= config.FREEZE_THRESHOLD:
            if not self.freeze_lockout:
                self.freeze_lockout = True
                print(f"FREEZE LOCKOUT: evap {temp_f:.1f}F <= {config.FREEZE_THRESHOLD}F")
                if self.cooling_active:
                    self._cool_off()
        # Recovery: clear lockout when evaporator warms up
        elif temp_f >= config.FREEZE_RECOVERY:
            if self.freeze_lockout:
                self.freeze_lockout = False
                print(f"Freeze lockout cleared: evap {temp_f:.1f}F >= {config.FREEZE_RECOVERY}F")

    def update_bl_readings(self, temp_c, humidity):
        """Update Broadlink HTS2 sensor readings (with calibration offsets)"""
        if temp_c is not None:
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            temp_f += getattr(config, 'BL_TEMP_OFFSET', 0.0)
            self.bl_temp = round(temp_f, 1)
        else:
            self.bl_temp = None
        if humidity is not None:
            humidity += getattr(config, 'BL_HUMIDITY_OFFSET', 0.0)
            self.bl_humidity = round(humidity, 1)
        else:
            self.bl_humidity = None

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

    def set_humidity_setpoint(self, value):
        """Set humidity setpoint for dehumidification (% RH)"""
        self.humidity_setpoint = max(30, min(80, value))

    def set_schedule_mode(self, mode):
        """Set schedule mode synced from main unit ('home', 'away', 'sleep').
        Dehumidification is disabled during sleep mode."""
        if mode != self.schedule_mode:
            print(f"[remote] Schedule mode: {self.schedule_mode} -> {mode}")
        self.schedule_mode = mode

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

    # Whynter mode mapping: thermostat mode number → IR mode string
    WHYNTER_MODES = {0: 'off', 1: 'cool', 2: 'dehum', 3: 'fan', 4: 'heat'}
    WHYNTER_MODE_NAMES = {0: 'Off', 1: 'Cool', 2: 'Dehum', 3: 'Fan', 4: 'Heat'}

    def set_whynter_mode(self, mode):
        """Set Whynter portable AC mode (0=off, 1=cool, 2=dehum, 3=fan, 4=heat)"""
        if mode not in self.WHYNTER_MODES:
            print(f"Invalid Whynter mode: {mode}")
            return

        if mode == self.whynter_mode:
            print(f"Whynter already in mode {mode} ({self.WHYNTER_MODES[mode]})")
            return

        if not self.whynter:
            print("No Whynter controller available")
            return

        mode_name = self.WHYNTER_MODES[mode]
        success = config.DRY_RUN  # DRY_RUN always "succeeds"
        if mode == 0:
            print("Setting Whynter to OFF")
            if not config.DRY_RUN:
                success = self.whynter.send_off()
        else:
            print(f"Setting Whynter to {mode_name.upper()} mode")
            if not config.DRY_RUN:
                success = self.whynter.set_mode(mode_name)

        if success:
            self.whynter_mode = mode
            self.last_whynter_change = time.time()
        else:
            print("Whynter IR send failed — state not updated")

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
        success = config.DRY_RUN  # DRY_RUN always "succeeds"
        if not config.DRY_RUN:
            if mode == 1:
                success = self.heater.send_on()
            else:
                success = self.heater.send_off()

        if success:
            self.heater_mode = mode
            self.last_heater_change = time.time()
        else:
            print("Heater IR send failed — state not updated")

    def _can_change_heat(self):
        """Check if enough time has passed since last furnace state change"""
        return (time.time() - self.last_heat_change) >= config.MIN_CYCLE_TIME

    def _can_change_cool(self):
        """Check if enough time has passed since last A/C state change"""
        return (time.time() - self.last_cool_change) >= config.MIN_CYCLE_TIME

    def _can_start_compressor(self):
        """Check compressor short-cycle protection and freeze lockout"""
        if self.freeze_lockout:
            return False
        return (time.time() - self.last_compressor_off) >= config.COMPRESSOR_MIN_OFF_TIME

    def _can_change_whynter(self):
        """Check if enough time has passed since last Whynter change"""
        return (time.time() - self.last_whynter_change) >= config.MIN_CYCLE_TIME

    def _apparent_temp(self):
        """Humidity-adjusted apparent temperature for cooling decisions.
        At 50% RH: apparent = actual. Higher humidity feels warmer, lower feels cooler."""
        if self.current_temp is None:
            return None
        if self.current_humidity is None:
            return self.current_temp
        return self.current_temp + (self.current_humidity - 50) * config.HUMIDITY_COMFORT_FACTOR

    def _effective_humidity(self):
        """Average humidity across available sensors for more stable readings."""
        readings = []
        if self.current_humidity is not None:
            readings.append(self.current_humidity)
        if self.bl_humidity is not None:
            readings.append(self.bl_humidity)
        if not readings:
            return None
        return sum(readings) / len(readings)

    # ---- Multi-zone temperature ----

    def set_remote_temp(self, temp_f):
        """Store Main ESP32's temperature reading for multi-zone control"""
        self.remote_temp = temp_f
        self.remote_temp_time = time.time()

    def _remote_temp_if_fresh(self):
        """Return remote temp if fresh (within 120s), else None"""
        if self.remote_temp is None:
            return None
        if time.time() - self.remote_temp_time > 120:
            return None
        return self.remote_temp

    def _effective_cool_temp(self):
        """Worst-case (hottest) temperature across zones for cooling decisions"""
        local = self._apparent_temp()
        remote = self._remote_temp_if_fresh()
        if local is None and remote is None:
            return None
        if local is None:
            return remote
        if remote is None:
            return local
        return max(local, remote)

    def _effective_heat_temp(self):
        """Worst-case (coldest) temperature across zones for heating decisions"""
        local = self.current_temp
        remote = self._remote_temp_if_fresh()
        if local is None and remote is None:
            return None
        if local is None:
            return remote
        if remote is None:
            return local
        return min(local, remote)

    # ---- Fan relay control ----

    def _set_fan(self, speed):
        """Activate a single fan speed relay. Only one active at a time."""
        if speed == config.FAN_AUTO:
            speed = self._auto_fan_speed()

        if config.DRY_RUN:
            return

        # Deactivate all fan relays first (mutual exclusion)
        self._relay_off(self.relay_fan_low)
        self._relay_off(self.relay_fan_high)

        # Activate the requested speed
        if speed == config.FAN_LOW:
            self._relay_on(self.relay_fan_low)
        elif speed == config.FAN_HIGH:
            self._relay_on(self.relay_fan_high)

    def _fan_off(self):
        """Turn off all fan relays"""
        if not config.DRY_RUN:
            self._relay_off(self.relay_fan_low)
            self._relay_off(self.relay_fan_high)

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
            if self.rgb_led:
                self._update_led_status()
            return

        if self.mode == config.MODE_OFF:
            # Mode OFF only kills relays (furnace/compressor/fan), not IR devices.
            # IR devices (Whynter, heater) are manual overrides controlled independently.
            # set_mode(OFF) already called _all_off() on transition.
            if self.heating_active:
                self._heat_off()
            if self.cooling_active:
                self._cool_off()
            if self.rgb_led:
                self._update_led_status()
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

        # Whynter boost: auto-enable portable AC when needed
        if self.cooling_active and self.whynter and self.whynter_mode == 0:
            boost_reason = None
            # Cooldown: don't re-boost within 10 minutes of last boost-off
            if self.boost_off_time > 0 and (now - self.boost_off_time) < config.DEHUM_MIN_OFF_TIME:
                pass  # In cooldown period
            else:
                # Trigger 1: temp far exceeds setpoint
                if self.current_temp >= (self.cool_setpoint + config.BOOST_THRESHOLD):
                    boost_reason = f"temp {self.current_temp:.1f}F > setpoint+{config.BOOST_THRESHOLD}"
                # Trigger 2: rooftop AC stalled (running 10+ min with no temp drop)
                elif (self.cooling_start_temp is not None
                      and now - self.cooling_start_time >= config.BOOST_STALL_TIME
                      and self.current_temp >= self.cooling_start_temp):
                    boost_reason = f"stall: {self.current_temp:.1f}F after {int((now - self.cooling_start_time) / 60)}min (started at {self.cooling_start_temp:.1f}F)"
            if boost_reason and self._can_change_whynter():
                print(f"Whynter boost: {boost_reason}")
                self.set_whynter_mode(1)
                self.boost_active = True
        # Auto-disable Whynter boost when apparent temp comes back within range
        # Only applies when boost_active — avoids killing dehum or manual Whynter use
        elif self.cooling_active and self.whynter and self.boost_active and self.whynter_mode != 0 and not self.dehum_active:
            apparent = self._apparent_temp()
            if apparent is not None and apparent <= (self.cool_setpoint + config.HYSTERESIS):
                if self._can_change_whynter():
                    print(f"Whynter boost off: apparent {apparent:.1f}F <= {self.cool_setpoint + config.HYSTERESIS:.1f}F")
                    self.set_whynter_mode(0)
                    self.boost_active = False
                    # Reset stall baseline so it doesn't immediately re-trigger
                    self.cooling_start_time = now
                    self.cooling_start_temp = self.current_temp
                    self.boost_off_time = now

        # Dehumidification: run Whynter in dehum mode when humidity is high
        self._control_dehum()

        # Update RGB LED status
        if self.rgb_led:
            self._update_led_status()

    def _update_led_status(self):
        """Update RGB LED based on current thermostat state"""
        if not self.rgb_led:
            return

        status = {
            'mode': self.mode,
            'heating_active': self.heating_active,
            'cooling_active': self.cooling_active,
            'fan_only': self.fan_only,
            'dehum_active': self.dehum_active
        }

        # Check for freeze warning or communication errors
        freeze_warning = self.freeze_lockout
        comm_error = False  # Could be set based on Broadlink connection status

        self.rgb_led.update_status(status, freeze_warning, comm_error)

    def _control_dehum(self):
        """Dehumidification control — turns Whynter on in dehum mode and lets
        the Whynter's built-in humidity sensor manage compressor cycling.
        ESP32 only decides when to enable/disable dehum mode based on:
        - Sustained humidity above setpoint (avoids reacting to brief spikes)
        - Temperature guards (too cold, heating active)
        Whynter has a drain hose so no tank-full shutoff concerns."""
        humidity = self._effective_humidity()
        if humidity is None or not self.whynter:
            return

        now = time.time()

        # Never dehumidify during sleep mode — avoid noise disturbance
        if self.schedule_mode == 'sleep':
            if self.dehum_active:
                if self._can_change_whynter():
                    print("Dehum OFF: sleep mode active")
                    self.set_whynter_mode(0)
                    self.dehum_active = False
                    self.dehum_trigger_time = 0
                    self._stop_dehum_fan()
            return

        # Never dehumidify while furnace is heating — they fight each other
        if self.heating_active:
            if self.dehum_active:
                if self._can_change_whynter():
                    print(f"Dehum OFF: heating active, temp {self.current_temp:.1f}F")
                    self.set_whynter_mode(0)
                    self.dehum_active = False
                    self.dehum_trigger_time = 0
            return

        # Don't run dehum if temp is too cold (near heat setpoint or 5°F below cool setpoint)
        if self.current_temp is not None:
            too_cold = (self.current_temp <= (self.heat_setpoint + config.HYSTERESIS)
                        or self.current_temp <= (self.cool_setpoint - 5))
        else:
            too_cold = False

        if not self.dehum_active and self.whynter_mode == 0:
            if too_cold:
                self.dehum_trigger_time = 0
                return

            if humidity > self.humidity_setpoint:
                # Sustained threshold — humidity must stay above setpoint to avoid reacting to spikes
                if self.dehum_trigger_time == 0:
                    self.dehum_trigger_time = now
                    print(f"Dehum trigger: avg humidity {humidity:.1f}% > {self.humidity_setpoint}%, waiting {config.DEHUM_SUSTAINED_TIME}s")
                    return

                elapsed = now - self.dehum_trigger_time
                if elapsed < config.DEHUM_SUSTAINED_TIME:
                    return  # Still waiting

                # Sustained threshold met — turn on Whynter dehum mode and leave it running
                if self._can_change_whynter():
                    print(f"Dehum ON: avg humidity {humidity:.1f}% > {self.humidity_setpoint}% for {int(elapsed)}s — Whynter manages cycling")
                    self.set_whynter_mode(2)  # 2 = dehum mode
                    if self.whynter_mode == 2:
                        self.dehum_active = True
                        self.dehum_trigger_time = 0
                        # Run rooftop fan low to circulate air and equalize zone temps
                        if not self.cooling_active:
                            print("Dehum ON: starting rooftop fan low for air circulation")
                            self.set_fan_speed(config.FAN_LOW)
                            self.fan_only = True
            else:
                # Humidity dropped below setpoint before sustained time — spike passed
                if self.dehum_trigger_time > 0:
                    print(f"Dehum trigger reset: avg humidity {humidity:.1f}% < {self.humidity_setpoint}%")
                    self.dehum_trigger_time = 0

        elif self.dehum_active:
            # Guard: stop if temp is too cold
            if too_cold:
                if self._can_change_whynter():
                    print(f"Dehum OFF: temp {self.current_temp:.1f}F too cold (heat={self.heat_setpoint}F, cool={self.cool_setpoint}F)")
                    self.set_whynter_mode(0)
                    self.dehum_active = False
                    self._stop_dehum_fan()
                    return

            # Turn off only when humidity is well below setpoint — Whynter handles cycling in between
            target = self.humidity_setpoint - config.HUMIDITY_HYSTERESIS
            if humidity < target:
                if self._can_change_whynter():
                    print(f"Dehum OFF: avg humidity {humidity:.1f}% < {target}% — target reached")
                    self.set_whynter_mode(0)
                    self.dehum_active = False
                    self._stop_dehum_fan()

    def _stop_dehum_fan(self):
        """Stop rooftop fan that was started for dehum air circulation.
        Only stops if we started it (fan_only=True) and cooling is not active."""
        if self.fan_only and not self.cooling_active:
            print("Dehum fan OFF: stopping rooftop circulation fan")
            self.set_fan_speed(config.FAN_OFF)
            self.fan_only = False

    def _control_heat(self):
        """Heating control with hysteresis, using worst-case (coldest) zone temp"""
        effective = self._effective_heat_temp()
        if effective is None:
            return
        if self.heating_active:
            if effective >= self.heat_setpoint:
                if self._can_change_heat():
                    self._heat_off()
        else:
            if effective <= (self.heat_setpoint - config.HYSTERESIS):
                if self._can_change_heat():
                    self._heat_on()

    def _control_cool(self):
        """Cooling control with hysteresis, using worst-case (hottest) zone temp"""
        effective = self._effective_cool_temp()
        if effective is None:
            return
        if self.cooling_active:
            if effective <= self.cool_setpoint:
                if self._can_change_cool():
                    self._cool_off()
        else:
            if effective >= (self.cool_setpoint + config.HYSTERESIS):
                if self._can_change_cool() and self._can_start_compressor():
                    self._cool_on()

    def _control_auto(self):
        """Auto mode - heat or cool as needed, using worst-case zone temps"""
        # Heating: use coldest zone temp
        heat_temp = self._effective_heat_temp()
        if heat_temp is not None:
            if heat_temp <= (self.heat_setpoint - config.HYSTERESIS):
                if not self.heating_active and self._can_change_heat():
                    self._cool_off()
                    self._heat_on()
            elif heat_temp >= self.heat_setpoint and self.heating_active:
                if self._can_change_heat():
                    self._heat_off()

        # Cooling: use hottest zone temp
        cool_temp = self._effective_cool_temp()
        if cool_temp is None:
            return
        if cool_temp >= (self.cool_setpoint + config.HYSTERESIS):
            if not self.cooling_active and self._can_change_cool() and self._can_start_compressor():
                self._heat_off()
                self._cool_on()
        elif cool_temp <= self.cool_setpoint and self.cooling_active:
            if self._can_change_cool():
                self._cool_off()

    # ---- Heat on/off ----

    def _heat_on(self):
        """Turn on furnace and IR heater"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        remote_str = f", kitchen: {self.remote_temp:.1f}" if self.remote_temp is not None else ""
        print(f"{dry_run}HEAT ON (temp: {temp_str}F{remote_str}, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self._relay_on(self.relay_furnace)
        self.heating_active = True
        self.last_heat_change = time.time()
        # Auto-trigger IR heater when furnace turns on
        if self.heater_mode == 0:
            self.set_heater_mode(1)

    def _heat_off(self):
        """Turn off furnace and IR heater"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        remote_str = f", kitchen: {self.remote_temp:.1f}" if self.remote_temp is not None else ""
        print(f"{dry_run}HEAT OFF (temp: {temp_str}F{remote_str}, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self._relay_off(self.relay_furnace)
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
        remote_str = f", kitchen: {self.remote_temp:.1f}" if self.remote_temp is not None else ""
        speed = self.fan_speed if self.fan_speed != config.FAN_OFF else config.FAN_HIGH
        speed_name = config.FAN_NAMES.get(speed, '?')
        apparent = self._apparent_temp()
        apparent_str = f", feels: {apparent:.1f}" if apparent is not None and self.current_humidity is not None else ""
        print(f"{dry_run}COOL ON (temp: {temp_str}F{apparent_str}{remote_str}, setpoint: {self.cool_setpoint}F, fan: {speed_name})")

        # Start fan before compressor
        self._set_fan(speed)

        if not config.DRY_RUN:
            # Fan pre-run delay before compressor
            time.sleep(config.FAN_PRE_RUN)
            self._relay_on(self.relay_compressor)

        self.cooling_active = True
        self.fan_post_run_until = 0  # Cancel any post-run timer
        self.last_cool_change = time.time()
        self.cooling_start_time = time.time()
        self.cooling_start_temp = self.current_temp

    def _cool_off(self):
        """Turn off rooftop AC: compressor first, fan continues for post-run"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        remote_str = f", kitchen: {self.remote_temp:.1f}" if self.remote_temp is not None else ""
        apparent = self._apparent_temp()
        apparent_str = f", feels: {apparent:.1f}" if apparent is not None and self.current_humidity is not None else ""
        print(f"{dry_run}COOL OFF (temp: {temp_str}F{apparent_str}{remote_str}, setpoint: {self.cool_setpoint}F)")

        if not config.DRY_RUN:
            self._relay_off(self.relay_compressor)

        self.cooling_active = False
        self.last_compressor_off = time.time()
        self.last_cool_change = time.time()
        # Auto-turn off Whynter boost when rooftop AC stops (but not if dehumidifying)
        if self.whynter_mode != 0 and not self.dehum_active:
            self.set_whynter_mode(0)
            self.boost_active = False

        # Fan post-run: keep fan going to extract residual cooling
        if not self.fan_only:
            self.fan_post_run_until = time.time() + config.FAN_POST_RUN

    # ---- All off ----

    def _all_off(self):
        """Turn off all systems"""
        if self.heating_active or self.cooling_active or self.fan_only or self.whynter_mode != 0 or self.heater_mode != 0:
            if not config.DRY_RUN:
                self._relay_off(self.relay_furnace)
                self._relay_off(self.relay_compressor)
                self._relay_off(self.relay_fan_low)
                self._relay_off(self.relay_fan_high)
                if self.whynter and self.whynter_mode != 0:
                    self.whynter.send_off()
                if self.heater and self.heater_mode != 0:
                    self.heater.send_off()
            if self.cooling_active:
                self.last_compressor_off = time.time()
            self.heating_active = False
            self.cooling_active = False
            self.fan_only = False
            self.dehum_active = False
            self.dehum_trigger_time = 0
            self.dehum_stop_time = time.time()
            self.fan_post_run_until = 0
            if self.whynter_mode != 0:
                self.whynter_mode = 0
                self.last_whynter_change = time.time()
            if self.heater_mode != 0:
                self.heater_mode = 0
                self.last_heater_change = time.time()
            self.last_heat_change = time.time()
            self.last_cool_change = time.time()

    def force_all_off(self):
        """Force all systems off - sends IR regardless of tracked state"""
        print("FORCE ALL OFF - unconditional shutdown")
        if not config.DRY_RUN:
            # Turn off all relays
            self._relay_off(self.relay_furnace)
            self._relay_off(self.relay_compressor)
            self._relay_off(self.relay_fan_low)
            self._relay_off(self.relay_fan_high)
            # Force IR off - send regardless of tracked state
            if self.whynter:
                self.whynter.send_off()
            if self.heater:
                self.heater.send_force_off()

        # Reset all state
        if self.cooling_active:
            self.last_compressor_off = time.time()
        self.heating_active = False
        self.cooling_active = False
        self.fan_only = False
        self.dehum_active = False
        self.dehum_trigger_time = 0
        self.dehum_stop_time = time.time()
        self.fan_post_run_until = 0
        self.whynter_mode = 0
        self.heater_mode = 0
        self.last_whynter_change = time.time()
        self.last_heater_change = time.time()
        self.last_heat_change = time.time()
        self.last_cool_change = time.time()

    def _furnace_relay(self, on):
        """Direct furnace relay control"""
        if not config.DRY_RUN:
            self._relay_on(self.relay_furnace) if on else self._relay_off(self.relay_furnace)

    def get_status(self):
        """Get current status as dict"""
        heater_names = {0: 'Off', 1: 'On'}
        apparent = self._apparent_temp()
        return {
            'temp': self.current_temp,
            'apparent_temp': round(apparent, 1) if apparent is not None else None,
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
            'humidity_setpoint': self.humidity_setpoint,
            'schedule_mode': self.schedule_mode,
            'dehum_active': self.dehum_active,
            'dehum_waiting': self.dehum_trigger_time > 0,
            'whynter_mode': self.whynter_mode,
            'whynter_mode_name': self.WHYNTER_MODE_NAMES.get(self.whynter_mode, '?'),
            'heater_mode': self.heater_mode,
            'heater_mode_name': heater_names.get(self.heater_mode, '?'),
            'evap_temp': self.evap_temp,
            'freeze_lockout': self.freeze_lockout,
            'bl_temp': self.bl_temp,
            'bl_humidity': self.bl_humidity,
            'remote_temp': self.remote_temp,
            'dry_run': config.DRY_RUN,
            'debug': config.DEBUG
        }

    def set_led_color(self, color_name):
        """Manually set LED color (for testing)"""
        if self.rgb_led:
            self.rgb_led.set_color(color_name)
