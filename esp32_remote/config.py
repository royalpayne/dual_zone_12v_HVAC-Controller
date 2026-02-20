# ESP32 Remote - Configuration
# ============================

# WiFi Settings (override in config_local.py)
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Static IP Configuration (ESP32 Remote - migrated from Pico W)
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

# Sensor calibration offsets (added to raw readings)
TEMP_OFFSET = 0.0       # degrees F
HUMIDITY_OFFSET = 0.0   # percent
PRESSURE_OFFSET = 0.0   # hPa

# Hysteresis (prevents rapid cycling)
HYSTERESIS = 1.5

# Boost mode - portable unit kicks in when temp exceeds setpoint by this amount
BOOST_THRESHOLD = 5  # degrees F
BOOST_STALL_TIME = 600  # seconds (10 min) - boost if rooftop AC runs this long with no temp drop

# Dehumidification (via Whynter cool mode - evaporates condensate out exhaust)
HUMIDITY_SETPOINT = 55      # % RH — trigger Whynter when exceeded
HUMIDITY_HYSTERESIS = 5     # % RH — turn off at setpoint minus this

# Apparent temperature: adjust cooling decisions based on humidity for comfort + efficiency
# Each 10% RH above 50% feels ~1°F warmer; below 50% feels ~1°F cooler
# Effect: AC runs sooner when humid (dehumidifies), rests longer when dry (saves energy)
HUMIDITY_COMFORT_FACTOR = 0.1  # °F per 1% RH deviation from 50%

# Short-cycle protection (minimum seconds between state changes)
MIN_CYCLE_TIME = 30  # 30 seconds

# Sensor Settings
SENSOR_READ_INTERVAL = 5  # seconds between readings

# Debug and dry-run modes
DEBUG = False
DRY_RUN = False

# ============================================================
# HARDWARE CONFIGURATION (ESP32-S3-N16R8 Pin Assignments)
# ============================================================
# GPIO 22-25 don't exist on ESP32-S3
# GPIO 26-32 reserved for SPI flash
# GPIO 33-37 reserved for Octal PSRAM
# GPIO 19/20 reserved for native USB

# I2C for BMP280 and OLED
I2C_SDA_PIN = 8
I2C_SCL_PIN = 9
I2C_FREQ = 400000

# Relay pins (GPIO 38-42: no strapping conflicts on ESP32-S3-N16R8)
RELAY_FURNACE_PIN = 38
RELAY_COMPRESSOR_PIN = 39       # Rooftop AC compressor — 120VAC via HL-52S relay
RELAY_FAN_LOW_PIN = 40          # Rooftop AC fan low speed — 120VAC via HL-52S relay
RELAY_FAN_HIGH_PIN = 41         # Rooftop AC fan high speed — 120VAC via HL-52S relay

# Relay polarity: All relays are active HIGH (value=1 = ON, value=0 = OFF)
# Relays 2-4 (GPIO 39-41) switch 120VAC directly to Brisk II (no Dometic control box)
# Relay 1 (GPIO 38) is dry contact closure for furnace (separate circuit)

# DS18B20 evaporator freeze sensor (1-Wire on GPIO 42)
FREEZE_SENSOR_PIN = 42          # DS18B20 data pin (needs 4.7K pull-up to 3.3V)
FREEZE_THRESHOLD = 32.0         # °F — cut compressor if evaporator drops below this
FREEZE_RECOVERY = 45.0          # °F — allow compressor restart above this temp
FREEZE_CHECK_INTERVAL = 5       # seconds between freeze sensor reads

# Broadlink RM4 Mini (WiFi IR blaster - replaces direct IR hardware)
BROADLINK_IP = None       # Set after discovery, or static IP in config_local.py
BROADLINK_TIMEOUT = 3     # UDP timeout seconds
BROADLINK_RETRIES = 3     # Retry count for failed commands

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

# Fan Speed (no medium - only 2 speeds to fit 5-wire cable)
FAN_OFF = 0
FAN_LOW = 1
FAN_HIGH = 2
FAN_AUTO = 3

FAN_NAMES = {
    FAN_OFF: "Off",
    FAN_LOW: "Low",
    FAN_HIGH: "High",
    FAN_AUTO: "Auto"
}

# Compressor protection (seconds)
COMPRESSOR_MIN_OFF_TIME = 180   # 3 minutes between off→on
FAN_PRE_RUN = 3                 # Fan starts 3s before compressor
FAN_POST_RUN = 30               # Fan runs 30s after compressor stops

# ============================================================
# LOCAL OVERRIDES
# ============================================================

try:
    from config_local import *
except ImportError:
    pass
