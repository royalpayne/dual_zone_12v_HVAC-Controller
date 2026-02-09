# Thermostat Web Server - With Remote Integration
import socket
import json
import config
from remote_client import RemoteClient

class ThermostatWebServer:
    def __init__(self, thermostat, scheduler=None, remote=None):
        self.thermostat = thermostat
        self.scheduler = scheduler
        self.socket = None
        self.remote = remote
        self.pressure_history = []  # Track pressure for trend
        self.max_history = 3

    def start(self, port=80):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', port))
        self.socket.listen(5)
        self.socket.setblocking(False)
        print(f"Web server started on port {port}")

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
        elif 'GET /api/schedule' in request:
            return self._api_schedule()
        elif 'GET /api/remote' in request:
            return self._api_remote_status()
        elif 'POST /api/schedule/' in request:
            return self._handle_schedule_post(request)
        elif 'POST /api/remote/' in request:
            return self._handle_remote_post(request)
        elif 'POST /api/' in request:
            return self._handle_post(request)
        else:
            return self._serve_html()

    def _api_status(self):
        status = self.thermostat.get_status()
        # Add remote connection status
        remote_status = self.remote.get_status()
        status['remote_connected'] = remote_status is not None
        if remote_status:
            status['remote'] = remote_status
        # Add pressure trend
        if status.get('pressure'):
            status['pressure_trend'] = self._get_pressure_trend(status['pressure'])
        body = json.dumps(status)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"

    def _api_remote_status(self):
        remote_status = self.remote.get_status()
        if remote_status:
            body = json.dumps(remote_status)
        else:
            body = json.dumps({'error': 'Remote not connected'})
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"

    def _get_pressure_trend(self, current_pressure):
        """Determine pressure trend: 'rising', 'falling', or 'steady'"""
        if current_pressure is None:
            return 'steady'
        self.pressure_history.append(current_pressure)
        if len(self.pressure_history) > self.max_history:
            self.pressure_history.pop(0)
        if len(self.pressure_history) < 2:
            return 'steady'
        avg_previous = sum(self.pressure_history[:-1]) / len(self.pressure_history[:-1])
        change = current_pressure - avg_previous
        if change > 0.5:
            return 'rising'
        elif change < -0.5:
            return 'falling'
        else:
            return 'steady'

    def _api_schedule(self):
        if self.scheduler:
            body = json.dumps(self.scheduler.get_status())
        else:
            body = json.dumps({'error': 'Scheduler not available'})
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"

    def _handle_schedule_post(self, request):
        try:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            data = json.loads(body)

            if 'POST /api/schedule/enable' in request:
                self.scheduler.set_enabled(data.get('enabled', False))
            elif 'POST /api/schedule/mode' in request:
                mode = data.get('mode', 'home')
                hours = data.get('hours', 0)
                if hours > 0:
                    self.scheduler.set_hold(mode, hours)
                else:
                    self.scheduler.set_hold(mode, 0)
                    self.scheduler.current_mode = mode
                    self.scheduler._apply_mode(mode)
            elif 'POST /api/schedule/preset' in request:
                mode = data.get('mode', 'home')
                heat = data.get('heat', 70)
                cool = data.get('cool', 74)
                self.scheduler.set_preset(mode, heat, cool)
            elif 'POST /api/schedule/day' in request:
                day = data.get('day', 'mon')
                entries = data.get('entries', [])
                self.scheduler.set_schedule_entry(day, entries)
        except Exception as e:
            print(f"Schedule POST error: {e}")
        return self._api_schedule()

    def _handle_post(self, request):
        try:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            data = json.loads(body)

            if 'POST /api/mode' in request:
                self.thermostat.set_mode(int(data.get('mode', 0)))
            elif 'POST /api/heat_setpoint' in request:
                self.thermostat.set_heat_setpoint(float(data.get('temp', 68)))
            elif 'POST /api/cool_setpoint' in request:
                self.thermostat.set_cool_setpoint(float(data.get('temp', 75)))
        except:
            pass
        return self._api_status()

    def _handle_remote_post(self, request):
        try:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            data = json.loads(body)

            if 'POST /api/remote/mode' in request:
                self.remote.set_mode(int(data.get('mode', 0)))
            elif 'POST /api/remote/heat_setpoint' in request:
                self.remote.set_heat_setpoint(int(data.get('temp', 68)))
            elif 'POST /api/remote/cool_setpoint' in request:
                self.remote.set_cool_setpoint(int(data.get('temp', 75)))
            elif 'POST /api/remote/whynter_mode' in request:
                self.remote.set_whynter_mode(int(data.get('mode', 0)))
            elif 'POST /api/remote/heater_mode' in request:
                self.remote.set_heater_mode(int(data.get('mode', 0)))
            elif 'POST /api/remote/fan_speed' in request:
                self.remote.set_fan_speed(int(data.get('speed', 4)))
            elif 'POST /api/remote/fan_only' in request:
                self.remote.set_fan_only(data.get('on', False))
            elif 'POST /api/remote/sync' in request:
                # Sync ESP32 setpoints to remote (one call at a time with short delay)
                import time
                self.remote.set_heat_setpoint(int(self.thermostat.heat_setpoint))
                time.sleep(0.2)
                self.remote.set_cool_setpoint(int(self.thermostat.cool_setpoint))
                time.sleep(0.2)
                self.remote.set_mode(self.thermostat.mode)
        except Exception as e:
            print(f"Remote POST error: {e}")
        return self._api_remote_status()

    def _serve_html(self):
        html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RV Thermostat</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:20px}
