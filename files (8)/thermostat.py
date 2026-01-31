# Thermostat Controller
# Dual sensors, scheduler integration, remote relay control

import time
import urequests
import config

class Thermostat:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        
        # Operating mode
        self.mode = config.MODE_OFF
        self.cool_system = config.COOL_SYSTEM_ROOFTOP
        
        # Local sensor (ESP32/Kitchen)
        self.local_temp = None
        self.local_humidity = None
        self.local_pressure = None
        
        # Remote sensor (Pico/Living Room)
        self.remote_temp = None
        self.remote_humidity = None
        self.remote_online = False
        
        # Average for control
        self.avg_temp = None
        
        # State
        self.heating = False
        self.cooling = False
        self.last_change = 0
        
        # IR transmitter
        self.ir_tx = None
        
        # Pico URL
        self.pico_url = f"http://{config.PICO_IP}:{config.PICO_PORT}"
    
    @property
    def heat_setpoint(self):
        h, _ = self.scheduler.get_setpoints()
        return h
    
    @property
    def cool_setpoint(self):
        _, c = self.scheduler.get_setpoints()
        return c
    
    def set_ir_transmitter(self, ir):
        self.ir_tx = ir
    
    def update_local(self, temp, humidity, pressure):
        self.local_temp = temp
        self.local_humidity = humidity
        self.local_pressure = pressure
        self._calc_avg()
    
    def fetch_remote(self):
        """Get readings from Pico"""
        try:
            r = urequests.get(f"{self.pico_url}/status", timeout=3)
            data = r.json()
            r.close()
            self.remote_temp = data.get('temp')
            self.remote_humidity = data.get('humidity')
            self.remote_online = True
            self._calc_avg()
            return True
        except Exception as e:
            print(f"Pico fetch: {e}")
            self.remote_online = False
            self._calc_avg()
            return False
    
    def _calc_avg(self):
        if self.local_temp and self.remote_temp:
            self.avg_temp = (self.local_temp + self.remote_temp) / 2
        elif self.local_temp:
            self.avg_temp = self.local_temp
        elif self.remote_temp:
            self.avg_temp = self.remote_temp
        else:
            self.avg_temp = None
    
    def _relay_cmd(self, relay, on):
        """Send command to Pico relays"""
        try:
            cmd = "on" if on else "off"
            r = urequests.get(f"{self.pico_url}/relay/{relay}/{cmd}", timeout=3)
            r.close()
            return True
        except Exception as e:
            print(f"Relay cmd: {e}")
            return False
    
    def set_mode(self, mode):
        if mode in config.MODE_NAMES:
            self.mode = mode
            if mode == config.MODE_OFF:
                self._all_off()
    
    def set_cool_system(self, sys):
        if sys in config.COOL_SYSTEM_NAMES:
            self.cool_system = sys
    
    def adjust_heat(self, delta):
        """Adjust heat setpoint - creates hold"""
        h, c = self.scheduler.get_setpoints()
        new_h = max(config.MIN_SETPOINT, min(config.MAX_SETPOINT, h + delta))
        self.scheduler.set_hold(new_h, c)
    
    def adjust_cool(self, delta):
        """Adjust cool setpoint - creates hold"""
        h, c = self.scheduler.get_setpoints()
        new_c = max(config.MIN_SETPOINT, min(config.MAX_SETPOINT, c + delta))
        self.scheduler.set_hold(h, new_c)
    
    def _can_change(self):
        return (time.time() - self.last_change) >= config.MIN_CYCLE_TIME
    
    def run(self):
        """Main control loop"""
        if self.avg_temp is None:
            return
        
        if self.mode == config.MODE_OFF:
            self._all_off()
            return
        
        h_sp = self.heat_setpoint
        c_sp = self.cool_setpoint
        hyst = config.HYSTERESIS
        
        if self.mode == config.MODE_HEAT or self.mode == config.MODE_AUTO:
            if self.heating:
                if self.avg_temp >= h_sp and self._can_change():
                    self._heat_off()
            else:
                if self.avg_temp <= (h_sp - hyst) and self._can_change():
                    self._heat_on()
        
        if self.mode == config.MODE_COOL or self.mode == config.MODE_AUTO:
            if self.cooling:
                if self.avg_temp <= c_sp and self._can_change():
                    self._cool_off()
            else:
                if self.avg_temp >= (c_sp + hyst) and self._can_change():
                    self._cool_on()
    
    def _heat_on(self):
        print(f"HEAT ON {self.avg_temp:.1f}F")
        self._relay_cmd("furnace", True)
        self.heating = True
        self.last_change = time.time()
    
    def _heat_off(self):
        print(f"HEAT OFF {self.avg_temp:.1f}F")
        self._relay_cmd("furnace", False)
        self.heating = False
        self.last_change = time.time()
    
    def _cool_on(self):
        print(f"COOL ON {self.avg_temp:.1f}F")
        if self.cool_system == config.COOL_SYSTEM_ROOFTOP:
            self._relay_cmd("rooftop", True)
        else:
            if self.ir_tx:
                self.ir_tx.send_on()
        self.cooling = True
        self.last_change = time.time()
    
    def _cool_off(self):
        print(f"COOL OFF {self.avg_temp:.1f}F")
        if self.cool_system == config.COOL_SYSTEM_ROOFTOP:
            self._relay_cmd("rooftop", False)
        else:
            if self.ir_tx:
                self.ir_tx.send_off()
        self.cooling = False
        self.last_change = time.time()
    
    def _all_off(self):
        if self.heating or self.cooling:
            self._relay_cmd("all", False)
            if self.ir_tx:
                self.ir_tx.send_off()
            self.heating = False
            self.cooling = False
            self.last_change = time.time()
    
    def get_status(self):
        """Full status for API"""
        status = {
            'avg': self.avg_temp,
            'l_temp': self.local_temp,
            'l_hum': self.local_humidity,
            'l_pres': self.local_pressure,
            'r_temp': self.remote_temp,
            'r_hum': self.remote_humidity,
            'r_online': self.remote_online,
            'mode': self.mode,
            'mode_name': config.MODE_NAMES.get(self.mode),
            'heat_sp': self.heat_setpoint,
            'cool_sp': self.cool_setpoint,
            'heating': self.heating,
            'cooling': self.cooling,
            'cool_sys': self.cool_system,
            'l_name': config.LOCATION_LOCAL,
            'r_name': config.LOCATION_REMOTE
        }
        status.update(self.scheduler.get_status())
        return status
