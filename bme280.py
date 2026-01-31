# BME280 MicroPython Driver
# Temperature, Humidity, and Pressure

from micropython import const
import time

# Registers
REG_CHIP_ID = const(0xD0)
REG_RESET = const(0xE0)
REG_CTRL_HUM = const(0xF2)
REG_STATUS = const(0xF3)
REG_CTRL_MEAS = const(0xF4)
REG_CONFIG = const(0xF5)
REG_DATA = const(0xF7)
REG_DIG_T1 = const(0x88)
REG_DIG_H1 = const(0xA1)
REG_DIG_H2 = const(0xE1)

# Chip ID
BME280_CHIP_ID = const(0x60)

# Oversampling
OVERSAMPLE_1 = const(1)
OVERSAMPLE_2 = const(2)
OVERSAMPLE_4 = const(3)
OVERSAMPLE_8 = const(4)
OVERSAMPLE_16 = const(5)

# Power modes
MODE_SLEEP = const(0)
MODE_FORCED = const(1)
MODE_NORMAL = const(3)


class BME280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr

        # Verify chip ID
        chip_id = self._read_byte(REG_CHIP_ID)
        if chip_id != BME280_CHIP_ID:
            raise RuntimeError(f"BME280 not found. Chip ID: {hex(chip_id)} (expected 0x60)")

        # Read calibration data
        self._read_calibration()

        # Configure humidity oversampling first (must be done before CTRL_MEAS)
        self._write_byte(REG_CTRL_HUM, OVERSAMPLE_1)

        # Configure: 16x oversampling for temp/pressure, normal mode
        # ctrl_meas: osrs_t[7:5] osrs_p[4:2] mode[1:0]
        self._write_byte(REG_CTRL_MEAS, (OVERSAMPLE_16 << 5) | (OVERSAMPLE_16 << 2) | MODE_NORMAL)

        # Config: standby 0.5ms, filter coeff 16
        self._write_byte(REG_CONFIG, (0 << 5) | (4 << 2))

        time.sleep_ms(10)  # Wait for measurement

    def _read_byte(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _read_u16_le(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return data[0] | (data[1] << 8)

    def _read_s16_le(self, reg):
        val = self._read_u16_le(reg)
        return val if val < 32768 else val - 65536

    def _write_byte(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))

    def _read_calibration(self):
        """Read temperature, pressure, and humidity calibration data"""
        # Temperature calibration
        self.dig_T1 = self._read_u16_le(REG_DIG_T1)
        self.dig_T2 = self._read_s16_le(REG_DIG_T1 + 2)
        self.dig_T3 = self._read_s16_le(REG_DIG_T1 + 4)

        # Pressure calibration
        self.dig_P1 = self._read_u16_le(REG_DIG_T1 + 6)
        self.dig_P2 = self._read_s16_le(REG_DIG_T1 + 8)
        self.dig_P3 = self._read_s16_le(REG_DIG_T1 + 10)
        self.dig_P4 = self._read_s16_le(REG_DIG_T1 + 12)
        self.dig_P5 = self._read_s16_le(REG_DIG_T1 + 14)
        self.dig_P6 = self._read_s16_le(REG_DIG_T1 + 16)
        self.dig_P7 = self._read_s16_le(REG_DIG_T1 + 18)
        self.dig_P8 = self._read_s16_le(REG_DIG_T1 + 20)
        self.dig_P9 = self._read_s16_le(REG_DIG_T1 + 22)

        # Humidity calibration
        self.dig_H1 = self._read_byte(REG_DIG_H1)
        self.dig_H2 = self._read_s16_le(REG_DIG_H2)
        self.dig_H3 = self._read_byte(REG_DIG_H2 + 2)

        # H4 and H5 are split across bytes
        e4 = self._read_byte(REG_DIG_H2 + 3)
        e5 = self._read_byte(REG_DIG_H2 + 4)
        e6 = self._read_byte(REG_DIG_H2 + 5)

        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        if self.dig_H4 & 0x800:
            self.dig_H4 -= 4096

        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        if self.dig_H5 & 0x800:
            self.dig_H5 -= 4096

        self.dig_H6 = self._read_byte(REG_DIG_H2 + 6)
        if self.dig_H6 > 127:
            self.dig_H6 -= 256

    def _read_raw_data(self):
        """Read raw ADC values"""
        # Read all 8 bytes: pressure(3), temp(3), humidity(2)
        data = self.i2c.readfrom_mem(self.addr, REG_DATA, 8)

        pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        humidity_raw = (data[6] << 8) | data[7]

        return temp_raw, pressure_raw, humidity_raw

    def _compensate_temperature(self, adc_T):
        """Compensate temperature and return t_fine for other calculations"""
        var1 = ((adc_T >> 3) - (self.dig_T1 << 1)) * self.dig_T2 >> 11
        var2 = (((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1) >> 12) * self.dig_T3 >> 14
        t_fine = var1 + var2
        temp = (t_fine * 5 + 128) >> 8
        return temp, t_fine

    def _compensate_pressure(self, adc_P, t_fine):
        """Compensate pressure reading"""
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1)) * self.dig_P1 >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc_P
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        return p / 256

    def _compensate_humidity(self, adc_H, t_fine):
        """Compensate humidity reading"""
        var_h = t_fine - 76800

        var_h = (((((adc_H << 14) - (self.dig_H4 << 20) - (self.dig_H5 * var_h)) +
                  16384) >> 15) * (((((((var_h * self.dig_H6) >> 10) *
                  (((var_h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) *
                  self.dig_H2 + 8192) >> 14))

        var_h = var_h - (((((var_h >> 15) * (var_h >> 15)) >> 7) * self.dig_H1) >> 4)
        var_h = 0 if var_h < 0 else var_h
        var_h = 419430400 if var_h > 419430400 else var_h

        return (var_h >> 12) / 1024.0

    def read(self):
        """
        Read temperature, pressure, and humidity
        Returns: (temp_celsius, pressure_pa, humidity_percent)
        """
        temp_raw, pressure_raw, humidity_raw = self._read_raw_data()

        # Compensate temperature first (needed for other readings)
        temp, t_fine = self._compensate_temperature(temp_raw)
        temp_c = temp / 100.0

        # Compensate pressure
        pressure_pa = self._compensate_pressure(pressure_raw, t_fine)

        # Compensate humidity
        humidity = self._compensate_humidity(humidity_raw, t_fine)

        return temp_c, pressure_pa, humidity

    def read_fahrenheit(self):
        """
        Read temperature in Fahrenheit, pressure in Pa, humidity in %
        Returns: (temp_fahrenheit, pressure_pa, humidity_percent)
        """
        temp_c, pressure_pa, humidity = self.read()
        temp_f = (temp_c * 9/5) + 32
        return temp_f, pressure_pa, humidity
