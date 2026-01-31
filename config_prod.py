# Production Environment Configuration
# =====================================
#
# Settings for deployed RV thermostat.
# These override the defaults in config.py when ENV=prod

CONFIG = {
    # WiFi - your RV's network
    "WIFI_SSID": "YOUR_RV_WIFI_SSID",
    "WIFI_PASSWORD": "YOUR_RV_WIFI_PASSWORD",

    # Production settings
    "DEBUG": False,
    "DRY_RUN": False,
}
