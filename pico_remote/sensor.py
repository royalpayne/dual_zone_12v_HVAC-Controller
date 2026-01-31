# Combined Sensor Module
# BMP280: Temperature + Pressure (more accurate)
# DHT11: Humidity only

from machine import Pin, I2C
import dht
import time
import config
from bmp280 import BMP280


class SensorHub:
    """Combines BMP280 and DHT11 for complete environmental readings"""
    
    def __init__(self, i2c=None):
        self.bmp280 = None
        self.dht11 = None
        
        # Initialize I2C if not provided
        if i2c is None:
            i2c = I2C(0, 
                      sda=Pin(config.I2C_SDA_PIN), 
                      scl=Pin(config.I2C_SCL_PIN), 
                      freq=config.I2C_FREQ)
        
        # Initialize BMP280
        try:
            self.bmp280 = BMP280(i2c, config.BMP280_ADDR)
            print("BMP280 initialized (temp + pressure)")
        except Exception as e:
            print(f"BMP280 init failed: {e}")
        
        # Initialize DHT11
        try:
            self.dht11 = dht.DHT11(Pin(config.DHT11_PIN))
            print("DHT11 initialized (humidity)")
        except Exception as e:
            print(f"DHT11 init failed: {e}")
        
        # Cache last readings
        self._last_temp_f = None
        self._last_humidity = None
        self._last_pressure = None
        self._last_read = 0
    
    def read(self):
        """
        Read all sensors.
        Returns: (temp_f, humidity, pressure_hpa)
        """
        temp_f = None
        humidity = None
        pressure = None
        
        # Read BMP280 (temperature + pressure)
        if self.bmp280:
            try:
                temp_f, pressure = self.bmp280.read_fahrenheit()
                self._last_temp_f = temp_f
                self._last_pressure = pressure
            except Exception as e:
                print(f"BMP280 read error: {e}")
                temp_f = self._last_temp_f
                pressure = self._last_pressure
        
        # Read DHT11 (humidity only)
        # DHT11 is slow - only read every 2+ seconds
        now = time.ticks_ms()
        if self.dht11 and time.ticks_diff(now, self._last_read) > 2000:
            try:
                self.dht11.measure()
                humidity = self.dht11.humidity()
                self._last_humidity = humidity
                self._last_read = now
                
                # If BMP280 failed, use DHT11 temp as fallback
                if temp_f is None:
                    temp_c = self.dht11.temperature()
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    self._last_temp_f = temp_f
            except Exception as e:
                print(f"DHT11 read error: {e}")
                humidity = self._last_humidity
        else:
            humidity = self._last_humidity
        
        return temp_f, humidity, pressure
    
    def read_temperature(self):
        """Read temperature in Fahrenheit"""
        temp_f, _, _ = self.read()
        return temp_f
    
    def read_humidity(self):
        """Read relative humidity %"""
        _, humidity, _ = self.read()
        return humidity
    
    def read_pressure(self):
        """Read pressure in hPa"""
        _, _, pressure = self.read()
        return pressure
    
    def get_status(self):
        """Return sensor status for diagnostics"""
        return {
            'bmp280': self.bmp280 is not None,
            'dht11': self.dht11 is not None
        }
