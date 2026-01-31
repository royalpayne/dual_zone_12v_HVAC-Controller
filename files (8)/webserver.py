# Web Server with Schedule Controls
import socket
import json
import config

class WebServer:
    def __init__(self, thermostat):
        self.therm = thermostat
        self.sock = None
    
    def start(self, port=80):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(5)
        self.sock.setblocking(False)
        print(f"Web server on port {port}")
    
    def poll(self):
        try:
            cl, addr = self.sock.accept()
            cl.settimeout(2)
            try:
                req = cl.recv(1024).decode()
                resp = self._route(req)
                cl.send(resp.encode())
            except:
                pass
            finally:
                cl.close()
        except:
            pass
    
    def _route(self, req):
        if 'GET /api/status' in req:
            return self._json(self.therm.get_status())
        elif 'POST /api/' in req:
            return self._post(req)
        elif 'GET /schedule' in req:
            return self._schedule_page()
        else:
            return self._main_page()
    
    def _json(self, data):
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}"
    
    def _post(self, req):
        try:
            body = req.split('\r\n\r\n')[1]
            d = json.loads(body)
            sched = self.therm.scheduler
            
            if '/api/mode' in req:
                self.therm.set_mode(d.get('v', 0))
            elif '/api/heat' in req:
                self.therm.adjust_heat(d.get('v', 0))
            elif '/api/cool' in req:
                self.therm.adjust_cool(d.get('v', 0))
            elif '/api/coolsys' in req:
                self.therm.set_cool_system(d.get('v', 0))
            elif '/api/quick' in req:
                sched.set_quick_mode(d.get('v', 0), d.get('h', 2))
            elif '/api/hold' in req:
                sched.set_hold(d.get('heat'), d.get('cool'), d.get('h'))
            elif '/api/resume' in req:
                sched.clear_hold()
            elif '/api/sched_en' in req:
                sched.schedule_enabled = d.get('v', True)
            elif '/api/sched_temps' in req:
                sched.set_schedule_temps(d.get('m'), d.get('heat'), d.get('cool'))
                sched.save()
            elif '/api/sched_day' in req:
                sched.set_schedule_entry(d.get('day'), d.get('entries'))
                sched.save()
        except Exception as e:
            print(f"POST err: {e}")
        return self._json(self.therm.get_status())
    
    def _main_page(self):
        h = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RV Thermostat</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:12px}
