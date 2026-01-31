# Thermostat Display UI
# Handles OLED screen layouts

import config


class ThermostatDisplay:
    def __init__(self, oled):
        self.oled = oled
    
    def clear(self):
        self.oled.fill(0)
    
    def show(self):
        self.oled.show()
    
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
        """Main thermostat display"""
        self.clear()
        
        # Temperature (large)
        if temp_f is not None:
            temp_str = f"{temp_f:.1f}F"
        else:
            temp_str = "--.-F"
        self.oled.text(temp_str, 0, 0)
        
        # Humidity
        if humidity is not None:
            hum_str = f"{humidity:.0f}%"
        else:
            hum_str = "--%"
        self.oled.text(hum_str, 80, 0)
        
        # Pressure (if available)
        if pressure is not None:
            # Convert hPa to inHg for US
            press_inhg = pressure * 0.02953
            self.oled.text(f"{press_inhg:.2f}inHg", 0, 12)
        
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
