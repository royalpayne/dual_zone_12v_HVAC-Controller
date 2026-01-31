# Thermostat Controller
# Handles heating/cooling logic with hysteresis and short-cycle protection

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
        
        # Cooling system selection
        self.cool_system = config.COOL_SYSTEM_ROOFTOP
        
        # Current readings
        self.current_temp = None
        self.current_humidity = None
        self.current_pressure = None
        
        # State tracking
        self.heating_active = False
        self.cooling_active = False
        self.last_state_change = 0
        
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
    
    def set_cool_system(self, system):
        """Set which cooling system to use"""
        if system in config.COOL_SYSTEM_NAMES:
            self.cool_system = system
    
    def _can_change_state(self):
        """Check if enough time has passed since last state change"""
        return (time.time() - self.last_state_change) >= config.MIN_CYCLE_TIME
    
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
        # Deadband between heat and cool setpoints
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
        """Turn on heating"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}HEAT ON (temp: {self.current_temp:.1f}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_furnace.value(0)  # Active LOW
        self.heating_active = True
        self.last_state_change = time.time()

    def _heat_off(self):
        """Turn off heating"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}HEAT OFF (temp: {self.current_temp:.1f}F, setpoint: {self.heat_setpoint}F)")
        if not config.DRY_RUN:
            self.relay_furnace.value(1)  # Inactive HIGH
        self.heating_active = False
        self.last_state_change = time.time()

    def _cool_on(self):
        """Turn on cooling"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}COOL ON (temp: {self.current_temp:.1f}F, setpoint: {self.cool_setpoint}F)")

        if not config.DRY_RUN:
            if self.cool_system == config.COOL_SYSTEM_ROOFTOP:
                self.relay_rooftop.value(0)  # Active LOW
            else:
                # Portable AC via IR
                if self.ir_transmitter:
                    self.ir_transmitter.send_on()

        self.cooling_active = True
        self.last_state_change = time.time()

    def _cool_off(self):
        """Turn off cooling"""
        dry_run = "(DRY RUN) " if config.DRY_RUN else ""
        print(f"{dry_run}COOL OFF (temp: {self.current_temp:.1f}F, setpoint: {self.cool_setpoint}F)")

        if not config.DRY_RUN:
            if self.cool_system == config.COOL_SYSTEM_ROOFTOP:
                self.relay_rooftop.value(1)  # Inactive HIGH
            else:
                # Portable AC via IR
                if self.ir_transmitter:
                    self.ir_transmitter.send_off()

        self.cooling_active = False
        self.last_state_change = time.time()

    def _all_off(self):
        """Turn off all systems"""
        if self.heating_active or self.cooling_active:
            if not config.DRY_RUN:
                self.relay_furnace.value(1)
                self.relay_rooftop.value(1)
                if self.ir_transmitter:
                    self.ir_transmitter.send_off()
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
