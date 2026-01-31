# Thermostat Web Server - With Pico Remote Integration
import socket
import json
import config
from pico_client import PicoClient

class ThermostatWebServer:
    def __init__(self, thermostat, scheduler=None, pico=None):
        self.thermostat = thermostat
        self.scheduler = scheduler
        self.socket = None
        self.pico = pico

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
        elif 'GET /api/schedule' in request:
            return self._api_schedule()
        elif 'GET /api/pico' in request:
            return self._api_pico_status()
        elif 'POST /api/schedule/' in request:
            return self._handle_schedule_post(request)
        elif 'POST /api/pico/' in request:
            return self._handle_pico_post(request)
        elif 'POST /api/' in request:
            return self._handle_post(request)
        else:
            return self._serve_html()

    def _api_status(self):
        status = self.thermostat.get_status()
        # Add Pico connection status
        pico_status = self.pico.get_status()
        status['pico_connected'] = pico_status is not None
        if pico_status:
            status['pico'] = pico_status
        body = json.dumps(status)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"

    def _api_pico_status(self):
        pico_status = self.pico.get_status()
        if pico_status:
            body = json.dumps(pico_status)
        else:
            body = json.dumps({'error': 'Pico not connected'})
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{body}"

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
            elif 'POST /api/cool_system' in request:
                self.thermostat.set_cool_system(int(data.get('system', 0)))
        except:
            pass
        return self._api_status()

    def _handle_pico_post(self, request):
        try:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            data = json.loads(body)

            if 'POST /api/pico/mode' in request:
                self.pico.set_mode(int(data.get('mode', 0)))
            elif 'POST /api/pico/heat_setpoint' in request:
                self.pico.set_heat_setpoint(int(data.get('temp', 68)))
            elif 'POST /api/pico/cool_setpoint' in request:
                self.pico.set_cool_setpoint(int(data.get('temp', 75)))
            elif 'POST /api/pico/boost' in request:
                self.pico.set_boost(data.get('on', False))
            elif 'POST /api/pico/sync' in request:
                # Sync ESP32 setpoints to Pico (one call at a time with short delay)
                import time
                self.pico.set_heat_setpoint(int(self.thermostat.heat_setpoint))
                time.sleep(0.2)
                self.pico.set_cool_setpoint(int(self.thermostat.cool_setpoint))
                time.sleep(0.2)
                self.pico.set_mode(self.thermostat.mode)
        except Exception as e:
            print(f"Pico POST error: {e}")
        return self._api_pico_status()

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
.btn.boost{background:#9d4edd}
.setrow{display:flex;align-items:center;justify-content:space-between;margin:12px 0}
.setval{font-size:28px;min-width:60px;text-align:center}
#status{text-align:center;padding:12px;border-radius:8px;background:#2a3f5f}
#status.heating{background:#e94560}
#status.cooling{background:#00b4d8}
#pstatus{text-align:center;padding:12px;border-radius:8px;background:#2a3f5f}
#pstatus.heating{background:#e94560}
#pstatus.cooling{background:#00b4d8}
#pstatus.boost{background:#9d4edd}
#pstatus.offline{background:#555}
h3{font-size:14px;color:#888;margin-bottom:8px}
.zone{border-top:2px solid #0f3460;padding-top:16px;margin-top:16px}
.zone-title{font-size:18px;color:#e94560;margin-bottom:12px;text-align:center}
.pico-title{color:#00b4d8}
.temp-small{font-size:32px;text-align:center}
.sync-card{background:#1f4068;text-align:center}
.btn.sync{background:#38b000;padding:16px 32px;font-size:18px}
.btn.sync.synced{background:#2a9d8f}
.btn.home{background:#38b000}
.btn.away{background:#f77f00}
.btn.sleep{background:#7b2cbf}
.sched-card{border:2px solid #38b000}
.sched-status{text-align:center;font-size:14px;margin-top:8px}
.toggle{display:flex;align-items:center;justify-content:center;gap:10px}
.switch{position:relative;width:50px;height:26px}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#555;border-radius:26px;transition:.3s}
.slider:before{position:absolute;content:"";height:20px;width:20px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s}
input:checked+.slider{background:#38b000}
input:checked+.slider:before{transform:translateX(24px)}
.day-tabs{display:flex;justify-content:space-around;margin:12px 0}
.day-tab{padding:8px 6px;border:none;background:#0f3460;color:#fff;border-radius:4px;cursor:pointer;font-size:12px}
.day-tab.active{background:#38b000}
.sched-list{margin:12px 0;max-height:150px;overflow-y:auto}
.sched-entry{display:flex;justify-content:space-between;align-items:center;padding:6px;background:#0f3460;margin:4px 0;border-radius:4px;font-size:14px}
.sched-entry .time{font-weight:bold}
.sched-entry .del{background:#e94560;border:none;color:#fff;padding:4px 8px;border-radius:4px;cursor:pointer}
.add-entry{display:flex;gap:8px;margin-top:12px}
.add-entry input,.add-entry select{padding:8px;border-radius:4px;border:none;background:#0f3460;color:#fff}
.add-entry input{width:80px}
.add-entry select{flex:1}
.btn.add{background:#38b000;padding:8px 16px}
</style>
</head>
<body>
<div class="card">
<div class="zone-title">Kitchen (ESP32)</div>
<div class="temp"><span id="temp">--</span>&deg;F</div>
<div class="row"><span id="hum">--%</span> | <span id="pres">--</span> inHg</div>
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
<h3>COOLING</h3>
<div class="row">
<button class="btn" id="s0" onclick="sys(0)">Rooftop</button>
<button class="btn" id="s1" onclick="sys(1)">Portable</button>
</div>
<h3>HEAT SETPOINT</h3>
<div class="setrow">
<button class="btn" onclick="adj('heat',-1)">-</button>
<span class="setval"><span id="hset">68</span>&deg;</span>
<button class="btn" onclick="adj('heat',1)">+</button>
</div>
<h3>COOL SETPOINT</h3>
<div class="setrow">
<button class="btn" onclick="adj('cool',-1)">-</button>
<span class="setval"><span id="cset">75</span>&deg;</span>
<button class="btn" onclick="adj('cool',1)">+</button>
</div>
</div>

<div class="card sched-card">
<div class="zone-title" style="color:#38b000">Schedule</div>
<div class="toggle">
<span>Schedule</span>
<label class="switch"><input type="checkbox" id="schedon" onchange="schedEnable(this.checked)"><span class="slider"></span></label>
</div>
<h3 style="margin-top:16px">QUICK MODE</h3>
<div class="row">
<button class="btn home" id="shome" onclick="schedMode('home')">HOME</button>
<button class="btn away" id="saway" onclick="schedMode('away')">AWAY</button>
<button class="btn sleep" id="ssleep" onclick="schedMode('sleep')">SLEEP</button>
</div>
<div class="sched-status" id="schedstatus">Schedule: OFF</div>
<h3 style="margin-top:16px">WEEKLY SCHEDULE</h3>
<div class="day-tabs">
<button class="day-tab active" onclick="selDay('mon')">Mon</button>
<button class="day-tab" onclick="selDay('tue')">Tue</button>
<button class="day-tab" onclick="selDay('wed')">Wed</button>
<button class="day-tab" onclick="selDay('thu')">Thu</button>
<button class="day-tab" onclick="selDay('fri')">Fri</button>
<button class="day-tab" onclick="selDay('sat')">Sat</button>
<button class="day-tab" onclick="selDay('sun')">Sun</button>
</div>
<div class="sched-list" id="schedlist"></div>
<div class="add-entry">
<input type="time" id="newtime" value="08:00">
<select id="newmode"><option value="home">Home</option><option value="away">Away</option><option value="sleep">Sleep</option></select>
<button class="btn add" onclick="addEntry()">+</button>
</div>
</div>

<div class="card sync-card">
<button class="btn sync" id="syncbtn" onclick="syncZones()">SYNC TO PICO</button>
<div style="margin-top:8px;font-size:12px;color:#888">Copy Kitchen settings to Living Room</div>
</div>

<div class="card">
<div class="zone-title pico-title">Living Room (Pico)</div>
<div class="temp-small"><span id="ptemp">--</span>&deg;F</div>
<div class="row"><span id="phum">--%</span></div>
<div id="pstatus">Offline</div>
</div>
<div class="card">
<h3>PICO MODE</h3>
<div class="row">
<button class="btn" id="pm0" onclick="pmode(0)">OFF</button>
<button class="btn" id="pm1" onclick="pmode(1)">HEAT</button>
<button class="btn" id="pm2" onclick="pmode(2)">COOL</button>
<button class="btn" id="pm3" onclick="pmode(3)">AUTO</button>
</div>
<h3>PICO HEAT SETPOINT</h3>
<div class="setrow">
<button class="btn" onclick="padj('heat',-1)">-</button>
<span class="setval"><span id="phset">68</span>&deg;</span>
<button class="btn" onclick="padj('heat',1)">+</button>
</div>
<h3>PICO COOL SETPOINT</h3>
<div class="setrow">
<button class="btn" onclick="padj('cool',-1)">-</button>
<span class="setval"><span id="pcset">75</span>&deg;</span>
<button class="btn" onclick="padj('cool',1)">+</button>
</div>
<h3>BOOST (Portable Unit)</h3>
<div class="row">
<button class="btn" id="boost" onclick="boost()">BOOST OFF</button>
</div>
</div>

<script>
var hs=68,cs=75,phs=68,pcs=75,pboost=false;
function upd(d){
document.getElementById('temp').textContent=d.temp?d.temp.toFixed(1):'--';
document.getElementById('hum').textContent=d.humidity?d.humidity+'%':'--%';
document.getElementById('pres').textContent=d.pressure?(d.pressure*0.02953).toFixed(2):'--';
document.getElementById('hset').textContent=d.heat_setpoint;
document.getElementById('cset').textContent=d.cool_setpoint;
hs=d.heat_setpoint;cs=d.cool_setpoint;
var st=document.getElementById('status');
st.className=d.heating_active?'heating':d.cooling_active?'cooling':'';
st.textContent=d.heating_active?'HEATING':d.cooling_active?'COOLING':'Idle';
for(var i=0;i<4;i++)document.getElementById('m'+i).className='btn'+(d.mode==i?' active':'');
document.getElementById('s0').className='btn'+(d.cool_system==0?' cool':'');
document.getElementById('s1').className='btn'+(d.cool_system==1?' cool':'');
if(d.pico){updPico(d.pico);}else{
var ps=document.getElementById('pstatus');ps.className='offline';ps.textContent='Offline';}
}
function updPico(p){
document.getElementById('ptemp').textContent=p.temp?p.temp.toFixed(1):'--';
document.getElementById('phum').textContent=p.humidity?p.humidity+'%':'--%';
document.getElementById('phset').textContent=p.heat_setpoint;
document.getElementById('pcset').textContent=p.cool_setpoint;
phs=p.heat_setpoint;pcs=p.cool_setpoint;pboost=p.boost_active;
var ps=document.getElementById('pstatus');
ps.className=p.boost_active?'boost':p.heating_active?'heating':p.cooling_active?'cooling':'';
ps.textContent=p.boost_active?'BOOST':p.heating_active?'HEATING':p.cooling_active?'COOLING':'Idle';
for(var i=0;i<4;i++)document.getElementById('pm'+i).className='btn'+(p.mode==i?' active':'');
document.getElementById('boost').className='btn'+(p.boost_active?' boost':'');
document.getElementById('boost').textContent=p.boost_active?'BOOST ON':'BOOST OFF';
}
function get(){fetch('/api/status').then(r=>r.json()).then(upd).catch(e=>console.log(e));}
function mode(m){fetch('/api/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(upd);}
function adj(t,d){var v=(t=='heat'?hs:cs)+d;fetch('/api/'+(t=='heat'?'heat':'cool')+'_setpoint',{method:'POST',body:JSON.stringify({temp:v})}).then(r=>r.json()).then(upd);}
function sys(s){fetch('/api/cool_system',{method:'POST',body:JSON.stringify({system:s})}).then(r=>r.json()).then(upd);}
function pmode(m){fetch('/api/pico/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updPico);}
function padj(t,d){var v=(t=='heat'?phs:pcs)+d;fetch('/api/pico/'+(t=='heat'?'heat':'cool')+'_setpoint',{method:'POST',body:JSON.stringify({temp:v})}).then(r=>r.json()).then(updPico);}
function boost(){fetch('/api/pico/boost',{method:'POST',body:JSON.stringify({on:!pboost})}).then(r=>r.json()).then(updPico);}
var scurr='home',senabled=false,sched={},selday='mon';
function updSched(s){
senabled=s.enabled;scurr=s.current_mode;sched=s.schedule||{};
document.getElementById('schedon').checked=s.enabled;
document.getElementById('shome').className='btn home'+(s.current_mode=='home'?' active':'');
document.getElementById('saway').className='btn away'+(s.current_mode=='away'?' active':'');
document.getElementById('ssleep').className='btn sleep'+(s.current_mode=='sleep'?' active':'');
var st=s.enabled?'Schedule: '+s.current_mode.toUpperCase():'Schedule: OFF';
if(s.hold_until)st+=' (hold)';
document.getElementById('schedstatus').textContent=st;
renderDay();
}
function renderDay(){
var list=document.getElementById('schedlist');
var entries=sched[selday]||[];
entries.sort(function(a,b){return a.time.localeCompare(b.time);});
list.innerHTML=entries.map(function(e,i){
var cls=e.mode=='home'?'#38b000':e.mode=='away'?'#f77f00':'#7b2cbf';
return '<div class="sched-entry"><span class="time">'+e.time+'</span><span style="color:'+cls+'">'+e.mode.toUpperCase()+'</span><button class="del" onclick="delEntry('+i+')">X</button></div>';
}).join('');
document.querySelectorAll('.day-tab').forEach(function(t){t.className='day-tab'+(t.textContent.toLowerCase()==selday?' active':'');});
}
function selDay(d){selday=d;renderDay();}
function addEntry(){
var t=document.getElementById('newtime').value;
var m=document.getElementById('newmode').value;
if(!t)return;
var entries=sched[selday]||[];
entries.push({time:t,mode:m});
sched[selday]=entries;
fetch('/api/schedule/day',{method:'POST',body:JSON.stringify({day:selday,entries:entries})}).then(r=>r.json()).then(updSched);
}
function delEntry(i){
var entries=sched[selday]||[];
entries.splice(i,1);
sched[selday]=entries;
fetch('/api/schedule/day',{method:'POST',body:JSON.stringify({day:selday,entries:entries})}).then(r=>r.json()).then(updSched);
}
function getSched(){fetch('/api/schedule').then(r=>r.json()).then(updSched).catch(e=>console.log(e));}
function schedEnable(en){fetch('/api/schedule/enable',{method:'POST',body:JSON.stringify({enabled:en})}).then(r=>r.json()).then(updSched);}
function schedMode(m){fetch('/api/schedule/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updSched);}
function syncZones(){
var btn=document.getElementById('syncbtn');
btn.textContent='SYNCING...';
btn.className='btn sync synced';
fetch('/api/pico/sync',{method:'POST',body:'{}'}).then(r=>r.json()).then(function(p){
updPico(p);btn.textContent='SYNCED!';
setTimeout(function(){btn.textContent='SYNC TO PICO';btn.className='btn sync';},2000);
}).catch(function(){btn.textContent='SYNC FAILED';btn.className='btn sync';});
}
get();getSched();setInterval(get,3000);setInterval(getSched,10000);
</script>
</body>
</html>"""
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}"
