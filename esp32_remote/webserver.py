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
        elif 'GET /api/relay/test' in request:
            return self._api_relay_test(request)
        elif 'GET /api/relay/furnace' in request:
            return self._api_furnace(request)
        elif 'GET /api/whynter' in request:
            return self._api_whynter(request)
        elif 'GET /api/ir/learn' in request:
            return self._api_ir_learn(request)
        elif 'GET /api/ir/codes' in request:
            return self._api_ir_codes()
        elif 'GET /api/ir/send' in request:
            return self._api_ir_send(request)
        elif 'GET /api/broadlink/status' in request:
            return self._api_broadlink_status()
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

    def _api_relay_test(self, request):
        """Direct relay test using thermostat's pin objects"""
        params = self._parse_query(request)
        gpio = int(params.get('gpio', '0'))
        on = params.get('on', '1') == '1'
        pin_map = {
            38: self.thermostat.relay_furnace,
            39: self.thermostat.relay_compressor,
            40: self.thermostat.relay_fan_low,
            42: self.thermostat.relay_fan_high,
        }
        # Fan relays (40, 42) use active HIGH, furnace/compressor use active LOW
        fan_gpios = (40, 42)
        if gpio in pin_map:
            p = pin_map[gpio]
            if gpio in fan_gpios:
                p.value(1 if on else 0)  # Active HIGH
            else:
                p.value(0 if on else 1)  # Active LOW
            actual = p.value()
            if gpio in fan_gpios:
                relay_on = actual == 1  # Active HIGH
            else:
                relay_on = actual == 0  # Active LOW
            return self._json_response({
                'gpio': gpio, 'requested': 'ON' if on else 'OFF',
                'pin_value': actual, 'relay_state': 'ON' if relay_on else 'OFF'
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

    def _api_ir_learn(self, request):
        """Learn an IR code via Broadlink (for heater only)"""
        if not self.heater:
            return self._json_response({'success': False, 'error': 'Heater not available'})
        params = self._parse_query(request)
        button = params.get('button', 'unknown')
        print(f"[IR] Learning '{button}' for heater")
        success = self.heater.learn(button, timeout_ms=10000)
        if success:
            return self._json_response({
                'success': True, 'button': button,
                'device': 'heater', 'codes': self.heater.get_codes()
            })
        return self._json_response({'success': False, 'error': 'No signal captured'})

    def _api_ir_codes(self):
        """List IR codes for all devices"""
        codes = {}
        if self.whynter:
            codes['whynter'] = self.whynter.get_codes()
        if self.heater:
            codes['heater'] = self.heater.get_codes()
        return self._json_response({'codes': codes})

    def _api_ir_send(self, request):
        """Send an IR code"""
        params = self._parse_query(request)
        button = params.get('button', '')
        device = params.get('device', 'whynter')
        if device == 'heater' and self.heater and button in self.heater.codes:
            self.heater.send(button)
            return self._json_response({'success': True, 'button': button, 'device': device})
        elif device == 'whynter' and self.whynter:
            # Protocol-based: map button names to methods
            if button == 'power':
                self.whynter.send_off() if self.whynter.power_on else self.whynter.send_on()
            elif button in ('cool', 'heat', 'dehum', 'fan'):
                self.whynter.set_mode(button)
            else:
                return self._json_response({'success': False, 'error': f'Unknown button: {button}'})
            return self._json_response({'success': True, 'button': button, 'device': device})
        return self._json_response({'success': False, 'error': f'Code not found: {button}'})

    def _api_broadlink_status(self):
        """Get Broadlink connection status"""
        if self.broadlink:
            return self._json_response(self.broadlink.get_status())
        return self._json_response({'error': 'Broadlink not configured'})
