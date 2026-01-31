# ESP32 Remote - Configuration
# ============================

# WiFi Settings (override in config_local.py)
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Static IP Configuration (ESP32 Remote - was Pico W)
STATIC_IP = "192.168.71.153"
SUBNET_MASK = "255.255.255.0"
GATEWAY = "192.168.71.1"
DNS_SERVER = "192.168.71.1"

# ESP32 Main Controller (for future API integration)
ESP32_IP = "192.168.1.100"
ESP32_PORT = 80

# Temperature Settings (in Fahrenheit)
DEFAULT_HEAT_SETPOINT = 68
DEFAULT_COOL_SETPOINT = 75
MIN_SETPOINT = 50
MAX_SETPOINT = 90

# Hysteresis (prevents rapid cycling)
HYSTERESIS = 1.5

# Boost mode - portable unit kicks in when temp exceeds setpoint by this amount
BOOST_THRESHOLD = 10  # degrees F

# Short-cycle protection (minimum seconds between state changes)
MIN_CYCLE_TIME = 180  # 3 minutes

# Sensor Settings
SENSOR_READ_INTERVAL = 5  # seconds between readings

# Debug and dry-run modes
DEBUG = False
DRY_RUN = True  # Enabled to prevent relay activation during testing

# ============================================================
# HARDWARE CONFIGURATION (ESP32 Pin Assignments)
# ============================================================

# I2C for BMP280 and OLED (ESP32 defaults)
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
I2C_FREQ = 400000

# DHT11 for humidity
DHT11_PIN = 4

# Relay pins
RELAY_FURNACE_PIN = 25
RELAY_ROOFTOP_AC_PIN = 26

# IR pins
IR_LED_PIN = 18           # IR transmitter
IR_RECEIVER_PIN = 19      # IR receiver (optional, for future use)

# I2C Addresses
BMP280_ADDR = 0x76
OLED_ADDR = 0x3C

# Display Settings
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

# ============================================================
# CONSTANTS
# ============================================================

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

# ============================================================
# LOCAL OVERRIDES
# ============================================================

try:
    from config_local import *
except ImportError:
    pass
