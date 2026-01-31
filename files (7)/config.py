# RV Thermostat Configuration
# ===========================

# WiFi Settings
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Temperature Settings (in Fahrenheit)
DEFAULT_HEAT_SETPOINT = 68
DEFAULT_COOL_SETPOINT = 75
MIN_SETPOINT = 50
MAX_SETPOINT = 90

# Hysteresis (prevents rapid cycling)
HYSTERESIS = 1.5

# Short-cycle protection (minimum seconds between state changes)
MIN_CYCLE_TIME = 180  # 3 minutes

# Sensor Settings
SENSOR_READ_INTERVAL = 5  # seconds between readings

# Pin Assignments
# I2C for BMP280 and OLED
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
I2C_FREQ = 400000

# DHT11 for humidity
DHT11_PIN = 16

# Relay pins
RELAY_FURNACE_PIN = 20
RELAY_ROOFTOP_AC_PIN = 21

# IR pins
IR_LED_PIN = 18
IR_RECEIVER_PIN = 19

# I2C Addresses
BMP280_ADDR = 0x76  # Some modules use 0x77
OLED_ADDR = 0x3C

# Display Settings
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

# Operating Modes
MODE_OFF = 0
MODE_HEAT = 1
MODE_COOL = 2
MODE_AUTO = 3

MODE_NAMES = {
    MODE_OFF: "OFF",
    MODE_HEAT: "HEAT", 
    MODE_COOL: "COOL",
    MODE_AUTO: "AUTO"
}

# Cooling system types
COOL_SYSTEM_ROOFTOP = 0
COOL_SYSTEM_PORTABLE = 1
COOL_SYSTEM_NAMES = {
    COOL_SYSTEM_ROOFTOP: "Rooftop",
    COOL_SYSTEM_PORTABLE: "Portable"
}
