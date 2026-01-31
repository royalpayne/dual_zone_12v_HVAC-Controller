# Development Environment Configuration
# ======================================
#
# Settings for local development and testing.
# These override the defaults in config.py when ENV=dev

CONFIG = {
    # WiFi - use your development network
    "WIFI_SSID": "YOUR_DEV_WIFI_SSID",
    "WIFI_PASSWORD": "YOUR_DEV_WIFI_PASSWORD",

    # Faster sensor reads for development
    "SENSOR_READ_INTERVAL": 2,

    # Shorter cycle time for testing (30 seconds instead of 3 minutes)
    "MIN_CYCLE_TIME": 30,

    # Debug mode - enables extra logging
    "DEBUG": True,

    # Disable actual relay control in dev (safety)
    "DRY_RUN": True,
}
