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
        self.whynter_mode = 0  # 0=off, 1=cool, 2=dehum, 3=fan, 4=heat
        self.last_state_change = 0
        self.last_whynter_change = 0

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

    def set_whynter_mode(self, mode):
        """Set Whynter portable AC mode (0=off, 1=on/cool)"""
        if mode < 0 or mode > 1:
            print(f"Invalid Whynter mode: {mode}")
            return

        if mode == self.whynter_mode:
            print(f"Whynter already in mode {mode}")
            return

        if not self.ir_transmitter:
            print("No IR transmitter available")
            return

        if mode == 0:
            # Turn off
            print("Setting Whynter to OFF")
            if not config.DRY_RUN:
                self.ir_transmitter.send_off()
        else:
            # Turn on in cool mode (default)
            print("Setting Whynter to COOL mode")
            if not config.DRY_RUN:
                self.ir_transmitter.set_mode('cool')

        self.whynter_mode = mode
        self.last_whynter_change = time.time()

    def _can_change_state(self):
        """Check if enough time has passed since last state change"""
        return (time.time() - self.last_state_change) >= config.MIN_CYCLE_TIME

    def _can_change_whynter(self):
        """Check if enough time has passed since last Whynter change"""
        return (time.time() - self.last_whynter_change) >= config.MIN_CYCLE_TIME

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


    def _all_off(self):
        """Turn off all systems"""
        changed = False
        if self.heating_active or self.cooling_active or self.whynter_mode != 0:
            if not config.DRY_RUN:
                self.relay_furnace.value(1)
                self.relay_rooftop.value(1)
                if self.ir_transmitter and self.whynter_mode != 0:
                    self.ir_transmitter.send_off()
            self.heating_active = False
            self.cooling_active = False
            if self.whynter_mode != 0:
                self.whynter_mode = 0
                self.last_whynter_change = time.time()
            self.last_state_change = time.time()

    def get_status(self):
        """Get current status as dict"""
        whynter_names = {0: 'Off', 1: 'On'}
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
            'whynter_mode': self.whynter_mode,
            'whynter_mode_name': whynter_names.get(self.whynter_mode, '?'),
            'dry_run': config.DRY_RUN,
            'debug': config.DEBUG
        }
