# ESP32 Remote - Web API Server
# ==============================
# Serves local thermostat status and accepts control commands

import socket
import json
import config


class RemoteAPI:
    """Simple web API for remote ESP32"""

    def __init__(self, thermostat, ir=None):
        self.thermostat = thermostat
        self.ir = ir
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
            client.settimeout(2.0)
            try:
                request = client.recv(1024).decode('utf-8')
                response = self._handle_request(request)
                client.send(response.encode('utf-8'))
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
        elif 'GET /api/boost' in request:
            return self._api_boost(request)
        elif 'GET /api/relay/furnace' in request:
            return self._api_furnace(request)
        elif 'GET /api/relay/rooftop' in request:
            return self._api_rooftop(request)
        else:
            return "HTTP/1.1 404 Not Found\r\n\r\n"
    
    def _api_status(self):
        status = self.thermostat.get_status()
        body = json.dumps(status)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"
    
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
    
    def _api_boost(self, request):
        params = self._parse_query(request)
        if 'on' in params:
            self.thermostat.set_boost(params['on'] == '1')
        return self._api_status()
    
    def _api_furnace(self, request):
        params = self._parse_query(request)
        if 'on' in params:
            self.thermostat._furnace_relay(params['on'] == '1')
        return self._api_status()
    
    def _api_rooftop(self, request):
        params = self._parse_query(request)
        if 'on' in params:
            self.thermostat._rooftop_relay(params['on'] == '1')
        return self._api_status()
