# Component Tests for RV Thermostat
# Run individual tests to verify wiring

from machine import Pin, I2C
import time
import config


def test_i2c_scan():
    """Scan I2C bus for devices"""
    print("\n=== I2C Scan ===")
    i2c = I2C(0, 
              sda=Pin(config.I2C_SDA_PIN), 
              scl=Pin(config.I2C_SCL_PIN), 
              freq=config.I2C_FREQ)
    devices = i2c.scan()
    
    if not devices:
        print("No I2C devices found!")
        print(f"Check wiring: SDA=GPIO{config.I2C_SDA_PIN}, SCL=GPIO{config.I2C_SCL_PIN}")
        return False
    
    print(f"Found {len(devices)} device(s):")
    for addr in devices:
        name = "Unknown"
        if addr == 0x76 or addr == 0x77:
            name = "BMP280/BME280"
        elif addr == 0x3C or addr == 0x3D:
            name = "OLED SSD1306"
        print(f"  0x{addr:02X} - {name}")
    return True


def test_bmp280():
    """Test BMP280 sensor"""
    print("\n=== BMP280 Test ===")
    try:
        from bmp280 import BMP280
        i2c = I2C(0, 
                  sda=Pin(config.I2C_SDA_PIN), 
                  scl=Pin(config.I2C_SCL_PIN), 
                  freq=config.I2C_FREQ)
        
        sensor = BMP280(i2c, config.BMP280_ADDR)
        
        for i in range(3):
            temp_f, pressure = sensor.read_fahrenheit()
            press_inhg = pressure * 0.02953
            print(f"  Reading {i+1}: {temp_f:.1f}°F, {press_inhg:.2f} inHg")
            time.sleep(1)
        
        print("BMP280 OK!")
        return True
    except Exception as e:
        print(f"BMP280 Error: {e}")
        return False


def test_dht11():
    """Test DHT11 sensor"""
    print("\n=== DHT11 Test ===")
    try:
        import dht
        sensor = dht.DHT11(Pin(config.DHT11_PIN))
        
        for i in range(3):
            sensor.measure()
            temp_c = sensor.temperature()
            humidity = sensor.humidity()
            temp_f = temp_c * 9/5 + 32
            print(f"  Reading {i+1}: {temp_f:.1f}°F, {humidity}% RH")
            time.sleep(2)
        
        print("DHT11 OK!")
        return True
    except Exception as e:
        print(f"DHT11 Error: {e}")
        return False


def test_oled():
    """Test OLED display"""
    print("\n=== OLED Test ===")
    try:
        from ssd1306 import SSD1306_I2C
        i2c = I2C(0, 
                  sda=Pin(config.I2C_SDA_PIN), 
                  scl=Pin(config.I2C_SCL_PIN), 
                  freq=config.I2C_FREQ)
        
        oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c, config.OLED_ADDR)
        
        oled.fill(0)
        oled.text("RV Thermostat", 10, 10)
        oled.text("OLED Test OK!", 10, 30)
        oled.show()
        
        print("Check display - you should see text")
        print("OLED OK!")
        return True
    except Exception as e:
        print(f"OLED Error: {e}")
        return False


def test_relays():
    """Test relay outputs"""
    print("\n=== Relay Test ===")
    print("WARNING: This will toggle relays!")
    print("Press Ctrl+C to skip")
    
    try:
        time.sleep(2)
        
        furnace = Pin(config.RELAY_FURNACE_PIN, Pin.OUT)
        rooftop = Pin(config.RELAY_ROOFTOP_AC_PIN, Pin.OUT)
        
        # Start inactive (HIGH for active-low relays)
        furnace.value(1)
        rooftop.value(1)
        
        print("  Testing furnace relay...")
        furnace.value(0)  # Activate
        time.sleep(1)
        furnace.value(1)  # Deactivate
        
        print("  Testing rooftop AC relay...")
        rooftop.value(0)  # Activate
        time.sleep(1)
        rooftop.value(1)  # Deactivate
        
        print("Did you hear the relays click?")
        print("Relays OK!")
        return True
    except KeyboardInterrupt:
        print("Skipped")
        return True
    except Exception as e:
        print(f"Relay Error: {e}")
        return False


def test_ir_receiver():
    """Test IR receiver"""
    print("\n=== IR Receiver Test ===")
    print("Point a remote at the receiver and press a button...")
    
    try:
        ir = Pin(config.IR_RECEIVER_PIN, Pin.IN)
        print(f"Initial state: {ir.value()} (should be 1)")
        
        changes = 0
        last = ir.value()
        start = time.ticks_ms()
        
        print("Waiting 10 seconds for signal...")
        while time.ticks_diff(time.ticks_ms(), start) < 10000:
            v = ir.value()
            if v != last:
                changes += 1
                last = v
        
        if changes > 10:
            print(f"Detected {changes} signal transitions")
            print("IR Receiver OK!")
            return True
        else:
            print(f"Only {changes} transitions - no signal detected")
            print("Check wiring or try different remote")
            return False
    except Exception as e:
        print(f"IR Receiver Error: {e}")
        return False


def test_sensors():
    """Test combined sensor module"""
    print("\n=== Combined Sensor Test ===")
    try:
        from sensor import SensorHub
        i2c = I2C(0, 
                  sda=Pin(config.I2C_SDA_PIN), 
                  scl=Pin(config.I2C_SCL_PIN), 
                  freq=config.I2C_FREQ)
        
        hub = SensorHub(i2c)
        status = hub.get_status()
        print(f"  BMP280: {'OK' if status['bmp280'] else 'MISSING'}")
        print(f"  DHT11:  {'OK' if status['dht11'] else 'MISSING'}")
        
        print("\nReadings:")
        for i in range(3):
            temp_f, humidity, pressure = hub.read()
            press_str = f"{pressure * 0.02953:.2f} inHg" if pressure else "N/A"
            hum_str = f"{humidity}%" if humidity else "N/A"
            temp_str = f"{temp_f:.1f}°F" if temp_f else "N/A"
            print(f"  {temp_str}, {hum_str}, {press_str}")
            time.sleep(2)
        
        print("Sensor Hub OK!")
        return True
    except Exception as e:
        print(f"Sensor Hub Error: {e}")
        return False


def test_all():
    """Run all tests"""
    print("=" * 40)
    print("RV Thermostat Component Tests")
    print("=" * 40)
    
    results = {}
    
    results['I2C'] = test_i2c_scan()
    results['BMP280'] = test_bmp280()
    results['DHT11'] = test_dht11()
    results['Sensors'] = test_sensors()
    results['OLED'] = test_oled()
    results['Relays'] = test_relays()
    results['IR Receiver'] = test_ir_receiver()
    
    print("\n" + "=" * 40)
    print("Test Summary")
    print("=" * 40)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    return all_passed
