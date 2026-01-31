# RV Thermostat - Pico W Trigger (Living Room)
# =============================================
# Provides: DHT11 sensor + relay control
# Receives commands from ESP32 main controller
#
# Wiring:
#   DHT11: S -> GPIO 16, + -> 3.3V, - -> GND
#   Relay IN1 (Furnace): GPIO 20
#   Relay IN2 (Rooftop AC): GPIO 21
#   Relay VCC: 5V (from VBUS or external)
#   Relay GND: GND

import network
import socket
import json
import time
from machine import Pin
import dht

# ===== CONFIGURATION =====
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

DHT_PIN = 16
RELAY_FURNACE = 20
RELAY_ROOFTOP = 21

# ===== SETUP =====
sensor = dht.DHT11(Pin(DHT_PIN))

relay_furnace = Pin(RELAY_FURNACE, Pin.OUT)
relay_rooftop = Pin(RELAY_ROOFTOP, Pin.OUT)
relay_furnace.value(1)  # OFF (active low)
relay_rooftop.value(1)

led = Pin("LED", Pin.OUT)

# Sensor cache
last_temp = None
last_hum = None
last_read = 0


def read_sensor():
    global last_temp, last_hum, last_read
    now = time.ticks_ms()
    if time.ticks_diff(now, last_read) > 2000:
        try:
            sensor.measure()
            last_temp = sensor.temperature() * 9/5 + 32
            last_hum = sensor.humidity()
            last_read = now
        except Exception as e:
            print(f"Sensor: {e}")
    return last_temp, last_hum


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Connected: {ip}")
        return ip
    
    print(f"Connecting to {WIFI_SSID}...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
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


def handle(req):
    temp, hum = read_sensor()
    
    # GET /status
    if 'GET /status' in req:
        data = {
            'temp': temp,
            'humidity': hum,
            'furnace': relay_furnace.value() == 0,
            'rooftop': relay_rooftop.value() == 0
        }
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}"
    
    # Relay control
    if '/relay/furnace/on' in req:
        relay_furnace.value(0)
        print("Furnace ON")
        return "HTTP/1.1 200 OK\r\n\r\nOK"
    
    if '/relay/furnace/off' in req:
        relay_furnace.value(1)
        print("Furnace OFF")
        return "HTTP/1.1 200 OK\r\n\r\nOK"
    
    if '/relay/rooftop/on' in req:
        relay_rooftop.value(0)
        print("Rooftop ON")
        return "HTTP/1.1 200 OK\r\n\r\nOK"
    
    if '/relay/rooftop/off' in req:
        relay_rooftop.value(1)
        print("Rooftop OFF")
        return "HTTP/1.1 200 OK\r\n\r\nOK"
    
    if '/relay/all/off' in req:
        relay_furnace.value(1)
        relay_rooftop.value(1)
        print("All OFF")
        return "HTTP/1.1 200 OK\r\n\r\nOK"
    
    # Status page
    html = f"""<!DOCTYPE html>
<html><head><title>Pico Trigger</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:20px}}</style>
</head><body>
<h1>Pico W - Living Room</h1>
<p>Temperature: {temp:.1f if temp else '--'}F</p>
<p>Humidity: {hum if hum else '--'}%</p>
<p>Furnace: {'ON' if relay_furnace.value()==0 else 'OFF'}</p>
<p>Rooftop AC: {'ON' if relay_rooftop.value()==0 else 'OFF'}</p>
<h3>API:</h3>
<ul>
<li>GET /status - JSON data</li>
<li>GET /relay/furnace/on|off</li>
<li>GET /relay/rooftop/on|off</li>
<li>GET /relay/all/off</li>
</ul>
</body></html>"""
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"


def main():
    ip = connect_wifi()
    if not ip:
        print("No WiFi - cannot start")
        return
    
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('', 80))
    srv.listen(5)
    print(f"Server: http://{ip}")
    
    # Ready blink
    for _ in range(3):
        led.toggle()
        time.sleep(0.2)
    led.value(0)
    
    while True:
        try:
            cl, addr = srv.accept()
            cl.settimeout(2)
            try:
                req = cl.recv(1024).decode()
                resp = handle(req)
                cl.send(resp.encode())
            except Exception as e:
                print(f"Req err: {e}")
            finally:
                cl.close()
        except Exception as e:
            pass
        time.sleep(0.01)


if __name__ == "__main__":
    main()
