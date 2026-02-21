# ESP32 Remote - Buzzer Alert System
# ===================================
# Passive buzzer on GPIO 21 for audio feedback

import time
from machine import Pin, PWM
import config


class Buzzer:
    """
    Passive buzzer controller for audio alerts

    Alert types:
    - Freeze warning: 3 beeps
    - System error: 5 beeps
    - Mode change confirmation: 1 beep
    - Temperature alert: 2 beeps
    """

    def __init__(self, pin=None):
        if pin is None:
            pin = config.BUZZER_PIN

        self.pwm = PWM(Pin(pin))
        self.pwm.duty(0)  # Off initially

        # Alert tracking
        self.last_freeze_alert_time = 0
        self.freeze_alert_interval = 300  # seconds (5 min between freeze alerts)
        self.enabled = True

    def tone(self, frequency, duration_ms):
        """Play a tone at specified frequency for duration"""
        if not self.enabled:
            return

        self.pwm.freq(frequency)
        self.pwm.duty(512)  # 50% duty cycle
        time.sleep_ms(duration_ms)
        self.pwm.duty(0)

    def beep(self, count=1, tone_ms=100, gap_ms=100):
        """
        Play a series of beeps

        Args:
            count: number of beeps
            tone_ms: duration of each beep
            gap_ms: silence between beeps
        """
        if not self.enabled:
            return

        for i in range(count):
            self.tone(2000, tone_ms)  # 2kHz tone
            if i < count - 1:  # Don't delay after last beep
                time.sleep_ms(gap_ms)

    def freeze_alert(self):
        """
        Freeze warning alert (3 beeps)
        Rate-limited to prevent continuous beeping
        """
        current_time = time.time()

        if current_time - self.last_freeze_alert_time < self.freeze_alert_interval:
            return  # Skip if we've alerted recently

        self.beep(count=3, tone_ms=200, gap_ms=200)
        self.last_freeze_alert_time = current_time
        print("⚠ Freeze alert sounded")

    def error_alert(self):
        """System error alert (5 beeps)"""
        self.beep(count=5, tone_ms=100, gap_ms=100)
        print("⚠ Error alert sounded")

    def confirmation_beep(self):
        """Single beep for mode change confirmation"""
        self.beep(count=1, tone_ms=50)

    def temperature_alert(self):
        """Temperature warning (2 beeps)"""
        self.beep(count=2, tone_ms=150, gap_ms=150)
        print("⚠ Temperature alert sounded")

    def enable(self):
        """Enable buzzer alerts"""
        self.enabled = True

    def disable(self):
        """Disable buzzer alerts (silent mode)"""
        self.enabled = False
        self.pwm.duty(0)  # Ensure buzzer is off

    def is_enabled(self):
        """Check if buzzer is enabled"""
        return self.enabled
