#!/usr/bin/env python3
"""RV Thermostat Data Logger — pulls history from Main ESP32 into SQLite.

Usage:
    python3 data_logger.py              # Run continuous logger (polls every 5 min)
    python3 data_logger.py --once       # Pull once and exit
    python3 data_logger.py --export     # Export database to CSV
    python3 data_logger.py --tail 20    # Show last N readings
"""

import sys
import time
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone, timedelta

# Configuration
MAIN_ESP32_IP = "192.168.71.152"
HISTORY_URL = f"http://{MAIN_ESP32_IP}/api/history"
DB_FILE = "thermostat_log.db"
POLL_INTERVAL = 300  # 5 minutes
TZ_OFFSET = -6  # US Central Standard Time

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
    """Fetch history entries from the ESP32."""
    url = f"{HISTORY_URL}?since={since}" if since else HISTORY_URL
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get('entries', [])
    except Exception as e:
        print(f"  Fetch error: {e}")
        return []


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


def main():
    if '--export' in sys.argv:
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
