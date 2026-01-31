# Thermostat Web Server
# Mobile-friendly interface with real-time updates

import socket
import json
import config


class ThermostatWebServer:
    def __init__(self, thermostat):
        self.thermostat = thermostat
        self.socket = None
    
    def start(self, port=80):
        """Start the web server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', port))
        self.socket.listen(5)
        self.socket.setblocking(False)
        print(f"Web server started on port {port}")
    
    def handle_requests(self):
        """Check for and handle incoming requests (non-blocking)"""
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
            pass  # No pending connections
    
    def _handle_request(self, request):
        """Route request to appropriate handler"""
        if 'GET /api/status' in request:
            return self._api_status()
        elif 'POST /api/mode' in request:
            return self._api_set_mode(request)
        elif 'POST /api/heat_setpoint' in request:
            return self._api_set_heat(request)
        elif 'POST /api/cool_setpoint' in request:
            return self._api_set_cool(request)
        elif 'POST /api/cool_system' in request:
            return self._api_set_cool_system(request)
        else:
            return self._serve_html()
    
    def _api_status(self):
        """Return current status as JSON"""
        status = self.thermostat.get_status()
        body = json.dumps(status)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"
    
    def _api_set_mode(self, request):
        """Set operating mode"""
        mode = self._extract_value(request, 'mode')
        if mode is not None:
            self.thermostat.set_mode(int(mode))
        return self._api_status()
    
    def _api_set_heat(self, request):
        """Set heat setpoint"""
        temp = self._extract_value(request, 'temp')
        if temp is not None:
            self.thermostat.set_heat_setpoint(float(temp))
        return self._api_status()
    
    def _api_set_cool(self, request):
        """Set cool setpoint"""
        temp = self._extract_value(request, 'temp')
        if temp is not None:
            self.thermostat.set_cool_setpoint(float(temp))
        return self._api_status()
    
    def _api_set_cool_system(self, request):
        """Set cooling system type"""
        system = self._extract_value(request, 'system')
        if system is not None:
            self.thermostat.set_cool_system(int(system))
        return self._api_status()
    
    def _extract_value(self, request, key):
        """Extract value from POST body"""
        try:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            data = json.loads(body)
            return data.get(key)
        except:
            return None
    
    def _serve_html(self):
        """Serve the main HTML page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RV Thermostat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, sans-serif; 
            background: #1a1a2e; 
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 400px; margin: 0 auto; }
        .card {
            background: #16213e;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .temp-display {
            text-align: center;
            padding: 30px 0;
        }
        .temp-value {
            font-size: 72px;
            font-weight: 200;
        }
        .temp-unit { font-size: 32px; opacity: 0.7; }
        .readings {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #2a3f5f;
        }
        .reading { text-align: center; }
        .reading-value { font-size: 24px; }
        .reading-label { font-size: 12px; opacity: 0.7; }
        .setpoint-control {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 16px 0;
        }
        .setpoint-label { font-size: 14px; opacity: 0.8; }
        .setpoint-value { font-size: 32px; min-width: 80px; text-align: center; }
        .btn {
            background: #0f3460;
            border: none;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 25px;
            font-size: 24px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:active { background: #1a5094; }
        .mode-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }
        .mode-btn {
            background: #0f3460;
            border: none;
            color: white;
            padding: 16px 8px;
            border-radius: 12px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .mode-btn.active { background: #e94560; }
        .cool-system {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 16px;
        }
        .system-btn {
            background: #0f3460;
            border: none;
            color: white;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
        }
        .system-btn.active { background: #00b4d8; }
        .status {
            text-align: center;
            padding: 16px;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 500;
        }
        .status.heating { background: #e94560; }
        .status.cooling { background: #00b4d8; }
        .status.idle { background: #2a3f5f; }
        h2 { font-size: 14px; opacity: 0.7; margin-bottom: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card temp-display">
            <div>
                <span class="temp-value" id="temp">--</span>
                <span class="temp-unit">°F</span>
            </div>
            <div class="readings">
                <div class="reading">
                    <div class="reading-value" id="humidity">--%</div>
                    <div class="reading-label">Humidity</div>
                </div>
                <div class="reading">
                    <div class="reading-value" id="pressure">--</div>
                    <div class="reading-label">inHg</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div id="status" class="status idle">Idle</div>
        </div>

        <div class="card">
            <h2>HEAT SETPOINT</h2>
            <div class="setpoint-control">
                <button class="btn" onclick="adjustHeat(-1)">−</button>
                <span class="setpoint-value"><span id="heat-set">68</span>°</span>
                <button class="btn" onclick="adjustHeat(1)">+</button>
            </div>
            <h2>COOL SETPOINT</h2>
            <div class="setpoint-control">
                <button class="btn" onclick="adjustCool(-1)">−</button>
                <span class="setpoint-value"><span id="cool-set">75</span>°</span>
                <button class="btn" onclick="adjustCool(1)">+</button>
            </div>
        </div>

        <div class="card">
            <h2>MODE</h2>
            <div class="mode-buttons">
                <button class="mode-btn" onclick="setMode(0)">OFF</button>
                <button class="mode-btn" onclick="setMode(1)">HEAT</button>
                <button class="mode-btn" onclick="setMode(2)">COOL</button>
                <button class="mode-btn" onclick="setMode(3)">AUTO</button>
            </div>
            <h2 style="margin-top:16px">COOLING SYSTEM</h2>
            <div class="cool-system">
                <button class="system-btn" onclick="setCoolSystem(0)">Rooftop</button>
                <button class="system-btn" onclick="setCoolSystem(1)">Portable</button>
            </div>
        </div>
    </div>

    <script>
        let currentMode = 0;
        let currentCoolSystem = 0;
        let heatSetpoint = 68;
        let coolSetpoint = 75;

        function updateUI(data) {
            if (data.temp !== null) {
                document.getElementById('temp').textContent = data.temp.toFixed(1);
            }
            if (data.humidity !== null) {
                document.getElementById('humidity').textContent = data.humidity.toFixed(0) + '%';
            }
            if (data.pressure !== null) {
                let inHg = (data.pressure * 0.02953).toFixed(2);
                document.getElementById('pressure').textContent = inHg;
            }
            
            document.getElementById('heat-set').textContent = data.heat_setpoint;
            document.getElementById('cool-set').textContent = data.cool_setpoint;
            heatSetpoint = data.heat_setpoint;
            coolSetpoint = data.cool_setpoint;
            currentMode = data.mode;
            currentCoolSystem = data.cool_system;

            // Update status
            let statusEl = document.getElementById('status');
            statusEl.className = 'status';
            if (data.heating_active) {
                statusEl.textContent = 'HEATING';
                statusEl.classList.add('heating');
            } else if (data.cooling_active) {
                statusEl.textContent = 'COOLING';
                statusEl.classList.add('cooling');
            } else {
                statusEl.textContent = 'Idle';
                statusEl.classList.add('idle');
            }

            // Update mode buttons
            document.querySelectorAll('.mode-btn').forEach((btn, i) => {
                btn.classList.toggle('active', i === data.mode);
            });

            // Update cool system buttons
            document.querySelectorAll('.system-btn').forEach((btn, i) => {
                btn.classList.toggle('active', i === data.cool_system);
            });
        }

        function fetchStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(updateUI)
                .catch(e => console.error(e));
        }

        function setMode(mode) {
            fetch('/api/mode', {
                method: 'POST',
                body: JSON.stringify({mode: mode})
            }).then(r => r.json()).then(updateUI);
        }

        function adjustHeat(delta) {
            fetch('/api/heat_setpoint', {
                method: 'POST',
                body: JSON.stringify({temp: heatSetpoint + delta})
            }).then(r => r.json()).then(updateUI);
        }

        function adjustCool(delta) {
            fetch('/api/cool_setpoint', {
                method: 'POST',
                body: JSON.stringify({temp: coolSetpoint + delta})
            }).then(r => r.json()).then(updateUI);
        }

        function setCoolSystem(system) {
            fetch('/api/cool_system', {
                method: 'POST',
                body: JSON.stringify({system: system})
            }).then(r => r.json()).then(updateUI);
        }

        fetchStatus();
        setInterval(fetchStatus, 3000);
    </script>
</body>
</html>'''
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
