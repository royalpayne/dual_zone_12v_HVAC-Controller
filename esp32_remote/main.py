# ESP32 Remote - Main Entry Point
# ================================
#
# Controls: Furnace relay, Rooftop AC relay, Portable AC + Heater via Broadlink IR
# Whynter portable AC: Cool, Dehum, Heat modes
# Dr. Heater: Power on/off

import time
import network
from machine import Pin, I2C

import config
from sensor import SensorHub
from ssd1306 import SSD1306_I2C
from display import ThermostatDisplay
from thermostat import ThermostatController
from broadlink_client import BroadlinkClient
from ir_whynter import WhynterIR
from ir_heater import HeaterController
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

    # Initialize sensors (BME280/BMP280)
    sensor = SensorHub(i2c)
    sensor_status = sensor.get_status()
    print(f"Sensor: {sensor_status['sensor_type']}")

    # Connect to WiFi
    ip = connect_wifi(display)

    # Start WebREPL for over-the-air updates (port 8266)
    if ip:
        import webrepl
        webrepl.start()
        print(f"WebREPL: ws://{ip}:8266")

    # Initialize Broadlink RM4 Mini (WiFi IR blaster)
    bl = BroadlinkClient()
    try:
        bl.auth()
        print(f"Broadlink connected at {bl.ip}")
    except Exception as e:
        print(f"Broadlink init failed: {e} (will retry on first use)")

    # Initialize Whynter portable AC controller
    whynter = WhynterIR(bl)
    print(f"Whynter IR codes: {whynter.get_codes()}")

    # Initialize Dr. Heater controller
    heater = HeaterController(bl)
    print(f"Heater IR codes: {heater.get_codes()}")

    # Initialize DS18B20 evaporator freeze sensor (GPIO 42)
    ds_sensor = None
    ds_rom = None
    try:
        import onewire
        import ds18x20
        ds_pin = Pin(config.FREEZE_SENSOR_PIN)
        ds_bus = onewire.OneWire(ds_pin)
        ds_sensor = ds18x20.DS18X20(ds_bus)
        roms = ds_sensor.scan()
        if roms:
            ds_rom = roms[0]
            print(f"DS18B20 freeze sensor found: {ds_rom.hex()}")
        else:
            print("DS18B20 not found on bus — freeze protection software-only disabled")
            ds_sensor = None
    except Exception as e:
        print(f"DS18B20 init failed: {e} — freeze protection software-only disabled")

    # Initialize thermostat controller
    thermostat = ThermostatController()
    thermostat.set_ir_transmitter(whynter)
    thermostat.set_heater_controller(heater)

    # Initialize API server
    api = RemoteAPI(thermostat, whynter=whynter, heater=heater, broadlink=bl)
    if ip:
        api.start(80)
        print(f"API: http://{ip}/api/status")

    # Main loop
    last_sensor_read = 0
    last_status_print = 0
    last_bl_keepalive = time.time()
    last_bl_sensor_read = 0
    last_freeze_read = 0

    print("ESP32 Remote running... Press Ctrl+C to stop")
    print(f"Furnace relay: GPIO {config.RELAY_FURNACE_PIN}")
    print(f"Compressor relay: GPIO {config.RELAY_COMPRESSOR_PIN}")
    print(f"Fan relays: Low={config.RELAY_FAN_LOW_PIN}, High={config.RELAY_FAN_HIGH_PIN}")
    print(f"Freeze sensor: GPIO {config.FREEZE_SENSOR_PIN} ({'found' if ds_sensor else 'not found'})")

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
                if display:
                    display.draw_main_screen(
                        temp_f, humidity, pressure,
                        thermostat.mode,
                        thermostat.heat_setpoint,
                        thermostat.cool_setpoint,
                        thermostat.heating_active,
                        thermostat.cooling_active
                    )

            # Read DS18B20 evaporator freeze sensor
            if ds_sensor and ds_rom and (now - last_freeze_read >= config.FREEZE_CHECK_INTERVAL):
                try:
                    ds_sensor.convert_temp()
                    time.sleep_ms(750)  # DS18B20 conversion time
                    temp_c = ds_sensor.read_temp(ds_rom)
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    thermostat.update_evap_temp(temp_f)
                except Exception as e:
                    print(f"DS18B20 read error: {e}")
                last_freeze_read = now

            # Read Broadlink HTS2 sensor (every 30 seconds)
            if now - last_bl_sensor_read >= 30:
                try:
                    result = bl.check_sensors()
                    if result:
                        thermostat.update_bl_readings(result[0], result[1])
                except Exception as e:
                    print(f"BL sensor error: {e}")
                last_bl_sensor_read = now

            # Broadlink keepalive (prevents sleep mode)
            if now - last_bl_keepalive >= 300:
                bl.ping()
                last_bl_keepalive = now

            # Print status periodically
            if config.DEBUG and (now - last_status_print >= 30):
                status = thermostat.get_status()
                temp_str = f"{status['temp']:.1f}" if status['temp'] is not None else "None"
                print(f"Temp: {temp_str}F, Mode: {status['mode_name']}, Heat: {status['heating_active']}, Cool: {status['cooling_active']}, Whynter: {status['whynter_mode_name']}")
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
