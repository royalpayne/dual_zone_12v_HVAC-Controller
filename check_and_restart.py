"""Connect to remote ESP32 via WebREPL, check for errors, force restart main.py"""
import socket, time, struct

REMOTE_IP = '192.168.71.153'
PASSWORD = 'V!ncent16'
FRAME_TXT = 0x81

class WS:
    def __init__(self, s): self.s = s
    def write(self, data, frame=FRAME_TXT):
        n = len(data)
        hdr = struct.pack('BB', frame, n) if n < 126 else struct.pack('>BBH', frame, 126, n)
        self.s.sendall(hdr + data)

def read_ws(s, timeout=3):
    s.settimeout(timeout)
    out = b''
    try:
        while True: out += s.recv(512)
    except: pass
    return out

def decode(raw):
    text = ''
    i = 0
    while i < len(raw):
        if i+1 < len(raw) and raw[i] == 0x81:
            n = raw[i+1]; text += raw[i+2:i+2+n].decode('utf-8','replace'); i += 2+n
        else: i += 1
    return text

ai = socket.getaddrinfo(REMOTE_IP, 8266)
s = socket.socket(); s.settimeout(8); s.connect(ai[0][4])
key = b'dGhlIHNhbXBsZSBub25jZQ=='
s.sendall(b'GET / HTTP/1.1\r\nHost: ' + REMOTE_IP.encode() + b'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ' + key + b'\r\nSec-WebSocket-Version: 13\r\n\r\n')
resp = b''
while b'\r\n\r\n' not in resp: resp += s.recv(1)
ws = WS(s)
time.sleep(0.3); read_ws(s, 1)
ws.write((PASSWORD + '\r\n').encode())
time.sleep(0.5); read_ws(s, 1)

# Interrupt whatever is running
ws.write(b'\r\x03\x03', frame=FRAME_TXT)
time.sleep(2); read_ws(s, 1)

# Check for last exception
ws.write(b'import sys; sys.print_exception(sys.last_value) if hasattr(sys,"last_value") and sys.last_value else print("no error")\r\n')
time.sleep(2)
out = decode(read_ws(s, 2))
print("Last error:", out[:500])

# Force restart main.py
ws.write(b'exec(open("_restart.py").read())\r\n')
time.sleep(3)
out2 = decode(read_ws(s, 3))
print("Restart output:", out2[:300])
s.close()
