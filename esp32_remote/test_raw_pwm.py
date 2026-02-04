# Test IR transmission using raw PWM instead of RMT
# This bypasses the peterhinch library to see if the issue is with RMT

from machine import Pin, PWM
import time

# Freshly captured power code
power_code = [9000, 4603, 525, 629, 548, 628, 526, 650, 527, 1759, 541, 655, 521, 681, 523, 1755, 572, 631, 528, 648, 522, 634, 519, 655, 544, 1757, 546, 634, 545, 1782, 522, 732, 445, 658, 544, 1755, 549, 628, 522, 635, 541, 634, 520, 658, 545, 1782, 519, 657, 547, 1757, 520, 658, 519, 657, 520, 1783, 518, 637, 542, 636, 541, 659, 519, 1782, 656, 523, 520]

print('\n=== Testing with RAW PWM (not RMT) ===')
print('This bypasses the peterhinch library')

# Initialize PWM on GPIO 18
pwm = PWM(Pin(18), freq=38000, duty=512)  # 38kHz carrier, ~50% duty
pwm.deinit()  # Start with it off

def send_pulse(duration_us):
    """Send a carrier pulse for duration_us microseconds"""
    pwm.init(freq=38000, duty=512)
    time.sleep_us(duration_us)
    pwm.deinit()

def send_space(duration_us):
    """Send a space (no carrier) for duration_us microseconds"""
    # Already off, just wait
    time.sleep_us(duration_us)

print('\nSending power code with raw PWM...')
print('Watching through phone camera - LED should FLASH briefly')
time.sleep(2)

# Send the code - alternating pulses and spaces
for i, duration in enumerate(power_code):
    if i % 2 == 0:  # Even indices are pulses (carrier on)
        send_pulse(duration)
    else:  # Odd indices are spaces (carrier off)
        send_space(duration)

# Ensure LED is off
pwm.deinit()
Pin(18, Pin.OUT).value(0)

print('\nDone! Did A/C respond?')
print('Also check: Is LED off now?')
