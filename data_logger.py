#!/usr/bin/env python3
"""RV Thermostat Data Logger — pulls history from Main ESP32 into SQLite.

Usage:
    python3 data_logger.py              # Run continuous logger (polls every 5 min)
    python3 data_logger.py --once       # Pull once and exit
    python3 data_logger.py --export     # Export database to CSV
    python3 data_logger.py --tail 20    # Show last N readings
    python3 data_logger.py --dashboard  # Start web dashboard on port 8080
    python3 data_logger.py --dashboard --port 9090  # Custom port
"""

import sys
import time
import json
import socket
import sqlite3
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta

# Configuration
MAIN_ESP32_IP = "192.168.71.152"
HISTORY_URL = f"http://{MAIN_ESP32_IP}/api/history"
DB_FILE = "thermostat_log.db"
POLL_INTERVAL = 300  # 5 minutes
TZ_OFFSET = -6  # US Central Standard Time

# Estimated power draw (watts) for each component
WATTS_ROOFTOP_COMPRESSOR = 1200  # Dometic Brisk II compressor
WATTS_ROOFTOP_FAN_LOW = 130      # Rooftop AC fan low speed
WATTS_ROOFTOP_FAN_HIGH = 180     # Rooftop AC fan high speed
WATTS_WHYNTER = 1300             # Whynter ARC-14SH (cool/dehum modes)
WATTS_DR_HEATER = 1500           # Dr. Infrared Heater
WATTS_FURNACE_BLOWER = 75        # RV furnace fan (heat is propane)
DEFAULT_ELEC_RATE = 0.13         # $/kWh

COLUMNS = [
    ('timestamp', 'INTEGER PRIMARY KEY'),
    ('kitchen_temp', 'REAL'),
    ('kitchen_humidity', 'REAL'),
    ('kitchen_pressure', 'REAL'),
    ('living_temp', 'REAL'),
    ('living_humidity', 'REAL'),
    ('living_pressure', 'REAL'),
    ('living_apparent_temp', 'REAL'),
    ('bl_temp', 'REAL'),
    ('bl_humidity', 'REAL'),
    ('mode', 'TEXT'),
    ('heat_setpoint', 'REAL'),
    ('cool_setpoint', 'REAL'),
    ('heating_active', 'INTEGER'),
    ('cooling_active', 'INTEGER'),
    ('whynter_mode', 'INTEGER'),
    ('heater_mode', 'INTEGER'),
    ('dehum_active', 'INTEGER'),
    ('fan_speed', 'INTEGER'),
]

# Map ESP32 history keys to SQLite column names
KEY_MAP = {
    'ts': 'timestamp',
    'k_temp': 'kitchen_temp',
    'k_hum': 'kitchen_humidity',
    'k_pres': 'kitchen_pressure',
    'l_temp': 'living_temp',
    'l_hum': 'living_humidity',
    'l_pres': 'living_pressure',
    'l_app': 'living_apparent_temp',
    'bl_temp': 'bl_temp',
    'bl_hum': 'bl_humidity',
    'mode': 'mode',
    'heat_sp': 'heat_setpoint',
    'cool_sp': 'cool_setpoint',
    'heating': 'heating_active',
    'cooling': 'cooling_active',
    'whynter': 'whynter_mode',
    'heater': 'heater_mode',
    'dehum': 'dehum_active',
    'fan': 'fan_speed',
}


