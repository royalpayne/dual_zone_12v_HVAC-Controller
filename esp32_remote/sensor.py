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

    # Cache interval: only read sensors every 1000ms (1 second)
    # This prevents blocking the web server on every API call
    CACHE_INTERVAL_MS = 1000

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
        self._last_sensor_read = 0  # Last time BMP/BME was read
        self._last_dht_read = 0      # Last time DHT11 was read
    
    def read(self):
        """
        Read all sensors with caching to prevent blocking.
        Only reads actual sensors if cache interval has elapsed.
        Returns: (temp_f, humidity, pressure_hpa)
        """
        now = time.ticks_ms()
        temp_f = None
        humidity = None
        pressure = None

        # Read BME280/BMP280 (only if cache expired)
        if self.sensor:
            if time.ticks_diff(now, self._last_sensor_read) > self.CACHE_INTERVAL_MS:
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
                    self._last_sensor_read = now
                except Exception as e:
                    print(f"{self.sensor_type} read error: {e}")
                    # Fall through to use cached values below

            # Use cached values if we didn't just read or if read failed
            if temp_f is None:
                temp_f = self._last_temp_f
            if pressure is None:
                pressure = self._last_pressure
            if humidity is None and self.sensor_type == 'BME280':
                humidity = self._last_humidity

        # Read DHT11 (only if BME280 not present or for backup)
        # DHT11 is slow - only read every 2+ seconds
        if self.dht11 and time.ticks_diff(now, self._last_dht_read) > 2000:
            try:
                self.dht11.measure()
                dht_humidity = self.dht11.humidity()
                self._last_dht_read = now

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

        # Use cached humidity if not reading DHT11 now
        if humidity is None:
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
