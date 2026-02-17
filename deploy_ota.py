#!/usr/bin/env python3
"""Deploy files to ESP32 devices over WiFi via WebREPL.

Usage:
    python3 deploy_ota.py remote   # Deploy esp32_remote/ files to Remote ESP32
    python3 deploy_ota.py main     # Deploy root files to Main ESP32
    python3 deploy_ota.py both     # Deploy to both
    python3 deploy_ota.py remote thermostat.py webserver.py  # Deploy specific files
"""

import sys
import struct
import time

try:
    import websocket
except ImportError:
    print("Install websocket-client: pip install websocket-client")
    sys.exit(1)

# Device configuration
DEVICES = {
    'remote': {
        'ip': '192.168.71.153',
        'files_dir': 'esp32_remote/',
        'files': [
            'main.py', 'boot.py', 'config.py', 'thermostat.py', 'webserver.py',
            'broadlink_client.py', 'ir_whynter.py', 'ir_heater.py',
            'sensor.py', 'display.py', 'ssd1306.py', 'webrepl_cfg.py',
        ],
    },
    'main': {
        'ip': '192.168.71.152',
        'files_dir': '',
        'files': [
            'main.py', 'boot.py', 'config.py', 'webserver.py',
            'thermostat_remote.py', 'remote_client.py', 'scheduler.py',
            'sensor.py', 'display.py', 'ssd1306.py', 'webrepl_cfg.py',
        ],
    },
}

PASSWORD = 'V!ncent16'
WEBREPL_REQ_S = "<2sBBQLH64s"


def upload_file(ip, local_path, remote_name):
    """Upload a single file via WebREPL"""
    ws = websocket.create_connection(f'ws://{ip}:8266', timeout=10)
    try:
        # Authenticate
        ws.recv()  # "Password: "
        ws.send(PASSWORD + '\r\n')
        ws.recv()  # "WebREPL connected\r\n>>> "

        # Read file
        with open(local_path, 'rb') as f:
            data = f.read()

        # Send PUT header (fixed 82-byte format)
        fname = remote_name.encode('utf-8')
        rec = struct.pack(WEBREPL_REQ_S, b"WA", 1, 0, 0, len(data), len(fname), fname)
        ws.send_binary(rec)
        ws.recv_frame()  # Initial ack

        # Send file data in 256-byte chunks
        offset = 0
        while offset < len(data):
            ws.send_binary(data[offset:offset + 256])
            offset += 256

        # Final ack
        resp = ws.recv_frame()
        rdata = resp.data if hasattr(resp, 'data') else resp
        if len(rdata) >= 2:
            status = struct.unpack('<H', rdata[-2:])[0]
            return status == 0
        return False
    finally:
        ws.close()


def deploy(target, specific_files=None):
    """Deploy files to a target device"""
    dev = DEVICES[target]
    ip = dev['ip']

    if specific_files:
        files = specific_files
    else:
        files = dev['files']

    print(f"\nDeploying to {target.upper()} ({ip})...")
    ok = 0
    fail = 0
    for fname in files:
        local_path = dev['files_dir'] + fname
        try:
            success = upload_file(ip, local_path, '/' + fname)
            status = 'OK' if success else 'FAIL'
            if success:
                ok += 1
            else:
                fail += 1
            with open(local_path, 'rb') as f:
                size = len(f.read())
            print(f"  {status}: {local_path} -> /{fname} ({size} bytes)")
        except FileNotFoundError:
            print(f"  SKIP: {local_path} (not found)")
        except Exception as e:
            print(f"  FAIL: {local_path} ({e})")
            fail += 1
        time.sleep(0.3)  # Brief pause between uploads

    print(f"  Done: {ok} uploaded, {fail} failed")
    if fail == 0 and ok > 0:
        print(f"  Soft reset {target}...")
        try:
            ws = websocket.create_connection(f'ws://{ip}:8266', timeout=10)
            ws.recv()
            ws.send(PASSWORD + '\r\n')
            ws.recv()
            ws.send('\x03')  # Ctrl+C = interrupt running code
            time.sleep(0.5)
            ws.send('\x03')  # Second Ctrl+C in case of nested try/except
            time.sleep(0.5)
            ws.send('\x04')  # Ctrl+D = soft reset at REPL prompt
            time.sleep(0.5)
            ws.close()
            print(f"  Reset sent. Device will reboot.")
        except Exception:
            print(f"  Could not reset — manually reboot or power cycle.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('remote', 'main', 'both'):
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]
    specific_files = sys.argv[2:] if len(sys.argv) > 2 else None

    if target == 'both':
        deploy('remote', specific_files)
        deploy('main', specific_files)
    else:
        deploy(target, specific_files)


if __name__ == '__main__':
    main()
