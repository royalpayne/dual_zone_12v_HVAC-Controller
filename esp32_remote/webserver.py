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

    def _api_relay_test(self, request):
        """Direct relay test using thermostat's pin objects"""
        params = self._parse_query(request)
        gpio = int(params.get('gpio', '0'))
        on = params.get('on', '1') == '1'
        pin_map = {
            38: self.thermostat.relay_furnace,
            39: self.thermostat.relay_compressor,
            40: self.thermostat.relay_fan_low,
            41: self.thermostat.relay_fan_high,
        }
        # All relays are active HIGH: value(1) = ON, value(0) = OFF
        if gpio in pin_map:
            p = pin_map[gpio]
            p.value(1 if on else 0)
            actual = p.value()
            return self._json_response({
                'gpio': gpio, 'requested': 'ON' if on else 'OFF',
                'pin_value': actual, 'relay_state': 'ON' if actual == 1 else 'OFF'
            })
        return self._json_response({'error': f'Invalid GPIO: {gpio}'})

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
