# RV Thermostat - ESP32 Main Controller
# =====================================
# Upload all files to ESP32, then reset

import time
import network
from machine import Pin, I2C
import dht

import config
from bmp280 import BMP280
from ssd1306 import SSD1306_I2C
from scheduler import Scheduler
from thermostat import Thermostat
from webserver import WebServer


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Connected: {ip}")
        return ip
    
    print(f"Connecting to {config.WIFI_SSID}...")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    
    for _ in range(20):
        if wlan.isconnected():
            break
        time.sleep(1)
        print(".", end="")
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\nConnected: {ip}")
        return ip
    
    print("\nWiFi failed!")
    return None


def main():
    # LED for status
    led = Pin(2, Pin.OUT)
    led.value(1)
    
    # I2C
    i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN), freq=config.I2C_FREQ)
    
    # Scan I2C
    devices = i2c.scan()
    print(f"I2C devices: {[hex(d) for d in devices]}")
    
    # OLED
    oled = None
    try:
        oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c, config.OLED_ADDR)
        oled.fill(0)
        oled.text("RV Thermostat", 10, 10)
        oled.text("Starting...", 20, 30)
        oled.show()
    except Exception as e:
        print(f"OLED error: {e}")
    
    # BMP280
    bmp = None
    try:
        bmp = BMP280(i2c, config.BMP280_ADDR)
        print("BMP280 OK")
    except Exception as e:
        print(f"BMP280 error: {e}")
    
    # DHT11
    dht_sensor = None
    try:
        dht_sensor = dht.DHT11(Pin(config.DHT_PIN))
        print("DHT11 OK")
    except Exception as e:
        print(f"DHT11 error: {e}")
    
    # WiFi
    if oled:
        oled.fill(0)
        oled.text("Connecting WiFi", 5, 20)
        oled.show()
    
    ip = connect_wifi()
    
    if oled and ip:
        oled.fill(0)
        oled.text("Connected!", 20, 10)
        oled.text(ip, 15, 30)
        oled.show()
        time.sleep(2)
    
    # Scheduler
    scheduler = Scheduler()
    scheduler.load()
    if ip:
        scheduler.sync_time()
    
    # Thermostat
    therm = Thermostat(scheduler)
    
    # Web server
    web = WebServer(therm)
    if ip:
        web.start()
    
    # Timers
    last_sensor = 0
    last_remote = 0
    last_sched = 0
    last_display = 0
    
    led.value(0)
    print("Running... Ctrl+C to stop")
    
    while True:
        try:
            web.poll()
            now = time.time()
            
            # Read local sensors
            if now - last_sensor >= config.SENSOR_READ_INTERVAL:
                temp_f = None
                humidity = None
                pressure = None
                
                if bmp:
                    try:
                        temp_f, pressure = bmp.read()
                    except:
                        pass
                
                if dht_sensor:
                    try:
                        dht_sensor.measure()
                        humidity = dht_sensor.humidity()
                        if temp_f is None:
                            temp_f = dht_sensor.temperature() * 9/5 + 32
                    except:
                        pass
                
                therm.update_local(temp_f, humidity, pressure)
                last_sensor = now
            
            # Fetch remote
            if now - last_remote >= 10:
                therm.fetch_remote()
                therm.run()
                last_remote = now
            
            # Update scheduler
            if now - last_sched >= 60:
                scheduler.update()
                last_sched = now
            
            # Update display
            if oled and now - last_display >= 2:
                oled.fill(0)
                
                # Time
                oled.text(f"{scheduler.get_day_str()} {scheduler.get_time_str()}", 0, 0)
                
                # Average temp
                if therm.avg_temp:
                    oled.text(f"{therm.avg_temp:.1f}F", 40, 16)
                else:
                    oled.text("--.-F", 40, 16)
                
                # Status
                if therm.heating:
                    oled.text("HEATING", 35, 32)
                elif therm.cooling:
                    oled.text("COOLING", 35, 32)
                else:
                    oled.text("Idle", 45, 32)
                
                # Mode and setpoints
                mode = config.MODE_NAMES.get(therm.mode, "?")
                oled.text(f"{mode} H:{therm.heat_setpoint} C:{therm.cool_setpoint}", 0, 48)
                
                # Schedule mode
                sched_name = config.SCHEDULE_MODE_NAMES.get(scheduler.current_mode, "?")
                if scheduler.hold_active:
                    sched_name += " HOLD"
                oled.text(sched_name, 0, 56)
                
                oled.show()
                last_display = now
            
            time.sleep(0.05)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
