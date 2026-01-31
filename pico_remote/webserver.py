# Pico Remote - Web Server / API
# ===============================
# Simple HTTP API for ESP32 communication

import socket
import json
import config
from ir_whynter import WhynterIR


class PicoAPI:
    def __init__(self, thermostat, ir=None):
        self.thermostat = thermostat
        self.ir = ir if ir else WhynterIR()
        self.socket = None
        self._ir_learning = False  # Track if currently learning

    def start(self, port=80):
        """Start the HTTP server"""
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(addr)
        self.socket.listen(5)
        self.socket.setblocking(False)
        print(f"API server listening on port {port}")

    def handle_requests(self):
        """Handle incoming HTTP requests (non-blocking)"""
        if not self.socket:
            return

        try:
            client, addr = self.socket.accept()
        except OSError:
            return  # No pending connections

        try:
            client.settimeout(2.0)
            request = client.recv(1024).decode('utf-8')

            if not request:
                client.close()
                return

            # Parse request
            lines = request.split('\r\n')
            if not lines:
                client.close()
                return

            method, path, _ = lines[0].split(' ', 2)

            # Parse query parameters
            params = {}
            if '?' in path:
                path, query = path.split('?', 1)
                for param in query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value

            # Route request
            response = self._route(method, path, params)

            # Send response
            client.send(response.encode('utf-8'))

        except Exception as e:
            print(f"API error: {e}")
        finally:
            client.close()

    def _route(self, method, path, params):
        """Route request to handler"""
        if path == '/api/status' or path == '/':
            return self._json_response(self.thermostat.get_status())

        elif path == '/api/mode':
            if 'mode' in params:
                mode = int(params['mode'])
                self.thermostat.set_mode(mode)
                return self._json_response({'ok': True, 'mode': mode})
            return self._json_response(self.thermostat.get_status())

        elif path == '/api/heat_setpoint':
            if 'temp' in params:
                temp = int(params['temp'])
                self.thermostat.set_heat_setpoint(temp)
                return self._json_response({'ok': True, 'heat_setpoint': temp})
            return self._json_response({'heat_setpoint': self.thermostat.heat_setpoint})

        elif path == '/api/cool_setpoint':
            if 'temp' in params:
                temp = int(params['temp'])
                self.thermostat.set_cool_setpoint(temp)
                return self._json_response({'ok': True, 'cool_setpoint': temp})
            return self._json_response({'cool_setpoint': self.thermostat.cool_setpoint})

        elif path == '/api/boost':
            # Manual boost control
            if 'on' in params:
                if params['on'] == '1':
                    self.thermostat._boost_on()
                else:
                    self.thermostat._boost_off()
                return self._json_response({'ok': True, 'boost_active': self.thermostat.boost_active})
            return self._json_response({'boost_active': self.thermostat.boost_active})

        elif path == '/api/relay/furnace':
            if 'on' in params:
                if params['on'] == '1':
                    self.thermostat._heat_on()
                else:
                    self.thermostat._heat_off()
                return self._json_response({'ok': True, 'heating_active': self.thermostat.heating_active})
            return self._json_response({'heating_active': self.thermostat.heating_active})

        elif path == '/api/relay/rooftop':
            if 'on' in params:
                if params['on'] == '1':
                    self.thermostat._cool_on()
                else:
                    self.thermostat._cool_off()
                return self._json_response({'ok': True, 'cooling_active': self.thermostat.cooling_active})
            return self._json_response({'cooling_active': self.thermostat.cooling_active})

        # IR Endpoints
        elif path == '/api/ir/status':
            return self._json_response(self.ir.get_status())

        elif path == '/api/ir/learn':
            if 'name' in params:
                name = params['name']
                # Start learning (blocking - up to 10 sec)
                self._ir_learning = True
                success = self.ir.learn(name, timeout_ms=10000)
                self._ir_learning = False
                if success:
                    return self._json_response({'ok': True, 'learned': name, 'codes': self.ir.get_codes()})
                else:
                    return self._json_response({'ok': False, 'error': 'No signal captured'})
            return self._json_response({'error': 'Missing name parameter'}, 400)

        elif path == '/api/ir/send':
            if 'name' in params:
                name = params['name']
                success = self.ir.send(name)
                return self._json_response({'ok': success, 'sent': name})
            return self._json_response({'error': 'Missing name parameter'}, 400)

        elif path == '/api/ir/delete':
            if 'name' in params:
                name = params['name']
                success = self.ir.delete_code(name)
                return self._json_response({'ok': success, 'deleted': name, 'codes': self.ir.get_codes()})
            return self._json_response({'error': 'Missing name parameter'}, 400)

        elif path == '/api/ir/codes':
            return self._json_response({'codes': self.ir.get_codes()})

        # Portable AC control (uses IR mode cycling)
        elif path == '/api/ir/power':
            if 'on' in params:
                if params['on'] == '1':
                    success = self.ir.send_on()
                else:
                    success = self.ir.send_off()
                return self._json_response({'ok': success, 'power': self.ir.power_on})
            return self._json_response({'power': self.ir.power_on})

        elif path == '/api/ir/mode':
            if 'mode' in params:
                target = params['mode']  # cool, dehum, fan, heat
                success = self.ir.set_mode(target)
                return self._json_response({
                    'ok': success,
                    'mode': self.ir.current_mode,
                    'power': self.ir.power_on
                })
            return self._json_response({
                'mode': self.ir.current_mode,
                'power': self.ir.power_on,
                'modes': ['cool', 'dehum', 'fan', 'heat']
            })

        elif path == '/api/ir/temperature':
            if 'temp' in params:
                target = int(params['temp'])
                success = self.ir.set_temperature(target)
                return self._json_response({
                    'ok': success,
                    'temp': self.ir.current_temp
                })
            return self._json_response({
                'temp': self.ir.current_temp,
                'min': 61,
                'max': 89
            })

        elif path == '/api/ir/fan':
            if 'speed' in params:
                target = params['speed']  # auto, low, med, high
                success = self.ir.set_fan_speed(target)
                return self._json_response({
                    'ok': success,
                    'fan': self.ir.current_fan
                })
            return self._json_response({
                'fan': self.ir.current_fan,
                'speeds': ['auto', 'low', 'med', 'high']
            })

        elif path == '/api/ir/set_cooling':
            # Set cooling mode with temp and fan in one call
            if 'temp' in params:
                temp = int(params['temp'])
                fan = params.get('fan', 'auto')
                success = self.ir.set_cooling(temp, fan)
                return self._json_response({
                    'ok': success,
                    'mode': self.ir.current_mode,
                    'temp': self.ir.current_temp,
                    'fan': self.ir.current_fan
                })
            return self._json_response({'error': 'Missing temp parameter'}, 400)

        elif path == '/api/ir/set_heating':
            # Set heating mode with temp and fan in one call
            if 'temp' in params:
                temp = int(params['temp'])
                fan = params.get('fan', 'auto')
                success = self.ir.set_heating(temp, fan)
                return self._json_response({
                    'ok': success,
                    'mode': self.ir.current_mode,
                    'temp': self.ir.current_temp,
                    'fan': self.ir.current_fan
                })
            return self._json_response({'error': 'Missing temp parameter'}, 400)

        elif path == '/api/ir/achieve_state':
            # Master control endpoint - set any combination of settings
            power = params.get('power')
            if power is not None:
                power = power == '1'
            mode = params.get('mode')
            temp = params.get('temp')
            if temp is not None:
                temp = int(temp)
            fan = params.get('fan')

            success = self.ir.achieve_state(power=power, mode=mode, temp=temp, fan=fan)
            return self._json_response({
                'ok': success,
                'state': {
                    'power': self.ir.power_on,
                    'mode': self.ir.current_mode,
                    'temp': self.ir.current_temp,
                    'fan': self.ir.current_fan
                }
            })

        else:
            return self._json_response({'error': 'Not found'}, 404)

    def _json_response(self, data, status=200):
        """Create JSON HTTP response"""
        body = json.dumps(data)
        status_text = 'OK' if status == 200 else 'Not Found'
        return (
            f"HTTP/1.1 {status} {status_text}\r\n"
            f"Content-Type: application/json\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
            f"{body}"
        )