def init_db():
    """Create database and table if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cols = ', '.join(f'{name} {typ}' for name, typ in COLUMNS)
    conn.execute(f'CREATE TABLE IF NOT EXISTS readings ({cols})')
    conn.commit()
    return conn


def get_last_timestamp(conn):
    """Get the most recent timestamp in the database."""
    row = conn.execute('SELECT MAX(timestamp) FROM readings').fetchone()
    return row[0] if row[0] else 0


def fetch_history(since=0):
    """Fetch history entries from the ESP32, paginating if needed."""
    all_entries = []
    current_since = since
    while True:
        url = f"{HISTORY_URL}?since={current_since}&limit=500" if current_since else f"{HISTORY_URL}?limit=500"
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                entries = data.get('entries', [])
                all_entries.extend(entries)
                if not data.get('more', False) or not entries:
                    break
                # Next page starts after the last entry
                current_since = max(e.get('ts', 0) for e in entries)
                print(f"  Fetched {len(all_entries)} entries so far, getting more...")
        except Exception as e:
            print(f"  Fetch error: {e}")
            break
    return all_entries


def store_entries(conn, entries):
    """Insert entries into SQLite, skipping duplicates."""
    col_names = [name for name, _ in COLUMNS]
    placeholders = ', '.join(['?'] * len(col_names))
    insert_sql = f'INSERT OR IGNORE INTO readings ({", ".join(col_names)}) VALUES ({placeholders})'

    count = 0
    for entry in entries:
        row = []
        for col_name, _ in COLUMNS:
            # Find the ESP32 key that maps to this column
            esp_key = None
            for k, v in KEY_MAP.items():
                if v == col_name:
                    esp_key = k
                    break
            value = entry.get(esp_key) if esp_key else None
            # Convert timestamp to integer
            if col_name == 'timestamp' and value is not None:
                value = int(value)
            row.append(value)
        conn.execute(insert_sql, row)
        count += 1

    conn.commit()
    return count


def format_timestamp(ts):
    """Format a MicroPython timestamp to local time string."""
    # MicroPython epoch is 2000-01-01, Python epoch is 1970-01-01
    # Offset: 946684800 seconds
    unix_ts = ts + 946684800
    dt = datetime.fromtimestamp(unix_ts, tz=timezone(timedelta(hours=TZ_OFFSET)))
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def pull_once(conn):
    """Pull new data from ESP32 and store it."""
    last_ts = get_last_timestamp(conn)
    print(f"  Last recorded: {format_timestamp(last_ts) if last_ts else 'none'}")
    entries = fetch_history(since=last_ts)
    if entries:
        count = store_entries(conn, entries)
        latest = max(e.get('ts', 0) for e in entries)
        print(f"  Stored {count} entries (latest: {format_timestamp(latest)})")
    else:
        print("  No new entries")
    return len(entries)


def export_csv():
    """Export the database to CSV."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute('SELECT * FROM readings ORDER BY timestamp')
    col_names = [desc[0] for desc in cursor.description]

    csv_file = DB_FILE.replace('.db', '.csv')
    with open(csv_file, 'w') as f:
        f.write(','.join(col_names) + '\n')
        for row in cursor:
            values = []
            for i, val in enumerate(row):
                if col_names[i] == 'timestamp' and val:
                    values.append(format_timestamp(val))
                else:
                    values.append(str(val) if val is not None else '')
            f.write(','.join(values) + '\n')

    total = conn.execute('SELECT COUNT(*) FROM readings').fetchone()[0]
    conn.close()
    print(f"Exported {total} readings to {csv_file}")


