#!/bin/bash
# Thermostat auto-sync: set RTC alarm to wake laptop from sleep every 2 hours
# Install: sudo cp thermostat-rtcwake.sh /usr/lib/systemd/system-sleep/
#          sudo chmod +x /usr/lib/systemd/system-sleep/thermostat-rtcwake.sh

case "$1" in
    pre)
        # Set RTC alarm to wake in 2 hours (7200 seconds)
        /usr/sbin/rtcwake -m no -s 7200
        ;;
    post)
        # Nothing needed — systemd timer's Persistent=true handles sync on wake
        ;;
esac
