# Test Environment Configuration
# ===============================
#
# Settings for automated testing and CI.
# These override the defaults in config.py when ENV=test

CONFIG = {
    # Test network (or mock)
    "WIFI_SSID": "TEST_NETWORK",
    "WIFI_PASSWORD": "TEST_PASSWORD",

    # Fast intervals for quick test cycles
    "SENSOR_READ_INTERVAL": 1,
    "MIN_CYCLE_TIME": 5,

    # Enable debug output
    "DEBUG": True,

    # Never control real hardware in tests
    "DRY_RUN": True,
}