def show_tail(n=20):
    """Show the last N readings."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        'SELECT timestamp, kitchen_temp, kitchen_humidity, living_temp, living_humidity, '
        'mode, heating_active, cooling_active, whynter_mode, dehum_active '
        'FROM readings ORDER BY timestamp DESC LIMIT ?', (n,)
    )

    rows = cursor.fetchall()
    if not rows:
        print("No data in database.")
        conn.close()
        return

    print(f"{'Time':<20} {'K.Temp':>6} {'K.Hum':>5} {'L.Temp':>6} {'L.Hum':>5} "
          f"{'Mode':<5} {'Heat':>4} {'Cool':>4} {'Whyn':>4} {'Dehm':>4}")
    print('-' * 85)
    for row in reversed(rows):
        ts_str = format_timestamp(row[0]) if row[0] else '?'
        k_temp = f"{row[1]:.1f}" if row[1] else '--'
        k_hum = f"{row[2]:.0f}%" if row[2] else '--'
        l_temp = f"{row[3]:.1f}" if row[3] else '--'
        l_hum = f"{row[4]:.0f}%" if row[4] else '--'
        mode = row[5] or '--'
        heat = row[6] or 0
        cool = row[7] or 0
        whyn = row[8] or 0
        dehm = row[9] or 0
        print(f"{ts_str:<20} {k_temp:>6} {k_hum:>5} {l_temp:>6} {l_hum:>5} "
              f"{mode:<5} {heat:>4} {cool:>4} {whyn:>4} {dehm:>4}")

    conn.close()


def run_continuous():
    """Run continuous polling loop."""
    conn = init_db()
    print(f"Data logger started — polling {MAIN_ESP32_IP} every {POLL_INTERVAL}s")
    print(f"Database: {DB_FILE}")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
            print(f"[{now.strftime('%H:%M:%S')}] Polling...")
            pull_once(conn)
        except KeyboardInterrupt:
            print("\nStopping logger.")
            break
        except Exception as e:
            print(f"  Error: {e}")

        try:
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\nStopping logger.")
            break

    conn.close()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RV Thermostat Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:16px}
h1{text-align:center;color:#00b4d8;margin-bottom:8px;font-size:1.4em}
.subtitle{text-align:center;color:#888;font-size:0.85em;margin-bottom:16px}
.controls{text-align:center;margin-bottom:16px}
.controls button{background:#16213e;color:#e0e0e0;border:1px solid #444;padding:8px 16px;margin:2px;
  cursor:pointer;border-radius:4px;font-size:0.9em}
.controls button.active{background:#00b4d8;color:#000;border-color:#00b4d8}
.controls button:hover{border-color:#00b4d8}
.chart-box{background:#16213e;border-radius:8px;padding:12px;margin-bottom:16px;position:relative}
.chart-box h2{color:#aaa;font-size:0.95em;margin-bottom:8px}
.chart-box canvas{width:100%!important;max-height:250px}
.energy-panel{background:#16213e;border-radius:8px;padding:16px;margin-bottom:16px}
.energy-panel h2{color:#aaa;font-size:0.95em;margin-bottom:12px}
.energy-total{text-align:center;margin-bottom:12px}
.energy-total .kwh{font-size:2em;color:#00b4d8;font-weight:bold}
.energy-total .cost{font-size:1.1em;color:#4cc9f0;margin-left:12px}
.energy-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}
.energy-item{background:#1a1a2e;border-radius:6px;padding:10px;text-align:center}
.energy-item .label{color:#888;font-size:0.75em;text-transform:uppercase;letter-spacing:0.5px}
.energy-item .value{color:#e0e0e0;font-size:1.1em;font-weight:bold;margin:4px 0}
.energy-item .runtime{color:#666;font-size:0.75em}
.away-panel{background:#16213e;border-radius:8px;padding:16px;margin-bottom:16px}
.away-panel h2{color:#aaa;font-size:0.95em;margin-bottom:12px}
.away-mode-indicator{text-align:center;margin-bottom:12px}
.away-mode-indicator .mode-badge{display:inline-block;padding:6px 20px;border-radius:20px;font-weight:bold;
  font-size:1.1em;letter-spacing:1px}
.away-mode-indicator .mode-badge.home{background:#0a4d2e;color:#2ecc71}
.away-mode-indicator .mode-badge.away{background:#4d2e0a;color:#e67e22}
.away-mode-indicator .mode-badge.sleep{background:#1a1a4d;color:#9b59b6}
.away-hold-info{text-align:center;color:#888;font-size:0.85em;margin-bottom:12px}
.away-btns{text-align:center;margin-bottom:12px}
.away-btns button{padding:8px 16px;margin:3px;border-radius:4px;border:1px solid #444;cursor:pointer;font-size:0.9em}
.away-btns .btn-away{background:#4d2e0a;color:#e67e22;border-color:#e67e22}
.away-btns .btn-away:hover{background:#6d3e1a}
.away-btns .btn-home{background:#0a4d2e;color:#2ecc71;border-color:#2ecc71}
.away-btns .btn-home:hover{background:#1a6d3e}
.away-btns .btn-dur{background:#16213e;color:#e0e0e0}
.away-btns .btn-dur:hover{border-color:#00b4d8}
.away-btns .btn-dur.active{background:#00b4d8;color:#000;border-color:#00b4d8}
.away-summary{text-align:center;color:#666;font-size:0.8em;margin-top:8px}
.status{text-align:center;color:#666;font-size:0.8em;margin-top:8px}
.link{text-align:center;margin-bottom:12px}
.link a{color:#00b4d8;text-decoration:none;font-size:0.85em}
.link a:hover{text-decoration:underline}
</style>
</head>
<body>
<h1>RV Thermostat Dashboard</h1>
<div class="link"><a href="http://192.168.71.152/" target="_blank">Open Thermostat Control Panel</a></div>
<div class="controls" id="range-btns">
  <button onclick="setRange(1)">1h</button>
  <button onclick="setRange(6)">6h</button>
  <button onclick="setRange(12)">12h</button>
  <button onclick="setRange(24)" class="active">24h</button>
  <button onclick="setRange(72)">3d</button>
  <button onclick="setRange(168)">7d</button>
</div>
<div class="chart-box"><h2>Temperature (&deg;F)</h2><canvas id="tempChart"></canvas></div>
<div class="chart-box"><h2>Humidity (% RH)</h2><canvas id="humChart"></canvas></div>
<div class="chart-box"><h2>System State</h2><canvas id="stateChart"></canvas></div>
<div class="energy-panel" id="energy-panel">
  <h2>Estimated Energy Usage</h2>
  <div class="energy-total">
    <span class="kwh" id="e-total">--</span> <span style="color:#888">kWh</span>
    <span class="cost" id="e-cost"></span>
  </div>
  <div class="energy-grid">
    <div class="energy-item"><div class="label">Rooftop Compressor</div><div class="value" id="e-comp">--</div><div class="runtime" id="e-comp-rt"></div></div>
    <div class="energy-item"><div class="label">Rooftop Fan</div><div class="value" id="e-fan">--</div><div class="runtime" id="e-fan-rt"></div></div>
    <div class="energy-item"><div class="label">Whynter</div><div class="value" id="e-whyn">--</div><div class="runtime" id="e-whyn-rt"></div></div>
    <div class="energy-item"><div class="label">Dr. Heater</div><div class="value" id="e-heat">--</div><div class="runtime" id="e-heat-rt"></div></div>
    <div class="energy-item"><div class="label">Furnace Blower</div><div class="value" id="e-furn">--</div><div class="runtime" id="e-furn-rt"></div></div>
  </div>
</div>
<div class="away-panel">
  <h2>Schedule Override</h2>
  <div class="away-mode-indicator"><span class="mode-badge home" id="mode-badge">HOME</span></div>
  <div class="away-hold-info" id="hold-info"></div>
  <div class="away-btns">
    <span style="color:#888;font-size:0.8em">Hold Home:</span>
    <button class="btn-home" onclick="holdHome(4)">4h</button>
    <button class="btn-home" onclick="holdHome(8)">8h</button>
    <button class="btn-home" onclick="holdHome(12)">12h</button>
  </div>
  <div class="away-btns">
    <span style="color:#888;font-size:0.8em">Hold Away:</span>
    <button class="btn-away" onclick="goAway(4)">4h</button>
    <button class="btn-away" onclick="goAway(8)">8h</button>
    <button class="btn-away" onclick="goAway(12)">12h</button>
    <button class="btn-away" onclick="goAway(24)">24h</button>
    <button class="btn-away" onclick="goAway(48)">48h</button>
  </div>
  <div class="away-btns">
    <button class="btn-home" onclick="cancelHold()" style="background:#16213e;color:#e0e0e0;border-color:#666">Cancel Hold</button>
  </div>
  <div class="away-summary" id="away-summary"></div>
</div>
<div class="status" id="status">Loading...</div>
<script>
let hours=24, refreshTimer=null;
const chartOpts=(yLabel)=>({
  responsive:true,maintainAspectRatio:false,animation:false,
  scales:{
    x:{type:'time',time:{tooltipFormat:'MMM d, h:mm a',displayFormats:{minute:'h:mm a',hour:'h a',day:'MMM d'}},
       ticks:{color:'#888',maxTicksLimit:8},grid:{color:'#2a2a4a'}},
    y:{title:{display:true,text:yLabel,color:'#aaa'},ticks:{color:'#888'},grid:{color:'#2a2a4a'}}
  },
  plugins:{legend:{labels:{color:'#ccc',boxWidth:12,padding:10}},tooltip:{mode:'index',intersect:false}},
  interaction:{mode:'nearest',axis:'x',intersect:false},
  elements:{point:{radius:0},line:{borderWidth:2}}
});
const tempChart=new Chart(document.getElementById('tempChart'),{type:'line',
  data:{datasets:[
    {label:'Kitchen',borderColor:'#e94560',data:[]},
    {label:'Living Room',borderColor:'#00b4d8',data:[]},
    {label:'HTS2',borderColor:'#9d4edd',data:[]},
    {label:'Heat SP',borderColor:'#ff6b35',borderDash:[5,5],borderWidth:1,data:[]},
    {label:'Cool SP',borderColor:'#4cc9f0',borderDash:[5,5],borderWidth:1,data:[]}
  ]},options:chartOpts('°F')});
const humChart=new Chart(document.getElementById('humChart'),{type:'line',
  data:{datasets:[
    {label:'Kitchen',borderColor:'#e94560',data:[]},
    {label:'Living Room',borderColor:'#00b4d8',data:[]},
    {label:'HTS2',borderColor:'#9d4edd',data:[]}
  ]},options:chartOpts('% RH')});
const stateChart=new Chart(document.getElementById('stateChart'),{type:'line',
  data:{datasets:[
    {label:'Heating',borderColor:'#e94560',backgroundColor:'rgba(233,69,96,0.15)',fill:true,stepped:true,data:[]},
    {label:'Cooling',borderColor:'#00b4d8',backgroundColor:'rgba(0,180,216,0.15)',fill:true,stepped:true,data:[]},
    {label:'Dehum',borderColor:'#9d4edd',backgroundColor:'rgba(157,77,221,0.15)',fill:true,stepped:true,data:[]},
    {label:'Whynter',borderColor:'#f72585',backgroundColor:'rgba(247,37,133,0.15)',fill:true,stepped:true,data:[]}
  ]},options:{...chartOpts('Active'),scales:{...chartOpts('Active').scales,
    y:{...chartOpts('Active').scales.y,min:-0.1,max:1.5,ticks:{color:'#888',stepSize:1,
       callback:v=>v===0?'Off':v===1?'On':''}}}}});

function setRange(h){
  hours=h;
  document.querySelectorAll('#range-btns button').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
  fetchData();fetchEnergy();
}
function fetchData(){
  fetch('/api/chart_data?hours='+hours).then(r=>r.json()).then(d=>{
    const ts=d.map(r=>new Date(r.t*1000));
    function zip(arr,key){return arr.map((r,i)=>({x:ts[i],y:r[key]})).filter(p=>p.y!=null);}
    tempChart.data.datasets[0].data=zip(d,'kt');
    tempChart.data.datasets[1].data=zip(d,'lt');
    tempChart.data.datasets[2].data=zip(d,'bt');
    tempChart.data.datasets[3].data=zip(d,'hsp');
    tempChart.data.datasets[4].data=zip(d,'csp');
    tempChart.update();
    humChart.data.datasets[0].data=zip(d,'kh');
    humChart.data.datasets[1].data=zip(d,'lh');
    humChart.data.datasets[2].data=zip(d,'bh');
    humChart.update();
    stateChart.data.datasets[0].data=zip(d,'heat');
    stateChart.data.datasets[1].data=zip(d,'cool');
    stateChart.data.datasets[2].data=zip(d,'dehum');
    stateChart.data.datasets[3].data=zip(d,'whyn');
    stateChart.update();
    document.getElementById('status').textContent=
      d.length+' data points | Last update: '+new Date().toLocaleTimeString();
  }).catch(e=>{document.getElementById('status').textContent='Error: '+e;});
}
function fmtKwh(v){return v<0.01?'0':v<1?v.toFixed(2):v.toFixed(1);}
function fmtRuntime(min){
  if(min<1)return '';
  if(min<60)return Math.round(min)+'m';
  let h=Math.floor(min/60),m=Math.round(min%60);
  return h+'h'+(m>0?' '+m+'m':'');
}
function fetchEnergy(){
  fetch('/api/energy?hours='+hours).then(r=>r.json()).then(d=>{
    document.getElementById('e-total').textContent=fmtKwh(d.total_kwh);
    document.getElementById('e-cost').textContent=d.est_cost>0?'~$'+d.est_cost.toFixed(2):'';
    const b=d.breakdown,rt=d.runtime_min;
    document.getElementById('e-comp').textContent=fmtKwh(b.compressor_kwh)+' kWh';
    document.getElementById('e-fan').textContent=fmtKwh(b.fan_kwh)+' kWh';
    document.getElementById('e-whyn').textContent=fmtKwh(b.whynter_kwh)+' kWh';
    document.getElementById('e-heat').textContent=fmtKwh(b.heater_kwh)+' kWh';
    document.getElementById('e-furn').textContent=fmtKwh(b.furnace_kwh)+' kWh';
    document.getElementById('e-comp-rt').textContent=fmtRuntime(rt.compressor_min);
    document.getElementById('e-fan-rt').textContent=fmtRuntime(rt.fan_min);
    document.getElementById('e-whyn-rt').textContent=fmtRuntime(rt.whynter_min);
    document.getElementById('e-heat-rt').textContent=fmtRuntime(rt.heater_min);
    document.getElementById('e-furn-rt').textContent=fmtRuntime(rt.furnace_min);
  }).catch(e=>{});
}
function goAway(h){
  fetch('/api/away',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({hours:h})}).then(r=>r.json()).then(d=>{
    if(d.ok)fetchScheduler();
  }).catch(e=>{});
}
function holdHome(h){
  fetch('/api/hold_home',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({hours:h})}).then(r=>r.json()).then(d=>{
    if(d.ok)fetchScheduler();
  }).catch(e=>{});
}
function cancelHold(){
  fetch('/api/home',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({})}).then(r=>r.json()).then(d=>{
    if(d.ok)fetchScheduler();
  }).catch(e=>{});
}
function fetchScheduler(){
  fetch('/api/scheduler_status').then(r=>r.json()).then(d=>{
    if(d.error){document.getElementById('away-summary').textContent='Scheduler unavailable';return;}
    const mode=d.current_mode||'home';
    const badge=document.getElementById('mode-badge');
    badge.textContent=mode.toUpperCase();
    badge.className='mode-badge '+mode;
    const info=document.getElementById('hold-info');
    if(d.hold_until){
      const remain=Math.max(0,d.hold_until-Date.now()/1000+946684800);
      const rh=Math.floor(remain/3600),rm=Math.floor((remain%3600)/60);
      info.textContent=rh>0?'Hold: '+rh+'h '+rm+'m remaining':'Hold: '+rm+'m remaining';
    }else{info.textContent=d.enabled?'Schedule active':'Schedule disabled';}
    const p=d.presets||{};
    const ap=p[mode]||{};
    const summary='Current: Heat '+( ap.heat||'?')+'°F | Cool '+(ap.cool||'?')+'°F | Humidity '+(ap.humidity||'?')+'%';
    const away=p.away||{};
    const home=p.home||{};
    const savings=mode==='away'?'':'Away profile: Heat '+away.heat+'°F | Cool '+away.cool+'°F | Humidity '+away.humidity+'%';
    document.getElementById('away-summary').textContent=summary+(savings?' — '+savings:'');
  }).catch(e=>{});
}
fetchData();fetchEnergy();fetchScheduler();
refreshTimer=setInterval(()=>{fetchData();fetchEnergy();fetchScheduler();},300000);
</script>
</body>
</html>"""


