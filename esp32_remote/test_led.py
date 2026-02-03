# LED Test for GPIO 18
# Quick test to verify LED circuit

from machine import Pin, PWM
import time

def test_led():
    print("\n=== LED Test ===")
    print("Testing LED on GPIO 18...")

    # Create PWM on GPIO 18
    tx = PWM(Pin(18))
    tx.freq(38000)
    tx.duty_u16(21845)

    print("LED should be glowing now!")
    print("Waiting 5 seconds...")
    time.sleep(5)

    # Turn off
    tx.deinit()
    Pin(18, Pin.OUT).value(0)

    print("Test complete!")
    print("================\n")

# Run the test
test_led()
