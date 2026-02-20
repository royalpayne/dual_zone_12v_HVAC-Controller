#!/usr/bin/env python3
"""Deploy files to ESP32 devices over WiFi via WebREPL (raw socket protocol).

Usage:
    python3 deploy_ota.py remote   # Deploy esp32_remote/ files to Remote ESP32
    python3 deploy_ota.py main     # Deploy root files to Main ESP32
    python3 deploy_ota.py both     # Deploy to both
    python3 deploy_ota.py remote thermostat.py webserver.py  # Deploy specific files
"""

import os
import socket
import struct
import sys
import time

# Device configuration
DEVICES = {
    'remote': {
        'ip': '192.168.71.153',
        'files_dir': 'esp32_remote/',
        'files': [
            'main.py', 'boot.py', 'config.py', 'thermostat.py', 'webserver.py',
            'broadlink_client.py', 'ir_whynter.py', 'ir_heater.py',
            'sensor.py', 'bme280.py', 'bmp280.py', 'display.py', 'ssd1306.py',
            'webrepl_cfg.py',
        ],
    },
    'main': {
        'ip': '192.168.71.152',
        'files_dir': '',
        'files': [
            'main.py', 'boot.py', 'config.py', 'webserver.py',
            'thermostat_remote.py', 'remote_client.py', 'scheduler.py',
            'sensor.py', 'bme280.py', 'bmp280.py', 'display.py', 'ssd1306.py',
            'webrepl_cfg.py',
        ],
    },
}

PASSWORD = 'V!ncent16'
WEBREPL_PORT = 8266

# WebREPL binary protocol constants (matches MicroPython webrepl_cli.py)
WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_VER = 3
FRAME_BIN = 0x82
FRAME_TXT = 0x81


class WebSocket:
    """Minimal WebSocket client matching MicroPython's WebREPL expectations."""

    def __init__(self, s):
        self.s = s
        self.buf = b""

    def write(self, data, frame=FRAME_BIN):
        l = len(data)
        if l < 126:
            hdr = struct.pack(">BB", frame, l)
        else:
            hdr = struct.pack(">BBH", frame, 126, l)
        self.s.sendall(hdr + data)

    def _recv_exactly(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.s.recv(n - len(buf))
            if not chunk:
                raise OSError("Connection closed")
            buf += chunk
        return buf

    def read(self, size, text_ok=False):
        if not self.buf:
            while True:
                hdr = self._recv_exactly(2)
                fl, sz = struct.unpack(">BB", hdr)
                if sz == 126:
                    (sz,) = struct.unpack(">H", self._recv_exactly(2))
                if fl == FRAME_BIN or (text_ok and fl == FRAME_TXT):
                    break
                # Skip unexpected / text frame (e.g. "WebREPL connected.\r\n")
                self._recv_exactly(sz)
            self.buf = self._recv_exactly(sz)

        d = self.buf[:size]
        self.buf = self.buf[size:]
        return d


def _handshake(s):
    """HTTP WebSocket upgrade — minimal handshake for MicroPython WebREPL."""
    s.sendall(
        b"GET / HTTP/1.1\r\n"
        b"Host: echo.websocket.org\r\n"
        b"Connection: Upgrade\r\n"
        b"Upgrade: websocket\r\n"
        b"Sec-WebSocket-Key: foo\r\n"
        b"\r\n"
    )
    # Read HTTP response headers one byte at a time to avoid consuming
    # WebSocket frame data that MicroPython sends immediately after headers.
    buf = b""
    while not buf.endswith(b"\r\n\r\n"):
        b = s.recv(1)
        if not b:
            raise OSError("Connection closed during handshake")
        buf += b


def _login(ws, password):
    """Read "Password: " prompt, send password."""
    # Read until the colon in "Password: "
    while True:
        c = ws.read(1, text_ok=True)
        if c == b":":
            ws.read(1, text_ok=True)  # space
            break
    ws.write(password.encode("utf-8") + b"\r")
    # "WebREPL connected.\r\n" arrives as a text frame; it will be
    # skipped automatically by the next binary ws.read() call.


def _read_resp(ws):
    """Read 4-byte WB response, return status code (0 = OK)."""
    data = ws.read(4)
    sig, code = struct.unpack("<2sH", data)
    if sig != b"WB":
        raise OSError(f"Bad WebREPL response signature: {sig!r}")
    return code


def _connect(ip):
    """Open TCP socket, do WebSocket handshake, login. Returns (sock, ws)."""
    s = socket.socket()
    s.settimeout(15)
    ai = socket.getaddrinfo(ip, WEBREPL_PORT)
    s.connect(ai[0][4])
    _handshake(s)
    ws = WebSocket(s)
    _login(ws, PASSWORD)
    return s, ws


def _put_file(ws, local_path, remote_name):
    """Upload local_path → remote_name using WebREPL binary PUT protocol."""
    sz = os.path.getsize(local_path)
    dest = remote_name.encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest), dest)
    # Split as webrepl_cli.py does — MicroPython reads header in two frames
    ws.write(rec[:10])
    ws.write(rec[10:])
    code = _read_resp(ws)
    if code != 0:
        raise OSError(f"PUT rejected: code {code}")

    sent = 0
    with open(local_path, "rb") as f:
        while True:
            buf = f.read(1024)
            if not buf:
                break
            ws.write(buf)
            sent += len(buf)
            sys.stdout.write(f"\r    {sent}/{sz} bytes")
            sys.stdout.flush()
    sys.stdout.write("\n")

    code = _read_resp(ws)
    if code != 0:
        raise OSError(f"PUT failed: code {code}")


def _soft_reset(ip):
    """Connect via WebREPL, interrupt main.py with Ctrl-C, then machine.reset()."""
    try:
        s, ws = _connect(ip)
        # Ctrl-C interrupts running main.py (sends KeyboardInterrupt)
        ws.write(b"\r\x03\x03", frame=FRAME_TXT)
        time.sleep(0.5)
        # Send machine.reset() in the REPL
        ws.write(b"import machine; machine.reset()\r\n", frame=FRAME_TXT)
        time.sleep(0.5)
        s.close()
        print("  Reset sent.")
    except Exception as e:
        print(f"  Reset failed ({e}) — power cycle or reset manually.")


def deploy(target, specific_files=None):
    """Deploy files to a target device via WebREPL."""
    dev = DEVICES[target]
    ip = dev['ip']
    files = specific_files if specific_files else dev['files']

    print(f"\nDeploying to {target.upper()} ({ip})...")
    ok = 0
    fail = 0

    for fname in files:
        local_path = dev['files_dir'] + fname
        if not os.path.exists(local_path):
            print(f"  SKIP  {local_path} (not found)")
            continue
        size = os.path.getsize(local_path)
        print(f"  {fname} ({size} bytes)...")
        s = None
        try:
            s, ws = _connect(ip)
            _put_file(ws, local_path, fname)
            s.close()
            print(f"  OK    {fname}")
            ok += 1
        except Exception as e:
            print(f"  FAIL  {fname} — {e}")
            fail += 1
        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass

    print(f"\n  {ok} uploaded, {fail} failed")
    if fail == 0 and ok > 0:
        print(f"  Resetting {target}...")
        _soft_reset(ip)
    elif fail > 0:
        print(f"  Retry failed files or check WiFi/WebREPL.")


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
