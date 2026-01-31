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

        # Temperature (large)
        if temp_f is not None:
            temp_str = f"{temp_f:.1f}F"
        else:
            temp_str = "--.-F"
        self.oled.text(temp_str, 0, 0)

        # Humidity with droplet icon
        if humidity is not None:
            hum_str = f"{humidity:.0f}%"
        else:
            hum_str = "--%"
        self.draw_droplet(70, 0)  # Draw droplet icon
        self.oled.text(hum_str, 80, 0)

        # Pressure with trend arrow (if available)
        if pressure is not None:
            # Convert hPa to inHg for US
            press_inhg = pressure * 0.02953
            trend = self.get_pressure_trend(pressure)

            # Draw trend arrow
            if trend == 'rising':
                self.draw_arrow_up(0, 13)
            elif trend == 'falling':
                self.draw_arrow_down(0, 13)
            else:  # steady
                self.draw_arrow_right(0, 15)

            # Draw pressure value
            self.oled.text(f"{press_inhg:.2f}\"", 10, 12)

        # Mode and setpoint
        mode_name = config.MODE_NAMES.get(mode, "???")
        self.oled.text(f"Mode: {mode_name}", 0, 28)
        self.oled.text(f"Set:  {setpoint:.0f}F", 0, 40)

        # Active status
        if heating_active:
            self.oled.text(">>> HEATING <<<", 0, 54)
        elif cooling_active:
            self.oled.text(">>> COOLING <<<", 0, 54)
        else:
            self.oled.text("Idle", 0, 54)

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
