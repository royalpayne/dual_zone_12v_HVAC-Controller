# Thermostat Web Server - With Remote Integration
import socket
import json
import time
import btree
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
        # History buffer for data logging
        self.history = []
        self.history_max = getattr(config, 'HISTORY_MAX', 1440)
        # Persistent history via btree
        self._db = None
        self._db_file = None
        self._writes_since_flush = 0
        self._init_history_db()

    def _init_history_db(self):
        """Open/create btree file and reload recent history into RAM"""
        import os
        db_file = getattr(config, 'HISTORY_DB_FILE', 'history.db')
        try:
            # Check if file exists and its size
            file_exists = False
            try:
                stat = os.stat(db_file)
                file_exists = True
                print(f"History DB: file exists, {stat[6]} bytes")
                # If file is 0 bytes, it's invalid — remove and recreate
                if stat[6] == 0:
                    os.remove(db_file)
                    file_exists = False
                    print("History DB: removed empty file")
            except OSError:
                print("History DB: creating new file")

            if file_exists:
                self._db_file = open(db_file, 'r+b')
            else:
                self._db_file = open(db_file, 'w+b')
            self._db = btree.open(self._db_file)
            self._prune_history_db()
            # Reload recent entries into RAM history
            count = 0
            for key in self._db:
                entry = json.loads(self._db[key])
                self.history.append(entry)
                count += 1
            # Trim to max if btree had more than HISTORY_MAX
            if len(self.history) > self.history_max:
                self.history = self.history[-self.history_max:]
            print(f"History DB: loaded {count} entries from flash")
        except Exception as e:
            print(f"History DB init error: {e}")
            # If btree open failed on existing file, try fresh start
            try:
                if self._db_file:
                    self._db_file.close()
                try:
                    os.remove(db_file)
                except:
                    pass
                self._db_file = open(db_file, 'w+b')
                self._db = btree.open(self._db_file)
                print("History DB: created fresh after error")
            except Exception as e2:
                print(f"History DB fresh start failed: {e2}")
                self._db = None

    def _prune_history_db(self):
        """Delete entries older than HISTORY_PERSIST_DAYS"""
        if not self._db:
            return
        max_age = getattr(config, 'HISTORY_PERSIST_DAYS', 7) * 86400
        cutoff = time.time() - max_age
        cutoff_key = ("%010d" % int(cutoff)).encode()
        pruned = 0
        keys_to_delete = []
        for key in self._db:
            if key < cutoff_key:
                keys_to_delete.append(key)
            else:
                break  # Keys are sorted, no need to continue
        for key in keys_to_delete:
            del self._db[key]
            pruned += 1
        if pruned:
            self._db.flush()
            print(f"History DB: pruned {pruned} old entries")

    def _db_write(self, entry):
        """Write entry to btree and flush to flash"""
        if not self._db:
            return
        try:
            key = ("%010d" % int(entry['ts'])).encode()
            self._db[key] = json.dumps(entry).encode()
            self._writes_since_flush += 1
            self._db.flush()
        except Exception as e:
            print(f"History DB write error: {e}")

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
        if 'GET /api/history' in request:
            return self._api_history(request)
        elif 'GET /api/status' in request:
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

    def record_snapshot(self):
        """Record a data point from current thermostat + remote status"""
        ts = time.time()
        status = self.thermostat.get_status()
        remote = self.remote.get_status() if self.remote else None

        entry = {
            'ts': ts,
            'k_temp': status.get('temp'),
            'k_hum': status.get('humidity'),
            'k_pres': status.get('pressure'),
            'mode': status.get('mode_name'),
            'heat_sp': status.get('heat_setpoint'),
            'cool_sp': status.get('cool_setpoint'),
        }

        if remote:
            entry.update({
                'l_temp': remote.get('temp'),
                'l_hum': remote.get('humidity'),
                'l_pres': remote.get('pressure'),
                'l_app': remote.get('apparent_temp'),
                'bl_temp': remote.get('bl_temp'),
                'bl_hum': remote.get('bl_humidity'),
                'heating': 1 if remote.get('heating_active') else 0,
                'cooling': 1 if remote.get('cooling_active') else 0,
                'whynter': remote.get('whynter_mode', 0),
                'heater': remote.get('heater_mode', 0),
                'dehum': 1 if remote.get('dehum_active') else 0,
                'fan': remote.get('fan_speed', 0),
            })

        self.history.append(entry)
        if len(self.history) > self.history_max:
            self.history = self.history[-self.history_max:]
        self._db_write(entry)

    def _api_history(self, request):
        """Return history buffer, optionally filtered by ?since=<timestamp>.
        Queries btree directly for data older than RAM buffer.
        Supports ?limit=N to cap results (default 500)."""
        since = 0
        limit = 500
        if '?since=' in request or '&since=' in request:
            try:
                sep = '?since=' if '?since=' in request else '&since='
                idx = request.index(sep) + len(sep)
                end = idx
                while end < len(request) and request[end] in '0123456789.':
                    end += 1
                since = float(request[idx:end])
            except (ValueError, IndexError):
                pass
        if 'limit=' in request:
            try:
                sep = '?limit=' if '?limit=' in request else '&limit='
                idx = request.index(sep) + len(sep)
                end = idx
                while end < len(request) and request[end] in '0123456789':
                    end += 1
                limit = min(int(request[idx:end]), 2000)
            except (ValueError, IndexError):
                pass

        data = []
        if self._db and since > 0:
            # Use btree range query starting just after since
            since_key = ("%010d" % int(since)).encode()
            try:
                for key in self._db.keys(since_key):
                    if key <= since_key:
                        continue
                    data.append(json.loads(self._db[key]))
                    if len(data) >= limit:
                        break
            except Exception:
                # Fallback: iterate from start
                for key in self._db:
                    if key <= since_key:
                        continue
                    data.append(json.loads(self._db[key]))
                    if len(data) >= limit:
                        break
        elif since > 0:
            data = [e for e in self.history if e['ts'] > since]
            data = data[:limit]
        else:
            if self._db:
                for key in self._db:
                    data.append(json.loads(self._db[key]))
                    if len(data) >= limit:
                        break
            else:
                data = self.history[:limit]

        more = len(data) >= limit
        body = json.dumps({'count': len(data), 'entries': data, 'more': more})
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n{body}"

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
                humidity = data.get('humidity', None)
                self.scheduler.set_preset(mode, heat, cool, humidity)
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
            elif 'POST /api/sync_enabled' in request:
                self.thermostat.set_sync_enabled(bool(data.get('enabled', True)))
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
            elif 'POST /api/remote/force_all_off' in request:
                self.remote.force_all_off()
            elif 'POST /api/remote/fan_speed' in request:
                self.remote.set_fan_speed(int(data.get('speed', 4)))
            elif 'POST /api/remote/fan_only' in request:
                self.remote.set_fan_only(data.get('on', False))
            elif 'POST /api/remote/humidity_setpoint' in request:
                self.thermostat.set_humidity_setpoint(int(data.get('value', 55)))
            elif 'POST /api/remote/sync' in request:
                # Sync ESP32 setpoints to remote (one call at a time with short delay)
                import time
                self.remote.set_heat_setpoint(int(self.thermostat.heat_setpoint))
                time.sleep(0.2)
                self.remote.set_cool_setpoint(int(self.thermostat.cool_setpoint))
                time.sleep(0.2)
                self.remote.set_humidity_setpoint(int(self.thermostat.humidity_setpoint))
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
.btn.sync.on{background:#2a9d8f}
.btn.home{background:#38b000}
.preset-row{display:flex;align-items:center;justify-content:space-between;margin:6px 0;padding:8px;background:#0f3460;border-radius:8px}
.preset-row label{font-size:13px;min-width:50px}
.preset-row input[type=number]{width:50px;background:#1a1a2e;color:#eee;border:1px solid #444;border-radius:4px;padding:4px;text-align:center;font-size:14px}
.sch-entry{display:flex;align-items:center;gap:8px;margin:4px 0;padding:6px 8px;background:#0f3460;border-radius:8px}
.sch-entry input[type=time]{background:#1a1a2e;color:#eee;border:1px solid #444;border-radius:4px;padding:4px;font-size:14px}
.sch-entry select{background:#1a1a2e;color:#eee;border:1px solid #444;border-radius:4px;padding:4px;font-size:14px}
.sch-entry .del{background:#e94560;border:none;color:#fff;padding:2px 8px;border-radius:4px;cursor:pointer;font-size:14px}
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
<div style="font-size:14px;color:#888;margin-bottom:8px">AUTO-SYNC ZONES</div>
<button class="btn sync" id="syncbtn" onclick="toggleSync()">OFF</button>
<div style="margin-top:8px;font-size:12px;color:#888">Kitchen settings &rarr; Living Room</div>
</div>

<div class="card" style="text-align:center">
<h3>SCHEDULE OVERRIDE</h3>
<div id="schmode" style="font-size:24px;font-weight:bold;margin:8px 0;color:#2ecc71">HOME</div>
<div id="schhold" style="font-size:12px;color:#888;margin-bottom:10px"></div>
<button class="btn" id="schtoggle" onclick="toggleSchEn()" style="padding:6px 14px;font-size:12px;background:#555;display:none">Enable Schedule</button>
<div style="margin-bottom:6px"><span style="font-size:12px;color:#888">Hold Home: </span>
<button class="btn home" onclick="schHold('home',4)" style="padding:8px 12px;font-size:13px">4h</button>
<button class="btn home" onclick="schHold('home',8)" style="padding:8px 12px;font-size:13px">8h</button>
<button class="btn home" onclick="schHold('home',12)" style="padding:8px 12px;font-size:13px">12h</button></div>
<div style="margin-bottom:6px"><span style="font-size:12px;color:#888">Hold Away: </span>
<button class="btn" onclick="schHold('away',4)" style="padding:8px 12px;font-size:13px;background:#e67e22">4h</button>
<button class="btn" onclick="schHold('away',8)" style="padding:8px 12px;font-size:13px;background:#e67e22">8h</button>
<button class="btn" onclick="schHold('away',12)" style="padding:8px 12px;font-size:13px;background:#e67e22">12h</button>
<button class="btn" onclick="schHold('away',24)" style="padding:8px 12px;font-size:13px;background:#e67e22">24h</button></div>
<button class="btn" onclick="schCancel()" style="padding:8px 16px;font-size:13px;background:#555">Cancel Hold</button>
</div>

<div class="card" id="schedit" style="display:none">
<h3 style="text-align:center">SCHEDULE SETTINGS</h3>
<div style="text-align:center;margin:8px 0">
<button class="btn" id="schenbtn" onclick="toggleSchEn()" style="padding:8px 16px;font-size:13px">Enabled</button>
</div>
<h3 style="margin-top:12px">PRESET TEMPERATURES</h3>
<div id="presets"></div>
<h3 style="margin-top:16px">WEEKDAY SCHEDULE</h3>
<div id="sch_weekday"></div>
<button class="btn" onclick="addEntry('weekday')" style="padding:6px 12px;font-size:12px;margin-top:6px;background:#2a9d8f">+ Add</button>
<h3 style="margin-top:16px">WEEKEND SCHEDULE</h3>
<div id="sch_weekend"></div>
<button class="btn" onclick="addEntry('weekend')" style="padding:6px 12px;font-size:12px;margin-top:6px;background:#2a9d8f">+ Add</button>
</div>

<div class="card" style="text-align:center">
<button class="btn" onclick="toggleSchEdit()" style="padding:8px 16px;font-size:13px;background:#2a9d8f" id="scheditbtn">Edit Schedule</button>
</div>

<div class="card">
<div class="zone-title remote-title">Living Room (Remote)</div>
<div class="temp-small"><span id="ptemp">--</span>&deg;F <span id="pfeels" style="font-size:16px;color:#888"></span></div>
<div class="row">💧 <span id="phum">--%</span> | <span id="pptrend">→</span> <span id="ppres">--</span> inHg</div>
<div id="blsensor" style="text-align:center;font-size:13px;color:#888;margin-top:4px"></div>
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
<button class="btn" id="w1" onclick="whynter(1)">COOL</button>
<button class="btn" id="w2" onclick="whynter(2)">DEHUM</button>
<button class="btn" id="w3" onclick="whynter(3)">FAN</button>
</div>
<h3>HUMIDITY SETPOINT (AUTO DEHUM)</h3>
<div class="setlabel"><span>30%</span><span id="humset">55</span>%<span>80%</span></div>
<input type="range" min="30" max="80" value="55" class="slider cool" id="humslider" oninput="setRHumidity(this.value)">
<h3>IR HEATER</h3>
<div class="row">
<button class="btn" id="h0" onclick="heater(0)">OFF</button>
<button class="btn" id="h1" onclick="heater(1)">ON</button>
</div>
<h3 style="margin-top:20px;color:#ff4444;">EMERGENCY SHUTDOWN</h3>
<div class="row">
<button class="btn heater" onclick="forceAllOff()" style="background:#ff4444;font-weight:bold;">FORCE ALL OFF</button>
</div>
</div>

<div style="text-align:center;margin-bottom:16px">
<a href="http://192.168.71.151:8080" style="color:#00b4d8;font-size:16px">Energy Dashboard &amp; Stats</a>
</div>

<script>
var hs=68,cs=75,rhs=68,rcs=75,rwhynter=0,rheater=0;
var adjustingHeat=false,adjustingCool=false,adjustingRHeat=false,adjustingRCool=false,adjustingRHum=false;
var heatTimer,coolTimer,rheatTimer,rcoolTimer,rhumTimer;
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
if(d.sync_enabled!==undefined){syncOn=d.sync_enabled;updSyncBtn();}
if(d.remote){updRemote(d.remote);}else{
var ps=document.getElementById('pstatus');ps.className='offline';ps.textContent='Offline';}
}
function updRemote(r){
document.getElementById('ptemp').textContent=r.temp?r.temp.toFixed(1):'--';
var fe=document.getElementById('pfeels');
if(r.apparent_temp&&r.temp&&Math.abs(r.apparent_temp-r.temp)>=0.5){fe.textContent='(feels '+r.apparent_temp.toFixed(0)+'°)';}else{fe.textContent='';}
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
var dehumActive=r.dehum_active||false;
ps.className=dehumActive?'whynter':whynterActive?'whynter':heaterActive?'heating':r.heating_active?'heating':r.cooling_active?'cooling':'';
var wnames={1:'WHYNTER COOL',2:'WHYNTER DEHUM',3:'WHYNTER FAN',4:'WHYNTER HEAT'};
ps.textContent=dehumActive?'DEHUMIDIFYING':whynterActive?(wnames[r.whynter_mode]||'WHYNTER ON'):heaterActive?'IR HEATER ON':r.heating_active?'HEATING':r.cooling_active?'COOLING':r.fan_only?'FAN ONLY':'Idle';
for(var i=0;i<4;i++)document.getElementById('pm'+i).className='btn'+(r.mode==i?' active':'');
for(var i=0;i<4;i++)document.getElementById('w'+i).className='btn'+(r.whynter_mode==i?' whynter':'');
for(var i=0;i<2;i++)document.getElementById('h'+i).className='btn'+(r.heater_mode==i?' heater':'');
for(var i=1;i<=4;i++)document.getElementById('f'+i).className='btn'+(r.fan_speed==i?' fan':'');
document.getElementById('fo0').className='btn'+(!r.fan_only?' active':'');
document.getElementById('fo1').className='btn'+(r.fan_only?' fan':'');
if(!adjustingRHum&&r.humidity_setpoint){
document.getElementById('humset').textContent=r.humidity_setpoint;
document.getElementById('humslider').value=r.humidity_setpoint;
}
var bls=document.getElementById('blsensor');
if(r.bl_temp!=null){bls.textContent='HTS2: '+r.bl_temp.toFixed(1)+'°F | '+Math.round(r.bl_humidity)+'% RH';}else{bls.textContent='';}
}
function get(){fetch('/api/status').then(r=>r.json()).then(upd).catch(e=>console.log(e));}
function mode(m){fetch('/api/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(upd);}
function setHeat(v){adjustingHeat=true;document.getElementById('hset').textContent=v;clearTimeout(heatTimer);heatTimer=setTimeout(function(){fetch('/api/heat_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingHeat=false;},1000);});},500);}
function setCool(v){adjustingCool=true;document.getElementById('cset').textContent=v;clearTimeout(coolTimer);coolTimer=setTimeout(function(){fetch('/api/cool_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingCool=false;},1000);});},500);}
function rmode(m){fetch('/api/remote/mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updRemote);}
function setRHeat(v){adjustingRHeat=true;document.getElementById('phset').textContent=v;clearTimeout(rheatTimer);rheatTimer=setTimeout(function(){fetch('/api/remote/heat_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingRHeat=false;},1000);});},500);}
function setRCool(v){adjustingRCool=true;document.getElementById('pcset').textContent=v;clearTimeout(rcoolTimer);rcoolTimer=setTimeout(function(){fetch('/api/remote/cool_setpoint',{method:'POST',body:JSON.stringify({temp:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingRCool=false;},1000);});},500);}
function setRHumidity(v){adjustingRHum=true;document.getElementById('humset').textContent=v;clearTimeout(rhumTimer);rhumTimer=setTimeout(function(){fetch('/api/remote/humidity_setpoint',{method:'POST',body:JSON.stringify({value:parseInt(v)})}).then(r=>r.json()).then(function(d){setTimeout(function(){adjustingRHum=false;},1000);});},500);}
function whynter(m){fetch('/api/remote/whynter_mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updRemote);}
function heater(m){fetch('/api/remote/heater_mode',{method:'POST',body:JSON.stringify({mode:m})}).then(r=>r.json()).then(updRemote);}
function forceAllOff(){
for(var i=0;i<4;i++)document.getElementById('pm'+i).className='btn'+(i==0?' active':'');
for(var i=0;i<4;i++)document.getElementById('w'+i).className='btn'+(i==0?' whynter':'');
for(var i=0;i<2;i++)document.getElementById('h'+i).className='btn'+(i==0?' heater':'');
fetch('/api/remote/force_all_off',{method:'POST',body:'{}'}).then(r=>r.json()).then(updRemote);
}
function fanSpeed(s){fetch('/api/remote/fan_speed',{method:'POST',body:JSON.stringify({speed:s})}).then(r=>r.json()).then(updRemote);}
function fanOnly(on){fetch('/api/remote/fan_only',{method:'POST',body:JSON.stringify({on:on})}).then(r=>r.json()).then(updRemote);}
var syncOn=true;
function toggleSync(){
syncOn=!syncOn;
updSyncBtn();
fetch('/api/sync_enabled',{method:'POST',body:JSON.stringify({enabled:syncOn})}).then(r=>r.json()).then(upd);
}
function updSyncBtn(){
var btn=document.getElementById('syncbtn');
btn.textContent=syncOn?'ON':'OFF';
btn.className=syncOn?'btn sync on':'btn sync';
}
function schHold(m,h){fetch('/api/schedule/mode',{method:'POST',body:JSON.stringify({mode:m,hours:h})}).then(r=>r.json()).then(updSch);fetch('/api/schedule/enable',{method:'POST',body:JSON.stringify({enabled:true})});}
function schCancel(){fetch('/api/schedule/mode',{method:'POST',body:JSON.stringify({mode:'home',hours:0})}).then(r=>r.json()).then(updSch);}
function updSch(d){
if(!d)return;
var el=document.getElementById('schmode');
var m=d.current_mode||'home';
var colors={home:'#2ecc71',away:'#e67e22',sleep:'#9b59b6'};
el.textContent=m.toUpperCase();el.style.color=colors[m]||'#eee';
var hi=document.getElementById('schhold');
if(d.hold_until){var r=Math.max(0,d.hold_until-(Date.now()/1000-946684800));var rh=Math.floor(r/3600),rm=Math.floor((r%3600)/60);hi.textContent='Hold: '+(rh>0?rh+'h ':'')+rm+'m remaining';}
else{hi.textContent=d.enabled?'Schedule active':'Schedule off';}
var tb=document.getElementById('schtoggle');if(tb){tb.style.display='inline-block';tb.textContent=d.enabled?'Disable Schedule':'Enable Schedule';tb.style.background=d.enabled?'#555':'#2a9d8f';}
}
function getSch(){fetch('/api/schedule').then(r=>r.json()).then(function(d){updSch(d);updSchEdit(d);}).catch(e=>{});}
var schData=null;
var schEditOpen=false;
function toggleSchEdit(){
var el=document.getElementById('schedit');
schEditOpen=!schEditOpen;
el.style.display=schEditOpen?'block':'none';
document.getElementById('scheditbtn').textContent=schEditOpen?'Close Schedule':'Edit Schedule';
if(schEditOpen)getSch();
}
function toggleSchEn(){
if(!schData)return;
var en=!schData.enabled;
fetch('/api/schedule/enable',{method:'POST',body:JSON.stringify({enabled:en})}).then(r=>r.json()).then(function(d){updSch(d);updSchEdit(d);});
}
function updSchEdit(d){
if(!d)return;
schData=d;
var btn=document.getElementById('schenbtn');
btn.textContent=d.enabled?'Enabled':'Disabled';
btn.style.background=d.enabled?'#38b000':'#555';
var ph=document.getElementById('presets');
var h='';
var modes=['home','away','sleep'];
var colors={home:'#2ecc71',away:'#e67e22',sleep:'#9b59b6'};
for(var i=0;i<modes.length;i++){
var m=modes[i],p=d.presets[m];
h+='<div class="preset-row"><label style="color:'+colors[m]+'">'+m.charAt(0).toUpperCase()+m.slice(1)+'</label>';
h+='<span style="font-size:12px;color:#888">Heat</span><input type="number" min="55" max="85" value="'+p.heat+'" onchange="setPreset(\\''+m+'\\',this.value,null,null)">';
h+='<span style="font-size:12px;color:#888">Cool</span><input type="number" min="60" max="90" value="'+p.cool+'" onchange="setPreset(\\''+m+'\\',null,this.value,null)">';
if(p.humidity!==undefined){h+='<span style="font-size:12px;color:#888">Hum</span><input type="number" min="30" max="80" value="'+p.humidity+'" onchange="setPreset(\\''+m+'\\',null,null,this.value)">';}
h+='</div>';
}
ph.innerHTML=h;
renderSch('weekday',d.schedule.weekday||[]);
renderSch('weekend',d.schedule.weekend||[]);
}
function renderSch(day,entries){
var el=document.getElementById('sch_'+day);
var h='';
for(var i=0;i<entries.length;i++){
var e=entries[i];
h+='<div class="sch-entry">';
h+='<input type="time" value="'+e.time+'" onchange="updEntry(\\''+day+'\\','+i+',\\'time\\',this.value)">';
h+='<select onchange="updEntry(\\''+day+'\\','+i+',\\'mode\\',this.value)">';
var opts=['home','away','sleep'];
for(var j=0;j<opts.length;j++){h+='<option value="'+opts[j]+'"'+(e.mode==opts[j]?' selected':'')+'>'+opts[j].charAt(0).toUpperCase()+opts[j].slice(1)+'</option>';}
h+='</select>';
h+='<button class="del" onclick="delEntry(\\''+day+'\\','+i+')">x</button>';
h+='</div>';
}
el.innerHTML=h;
}
function setPreset(m,heat,cool,hum){
if(!schData)return;
var p=schData.presets[m];
var body={mode:m,heat:heat?parseInt(heat):p.heat,cool:cool?parseInt(cool):p.cool};
if(hum!==null)body.humidity=parseInt(hum);
fetch('/api/schedule/preset',{method:'POST',body:JSON.stringify(body)}).then(r=>r.json()).then(function(d){updSch(d);updSchEdit(d);});
}
function updEntry(day,idx,field,val){
if(!schData)return;
var entries=schData.schedule[day]||[];
entries[idx][field]=val;
entries.sort(function(a,b){return a.time<b.time?-1:a.time>b.time?1:0;});
fetch('/api/schedule/day',{method:'POST',body:JSON.stringify({day:day,entries:entries})}).then(r=>r.json()).then(function(d){updSch(d);updSchEdit(d);});
}
function addEntry(day){
if(!schData)return;
var entries=schData.schedule[day]||[];
entries.push({time:'12:00',mode:'home'});
entries.sort(function(a,b){return a.time<b.time?-1:a.time>b.time?1:0;});
fetch('/api/schedule/day',{method:'POST',body:JSON.stringify({day:day,entries:entries})}).then(r=>r.json()).then(function(d){updSch(d);updSchEdit(d);});
}
function delEntry(day,idx){
if(!schData)return;
var entries=schData.schedule[day]||[];
entries.splice(idx,1);
fetch('/api/schedule/day',{method:'POST',body:JSON.stringify({day:day,entries:entries})}).then(r=>r.json()).then(function(d){updSch(d);updSchEdit(d);});
}
get();getSch();setInterval(get,3000);setInterval(getSch,30000);
</script>
</body>
</html>"""
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}"
