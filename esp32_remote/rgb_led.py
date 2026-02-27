# ESP32 Remote - RGB LED Status Indicator
# ========================================
# WS2812 RGB LED on GPIO 38 for visual system status

import time
from neopixel import NeoPixel
from machine import Pin
import config


class RGBStatusLED:
    """
    RGB LED status indicator using WS2812

    Status colors:
    - Red: Heating active
    - Blue: Cooling active
    - Green: Fan-only mode
    - Yellow: Auto mode
    - White: Idle/off
    - Blinking red: Freeze warning
    - Purple: System error
    - Orange: Communication failure
    """

    # Color definitions (R, G, B) - brightness scaled to ~15%
    COLORS = {
        'off': (0, 0, 0),
        'red': (38, 0, 0),          # Heating
        'blue': (0, 0, 38),         # Cooling
        'green': (0, 38, 0),        # Fan-only
        'yellow': (38, 38, 0),      # Auto mode
        'white': (38, 38, 38),      # Idle
        'purple': (38, 0, 38),      # Error
        'orange': (38, 18, 0),      # Communication failure
        'cyan': (0, 38, 38),        # Dehumidifier
    }

    def __init__(self, pin=None):
        if pin is None:
            pin = config.RGB_LED_PIN

        self.pixel = NeoPixel(Pin(pin), 1)  # Single WS2812 LED
        self.current_color = 'off'
        self.blink_state = False
        self.last_blink_time = 0
        self.blink_interval = 0.5  # seconds

        # Turn off LED on init
        self.set_color('off')

    def set_color(self, color_name):
        """Set LED to a solid color"""
        if color_name in self.COLORS:
            self.pixel[0] = self.COLORS[color_name]
            self.pixel.write()
            self.current_color = color_name

    def set_rgb(self, r, g, b):
        """Set LED to custom RGB values (0-255 each)"""
        # Scale down to 15% brightness
        self.pixel[0] = (int(r * 0.15), int(g * 0.15), int(b * 0.15))
        self.pixel.write()

    def blink(self, color_name):
        """
        Blink LED in specified color
        Call this repeatedly in a loop for continuous blinking
        """
        current_time = time.time()

        if current_time - self.last_blink_time >= self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time

            if self.blink_state:
                self.set_color(color_name)
            else:
                self.set_color('off')

    def update_status(self, thermostat_status, freeze_warning=False, comm_error=False):
        """
        Update LED based on thermostat status

        Colors: red=heating, blue=cooling, green=fan, yellow=auto,
                white=idle, purple=error, orange=comm failure, cyan=dehum
        """
        if freeze_warning:
            self.blink('red')
            return

        if comm_error:
            self.set_color('orange')
            return

        mode = thermostat_status.get('mode', 0)
        heating = thermostat_status.get('heating_active', False)
        cooling = thermostat_status.get('cooling_active', False)
        fan_only = thermostat_status.get('fan_only', False)
        dehum_active = thermostat_status.get('dehum_active', False)

        if heating:
            self.set_color('red')
        elif cooling:
            self.set_color('blue')
        elif dehum_active:
            self.set_color('cyan')
        elif fan_only:
            self.set_color('green')
        elif mode == config.MODE_AUTO:
            self.set_color('yellow')
        else:
            self.set_color('white')

    def off(self):
        """Turn off LED"""
        self.set_color('off')
