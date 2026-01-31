# ESP32 Remote - Thermostat Controller
# Handles heating/cooling with boost mode for portable unit

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
        self.boost_active = False  # Portable unit for extreme temps
        self.last_state_change = 0
        self.last_boost_change = 0

        # Initialize relay pins (active LOW for most relay modules)
        self.relay_furnace = Pin(config.RELAY_FURNACE_PIN, Pin.OUT)
        self.relay_rooftop = Pin(config.RELAY_ROOFTOP_AC_PIN, Pin.OUT)

        # Start with relays OFF (HIGH = inactive for active-low relays)
        self.relay_furnace.value(1)
        self.relay_rooftop.value(1)

        # IR transmitter (set later if available)
        self.ir_transmitter = None

    def set_ir_transmitter(self, ir_tx):
        """Attach IR transmitter for portable AC control"""
        self.ir_transmitter = ir_tx

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

    def _can_change_state(self):
        """Check if enough time has passed since last state change"""
        return (time.time() - self.last_state_change) >= config.MIN_CYCLE_TIME

    def _can_change_boost(self):
        """Check if enough time has passed since last boost change"""
        return (time.time() - self.last_boost_change) >= config.MIN_CYCLE_TIME

    def run_control_loop(self):
        """Main control logic - call periodically"""
        if self.current_temp is None:
            return

        if self.mode == config.MODE_OFF:
            self._all_off()
            return

        if self.mode == config.MODE_HEAT:
            self._control_heat()
        elif self.mode == config.MODE_COOL:
            self._control_cool()
        elif self.mode == config.MODE_AUTO:
            self._control_auto()

        # Check boost mode (portable unit for extreme temps)
        self._control_boost()

    def _control_heat(self):
        """Heating control with hysteresis"""
        if self.heating_active:
            # Turn off when we reach setpoint
            if self.current_temp >= self.heat_setpoint:
                if self._can_change_state():
                    self._heat_off()
        else:
            # Turn on when below setpoint - hysteresis
            if self.current_temp <= (self.heat_setpoint - config.HYSTERESIS):
                if self._can_change_state():
                    self._heat_on()

    def _control_cool(self):
        """Cooling control with hysteresis"""
        if self.cooling_active:
            # Turn off when we reach setpoint
            if self.current_temp <= self.cool_setpoint:
                if self._can_change_state():
                    self._cool_off()
        else:
            # Turn on when above setpoint + hysteresis
            if self.current_temp >= (self.cool_setpoint + config.HYSTERESIS):
                if self._can_change_state():
                    self._cool_on()

    def _control_auto(self):
        """Auto mode - heat or cool as needed"""
        # Heating logic
        if self.current_temp <= (self.heat_setpoint - config.HYSTERESIS):
            if not self.heating_active and self._can_change_state():
                self._cool_off()
                self._heat_on()
        elif self.current_temp >= self.heat_setpoint and self.heating_active:
            if self._can_change_state():
                self._heat_off()

        # Cooling logic
        if self.current_temp >= (self.cool_setpoint + config.HYSTERESIS):
            if not self.cooling_active and self._can_change_state():
                self._heat_off()
                self._cool_on()
        elif self.current_temp <= self.cool_setpoint and self.cooling_active:
            if self._can_change_state():
                self._cool_off()

    def _control_boost(self):
        """Boost mode - portable unit kicks in for extreme temps"""
        if not self.ir_transmitter:
            return

        boost_needed = False

        if self.mode == config.MODE_HEAT or (self.mode == config.MODE_AUTO and self.heating_active):
            # Boost heating: temp is more than BOOST_THRESHOLD below setpoint
            if self.current_temp <= (self.heat_setpoint - config.BOOST_THRESHOLD):
                boost_needed = True

        if self.mode == config.MODE_COOL or (self.mode == config.MODE_AUTO and self.cooling_active):
            # Boost cooling: temp is more than BOOST_THRESHOLD above setpoint
            if self.current_temp >= (self.cool_setpoint + config.BOOST_THRESHOLD):
                boost_needed = True

        # Apply boost state changes
        if boost_needed and not self.boost_active:
            if self._can_change_boost():
                self._boost_on()
        elif not boost_needed and self.boost_active:
            if self._can_change_boost():
                self._boost_off()

    def _heat_on(self):
        """Turn on furnace"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}HEAT ON (temp: {temp_str}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_furnace.value(0)  # Active LOW
        self.heating_active = True
        self.last_state_change = time.time()

    def _heat_off(self):
        """Turn off furnace"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}HEAT OFF (temp: {temp_str}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_furnace.value(1)  # Inactive HIGH
        self.heating_active = False
        self.last_state_change = time.time()

    def _cool_on(self):
        """Turn on rooftop AC"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}COOL ON (temp: {temp_str}F, setpoint: {self.cool_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_rooftop.value(0)  # Active LOW
        self.cooling_active = True
        self.last_state_change = time.time()

    def _cool_off(self):
        """Turn off rooftop AC"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}COOL OFF (temp: {temp_str}F, setpoint: {self.cool_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_rooftop.value(1)  # Inactive HIGH
        self.cooling_active = False
        self.last_state_change = time.time()

    def _boost_on(self):
        """Turn on portable AC/heater for boost with aggressive settings"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        mode_str = "HEAT" if self.heating_active else "COOL"
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"

        if not config.DRY_RUN and self.ir_transmitter:
            if self.heating_active:
                # Boost heating: set to higher temp on high fan for max output
                boost_temp = min(85, self.heat_setpoint + 5)  # Cap at reasonable max
                print(f"{dry_run}BOOST ON (HEAT mode, current: {temp_str}F, boost target: {boost_temp}F, fan: high)")
                self.ir_transmitter.set_heating(boost_temp, fan_speed='high')
            else:
                # Boost cooling: set to lower temp on high fan for max output
                boost_temp = max(65, self.cool_setpoint - 5)  # Cap at reasonable min
                print(f"{dry_run}BOOST ON (COOL mode, current: {temp_str}F, boost target: {boost_temp}F, fan: high)")
                self.ir_transmitter.set_cooling(boost_temp, fan_speed='high')
        else:
            print(f"{dry_run}BOOST ON ({mode_str} mode, temp: {temp_str}F)")

        self.boost_active = True
        self.last_boost_change = time.time()

    def _boost_off(self):
        """Turn off portable AC/heater"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        temp_str = f"{self.current_temp:.1f}" if self.current_temp is not None else "None"
        print(f"{dry_run}BOOST OFF (temp: {temp_str}F)")
        if not config.DRY_RUN and self.ir_transmitter:
            self.ir_transmitter.send_off()
        self.boost_active = False
        self.last_boost_change = time.time()

    def _all_off(self):
        """Turn off all systems"""
        changed = False
        if self.heating_active or self.cooling_active or self.boost_active:
            if not config.DRY_RUN:
                self.relay_furnace.value(1)
                self.relay_rooftop.value(1)
                if self.ir_transmitter:
                    self.ir_transmitter.send_off()
            self.heating_active = False
            self.cooling_active = False
            self.boost_active = False
            self.last_state_change = time.time()
            self.last_boost_change = time.time()

    def get_status(self):
        """Get current status as dict"""
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
            'boost_active': self.boost_active,
            'dry_run': config.DRY_RUN,
            'debug': config.DEBUG
        }
