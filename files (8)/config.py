# RV Thermostat - ESP32 Main Controller Configuration
# ==================================================

# WiFi Settings
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Pico W Trigger Settings
PICO_IP = "192.168.71.151"  # Update with your Pico's IP
PICO_PORT = 80

# Temperature Settings (Fahrenheit)
DEFAULT_HEAT_SETPOINT = 68
DEFAULT_COOL_SETPOINT = 75
MIN_SETPOINT = 50
MAX_SETPOINT = 90

# Hysteresis and timing
HYSTERESIS = 1.5
MIN_CYCLE_TIME = 180  # 3 minutes

# Sensor read interval
SENSOR_READ_INTERVAL = 5

# Pin Assignments - ESP32
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
I2C_FREQ = 400000

DHT_PIN = 4
IR_LED_PIN = 18
IR_RECEIVER_PIN = 19

# I2C Addresses
BMP280_ADDR = 0x76
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

# Location names
LOCATION_LOCAL = "Kitchen"
LOCATION_REMOTE = "Living Room"

# Schedule Modes
SCHEDULE_HOME = 0
SCHEDULE_AWAY = 1
SCHEDULE_SLEEP = 2

SCHEDULE_MODE_NAMES = {
    SCHEDULE_HOME: "Home",
    SCHEDULE_AWAY: "Away",
    SCHEDULE_SLEEP: "Sleep"
}

# Temperature presets for each schedule mode (heat, cool)
SCHEDULE_TEMPS = {
    SCHEDULE_HOME: (70, 74),
    SCHEDULE_AWAY: (62, 80),
    SCHEDULE_SLEEP: (66, 72)
}

# Default weekly schedule
# Format: [(hour, minute, mode), ...]
# Days: 0=Monday ... 6=Sunday
DEFAULT_SCHEDULE = {
    0: [(6, 0, SCHEDULE_HOME), (8, 0, SCHEDULE_AWAY), (17, 0, SCHEDULE_HOME), (22, 0, SCHEDULE_SLEEP)],
    1: [(6, 0, SCHEDULE_HOME), (8, 0, SCHEDULE_AWAY), (17, 0, SCHEDULE_HOME), (22, 0, SCHEDULE_SLEEP)],
    2: [(6, 0, SCHEDULE_HOME), (8, 0, SCHEDULE_AWAY), (17, 0, SCHEDULE_HOME), (22, 0, SCHEDULE_SLEEP)],
    3: [(6, 0, SCHEDULE_HOME), (8, 0, SCHEDULE_AWAY), (17, 0, SCHEDULE_HOME), (22, 0, SCHEDULE_SLEEP)],
    4: [(6, 0, SCHEDULE_HOME), (8, 0, SCHEDULE_AWAY), (17, 0, SCHEDULE_HOME), (23, 0, SCHEDULE_SLEEP)],
    5: [(7, 0, SCHEDULE_HOME), (23, 0, SCHEDULE_SLEEP)],
    6: [(7, 0, SCHEDULE_HOME), (22, 0, SCHEDULE_SLEEP)],
}

# Timezone offset from UTC (EST=-5, CST=-6, MST=-7, PST=-8)
TIMEZONE_OFFSET = -5
NTP_HOST = "pool.ntp.org"
