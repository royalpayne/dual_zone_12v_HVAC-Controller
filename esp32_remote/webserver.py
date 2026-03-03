# ESP32 Remote - Web API Server
# ==============================
# Serves local thermostat status and accepts control commands

import socket
import json
import config


class RemoteAPI:
    """Simple web API for remote ESP32"""

    def __init__(self, thermostat, whynter=None, heater=None, broadlink=None):
        self.thermostat = thermostat
        self.whynter = whynter
        self.heater = heater
        self.broadlink = broadlink
        self.socket = None

    def start(self, port=80):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', port))
        self.socket.listen(5)
        self.socket.setblocking(False)
        print(f"API server started on port {port}")

    def handle_requests(self):
        try:
            client, addr = self.socket.accept()
            client.settimeout(5.0)
            try:
                request = client.recv(1024).decode('utf-8')
                response = self._handle_request(request)
                client.sendall(response.encode('utf-8'))
            except Exception as e:
                print(f"Request error: {e}")
            finally:
                client.close()
        except OSError:
            pass

    def _handle_request(self, request):
        if 'GET /api/status' in request:
            return self._api_status()
        elif 'GET /api/mode' in request:
            return self._api_mode(request)
        elif 'GET /api/heat_setpoint' in request:
            return self._api_heat_setpoint(request)
        elif 'GET /api/cool_setpoint' in request:
            return self._api_cool_setpoint(request)
        elif 'GET /api/whynter_mode' in request:
            return self._api_whynter_mode(request)
        elif 'GET /api/heater_mode' in request:
            return self._api_heater_mode(request)
        elif 'GET /api/fan_speed' in request:
            return self._api_fan_speed(request)
        elif 'GET /api/fan_only' in request:
            return self._api_fan_only(request)
        elif 'GET /api/humidity_setpoint' in request:
            return self._api_humidity_setpoint(request)
        elif 'GET /api/remote_temp' in request:
            return self._api_remote_temp(request)
        elif 'GET /api/relay/test' in request:
            return self._api_relay_test(request)
        elif 'GET /api/relay/furnace' in request:
            return self._api_furnace(request)
        elif 'GET /api/whynter' in request:
            return self._api_whynter(request)
        elif 'GET /api/heater' in request:
            return self._api_heater(request)
        elif 'GET /api/ir/codes' in request:
            return self._api_ir_codes()
        elif 'GET /api/broadlink/sensors' in request:
            return self._api_broadlink_sensors()
        elif 'GET /api/broadlink/status' in request:
            return self._api_broadlink_status()
        elif 'GET /api/force_all_off' in request:
            return self._api_force_all_off()
        elif 'GET /api/led' in request:
            return self._api_led(request)
        elif 'GET /api/i2c_scan' in request:
            return self._api_i2c_scan(request)
        elif 'GET /api/onewire_scan' in request:
            return self._api_onewire_scan(request)
        elif 'GET /api/gpio_test' in request:
            return self._api_gpio_test()
        else:
            return "HTTP/1.1 404 Not Found\r\n\r\n"

    def _json_response(self, data):
        body = json.dumps(data)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"

    def _api_status(self):
        status = self.thermostat.get_status()
        return self._json_response(status)

    def _parse_query(self, request):
        """Extract query parameters from GET request"""
        params = {}
        if '?' in request:
            query_start = request.find('?')
            query_end = request.find(' HTTP/')
            query = request[query_start+1:query_end]
            for param in query.split('&'):
                if '=' in param:
                    key, val = param.split('=', 1)
                    params[key] = val
        return params

    def _api_mode(self, request):
        params = self._parse_query(request)
        if 'mode' in params:
            self.thermostat.set_mode(int(params['mode']))
        return self._api_status()

    def _api_heat_setpoint(self, request):
        params = self._parse_query(request)
        if 'temp' in params:
            self.thermostat.set_heat_setpoint(float(params['temp']))
        return self._api_status()

    def _api_cool_setpoint(self, request):
        params = self._parse_query(request)
        if 'temp' in params:
            self.thermostat.set_cool_setpoint(float(params['temp']))
        return self._api_status()

    def _api_whynter_mode(self, request):
        params = self._parse_query(request)
        if 'mode' in params:
            self.thermostat.set_whynter_mode(int(params['mode']))
        return self._api_status()

    def _api_heater_mode(self, request):
        params = self._parse_query(request)
        if 'mode' in params:
            self.thermostat.set_heater_mode(int(params['mode']))
        return self._api_status()

    def _api_fan_speed(self, request):
        params = self._parse_query(request)
        if 'speed' in params:
            self.thermostat.set_fan_speed(int(params['speed']))
        return self._api_status()

    def _api_fan_only(self, request):
        params = self._parse_query(request)
        if 'on' in params:
            self.thermostat.set_fan_only(params['on'] == '1')
        return self._api_status()

    def _api_humidity_setpoint(self, request):
        params = self._parse_query(request)
        if 'value' in params:
            self.thermostat.set_humidity_setpoint(float(params['value']))
        return self._api_status()

    def _api_remote_temp(self, request):
        """Accept Main ESP32 temperature for multi-zone control"""
        params = self._parse_query(request)
        if 'temp' in params:
            self.thermostat.set_remote_temp(float(params['temp']))
        return self._api_status()

    def _api_relay_test(self, request):
        """Direct relay test: /api/relay/test?ch=1&on=1 or ?ch=furnace&on=0"""
        params = self._parse_query(request)
        on = params.get('on', '1') == '1'
        ch = params.get('ch', '')
        relay_map = {
            '1': ('furnace', self.thermostat.relay_furnace, config.RELAY_FURNACE_PIN),
            'furnace': ('furnace', self.thermostat.relay_furnace, config.RELAY_FURNACE_PIN),
            '2': ('compressor', self.thermostat.relay_compressor, config.RELAY_COMPRESSOR_PIN),
            'compressor': ('compressor', self.thermostat.relay_compressor, config.RELAY_COMPRESSOR_PIN),
            '3': ('fan_low', self.thermostat.relay_fan_low, config.RELAY_FAN_LOW_PIN),
            'fan_low': ('fan_low', self.thermostat.relay_fan_low, config.RELAY_FAN_LOW_PIN),
            '4': ('fan_high', self.thermostat.relay_fan_high, config.RELAY_FAN_HIGH_PIN),
            'fan_high': ('fan_high', self.thermostat.relay_fan_high, config.RELAY_FAN_HIGH_PIN),
        }
        inv = self.thermostat._relay_invert
        if ch in relay_map:
            name, pin, gpio = relay_map[ch]
            self.thermostat._relay_on(pin) if on else self.thermostat._relay_off(pin)
            is_on = self.thermostat._relay_is_on(pin)
            return self._json_response({
                'relay': name, 'gpio': gpio,
                'requested': 'ON' if on else 'OFF',
                'actual': 'ON' if is_on else 'OFF'
            })
        # No ch param — return all relay states
        t = self.thermostat
        return self._json_response({
            'furnace': {'gpio': config.RELAY_FURNACE_PIN, 'state': 'ON' if t._relay_is_on(t.relay_furnace) else 'OFF'},
            'compressor': {'gpio': config.RELAY_COMPRESSOR_PIN, 'state': 'ON' if t._relay_is_on(t.relay_compressor) else 'OFF'},
            'fan_low': {'gpio': config.RELAY_FAN_LOW_PIN, 'state': 'ON' if t._relay_is_on(t.relay_fan_low) else 'OFF'},
            'fan_high': {'gpio': config.RELAY_FAN_HIGH_PIN, 'state': 'ON' if t._relay_is_on(t.relay_fan_high) else 'OFF'},
        })

    def _api_furnace(self, request):
        params = self._parse_query(request)
        if 'on' in params:
            self.thermostat._furnace_relay(params['on'] == '1')
        return self._api_status()

    def _api_whynter(self, request):
        """Control Whynter portable AC via protocol-based IR"""
        if not self.whynter:
            return self._json_response({'error': 'Whynter not available'})
        params = self._parse_query(request)
        # /api/whynter?power=on|off
        # /api/whynter?mode=cool|heat|dehum|fan
        # /api/whynter?temp=61-89
        # /api/whynter?fan=auto|low|med|high
        # /api/whynter (no params = get status)
        if 'power' in params:
            if params['power'] == 'off':
                self.whynter.send_off()
            else:
                self.whynter.send_on()
        elif 'mode' in params:
            self.whynter.set_mode(params['mode'])
        elif 'temp' in params:
            self.whynter.set_temperature(int(params['temp']))
        elif 'fan' in params:
            self.whynter.set_fan_speed(params['fan'])
        return self._json_response(self.whynter.get_status())

    def _api_heater(self, request):
        """Control Dr. Heater via captured IR codes"""
        if not self.heater:
            return self._json_response({'error': 'Heater not available'})
        params = self._parse_query(request)
        # /api/heater?power=on|off|toggle|force_off
        # /api/heater?learn=<name>  (learn new button from remote)
        # /api/heater (no params = get status)
        if 'power' in params:
            if params['power'] == 'on':
                self.heater.send_on()
            elif params['power'] == 'off':
                self.heater.send_off()
            elif params['power'] == 'force_off':
                self.heater.send_force_off()
                self.thermostat.set_heater_mode(0)  # Sync thermostat state
            else:
                self.heater.send_power()
        elif 'learn' in params:
            name = params['learn']
            success = self.heater.learn(name, timeout_ms=10000)
            return self._json_response({'success': success, 'codes': self.heater.get_codes()})
        return self._json_response(self.heater.get_status())

    def _api_ir_codes(self):
        """List IR codes for all devices"""
        codes = {}
        if self.whynter:
            codes['whynter'] = self.whynter.get_codes()
        if self.heater:
            codes['heater'] = self.heater.get_codes()
        return self._json_response({'codes': codes})

    def _api_broadlink_sensors(self):
        """Read Broadlink HTS2 sensor on demand"""
        if not self.broadlink:
            return self._json_response({'error': 'Broadlink not configured'})
        result = self.broadlink.check_sensors()
        if result:
            temp_f = round(result[0] * 9.0 / 5.0 + 32.0, 1)
            return self._json_response({
                'temp_c': result[0], 'temp_f': temp_f,
                'humidity': result[1]
            })
        return self._json_response({'error': 'Sensor read failed'})

    def _api_broadlink_status(self):
        """Get Broadlink connection status"""
        if self.broadlink:
            return self._json_response(self.broadlink.get_status())
        return self._json_response({'error': 'Broadlink not configured'})

    def _api_force_all_off(self):
        """Force all systems off - relays + IR devices"""
        self.thermostat.force_all_off()
        return self._api_status()

    def _api_led(self, request):
        """Control RGB LED - set color or get status"""
        params = self._parse_query(request)
        # /api/led?color=red|blue|green|yellow|white|purple|orange|cyan|off
        # /api/led  (get status - LED color is set automatically by thermostat)
        if 'color' in params:
            self.thermostat.set_led_color(params['color'])
            return self._json_response({'color': params['color'], 'status': 'ok'})
        return self._json_response({'status': 'LED controlled by thermostat state'})

    def _api_i2c_scan(self, request=''):
        """Scan I2C bus and return found devices. Optional ?sda=N&scl=N to test other pins."""
        from machine import Pin, SoftI2C
        params = self._parse_query(request)
        sda_pin = int(params['sda']) if 'sda' in params else config.I2C_SDA_PIN
        scl_pin = int(params['scl']) if 'scl' in params else config.I2C_SCL_PIN
        freq = int(params.get('freq', str(config.I2C_FREQ)))
        try:
            i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq, timeout=50000)
            devices = i2c.scan()
        except Exception as e:
            return self._json_response({
                'sda_pin': sda_pin, 'scl_pin': scl_pin,
                'error': str(e), 'device_count': 0, 'devices': []
            })
        known = {0x76: 'BME280', 0x77: 'BME280/BMP280', 0x3C: 'SSD1306 OLED', 0x3D: 'SSD1306 OLED'}
        result = []
        for addr in devices:
            result.append({
                'address': hex(addr),
                'decimal': addr,
                'device': known.get(addr, 'Unknown')
            })
        return self._json_response({
            'sda_pin': sda_pin,
            'scl_pin': scl_pin,
            'freq': freq,
            'device_count': len(devices),
            'devices': result
        })

    def _api_onewire_scan(self, request=''):
        """Scan 1-Wire bus for DS18B20 sensors. Optional ?pin=N to test other pins."""
        from machine import Pin
        params = self._parse_query(request)
        data_pin = int(params['pin']) if 'pin' in params else config.FREEZE_SENSOR_PIN
        try:
            import onewire
            import ds18x20
            ow = onewire.OneWire(Pin(data_pin))
            ds = ds18x20.DS18X20(ow)
            roms = ds.scan()
            devices = [rom.hex() for rom in roms]
            # Try a temp read if devices found
            temp = None
            if roms:
                import time
                ds.convert_temp()
                time.sleep_ms(750)
                temp_c = ds.read_temp(roms[0])
                temp = round(temp_c * 9.0 / 5.0 + 32.0, 1)
            return self._json_response({
                'pin': data_pin, 'device_count': len(roms),
                'devices': devices, 'temp_f': temp
            })
        except Exception as e:
            return self._json_response({
                'pin': data_pin, 'error': str(e),
                'device_count': 0, 'devices': []
            })

    def _api_gpio_test(self):
        """Run GPIO pin test live and return results"""
        from machine import Pin
        import time as t

        RESERVED = {
            0: "Strapping", 3: "Strapping", 45: "Strapping", 46: "Strapping",
            19: "USB D-", 20: "USB D+",
            22: "N/A", 23: "N/A", 24: "N/A", 25: "N/A",
            26: "Flash", 27: "Flash", 28: "Flash", 29: "Flash",
            30: "Flash", 31: "Flash", 32: "Flash", 33: "Flash",
            34: "Flash", 35: "Flash", 36: "Flash", 37: "Flash",
        }
        # Skip pins currently in use (would crash I2C, relays, etc)
        in_use = {
            config.I2C_SDA_PIN, config.I2C_SCL_PIN,
            config.RELAY_FURNACE_PIN, config.RELAY_COMPRESSOR_PIN,
            config.RELAY_FAN_LOW_PIN, config.RELAY_FAN_HIGH_PIN,
            config.FREEZE_SENSOR_PIN, config.RGB_LED_PIN,
            config.RESET_BUTTON_PIN,
        }
        usable = []
        failed = []
        for gpio in range(0, 49):
            if gpio in RESERVED:
                continue
            if gpio in in_use:
                usable.append(gpio)  # Known good, skip toggle
                continue
            try:
                p = Pin(gpio, Pin.OUT)
                p.value(1); t.sleep_ms(5)
                h = p.value() == 1
                p.value(0); t.sleep_ms(5)
                l = p.value() == 0
                p.value(0)
                if h and l:
                    usable.append(gpio)
                else:
                    failed.append({'gpio': gpio, 'reason': f'readback H={h} L={l}'})
            except Exception as e:
                failed.append({'gpio': gpio, 'reason': str(e)})

        # Re-init relay pins to LOW (test may have toggled them)
        for rpin in [config.RELAY_FURNACE_PIN, config.RELAY_COMPRESSOR_PIN,
                     config.RELAY_FAN_LOW_PIN, config.RELAY_FAN_HIGH_PIN]:
            Pin(rpin, Pin.OUT).value(0)

        return self._json_response({
            'usable': usable,
            'usable_count': len(usable),
            'failed': failed,
            'failed_count': len(failed),
            'reserved_count': len(RESERVED),
        })
