# WORKING Whynter IR Test
# Uses 75% duty cycle for brighter LED output
# This configuration successfully controls the Whynter A/C

from machine import Pin, PWM
import time

# Freshly captured power code from working Whynter remote
power_code = [9000, 4603, 525, 629, 548, 628, 526, 650, 527, 1759, 541, 655, 521, 681,
              523, 1755, 572, 631, 528, 648, 522, 634, 519, 655, 544, 1757, 546, 634,
              545, 1782, 522, 732, 445, 658, 544, 1755, 549, 628, 522, 635, 541, 634,
              520, 658, 545, 1782, 519, 657, 547, 1757, 520, 658, 519, 657, 520, 1783,
              518, 637, 542, 636, 541, 659, 519, 1782, 656, 523, 520]

print('\n=== Whynter Power Toggle ===')
print('Sending IR command...')

# Initialize PWM with 38kHz carrier and 75% duty cycle (brighter)
pwm = PWM(Pin(18), freq=38000, duty=768)  # 768/1024 = 75%
pwm.deinit()

# Send the power code
for i, duration in enumerate(power_code):
    if i % 2 == 0:  # Pulse (carrier on)
        pwm.init(freq=38000, duty=768)
        time.sleep_us(duration)
        pwm.deinit()
    else:  # Space (carrier off)
        time.sleep_us(duration)

# Ensure LED is off
pwm.deinit()
Pin(18, Pin.OUT).value(0)

print('Done!')
