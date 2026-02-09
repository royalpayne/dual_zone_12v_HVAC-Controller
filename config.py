# RV Thermostat Configuration
# ===========================
#
# Default settings - these can be overridden by environment-specific
# config files (config_dev.py, config_prod.py, config_test.py) or
# local overrides (config_local.py).
#
# Priority (highest to lowest):
#   1. config_local.py
#   2. config_{env}.py (based on current environment)
#   3. defaults below

# Import environment system
from env import get_env, is_dev, is_prod, is_test, load_env_config

# ============================================================
# DEFAULT VALUES (can be overridden by environment configs)
# ============================================================

# WiFi Settings
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Static IP Configuration (ESP32)
STATIC_IP = "192.168.71.152"
SUBNET_MASK = "255.255.255.0"
GATEWAY = "192.168.71.1"
DNS_SERVER = "192.168.71.1"

# Temperature Settings (in Fahrenheit)
DEFAULT_HEAT_SETPOINT = 68
DEFAULT_COOL_SETPOINT = 75
MIN_SETPOINT = 50
MAX_SETPOINT = 90

# Default operating mode at boot (0=OFF, 1=HEAT, 2=COOL, 3=AUTO)
DEFAULT_MODE = 3  # AUTO

# Sensor calibration offsets (added to raw readings)
TEMP_OFFSET = 0.0       # degrees F
HUMIDITY_OFFSET = 0.0   # percent
PRESSURE_OFFSET = 0.0   # hPa

# Hysteresis (prevents rapid cycling)
HYSTERESIS = 1.5

# Short-cycle protection (minimum seconds between state changes)
MIN_CYCLE_TIME = 30  # 30 seconds

# Sensor Settings
SENSOR_READ_INTERVAL = 10  # seconds between readings

# Debug and dry-run modes
DEBUG = False
DRY_RUN = False  # When True, don't actually control relays

# ============================================================
# HARDWARE CONFIGURATION (typically not overridden)
# ============================================================

# Pin Assignments (ESP32-S3)
# I2C for BME280 and OLED
I2C_SDA_PIN = 8
I2C_SCL_PIN = 9
I2C_FREQ = 400000

# Relay pins
RELAY_FURNACE_PIN = 25
RELAY_ROOFTOP_AC_PIN = 26

# IR pins
IR_LED_PIN = 18
IR_RECEIVER_PIN = 19

# I2C Addresses
BMP280_ADDR = 0x76  # Some modules use 0x77
OLED_ADDR = 0x3C

# Display Settings
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

# USB Battery Pack Keep-Alive (prevents auto-shutoff)
# Note: Most USB packs need 50-100mA to stay awake - use LiPo + TP4056 instead
KEEPALIVE_ENABLED = False
KEEPALIVE_PIN = 2  # Unused GPIO - connect 100-200 ohm resistor to GND
KEEPALIVE_INTERVAL = 5  # seconds between pulses
KEEPALIVE_PULSE_MS = 50  # pulse duration in milliseconds

# ============================================================
# CONSTANTS (not overridable)
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
# APPLY ENVIRONMENT OVERRIDES
# ============================================================

# Load and apply environment-specific configuration
_overrides = load_env_config()

# Apply overrides to module globals
_key = _value = None
for _key, _value in _overrides.items():
    if _key in globals():
        globals()[_key] = _value
        if DEBUG or _overrides.get("DEBUG", False):
            print(f"[config] Override: {_key} = {_value}")

# Clean up temporary variables
del _overrides, _key, _value
