# Remote ESP32 API Client
# ========================
# Used by main ESP32 to communicate with remote ESP32

import socket
import json


class RemoteClient:
    def __init__(self, remote_ip, port=80):
        self.remote_ip = remote_ip
        self.port = port
        self.connected = False
        self.last_error_time = 0
        self.error_backoff = 10  # Skip requests for 10 seconds after error

    def _request(self, endpoint, params=None):
        """Make HTTP request to remote device using raw sockets"""
        import time

        # Skip if recently had an error (backoff)
        if time.time() - self.last_error_time < self.error_backoff:
            return None

        try:
            # Build URL path
            path = endpoint
            if params:
                query = '&'.join(f"{k}={v}" for k, v in params.items())
                path = f"{endpoint}?{query}"

            # Create socket and connect
            s = socket.socket()
            s.settimeout(2.0)  # 2 second timeout for ESP32-to-ESP32 communication
            addr = socket.getaddrinfo(self.remote_ip, self.port)[0][-1]
            s.connect(addr)

            # Send HTTP request
            request = f"GET {path} HTTP/1.0\r\nHost: {self.remote_ip}\r\nConnection: close\r\n\r\n"
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
            import time
            self.last_error_time = time.time()
            self.connected = False
            # Only print error once per backoff period to avoid spam
            print(f"Remote API error: {e} (backing off for {self.error_backoff}s)")
            return None

    def get_status(self):
        """Get remote thermostat status"""
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

    def set_whynter_mode(self, mode):
        """Set Whynter portable AC mode (0=off, 1=on/cool)"""
        return self._request('/api/whynter_mode', {'mode': mode})

    def set_heater_mode(self, mode):
        """Set IR heater mode (0=off, 1=on)"""
        return self._request('/api/heater_mode', {'mode': mode})

    def set_furnace(self, on):
        """Direct furnace relay control"""
        return self._request('/api/relay/furnace', {'on': 1 if on else 0})

    def set_fan_speed(self, speed):
        """Set fan speed (0=off, 1=low, 2=med, 3=high, 4=auto)"""
        return self._request('/api/fan_speed', {'speed': speed})

    def set_fan_only(self, on):
        """Set fan-only mode (no compressor)"""
        return self._request('/api/fan_only', {'on': 1 if on else 0})

    def set_humidity_setpoint(self, value):
        """Set humidity setpoint for auto-dehumidification (% RH)"""
        return self._request('/api/humidity_setpoint', {'value': value})

    def is_connected(self):
        """Check if remote is reachable"""
        status = self.get_status()
        return status is not None