def calc_energy(hours=24):
    """Calculate estimated energy usage from logged data.

    Walks consecutive readings, computes time intervals, and sums
    wattage × hours for each active component.
    """
    now_unix = time.time()
    cutoff_mp = now_unix - (hours * 3600) - 946684800

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        'SELECT timestamp, heating_active, cooling_active, whynter_mode, '
        'heater_mode, dehum_active, fan_speed '
        'FROM readings WHERE timestamp > ? ORDER BY timestamp',
        (cutoff_mp,)
    )
    rows = cursor.fetchall()
    conn.close()

    totals = {
        'compressor_kwh': 0.0,
        'fan_kwh': 0.0,
        'whynter_kwh': 0.0,
        'heater_kwh': 0.0,
        'furnace_kwh': 0.0,
    }
    runtime = {
        'compressor_min': 0.0,
        'fan_min': 0.0,
        'whynter_min': 0.0,
        'heater_min': 0.0,
        'furnace_min': 0.0,
    }

    for i in range(1, len(rows)):
        prev, curr = rows[i - 1], rows[i]
        dt_hours = (curr[0] - prev[0]) / 3600.0
        # Skip gaps > 15 minutes (logger wasn't running)
        if dt_hours > 0.25:
            continue

        # Use the state from the previous reading for this interval
        heating = prev[1] or 0
        cooling = prev[2] or 0
        whynter = prev[3] or 0
        heater = prev[4] or 0
        fan_speed = prev[6] or 0

        if cooling:
            totals['compressor_kwh'] += WATTS_ROOFTOP_COMPRESSOR * dt_hours / 1000
            runtime['compressor_min'] += dt_hours * 60

        if fan_speed == 1:
            totals['fan_kwh'] += WATTS_ROOFTOP_FAN_LOW * dt_hours / 1000
            runtime['fan_min'] += dt_hours * 60
        elif fan_speed == 2:
            totals['fan_kwh'] += WATTS_ROOFTOP_FAN_HIGH * dt_hours / 1000
            runtime['fan_min'] += dt_hours * 60

        if whynter:
            totals['whynter_kwh'] += WATTS_WHYNTER * dt_hours / 1000
            runtime['whynter_min'] += dt_hours * 60

        if heater:
            totals['heater_kwh'] += WATTS_DR_HEATER * dt_hours / 1000
            runtime['heater_min'] += dt_hours * 60

        if heating:
            totals['furnace_kwh'] += WATTS_FURNACE_BLOWER * dt_hours / 1000
            runtime['furnace_min'] += dt_hours * 60

    total_kwh = sum(totals.values())
    return {
        'hours': hours,
        'total_kwh': round(total_kwh, 3),
        'breakdown': {k: round(v, 3) for k, v in totals.items()},
        'runtime_min': {k: round(v, 1) for k, v in runtime.items()},
        'data_points': len(rows),
    }


