# RV Thermostat - Main Entry Point
# ================================
# 
# Upload all .py files to your Pico W, then reset.
# Connect to the WiFi and open the IP address in your browser.

import time
import network
from machine import Pin, I2C

import config
from sensor import SensorHub
from ssd1306 import SSD1306_I2C
from display import ThermostatDisplay
from remote_client import RemoteClient
from thermostat_remote import RemoteThermostatController
from webserver import ThermostatWebServer
from scheduler import Scheduler

# Remote ESP32 IP
REMOTE_IP = "192.168.71.153"


def connect_wifi(display):
    """Connect to WiFi network with static IP"""
    wlan = network.WLAN(network.STA_IF)

    # ESP32 requires proper init sequence
    wlan.active(False)
    time.sleep(0.5)
    wlan.active(True)
    time.sleep(1)

    # Configure static IP before connecting
    wlan.ifconfig((config.STATIC_IP, config.SUBNET_MASK, config.GATEWAY, config.DNS_SERVER))
    print(f"Static IP configured: {config.STATIC_IP}")

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Already connected: {ip}")
        if display:
            display.draw_wifi_status(True, ip)
        return ip

    print(f"Connecting to {config.WIFI_SSID}...")
    if display:
        display.draw_wifi_status(False)

    # ESP32 needs disconnect before connect
    wlan.disconnect()
    time.sleep(0.5)

    try:
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    except OSError as e:
        print(f"Connect error: {e}, retrying...")
        time.sleep(1)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    # Wait for connection with timeout
    max_wait = 20
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print(".", end="")
        time.sleep(1)

    if not wlan.isconnected():
        print("\nWiFi connection failed!")
        if display:
            display.draw_error("WiFi Failed")
        return None

    ip = wlan.ifconfig()[0]
    print(f"\nConnected: {ip}")
    if display:
        display.draw_wifi_status(True, ip)
    time.sleep(2)
    return ip


def main():
    """Main entry point"""
    # Initialize I2C
    i2c = I2C(0, 
              sda=Pin(config.I2C_SDA_PIN), 
              scl=Pin(config.I2C_SCL_PIN), 
              freq=config.I2C_FREQ)
    
    # Initialize OLED display
    try:
        oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c, config.OLED_ADDR)
        display = ThermostatDisplay(oled)
        display.draw_startup()
    except Exception as e:
        print(f"OLED init failed: {e}")
        display = None
    
    # Initialize sensors (BME280/BMP280)
    sensor = SensorHub(i2c)
    sensor_status = sensor.get_status()
    print(f"Sensor: {sensor_status['sensor_type']}")
    
    # Connect to WiFi
    if display:
        ip = connect_wifi(display)
    else:
        ip = None
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            time.sleep(10)
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
    
    # Initialize remote ESP32 client for relay/IR control
    remote = RemoteClient(REMOTE_IP)
    print(f"Remote ESP32 at {REMOTE_IP}")

    # Initialize thermostat controller (controls remote ESP32)
    thermostat = RemoteThermostatController(remote)

    # Initialize scheduler
    scheduler = Scheduler(thermostat)

    # Initialize web server (pass remote client for direct API access)
    webserver = ThermostatWebServer(thermostat, scheduler, remote)
    if ip:
        webserver.start()
        print(f"Open http://{ip} in your browser")
    
    # Main loop
    last_sensor_read = 0
    
    print("Thermostat running... Press Ctrl+C to stop")
    
    while True:
        try:
            # Handle web requests
            webserver.handle_requests()
            
            # Read sensors periodically
            now = time.time()
            if now - last_sensor_read >= config.SENSOR_READ_INTERVAL:
                temp_f, humidity, pressure = sensor.read()
                thermostat.update_readings(temp_f, humidity, pressure)
                last_sensor_read = now
                
                # Run scheduler (checks time-based mode changes)
                scheduler.run()

                # Run control logic
                thermostat.run_control_loop()
                
                # Update display
                if display:
                    display.draw_main_screen(
                        temp_f, humidity, pressure,
                        thermostat.mode,
                        thermostat.heat_setpoint,
                        thermostat.cool_setpoint,
                        thermostat.heating_active,
                        thermostat.cooling_active
                    )
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
