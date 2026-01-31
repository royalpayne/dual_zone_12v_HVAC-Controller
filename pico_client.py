# Pico Remote API Client
# =======================
# Used by ESP32 to communicate with Pico remote

import socket
import json


class PicoClient:
    def __init__(self, pico_ip, port=80):
        self.pico_ip = pico_ip
        self.port = port
        self.connected = False

    def _request(self, endpoint, params=None):
        """Make HTTP request to Pico using raw sockets"""
        try:
            # Build URL path
            path = endpoint
            if params:
                query = '&'.join(f"{k}={v}" for k, v in params.items())
                path = f"{endpoint}?{query}"

            # Create socket and connect
            s = socket.socket()
            s.settimeout(3)
            addr = socket.getaddrinfo(self.pico_ip, self.port)[0][-1]
            s.connect(addr)

            # Send HTTP request
            request = f"GET {path} HTTP/1.0\r\nHost: {self.pico_ip}\r\nConnection: close\r\n\r\n"
            s.send(request.encode())

            # Receive response
            response = b""
            while True:
                chunk = s.recv(512)
                if not chunk:
                    break
                response += chunk

            s.close()

            # Parse response
            response = response.decode('utf-8')

            # Find JSON body (after headers)
            body_start = response.find('\r\n\r\n')
            if body_start == -1:
                return None

            body = response[body_start + 4:]
            data = json.loads(body)
            self.connected = True
            return data

        except Exception as e:
            print(f"Pico API error: {e}")
            self.connected = False
            return None

    def get_status(self):
        """Get Pico thermostat status"""
        return self._request('/api/status')

    def set_mode(self, mode):
        """Set operating mode (0=OFF, 1=HEAT, 2=COOL, 3=AUTO)"""
        return self._request('/api/mode', {'mode': mode})

    def set_heat_setpoint(self, temp):
        """Set heating setpoint"""
        return self._request('/api/heat_setpoint', {'temp': temp})

    def set_cool_setpoint(self, temp):
        """Set cooling setpoint"""
        return self._request('/api/cool_setpoint', {'temp': temp})

    def set_boost(self, on):
        """Manual boost control"""
        return self._request('/api/boost', {'on': 1 if on else 0})

    def set_furnace(self, on):
        """Direct furnace relay control"""
        return self._request('/api/relay/furnace', {'on': 1 if on else 0})

    def set_rooftop(self, on):
        """Direct rooftop AC relay control"""
        return self._request('/api/relay/rooftop', {'on': 1 if on else 0})

    def is_connected(self):
        """Check if Pico is reachable"""
        status = self.get_status()
        return status is not None
