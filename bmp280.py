# BMP280 MicroPython Driver
# Temperature and Pressure only (no humidity)

from micropython import const
import time

# Registers
REG_CHIP_ID = const(0xD0)
REG_RESET = const(0xE0)
REG_STATUS = const(0xF3)
REG_CTRL_MEAS = const(0xF4)
REG_CONFIG = const(0xF5)
REG_DATA = const(0xF7)
REG_DIG_T1 = const(0x88)

# Chip ID
BMP280_CHIP_ID = const(0x58)

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


class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        
        # Verify chip ID
        chip_id = self._read_byte(REG_CHIP_ID)
        if chip_id != BMP280_CHIP_ID:
            raise RuntimeError(f"BMP280 not found. Chip ID: {hex(chip_id)}")
        
        # Read calibration data
        self._read_calibration()
        
        # Configure: 16x oversampling, normal mode
        # ctrl_meas: osrs_t[7:5] osrs_p[4:2] mode[1:0]
        self._write_byte(REG_CTRL_MEAS, (OVERSAMPLE_16 << 5) | (OVERSAMPLE_16 << 2) | MODE_NORMAL)
        
        # Config: standby 0.5ms, filter coeff 16
        self._write_byte(REG_CONFIG, (0 << 5) | (4 << 2))
        
        time.sleep_ms(50)
    
    def _read_byte(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
    
    def _read_bytes(self, reg, count):
        return self.i2c.readfrom_mem(self.addr, reg, count)
    
    def _write_byte(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))
    
    def _read_calibration(self):
        # Read temperature and pressure calibration (26 bytes starting at 0x88)
        cal = self._read_bytes(REG_DIG_T1, 26)
        
        # Temperature calibration
        self.dig_T1 = cal[0] | (cal[1] << 8)
        self.dig_T2 = self._signed(cal[2] | (cal[3] << 8))
        self.dig_T3 = self._signed(cal[4] | (cal[5] << 8))
        
        # Pressure calibration
        self.dig_P1 = cal[6] | (cal[7] << 8)
        self.dig_P2 = self._signed(cal[8] | (cal[9] << 8))
        self.dig_P3 = self._signed(cal[10] | (cal[11] << 8))
        self.dig_P4 = self._signed(cal[12] | (cal[13] << 8))
        self.dig_P5 = self._signed(cal[14] | (cal[15] << 8))
        self.dig_P6 = self._signed(cal[16] | (cal[17] << 8))
        self.dig_P7 = self._signed(cal[18] | (cal[19] << 8))
        self.dig_P8 = self._signed(cal[20] | (cal[21] << 8))
        self.dig_P9 = self._signed(cal[22] | (cal[23] << 8))
        
        self.t_fine = 0
    
    def _signed(self, val):
        if val >= 0x8000:
            return val - 0x10000
        return val
    
    def _read_raw(self):
        # Read 6 bytes: press[19:12], press[11:4], press[3:0], temp[19:12], temp[11:4], temp[3:0]
        data = self._read_bytes(REG_DATA, 6)
        
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        return raw_temp, raw_press
    
    def _compensate_temp(self, raw_temp):
        # From BMP280 datasheet
        var1 = ((raw_temp / 16384.0) - (self.dig_T1 / 1024.0)) * self.dig_T2
        var2 = (((raw_temp / 131072.0) - (self.dig_T1 / 8192.0)) ** 2) * self.dig_T3
        self.t_fine = var1 + var2
        return self.t_fine / 5120.0
    
    def _compensate_press(self, raw_press):
        # From BMP280 datasheet
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        
        if var1 == 0:
            return 0
        
        pressure = 1048576.0 - raw_press
        pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
        var1 = self.dig_P9 * pressure * pressure / 2147483648.0
        var2 = pressure * self.dig_P8 / 32768.0
        pressure = pressure + (var1 + var2 + self.dig_P7) / 16.0
        
        return pressure / 100.0  # Return hPa
    
    def read(self):
        """Read temperature (Celsius) and pressure (hPa)"""
        raw_temp, raw_press = self._read_raw()
        temp_c = self._compensate_temp(raw_temp)
        pressure = self._compensate_press(raw_press)
        return temp_c, pressure
    
    def read_fahrenheit(self):
        """Read temperature (Fahrenheit) and pressure (hPa)"""
        temp_c, pressure = self.read()
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f, pressure
