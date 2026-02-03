# IR LED Test - check with phone camera
from machine import Pin, PWM
import time

print('IR LED on for 10 seconds - check with phone camera')
tx = PWM(Pin(18))
tx.freq(38000)
tx.duty_u16(32768)
time.sleep(10)
tx.deinit()
Pin(18, Pin.OUT).value(0)
print('Done')
