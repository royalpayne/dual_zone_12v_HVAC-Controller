# BMP280 Driver for ESP32
from micropython import const
import time

REG_CHIP_ID = const(0xD0)
REG_CTRL_MEAS = const(0xF4)
REG_CONFIG = const(0xF5)
REG_DATA = const(0xF7)
REG_DIG_T1 = const(0x88)

class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        
        chip_id = self.i2c.readfrom_mem(self.addr, REG_CHIP_ID, 1)[0]
        if chip_id not in (0x58, 0x60):
            raise RuntimeError(f"BMP280 not found: {hex(chip_id)}")
        
        self._read_calibration()
        self.i2c.writeto_mem(self.addr, REG_CTRL_MEAS, bytes([0b10110111]))
        self.i2c.writeto_mem(self.addr, REG_CONFIG, bytes([0b00010000]))
        time.sleep_ms(50)
    
    def _read_calibration(self):
        cal = self.i2c.readfrom_mem(self.addr, REG_DIG_T1, 26)
        self.dig_T1 = cal[0] | (cal[1] << 8)
        self.dig_T2 = self._signed(cal[2] | (cal[3] << 8))
        self.dig_T3 = self._signed(cal[4] | (cal[5] << 8))
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
        return val - 0x10000 if val >= 0x8000 else val
    
    def read(self):
        data = self.i2c.readfrom_mem(self.addr, REG_DATA, 6)
        raw_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        var1 = ((raw_t / 16384.0) - (self.dig_T1 / 1024.0)) * self.dig_T2
        var2 = (((raw_t / 131072.0) - (self.dig_T1 / 8192.0)) ** 2) * self.dig_T3
        self.t_fine = var1 + var2
        temp_c = self.t_fine / 5120.0
        
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            pressure = 0
        else:
            pressure = 1048576.0 - raw_p
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = self.dig_P9 * pressure * pressure / 2147483648.0
            var2 = pressure * self.dig_P8 / 32768.0
            pressure = (pressure + (var1 + var2 + self.dig_P7) / 16.0) / 100.0
        
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f, pressure