def esp32_post(path, data):
    """Send a POST request to the Main ESP32.

    ESP32 MicroPython webserver doesn't always send Content-Length,
    so we use a short timeout and accept partial/no response.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((MAIN_ESP32_IP, 80))
        body = json.dumps(data)
        request = (f"POST {path} HTTP/1.0\r\n"
                   f"Host: {MAIN_ESP32_IP}\r\n"
                   f"Content-Type: application/json\r\n"
                   f"Content-Length: {len(body)}\r\n"
                   f"Connection: close\r\n\r\n{body}")
        s.sendall(request.encode())
        # Read response (may be partial — that's OK, command was sent)
        resp = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                resp += chunk
        except socket.timeout:
            pass
        # Parse JSON from response body
        text = resp.decode()
        if '\r\n\r\n' in text:
            return json.loads(text.split('\r\n\r\n', 1)[1])
        return {'sent': True}
    finally:
        s.close()


def esp32_get(path):
    """Send a GET request to the Main ESP32.

    Uses raw socket with HTTP/1.0 to force connection close.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((MAIN_ESP32_IP, 80))
        request = (f"GET {path} HTTP/1.0\r\n"
                   f"Host: {MAIN_ESP32_IP}\r\n"
                   f"Connection: close\r\n\r\n")
        s.sendall(request.encode())
        resp = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                resp += chunk
        except socket.timeout:
            pass
        text = resp.decode()
        if '\r\n\r\n' in text:
            return json.loads(text.split('\r\n\r\n', 1)[1])
        return {'error': 'no response'}
    finally:
        s.close()


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the dashboard web server."""

    def log_message(self, format, *args):
        pass  # Suppress request logging

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/chart_data':
            self._api_chart_data(parsed)
        elif parsed.path == '/api/energy':
            self._api_energy(parsed)
        elif parsed.path == '/api/scheduler_status':
            self._api_scheduler_status()
        elif parsed.path == '/':
            self._serve_dashboard()
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_len)) if content_len else {}
        if parsed.path == '/api/away':
            self._api_away(body)
        elif parsed.path == '/api/hold_home':
            self._api_hold_home(body)
        elif parsed.path == '/api/home':
            self._api_home(body)
        else:
            self.send_error(404)

    def _serve_dashboard(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(DASHBOARD_HTML.encode())

    def _api_energy(self, parsed):
        params = parse_qs(parsed.query)
        hours = min(int(params.get('hours', ['24'])[0]), 168)
        rate = float(params.get('rate', [str(DEFAULT_ELEC_RATE)])[0])
        result = calc_energy(hours)
        result['rate'] = rate
        result['est_cost'] = round(result['total_kwh'] * rate, 2)
        self._json_response(result)

    def _api_scheduler_status(self):
        """Proxy scheduler status from ESP32."""
        try:
            data = esp32_get('/api/schedule')
        except Exception as e:
            data = {'error': str(e)}
        self._json_response(data)

    def _api_away(self, body):
        """Activate away mode on ESP32 scheduler."""
        hours = body.get('hours', 8)
        try:
            # Set hold first (applies away setpoints immediately),
            # then enable scheduler (so it resumes after hold expires)
            esp32_post('/api/schedule/mode', {'mode': 'away', 'hours': hours})
            esp32_post('/api/schedule/enable', {'enabled': True})
            data = {'ok': True, 'mode': 'away', 'hours': hours}
        except Exception as e:
            data = {'ok': False, 'error': str(e)}
        self._json_response(data)

    def _api_hold_home(self, body):
        """Hold home mode for N hours (overrides schedule)."""
        hours = body.get('hours', 8)
        try:
            esp32_post('/api/schedule/mode', {'mode': 'home', 'hours': hours})
            esp32_post('/api/schedule/enable', {'enabled': True})
            data = {'ok': True, 'mode': 'home', 'hours': hours}
        except Exception as e:
            data = {'ok': False, 'error': str(e)}
        self._json_response(data)

    def _api_home(self, body):
        """Cancel hold, return to schedule."""
        try:
            esp32_post('/api/schedule/mode', {'mode': 'home', 'hours': 0})
            data = {'ok': True, 'mode': 'home'}
        except Exception as e:
            data = {'ok': False, 'error': str(e)}
        self._json_response(data)

    def _json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _api_chart_data(self, parsed):
        params = parse_qs(parsed.query)
        hours = min(int(params.get('hours', ['24'])[0]), 168)

        # Calculate time cutoff (MicroPython epoch: 2000-01-01)
        now_unix = time.time()
        cutoff_unix = now_unix - (hours * 3600)
        cutoff_mp = cutoff_unix - 946684800  # Convert to MicroPython epoch

        conn = sqlite3.connect(DB_FILE)
        # Downsample: pick interval based on range
        if hours <= 1:
            step = 1  # every reading
        elif hours <= 12:
            step = 5  # ~5 min
        elif hours <= 48:
            step = 10  # ~10 min
        else:
            step = 30  # ~30 min

        cursor = conn.execute(
            'SELECT timestamp, kitchen_temp, kitchen_humidity, living_temp, living_humidity, '
            'bl_temp, bl_humidity, heat_setpoint, cool_setpoint, '
            'heating_active, cooling_active, dehum_active, whynter_mode '
            'FROM readings WHERE timestamp > ? ORDER BY timestamp',
            (cutoff_mp,)
        )

        rows = cursor.fetchall()
        conn.close()

        # Downsample by taking every Nth row
        if step > 1 and len(rows) > step:
            rows = rows[::step] + [rows[-1]]  # Always include latest

        data = []
        for r in rows:
            ts_unix = r[0] + 946684800 if r[0] else 0
            data.append({
                't': ts_unix,
                'kt': r[1], 'kh': r[2],
                'lt': r[3], 'lh': r[4],
                'bt': r[5], 'bh': r[6],
                'hsp': r[7], 'csp': r[8],
                'heat': r[9] or 0, 'cool': r[10] or 0,
                'dehum': r[11] or 0, 'whyn': 1 if r[12] else 0
            })

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def run_dashboard(port=8080):
    """Start the dashboard web server with background data logging."""
    # Main thread connection — for initial pull only
    conn = init_db()

    # Pull initial data before starting server
    print(f"Pulling initial data from {MAIN_ESP32_IP}...")
    try:
        pull_once(conn)
    except Exception:
        pass
    conn.close()

    # Background logger gets its own connection (SQLite is not thread-safe)
    def logger_thread():
        logger_conn = init_db()
        while True:
            try:
                pull_once(logger_conn)
            except Exception as e:
                print(f"  Logger error: {e}")
            time.sleep(POLL_INTERVAL)

    t = threading.Thread(target=logger_thread, daemon=True)
    t.start()

    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"Dashboard: http://localhost:{port}")
    print(f"Data logger running in background (polling every {POLL_INTERVAL}s)")
    print("Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
        server.shutdown()


def main():
    if '--dashboard' in sys.argv:
        port = 8080
        if '--port' in sys.argv:
            idx = sys.argv.index('--port')
            port = int(sys.argv[idx + 1])
        run_dashboard(port)
    elif '--export' in sys.argv:
        export_csv()
    elif '--tail' in sys.argv:
        idx = sys.argv.index('--tail')
        n = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 20
        show_tail(n)
    elif '--once' in sys.argv:
        conn = init_db()
        pull_once(conn)
        conn.close()
    else:
        run_continuous()


if __name__ == '__main__':
    main()
