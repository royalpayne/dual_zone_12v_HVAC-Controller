# Quick diagnostic script
import network
import time

print("=== Pico Diagnostic ===")
print("1. Checking WiFi...")
wlan = network.WLAN(network.STA_IF)
print(f"  Connected: {wlan.isconnected()}")
if wlan.isconnected():
    print(f"  IP: {wlan.ifconfig()[0]}")

print("\n2. Testing imports...")
try:
    import config
    print(f"  ✓ config")
    print(f"    IR_LED_PIN: {config.IR_LED_PIN}")
except Exception as e:
    print(f"  ✗ config: {e}")

try:
    from ir_whynter import WhynterIR
    print(f"  ✓ ir_whynter.WhynterIR")
except Exception as e:
    print(f"  ✗ ir_whynter: {e}")

try:
    from webserver import PicoAPI
    print(f"  ✓ webserver.PicoAPI")
except Exception as e:
    print(f"  ✗ webserver: {e}")

try:
    from thermostat import ThermostatController
    print(f"  ✓ thermostat.ThermostatController")
except Exception as e:
    print(f"  ✗ thermostat: {e}")

print("\n3. Testing IR init...")
try:
    ir = WhynterIR(config.IR_LED_PIN)
    print(f"  ✓ IR initialized")
    print(f"    Learned codes: {ir.get_codes()}")
except Exception as e:
    print(f"  ✗ IR init failed: {e}")
    import sys
    sys.print_exception(e)

print("\n4. Testing API init...")
try:
    from thermostat import ThermostatController
    t = ThermostatController()
    api = PicoAPI(t, ir)
    print(f"  ✓ API initialized")
except Exception as e:
    print(f"  ✗ API init failed: {e}")
    import sys
    sys.print_exception(e)

print("\n5. Testing API start...")
try:
    api.start(80)
    print(f"  ✓ API server started on port 80")
    time.sleep(2)
    print(f"  Server should be accessible at http://{wlan.ifconfig()[0]}/api/ir/status")
except Exception as e:
    print(f"  ✗ API start failed: {e}")
    import sys
    sys.print_exception(e)

print("\n=== Diagnostic Complete ===")
print("Server is running. Press Ctrl+C to stop.")

# Keep running to maintain server
while True:
    api.handle_requests()
    time.sleep(0.1)