.card{background:#16213e;border-radius:16px;padding:20px;margin-bottom:16px;max-width:400px;margin-left:auto;margin-right:auto}
.temp{font-size:48px;text-align:center}
.row{display:flex;justify-content:space-around;margin:16px 0}
.btn{background:#0f3460;border:none;color:#fff;padding:12px 20px;border-radius:8px;font-size:16px;cursor:pointer}
.btn.active{background:#e94560}
.btn.cool{background:#00b4d8}
.btn.whynter{background:#9d4edd}
.btn.heater{background:#ff6b35}
.btn.fan{background:#38b000}
.setrow{display:flex;align-items:center;justify-content:space-between;margin:12px 0}
.setval{font-size:28px;min-width:60px;text-align:center}
.slider{width:100%;height:8px;border-radius:4px;background:#0f3460;outline:none;-webkit-appearance:none;margin:8px 0}
.slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:24px;height:24px;border-radius:50%;background:#e94560;cursor:pointer}
.slider::-moz-range-thumb{width:24px;height:24px;border-radius:50%;background:#e94560;cursor:pointer;border:none}
.slider.cool::-webkit-slider-thumb{background:#00b4d8}
.slider.cool::-moz-range-thumb{background:#00b4d8}
.setlabel{display:flex;justify-content:space-between;font-size:12px;color:#888;margin-bottom:4px}
#status{text-align:center;padding:12px;border-radius:8px;background:#2a3f5f}
#status.heating{background:#e94560}
#status.cooling{background:#00b4d8}
#pstatus{text-align:center;padding:12px;border-radius:8px;background:#2a3f5f}
#pstatus.heating{background:#e94560}
#pstatus.cooling{background:#00b4d8}
#pstatus.whynter{background:#9d4edd}
#pstatus.offline{background:#555}
h3{font-size:14px;color:#888;margin-bottom:8px}
.zone{border-top:2px solid #0f3460;padding-top:16px;margin-top:16px}
.zone-title{font-size:18px;color:#e94560;margin-bottom:12px;text-align:center}
.remote-title{color:#00b4d8}
.temp-small{font-size:32px;text-align:center}
.sync-card{background:#1f4068;text-align:center}
.btn.sync{background:#38b000;padding:16px 32px;font-size:18px}
.btn.sync.synced{background:#2a9d8f}
.btn.home{background:#38b000}
</style>
</head>
<body>
<div class="card">
<div class="zone-title">Kitchen (ESP32)</div>
<div class="temp"><span id="temp">--</span>&deg;F</div>
<div class="row">💧 <span id="hum">--%</span> | <span id="ptrend">→</span> <span id="pres">--</span> inHg</div>
<div id="status">Idle</div>
</div>
<div class="card">
<h3>MODE</h3>
<div class="row">
<button class="btn" id="m0" onclick="mode(0)">OFF</button>
<button class="btn" id="m1" onclick="mode(1)">HEAT</button>
<button class="btn" id="m2" onclick="mode(2)">COOL</button>
<button class="btn" id="m3" onclick="mode(3)">AUTO</button>
</div>
<h3>HEAT SETPOINT</h3>
<div class="setlabel"><span>60°</span><span id="hset">68</span>°<span>85°</span></div>
<input type="range" min="60" max="85" value="68" class="slider" id="hslider" oninput="setHeat(this.value)">
<h3>COOL SETPOINT</h3>
<div class="setlabel"><span>60°</span><span id="cset">75</span>°<span>85°</span></div>
<input type="range" min="60" max="85" value="75" class="slider cool" id="cslider" oninput="setCool(this.value)">
</div>

<div class="card sync-card">
<button class="btn sync synced" id="syncbtn" onclick="syncZones()">SYNCED!</button>
<div style="margin-top:8px;font-size:12px;color:#888">Copy Kitchen settings to Living Room</div>
</div>

<div class="card">
<div class="zone-title remote-title">Living Room (Remote)</div>
<div class="temp-small"><span id="ptemp">--</span>&deg;F</div>
<div class="row">💧 <span id="phum">--%</span> | <span id="pptrend">→</span> <span id="ppres">--</span> inHg</div>
<div id="pstatus">Offline</div>
</div>
<div class="card">
<h3>REMOTE MODE</h3>
<div class="row">
<button class="btn" id="pm0" onclick="rmode(0)">OFF</button>
<button class="btn" id="pm1" onclick="rmode(1)">HEAT</button>
<button class="btn" id="pm2" onclick="rmode(2)">COOL</button>
<button class="btn" id="pm3" onclick="rmode(3)">AUTO</button>
</div>
<h3>REMOTE HEAT SETPOINT</h3>
<div class="setlabel"><span>60°</span><span id="phset">68</span>°<span>85°</span></div>
<input type="range" min="60" max="85" value="68" class="slider" id="phslider" oninput="setRHeat(this.value)">
<h3>REMOTE COOL SETPOINT</h3>
<div class="setlabel"><span>60°</span><span id="pcset">75</span>°<span>85°</span></div>
<input type="range" min="60" max="85" value="75" class="slider cool" id="pcslider" oninput="setRCool(this.value)">
<h3>ROOFTOP FAN</h3>
<div class="row">
<button class="btn" id="f1" onclick="fanSpeed(1)">LOW</button>
<button class="btn" id="f2" onclick="fanSpeed(2)">MED</button>
<button class="btn" id="f3" onclick="fanSpeed(3)">HIGH</button>
<button class="btn" id="f4" onclick="fanSpeed(4)">AUTO</button>
</div>
<div class="row">
<button class="btn" id="fo0" onclick="fanOnly(0)">FAN OFF</button>
<button class="btn" id="fo1" onclick="fanOnly(1)">FAN ONLY</button>
</div>
<h3>WHYNTER PORTABLE UNIT</h3>
<div class="row">
<button class="btn" id="w0" onclick="whynter(0)">OFF</button>
<button class="btn" id="w1" onclick="whynter(1)">ON</button>
</div>
<h3>IR HEATER</h3>
<div class="row">
<button class="btn" id="h0" onclick="heater(0)">OFF</button>
<button class="btn" id="h1" onclick="heater(1)">ON</button>
</div>
</div>

<script>
var hs=68,cs=75,rhs=68,rcs=75,rwhynter=0,rheater=0;
var adjustingHeat=false,adjustingCool=false,adjustingRHeat=false,adjustingRCool=false;
var heatTimer,coolTimer,rheatTimer,rcoolTimer;
function upd(d){
document.getElementById('temp').textContent=d.temp?d.temp.toFixed(1):'--';
document.getElementById('hum').textContent=d.humidity?Math.round(d.humidity)+'%':'--%';
document.getElementById('pres').textContent=d.pressure?(d.pressure*0.02953).toFixed(2):'--';
var trend=d.pressure_trend||'steady';
document.getElementById('ptrend').textContent=trend=='rising'?'↑':trend=='falling'?'↓':'→';
if(!adjustingHeat){
document.getElementById('hset').textContent=d.heat_setpoint;
document.getElementById('hslider').value=d.heat_setpoint;
}
if(!adjustingCool){
document.getElementById('cset').textContent=d.cool_setpoint;
document.getElementById('cslider').value=d.cool_setpoint;
}
hs=d.heat_setpoint;cs=d.cool_setpoint;
var st=document.getElementById('status');
st.className=d.heating_active?'heating':d.cooling_active?'cooling':'';
st.textContent=d.heating_active?'HEATING':d.cooling_active?'COOLING':'Idle';
for(var i=0;i<4;i++)document.getElementById('m'+i).className='btn'+(d.mode==i?' active':'');
if(d.remote){updRemote(d.remote);}else{
var ps=document.getElementById('pstatus');ps.className='offline';ps.textContent='Offline';}
}
function updRemote(r){
document.getElementById('ptemp').textContent=r.temp?r.temp.toFixed(1):'--';
document.getElementById('phum').textContent=r.humidity?Math.round(r.humidity)+'%':'--%';
document.getElementById('ppres').textContent=r.pressure?(r.pressure*0.02953).toFixed(2):'--';
document.getElementById('pptrend').textContent='→';
if(!adjustingRHeat){
document.getElementById('phset').textContent=r.heat_setpoint;
document.getElementById('phslider').value=r.heat_setpoint;
}
if(!adjustingRCool){
document.getElementById('pcset').textContent=r.cool_setpoint;
document.getElementById('pcslider').value=r.cool_setpoint;
}
rhs=r.heat_setpoint;rcs=r.cool_setpoint;rwhynter=r.whynter_mode||0;rheater=r.heater_mode||0;
var ps=document.getElementById('pstatus');
var whynterActive=r.whynter_mode>0;
var heaterActive=r.heater_mode>0;
ps.className=whynterActive?'whynter':heaterActive?'heating':r.heating_active?'heating':r.cooling_active?'cooling':'';
ps.textContent=whynterActive?'WHYNTER ON':heaterActive?'IR HEATER ON':r.heating_active?'HEATING':r.cooling_active?'COOLING':r.fan_only?'FAN ONLY':'Idle';
for(var i=0;i<4;i++)document.getElementById('pm'+i).className='btn'+(r.mode==i?' active':'');
for(var i=0;i<2;i++)document.getElementById('w'+i).className='btn'+(r.whynter_mode==i?' whynter':'');
for(var i=0;i<2;i++)document.getElementById('h'+i).className='btn'+(r.heater_mode==i?' heater':'');
for(var i=1;i<=4;i++)document.getElementById('f'+i).className='btn'+(r.fan_speed==i?' fan':'');
document.getElementById('fo0').className='btn'+(!r.fan_only?' active':'');
document.getElementById('fo1').className='btn'+(r.fan_only?' fan':'');
}
function get(){fetch('/api/status').then(r=>r.json()).then(upd).catch(e=>console.log(e));}
function mode(m){fetch('/api/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(upd);}
function setHeat(v){adjustingHeat=true;document.getElementById('hset').textContent=v;clearTimeout(heatTimer);heatTimer=setTimeout(function(){fetch('/api/heat_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingHeat=false;},1000);});},500);}
function setCool(v){adjustingCool=true;document.getElementById('cset').textContent=v;clearTimeout(coolTimer);coolTimer=setTimeout(function(){fetch('/api/cool_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingCool=false;},1000);});},500);}
function rmode(m){fetch('/api/remote/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updRemote);}
function setRHeat(v){adjustingRHeat=true;document.getElementById('phset').textContent=v;clearTimeout(rheatTimer);rheatTimer=setTimeout(function(){fetch('/api/remote/heat_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingRHeat=false;},1000);});},500);}
function setRCool(v){adjustingRCool=true;document.getElementById('pcset').textContent=v;clearTimeout(rcoolTimer);rcoolTimer=setTimeout(function(){fetch('/api/remote/cool_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingRCool=false;},1000);});},500);}
function whynter(m){fetch('/api/remote/whynter_mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updRemote);}
function heater(m){fetch('/api/remote/heater_mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updRemote);}
function fanSpeed(s){fetch('/api/remote/fan_speed',{method:'POST',body:JSON.stringify({speed:s})}).then(r=>r.json()).then(updRemote);}
function fanOnly(on){fetch('/api/remote/fan_only',{method:'POST',body:JSON.stringify({on:on})}).then(r=>r.json()).then(updRemote);}
function syncZones(){
var btn=document.getElementById('syncbtn');
btn.textContent='SYNCING...';
btn.className='btn sync synced';
fetch('/api/remote/sync',{method:'POST',body:'{}'}).then(r=>r.json()).then(function(r){
updRemote(r);btn.textContent='SYNCED!';
setTimeout(function(){btn.textContent='SYNCED!';btn.className='btn sync synced';},2000);
}).catch(function(){btn.textContent='SYNC FAILED';btn.className='btn sync';});
}
get();setInterval(get,3000);
</script>
</body>
</html>"""
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}"
