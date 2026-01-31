# SSD1306 OLED Driver
from micropython import const
import framebuf

SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)
SET_CONTRAST = const(0x81)

class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self._init_display()

    def _init_display(self):
        for cmd in (
            SET_DISP | 0x00, SET_MEM_ADDR, 0x00, SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01, SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08, SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x02,
            SET_DISP_CLK_DIV, 0x80, SET_PRECHARGE, 0xF1,
            SET_VCOM_DESEL, 0x30, SET_CONTRAST, 0xFF, 0xA4, 0xA6,
            SET_CHARGE_PUMP, 0x14, SET_DISP | 0x01,
        ):
            self.i2c.writeto(self.addr, bytes([0x80, cmd]))
        self.fill(0)
        self.show()

    def show(self):
        self.i2c.writeto(self.addr, bytes([0x80, SET_COL_ADDR]))
        self.i2c.writeto(self.addr, bytes([0x80, 0]))
        self.i2c.writeto(self.addr, bytes([0x80, self.width - 1]))
        self.i2c.writeto(self.addr, bytes([0x80, SET_PAGE_ADDR]))
        self.i2c.writeto(self.addr, bytes([0x80, 0]))
        self.i2c.writeto(self.addr, bytes([0x80, self.pages - 1]))
        self.i2c.writeto(self.addr, bytes([0x40]) + self.buffer)
