# ESP32 Remote - Main Entry Point
# ================================
#
# Controls: Furnace relay, Rooftop AC relay, Portable AC via IR
# Boost mode: Portable unit activates when temp exceeds setpoint by 10F

import time
import network
from machine import Pin, I2C

import config
from sensor import SensorHub
from ssd1306 import SSD1306_I2C
from display import ThermostatDisplay
from thermostat import ThermostatController
from ir_whynter import WhynterIR
from webserver import RemoteAPI


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
    print("ESP32 Remote starting...")
    print(f"DRY_RUN: {config.DRY_RUN}")
    print(f"BOOST_THRESHOLD: {config.BOOST_THRESHOLD}F")

    # Initialize I2C
    i2c = I2C(0,
              sda=Pin(config.I2C_SDA_PIN),
              scl=Pin(config.I2C_SCL_PIN),
              freq=config.I2C_FREQ)

    # Scan I2C bus
    devices = i2c.scan()
    print(f"I2C devices: {[hex(d) for d in devices]}")

    # Initialize OLED display
    display = None
    try:
        oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c, config.OLED_ADDR)
        display = ThermostatDisplay(oled)
        display.draw_startup()
    except Exception as e:
        print(f"OLED init failed: {e}")

    # Initialize sensors (BMP280 + DHT11)
    sensor = SensorHub(i2c)
    sensor_status = sensor.get_status()
    print(f"Sensors: BMP280={sensor_status['bmp280']}, DHT11={sensor_status['dht11']}")

    # Connect to WiFi
    ip = connect_wifi(display)

    # Initialize IR transmitter for Whynter portable AC
    ir = WhynterIR(config.IR_LED_PIN)
    print(f"IR module on GPIO {config.IR_LED_PIN}")
    print(f"Learned IR codes: {ir.get_codes()}")

    # Initialize thermostat controller
    thermostat = ThermostatController()
    thermostat.set_ir_transmitter(ir)

    # Initialize API server (share IR instance)
    api = RemoteAPI(thermostat, ir)
    if ip:
        api.start(80)
        print(f"API: http://{ip}/api/status")

    # Main loop
    last_sensor_read = 0
    last_status_print = 0

    print("ESP32 Remote running... Press Ctrl+C to stop")
    print(f"Furnace relay: GPIO {config.RELAY_FURNACE_PIN}")
    print(f"Rooftop AC relay: GPIO {config.RELAY_ROOFTOP_AC_PIN}")

    while True:
        try:
            # Handle API requests
            api.handle_requests()

            now = time.time()

            # Read sensors periodically
            if now - last_sensor_read >= config.SENSOR_READ_INTERVAL:
                temp_f, humidity, pressure = sensor.read()
                thermostat.update_readings(temp_f, humidity, pressure)
                last_sensor_read = now

                # Run control logic
                thermostat.run_control_loop()

                # Update display
                if display and temp_f is not None:
                    display.draw_main_screen(
                        temp_f, humidity, pressure,
                        thermostat.mode,
                        thermostat.heat_setpoint,
                        thermostat.cool_setpoint,
                        thermostat.heating_active,
                        thermostat.cooling_active
                    )

            # Print status periodically
            if config.DEBUG and (now - last_status_print >= 30):
                status = thermostat.get_status()
                temp_str = f"{status['temp']:.1f}" if status['temp'] is not None else "None"
                print(f"Temp: {temp_str}F, Mode: {status['mode_name']}, Heat: {status['heating_active']}, Cool: {status['cooling_active']}, Boost: {status['boost_active']}")
                last_status_print = now

            time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopping...")
            thermostat.set_mode(config.MODE_OFF)
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