.c{background:#16213e;border-radius:10px;padding:12px;margin-bottom:10px;max-width:380px;margin-left:auto;margin-right:auto}
.tm{text-align:center;color:#888;font-size:13px}
.avg{font-size:44px;text-align:center;margin:8px 0}
.zn{display:flex;justify-content:space-around;border-top:1px solid #2a3f5f;padding-top:10px;margin-top:10px}
.z{text-align:center}.zn-n{font-size:11px;color:#888}.zn-t{font-size:18px}.zn-h{font-size:11px;color:#888}
.off{color:#e94560}
.pr{text-align:center;font-size:11px;color:#888;margin-top:8px}
.st{text-align:center;padding:10px;border-radius:8px;background:#2a3f5f}
.st.heat{background:#e94560}.st.cool{background:#00b4d8}
.si{text-align:center;font-size:11px;color:#888;margin-top:6px}
.row{display:flex;justify-content:center;gap:6px;margin:8px 0;flex-wrap:wrap}
.b{background:#0f3460;border:none;color:#fff;padding:10px 14px;border-radius:6px;font-size:13px;cursor:pointer}
.b.on{background:#e94560}.b.home{background:#27ae60}.b.away{background:#f39c12}.b.sleep{background:#8e44ad}.b.cy{background:#00b4d8}
.b.sm{padding:8px 10px;font-size:12px}
.sr{display:flex;align-items:center;justify-content:space-between;margin:8px 0}
.sv{font-size:22px;min-width:50px;text-align:center}
h3{font-size:11px;color:#888;margin:8px 0 4px}
.hb{background:#f39c12;color:#000;padding:2px 8px;border-radius:8px;font-size:10px;display:inline-block}
a{color:#00b4d8}
</style></head><body>
<div class="c">
<div class="tm"><span id="dy">--</span> <span id="ti">--:--</span></div>
<div class="avg"><span id="av">--</span>&deg;F</div>
<div class="zn">
<div class="z"><div class="zn-n" id="ln">Kitchen</div><div class="zn-t"><span id="lt">--</span>&deg;</div><div class="zn-h"><span id="lh">--</span>%</div></div>
<div class="z"><div class="zn-n" id="rn">Living Room</div><div class="zn-t"><span id="rt">--</span>&deg;</div><div class="zn-h"><span id="rh">--</span>%</div></div>
</div>
<div class="pr"><span id="pr">--</span> inHg</div>
</div>
<div class="c">
<div class="st" id="st">Idle</div>
<div class="si" id="si"></div>
</div>
<div class="c">
<h3>QUICK MODE</h3>
<div class="row">
<button class="b home sm" onclick="qm(0)">Home</button>
<button class="b away sm" onclick="qm(1)">Away</button>
<button class="b sleep sm" onclick="qm(2)">Sleep</button>
<button class="b sm" onclick="res()">Resume</button>
</div>
</div>
<div class="c">
<h3>HEAT SETPOINT</h3>
<div class="sr">
<button class="b sm" onclick="adj('heat',-1)">-</button>
<span class="sv"><span id="hs">68</span>&deg;</span>
<button class="b sm" onclick="adj('heat',1)">+</button>
</div>
<h3>COOL SETPOINT</h3>
<div class="sr">
<button class="b sm" onclick="adj('cool',-1)">-</button>
<span class="sv"><span id="cs">75</span>&deg;</span>
<button class="b sm" onclick="adj('cool',1)">+</button>
</div>
</div>
<div class="c">
<h3>SYSTEM MODE</h3>
<div class="row">
<button class="b sm" id="m0" onclick="md(0)">OFF</button>
<button class="b sm" id="m1" onclick="md(1)">HEAT</button>
<button class="b sm" id="m2" onclick="md(2)">COOL</button>
<button class="b sm" id="m3" onclick="md(3)">AUTO</button>
</div>
<h3>COOLING SYSTEM</h3>
<div class="row">
<button class="b sm" id="c0" onclick="cs(0)">Rooftop</button>
<button class="b sm" id="c1" onclick="cs(1)">Portable</button>
</div>
</div>
<div class="c" style="text-align:center">
<a href="/schedule">Edit Schedule &rarr;</a>
</div>
<script>
function $(i){return document.getElementById(i)}
function upd(d){
$('dy').innerText=d.day||'--';
$('ti').innerText=d.time||'--:--';
$('av').innerText=d.avg?d.avg.toFixed(1):'--';
$('lt').innerText=d.l_temp?d.l_temp.toFixed(1):'--';
$('lh').innerText=d.l_hum||'--';
$('rt').innerText=d.r_temp?d.r_temp.toFixed(1):'--';
$('rh').innerText=d.r_hum||'--';
$('ln').innerText=d.l_name||'Kitchen';
var rn=d.r_name||'Living Room';
$('rn').innerText=d.r_online?rn:rn+' (offline)';
$('rn').className=d.r_online?'zn-n':'zn-n off';
$('pr').innerText=d.l_pres?(d.l_pres*0.02953).toFixed(2):'--';
$('hs').innerText=d.heat_sp;
$('cs').innerText=d.cool_sp;
var st=$('st');
st.className='st'+(d.heating?' heat':'')+(d.cooling?' cool':'');
st.innerText=d.heating?'HEATING':d.cooling?'COOLING':'Idle';
var si='';
if(d.sched_on){
si=d.sched_name;
if(d.hold){si+=' <span class="hb">HOLD'+(d.hold_mins?' '+Math.floor(d.hold_mins/60)+'h'+d.hold_mins%60+'m':'')+'</span>';}
else if(d.next_mins){si+=' &bull; '+d.next_mode+' in '+Math.floor(d.next_mins/60)+'h'+d.next_mins%60+'m';}
}else{si='Schedule OFF';}
$('si').innerHTML=si;
for(var i=0;i<4;i++)$('m'+i).className='b sm'+(d.mode==i?' on':'');
$('c0').className='b sm'+(d.cool_sys==0?' cy':'');
$('c1').className='b sm'+(d.cool_sys==1?' cy':'');
}
function post(u,d,cb){fetch('/api/'+u,{method:'POST',body:JSON.stringify(d)}).then(r=>r.json()).then(cb||upd);}
function get(){fetch('/api/status').then(r=>r.json()).then(upd).catch(e=>console.log(e));}
function md(v){post('mode',{v:v});}
function adj(t,v){post(t,{v:v});}
function cs(v){post('coolsys',{v:v});}
function qm(v){post('quick',{v:v,h:2});}
function res(){post('resume',{});}
get();setInterval(get,3000);
</script></body></html>"""
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html;charset=utf-8\r\n\r\n{h}"
    
    def _schedule_page(self):
        h = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Schedule</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:12px}
.c{background:#16213e;border-radius:10px;padding:12px;margin-bottom:10px;max-width:400px;margin-left:auto;margin-right:auto}
h2{font-size:16px;margin-bottom:12px}
h3{font-size:12px;color:#888;margin:12px 0 6px}
.row{display:flex;gap:8px;margin:6px 0;align-items:center;flex-wrap:wrap}
.b{background:#0f3460;border:none;color:#fff;padding:8px 12px;border-radius:6px;font-size:12px;cursor:pointer}
.b.on{background:#e94560}.b.home{background:#27ae60}.b.away{background:#f39c12}.b.sleep{background:#8e44ad}
input[type=number]{width:50px;padding:6px;border-radius:4px;border:none;background:#0f3460;color:#fff;text-align:center}
.tbl{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
.tbl th,.tbl td{padding:6px;text-align:left;border-bottom:1px solid #2a3f5f}
.tbl th{color:#888}
select{padding:6px;border-radius:4px;border:none;background:#0f3460;color:#fff}
a{color:#00b4d8}
.sw{display:flex;align-items:center;gap:10px}
.switch{width:44px;height:24px;background:#0f3460;border-radius:12px;position:relative;cursor:pointer}
.switch.on{background:#27ae60}
.switch:after{content:'';position:absolute;width:20px;height:20px;background:#fff;border-radius:10px;top:2px;left:2px;transition:0.2s}
.switch.on:after{left:22px}
.msg{background:#27ae60;padding:8px;border-radius:6px;text-align:center;display:none}
</style></head><body>
<div class="c">
<a href="/">&larr; Back</a>
<h2 style="margin-top:12px">Schedule Settings</h2>
<div class="sw">
<span>Schedule</span>
<div class="switch" id="sen" onclick="togSched()"></div>
<span id="senl">ON</span>
</div>
</div>
<div class="c">
<h3>MODE TEMPERATURES</h3>
<div class="row"><span class="b home" style="width:60px">Home</span>
Heat:<input type="number" id="hh" value="70"> Cool:<input type="number" id="hc" value="74">
<button class="b" onclick="saveTmp(0)">Save</button></div>
<div class="row"><span class="b away" style="width:60px">Away</span>
Heat:<input type="number" id="ah" value="62"> Cool:<input type="number" id="ac" value="80">
<button class="b" onclick="saveTmp(1)">Save</button></div>
<div class="row"><span class="b sleep" style="width:60px">Sleep</span>
Heat:<input type="number" id="sh" value="66"> Cool:<input type="number" id="sc" value="72">
<button class="b" onclick="saveTmp(2)">Save</button></div>
<div class="msg" id="msg">Saved!</div>
</div>
<div class="c">
<h3>WEEKLY SCHEDULE</h3>
<p style="font-size:11px;color:#888">Select day to edit:</p>
<div class="row">
<button class="b" id="d0" onclick="selDay(0)">Mon</button>
<button class="b" id="d1" onclick="selDay(1)">Tue</button>
<button class="b" id="d2" onclick="selDay(2)">Wed</button>
<button class="b" id="d3" onclick="selDay(3)">Thu</button>
<button class="b" id="d4" onclick="selDay(4)">Fri</button>
<button class="b" id="d5" onclick="selDay(5)">Sat</button>
<button class="b" id="d6" onclick="selDay(6)">Sun</button>
</div>
<div id="dayEdit" style="margin-top:12px"></div>
</div>
<script>
var sched={},curDay=0,temps={};
function $(i){return document.getElementById(i)}
function upd(d){
var sw=$('sen');
sw.className=d.sched_on?'switch on':'switch';
$('senl').innerText=d.sched_on?'ON':'OFF';
if(d.temps){
temps=d.temps;
$('hh').value=d.temps.home?d.temps.home[0]:70;
$('hc').value=d.temps.home?d.temps.home[1]:74;
$('ah').value=d.temps.away?d.temps.away[0]:62;
$('ac').value=d.temps.away?d.temps.away[1]:80;
$('sh').value=d.temps.sleep?d.temps.sleep[0]:66;
$('sc').value=d.temps.sleep?d.temps.sleep[1]:72;
}}
function post(u,d){return fetch('/api/'+u,{method:'POST',body:JSON.stringify(d)}).then(r=>r.json());}
function get(){fetch('/api/status').then(r=>r.json()).then(upd);}
function togSched(){
var on=$('sen').className.includes('on');
post('sched_en',{v:!on}).then(upd);
}
function saveTmp(m){
var ids=[['hh','hc'],['ah','ac'],['sh','sc']][m];
var h=parseInt($(ids[0]).value),c=parseInt($(ids[1]).value);
post('sched_temps',{m:m,heat:h,cool:c}).then(d=>{
upd(d);$('msg').style.display='block';
setTimeout(()=>$('msg').style.display='none',2000);
});}
function selDay(d){
curDay=d;
for(var i=0;i<7;i++)$('d'+i).className='b'+(i==d?' on':'');
renderDay();
}
function renderDay(){
var ents=sched[curDay]||[];
var html='<table class="tbl"><tr><th>Time</th><th>Mode</th><th></th></tr>';
ents.forEach((e,i)=>{
var t=('0'+e[0]).slice(-2)+':'+('0'+e[1]).slice(-2);
var modes=['Home','Away','Sleep'];
html+='<tr><td>'+t+'</td><td class="'+(e[2]==0?'home':e[2]==1?'away':'sleep')+'">'+modes[e[2]]+'</td>';
html+='<td><button class="b" onclick="delEnt('+i+')">X</button></td></tr>';
});
html+='</table>';
html+='<div class="row" style="margin-top:10px">';
html+='<input type="time" id="nt" value="06:00">';
html+='<select id="nm"><option value="0">Home</option><option value="1">Away</option><option value="2">Sleep</option></select>';
html+='<button class="b" onclick="addEnt()">Add</button></div>';
$('dayEdit').innerHTML=html;
}
function addEnt(){
var t=$('nt').value.split(':');
var h=parseInt(t[0]),m=parseInt(t[1]),mode=parseInt($('nm').value);
if(!sched[curDay])sched[curDay]=[];
sched[curDay].push([h,m,mode]);
sched[curDay].sort((a,b)=>a[0]*60+a[1]-b[0]*60-b[1]);
saveDay();
}
function delEnt(i){
sched[curDay].splice(i,1);
saveDay();
}
function saveDay(){
post('sched_day',{day:curDay,entries:sched[curDay]}).then(()=>{
$('msg').style.display='block';
setTimeout(()=>$('msg').style.display='none',2000);
renderDay();
});}
function loadSched(){
fetch('/api/status').then(r=>r.json()).then(d=>{
upd(d);
// Load full schedule via separate call or embed - for now use defaults
sched={0:[[6,0,0],[8,0,1],[17,0,0],[22,0,2]],1:[[6,0,0],[8,0,1],[17,0,0],[22,0,2]],2:[[6,0,0],[8,0,1],[17,0,0],[22,0,2]],3:[[6,0,0],[8,0,1],[17,0,0],[22,0,2]],4:[[6,0,0],[8,0,1],[17,0,0],[23,0,2]],5:[[7,0,0],[23,0,2]],6:[[7,0,0],[22,0,2]]};
selDay(0);
});}
loadSched();
</script></body></html>"""
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html;charset=utf-8\r\n\r\n{h}"
