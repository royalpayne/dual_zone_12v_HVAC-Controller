# Thermostat Display UI
# Handles OLED screen layouts

import config


class ThermostatDisplay:
    def __init__(self, oled):
        self.oled = oled
        self.pressure_history = []  # Track pressure for trend
        self.max_history = 3  # Number of readings to track
    
    def clear(self):
        self.oled.fill(0)
    
    def show(self):
        self.oled.show()

    def draw_droplet(self, x, y):
        """Draw a small water droplet icon (7x9 pixels)"""
        # Draw droplet shape
        self.oled.pixel(x+3, y, 1)
        self.oled.pixel(x+2, y+1, 1)
        self.oled.pixel(x+4, y+1, 1)
        for i in range(5):
            self.oled.pixel(x+1+i, y+2, 1)
        for i in range(7):
            self.oled.pixel(x+i, y+3, 1)
            self.oled.pixel(x+i, y+4, 1)
            self.oled.pixel(x+i, y+5, 1)
        for i in range(5):
            self.oled.pixel(x+1+i, y+6, 1)
        for i in range(3):
            self.oled.pixel(x+2+i, y+7, 1)
        self.oled.pixel(x+3, y+8, 1)

    def draw_arrow_up(self, x, y):
        """Draw upward arrow (5x7 pixels)"""
        self.oled.pixel(x+2, y, 1)
        self.oled.pixel(x+1, y+1, 1)
        self.oled.pixel(x+2, y+1, 1)
        self.oled.pixel(x+3, y+1, 1)
        self.oled.pixel(x, y+2, 1)
        self.oled.pixel(x+2, y+2, 1)
        self.oled.pixel(x+4, y+2, 1)
        for i in range(4):
            self.oled.pixel(x+2, y+3+i, 1)

    def draw_arrow_down(self, x, y):
        """Draw downward arrow (5x7 pixels)"""
        for i in range(4):
            self.oled.pixel(x+2, y+i, 1)
        self.oled.pixel(x, y+4, 1)
        self.oled.pixel(x+2, y+4, 1)
        self.oled.pixel(x+4, y+4, 1)
        self.oled.pixel(x+1, y+5, 1)
        self.oled.pixel(x+2, y+5, 1)
        self.oled.pixel(x+3, y+5, 1)
        self.oled.pixel(x+2, y+6, 1)

    def draw_arrow_right(self, x, y):
        """Draw horizontal arrow (7x5 pixels) - steady trend"""
        for i in range(5):
            self.oled.pixel(x+i, y+2, 1)
        self.oled.pixel(x+5, y+1, 1)
        self.oled.pixel(x+5, y+2, 1)
        self.oled.pixel(x+5, y+3, 1)
        self.oled.pixel(x+6, y+2, 1)

    def draw_large_text(self, text, x, y, scale=2):
        """Draw text at larger size by scaling pixels"""
        # Create temporary buffer to render normal text
        import framebuf

        # Calculate buffer size (8 pixels wide per char, 8 pixels tall)
        width = len(text) * 8
        height = 8
        temp_buffer = bytearray((width * height) // 8)
        temp_fb = framebuf.FrameBuffer(temp_buffer, width, height, framebuf.MONO_VLSB)

        # Draw text to temporary buffer
        temp_fb.text(text, 0, 0, 1)

        # Scale and copy to main display
        for py in range(height):
            for px in range(width):
                if temp_fb.pixel(px, py):
                    # Draw scaled pixel block
                    for sy in range(scale):
                        for sx in range(scale):
                            self.oled.pixel(x + px * scale + sx, y + py * scale + sy, 1)

    def get_pressure_trend(self, current_pressure):
        """
        Determine pressure trend: 'rising', 'falling', or 'steady'
        Threshold: >0.5 hPa change = rising/falling, else steady
        """
        if current_pressure is None:
            return 'steady'

        # Add current reading to history
        self.pressure_history.append(current_pressure)
        if len(self.pressure_history) > self.max_history:
            self.pressure_history.pop(0)

        # Need at least 2 readings to determine trend
        if len(self.pressure_history) < 2:
            return 'steady'

        # Compare current to average of previous readings
        avg_previous = sum(self.pressure_history[:-1]) / len(self.pressure_history[:-1])
        change = current_pressure - avg_previous

        if change > 0.5:
            return 'rising'
        elif change < -0.5:
            return 'falling'
        else:
            return 'steady'

    def draw_startup(self):
        """Show startup screen"""
        self.clear()
        self.oled.text("RV Thermostat", 10, 20)
        self.oled.text("Starting...", 20, 40)
        self.show()
    
    def draw_wifi_status(self, connected, ip=None):
        """Show WiFi connection status"""
        self.clear()
        if connected:
            self.oled.text("WiFi Connected", 5, 10)
            if ip:
                self.oled.text(ip, 5, 30)
                self.oled.text("Open in browser", 5, 50)
        else:
            self.oled.text("Connecting WiFi", 5, 20)
            self.oled.text(config.WIFI_SSID[:16], 5, 40)
        self.show()
    
    def draw_main_screen(self, temp_f, humidity, pressure, mode, setpoint,
                          heating_active, cooling_active):
        """Main thermostat display with graphical icons"""
        self.clear()

        # Temperature and humidity on top row (large text, 2x scale)
        if temp_f is not None:
            temp_str = f"{int(temp_f)}F"
        else:
            temp_str = "--F"
        self.draw_large_text(temp_str, 0, 0, 2)

        # Humidity in large text on right side
        if humidity is not None:
            hum_str = f"{int(humidity)}%"
        else:
            hum_str = "--%"
        # Position humidity on right side (128 - (3 chars * 16 pixels) = 80)
        self.draw_large_text(hum_str, 80, 0, 2)

        # Pressure with trend arrow
        if pressure is not None:
            # Convert hPa to inHg for US
            press_inhg = pressure * 0.02953
            trend = self.get_pressure_trend(pressure)

            # Draw trend arrow
            if trend == 'rising':
                self.draw_arrow_up(0, 20)
            elif trend == 'falling':
                self.draw_arrow_down(0, 20)
            else:  # steady
                self.draw_arrow_right(0, 22)

            # Draw pressure value
            self.oled.text(f"{press_inhg:.2f}\"", 10, 20)

        # Mode and setpoint
        mode_name = config.MODE_NAMES.get(mode, "???")
        self.oled.text(f"Mode: {mode_name}", 0, 34)
        self.oled.text(f"Set:  {setpoint:.0f}F", 0, 46)

        # Active status on bottom row
        if heating_active:
            self.oled.text(">>> HEATING <<<", 0, 56)
        elif cooling_active:
            self.oled.text(">>> COOLING <<<", 0, 56)
        else:
            self.oled.text("Idle", 0, 56)

        self.show()
    
    def draw_error(self, message):
        """Show error message"""
        self.clear()
        self.oled.text("ERROR", 40, 10)
        # Word wrap long messages
        words = message.split()
        line = ""
        y = 30
        for word in words:
            if len(line) + len(word) < 16:
                line += word + " "
            else:
                self.oled.text(line.strip(), 0, y)
                y += 12
                line = word + " "
        if line:
            self.oled.text(line.strip(), 0, y)
        self.show()
