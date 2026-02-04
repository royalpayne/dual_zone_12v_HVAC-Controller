# RV Thermostat Wiring Diagrams

This directory contains wiring diagrams for the RV thermostat system.

## IR LED Breadboard Wiring

**File:** [ir_led_breadboard.svg](ir_led_breadboard.svg)

Diagram showing how to wire a bare IR LED (940nm) to ESP32 GPIO 18 for testing IR transmission.

**Components:**
- ESP32 (GPIO 18 and GND)
- IR LED (940nm, clear LED)
- 100-220Ω resistor

**Connections:**
1. GPIO 18 → 100-220Ω resistor
2. Resistor → IR LED anode (long leg, +)
3. IR LED cathode (short leg, -) → GND

**Notes:**
- IR LEDs emit invisible 940nm infrared light
- Use phone camera to see the LED flash (appears purple/white)
- Polarity is critical - longer leg is anode (+), shorter leg is cathode (-)
- Resistor protects both the LED and GPIO pin

**Testing:**
After wiring, run this MicroPython code to test:

```python
from machine import Pin, PWM
import time

tx = PWM(Pin(18))
tx.freq(38000)
tx.duty_u16(21845)  # 33% duty cycle

print("IR LED should be flashing - watch through phone camera")
time.sleep(3)

tx.deinit()
Pin(18, Pin.OUT).value(0)
print("Done")
```

Watch the IR LED through your phone camera during the test - you should see it glow purple/white.
