# Combined Sensor Module
# BME280: Temperature + Humidity + Pressure (preferred)
# BMP280: Temperature + Pressure (fallback)
# DHT11: Humidity only (for boards without BME280)

from machine import Pin, I2C
import dht
import time
import config

# Try to import BME280 first, fallback to BMP280
try:
    from bme280 import BME280
    HAS_BME280 = True
except ImportError:
    HAS_BME280 = False

try:
    from bmp280 import BMP280
    HAS_BMP280 = True
except ImportError:
    HAS_BMP280 = False


class SensorHub:
    """Combines BME280/BMP280 and DHT11 for complete environmental readings"""

    def __init__(self, i2c=None):
        self.sensor = None
        self.sensor_type = None
        self.dht11 = None

        # Initialize I2C if not provided
        if i2c is None:
            i2c = I2C(0,
                      sda=Pin(config.I2C_SDA_PIN),
                      scl=Pin(config.I2C_SCL_PIN),
                      freq=config.I2C_FREQ)

        # Try BME280 first (has humidity built-in)
        if HAS_BME280:
            try:
                self.sensor = BME280(i2c, config.BMP280_ADDR)  # Uses same I2C address
                self.sensor_type = 'BME280'
                print("BME280 initialized (temp + humidity + pressure)")
            except Exception as e:
                print(f"BME280 init failed: {e}")

        # Fallback to BMP280 if BME280 not found
        if self.sensor is None and HAS_BMP280:
            try:
                self.sensor = BMP280(i2c, config.BMP280_ADDR)
                self.sensor_type = 'BMP280'
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

        # Read BME280/BMP280
        if self.sensor:
            try:
                if self.sensor_type == 'BME280':
                    # BME280 returns temp, pressure, AND humidity
                    temp_f, pressure, humidity = self.sensor.read_fahrenheit()
                    self._last_temp_f = temp_f
                    self._last_pressure = pressure
                    self._last_humidity = humidity
                else:
                    # BMP280 returns only temp and pressure
                    temp_f, pressure = self.sensor.read_fahrenheit()
                    self._last_temp_f = temp_f
                    self._last_pressure = pressure
            except Exception as e:
                print(f"{self.sensor_type} read error: {e}")
                temp_f = self._last_temp_f
                pressure = self._last_pressure
                if self.sensor_type == 'BME280':
                    humidity = self._last_humidity

        # Read DHT11 (only if BME280 not present or for backup)
        # DHT11 is slow - only read every 2+ seconds
        now = time.ticks_ms()
        if self.dht11 and time.ticks_diff(now, self._last_read) > 2000:
            try:
                self.dht11.measure()
                dht_humidity = self.dht11.humidity()
                self._last_read = now

                # Use DHT11 humidity if BME280 humidity not available
                if humidity is None:
                    humidity = dht_humidity
                    self._last_humidity = humidity

                # If main sensor failed, use DHT11 temp as fallback
                if temp_f is None:
                    temp_c = self.dht11.temperature()
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    self._last_temp_f = temp_f
            except Exception as e:
                print(f"DHT11 read error: {e}")
                if humidity is None:
                    humidity = self._last_humidity
        elif humidity is None:
            # Use cached humidity if not reading DHT11 now
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
            'sensor_type': self.sensor_type,
            'sensor_ok': self.sensor is not None,
            'bme280': self.sensor_type == 'BME280',
            'bmp280': self.sensor_type == 'BMP280',
            'dht11': self.dht11 is not None
        }
