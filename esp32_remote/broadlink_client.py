# Broadlink RM4 Mini - MicroPython UDP Client
# =============================================
# Implements the Broadlink protocol for IR send/learn
# Reference: https://github.com/mjg59/python-broadlink

import socket
import struct
import time

try:
    from ucryptolib import aes
except ImportError:
    from cryptolib import aes

import config

# Protocol constants
INITIAL_KEY = b'\x09\x76\x28\x34\x3f\xe9\x9e\x23\x76\x5c\x15\x13\xac\xcf\x8b\x02'
INITIAL_IV = b'\x56\x2e\x17\x99\x6d\x09\x3d\x28\xdd\xb3\xba\x69\x5a\x2e\x6f\x58'

# Broadlink IR data format marker
IR_MARKER = 0x26

# Microseconds per Broadlink timing unit (1 / 2^15 seconds)
US_PER_UNIT = 1000000.0 / 32768.0  # ~30.52 us


def _checksum(data):
    """Broadlink checksum: sum of bytes + 0xBEAF, masked to 16 bits"""
    return (sum(data) + 0xBEAF) & 0xFFFF


def _pad16(data):
    """Pad data to multiple of 16 bytes with zeros"""
    remainder = len(data) % 16
    if remainder:
        data = data + bytes(16 - remainder)
    return data


def pulses_to_broadlink(timings_us):
    """Convert microsecond pulse timings to Broadlink IR data format.

    Args:
        timings_us: list of pulse durations in microseconds [mark, space, mark, ...]

    Returns:
        bytes in Broadlink IR format
    """
    data = bytearray()
    for us in timings_us:
        units = int(us / US_PER_UNIT + 0.5)
        if units > 255:
            data.append(0x00)
            data.append((units >> 8) & 0xFF)
            data.append(units & 0xFF)
        else:
            data.append(units)

    # Build packet: marker + repeat + length + data
    packet = bytearray(4)
    packet[0] = IR_MARKER
    packet[1] = 0x00  # no repeat
    struct.pack_into('<H', packet, 2, len(data))
    packet.extend(data)
    return bytes(packet)


def broadlink_to_pulses(data):
    """Convert Broadlink IR data format to microsecond pulse timings.

    Args:
        data: bytes in Broadlink IR format

    Returns:
        list of pulse durations in microseconds
    """
    if not data or data[0] != IR_MARKER:
        return []

    length = struct.unpack_from('<H', data, 2)[0]
    timings = []
    i = 4
    end = min(4 + length, len(data))
    while i < end:
        if data[i] == 0x00:
            if i + 2 < end:
                units = (data[i + 1] << 8) | data[i + 2]
                i += 3
            else:
                break
        else:
            units = data[i]
            i += 1
        timings.append(int(units * US_PER_UNIT + 0.5))

    return timings


class BroadlinkClient:
    """MicroPython Broadlink RM4 Mini UDP protocol client"""

    def __init__(self, ip=None, mac=None, devtype=None):
        self.ip = ip or getattr(config, 'BROADLINK_IP', None)
        devtype = devtype or getattr(config, 'BROADLINK_DEVTYPE', 0x520c)
        self.mac = mac or b'\x00' * 6
        self.devtype = devtype
        self.port = 80

        self.aes_key = INITIAL_KEY
        self.device_id = 0
        self.count = 0x8000

        self.authed = False
        self.timeout = getattr(config, 'BROADLINK_TIMEOUT', 3)
        self.retries = getattr(config, 'BROADLINK_RETRIES', 3)

    def _encrypt(self, data):
        """AES-128-CBC encrypt (new cipher each call to reset IV)"""
        cipher = aes(self.aes_key, 2, INITIAL_IV)
        return cipher.encrypt(_pad16(data))

    def _decrypt(self, data):
        """AES-128-CBC decrypt"""
        cipher = aes(self.aes_key, 2, INITIAL_IV)
        return cipher.decrypt(_pad16(data))

    def _send_packet(self, command, payload):
        """Build, encrypt, and send a Broadlink packet. Returns decrypted response payload."""
        self.count = ((self.count + 1) | 0x8000) & 0xFFFF

        # Build 56-byte header
        header = bytearray(0x38)
        header[0x00:0x08] = b'\x5a\xa5\xaa\x55\x5a\xa5\xaa\x55'
        struct.pack_into('<H', header, 0x24, self.devtype)
        struct.pack_into('<H', header, 0x26, command)
        struct.pack_into('<H', header, 0x28, self.count)

        # MAC reversed
        mac = self.mac
        if isinstance(mac, (bytes, bytearray)) and len(mac) == 6:
            header[0x2A:0x30] = bytes(reversed(mac))

        struct.pack_into('<I', header, 0x30, self.device_id)

        # Payload checksum (before encryption)
        p_checksum = _checksum(payload)
        struct.pack_into('<H', header, 0x34, p_checksum)

        # Encrypt payload
        enc_payload = self._encrypt(bytes(payload))

        # Full packet
        packet = header + enc_payload

        # Full packet checksum (with checksum field zeroed)
        packet[0x20] = 0
        packet[0x21] = 0
        full_checksum = _checksum(packet)
        struct.pack_into('<H', packet, 0x20, full_checksum)

        # Send and receive
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(self.timeout)
            sock.sendto(packet, (self.ip, self.port))
            response, _ = sock.recvfrom(2048)
        finally:
            sock.close()

        if len(response) < 0x38:
            raise OSError("Response too short")

        # Check error code
        err = struct.unpack_from('<H', response, 0x22)[0]
        if err != 0:
            raise OSError(f"Device error: 0x{err:04x}")

        # Decrypt response payload
        enc_resp = response[0x38:]
        if len(enc_resp) > 0:
            return self._decrypt(enc_resp)
        return b''

    def discover(self, timeout=5):
        """Discover Broadlink devices on the local network.

        Returns list of (ip, mac, devtype) tuples.
        """
        # Build discovery packet
        now = time.localtime()
        packet = bytearray(0x30)
        # Timezone offset (hardcode 0)
        packet[0x08] = now[0] & 0xFF  # year low
        packet[0x09] = (now[0] >> 8) & 0xFF  # year high
        packet[0x0A] = now[1]  # month (1-indexed, but Broadlink doesn't care)
        packet[0x0B] = now[2]  # day
        packet[0x0C] = now[3]  # hour
        packet[0x0D] = now[4]  # minute
        packet[0x0E] = now[5]  # second
        packet[0x0F] = now[6]  # weekday
        packet[0x18] = ord('1')
        packet[0x1E] = 0x06
        checksum = _checksum(packet)
        struct.pack_into('<H', packet, 0x20, checksum)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)

        devices = []
        try:
            sock.sendto(packet, ('255.255.255.255', 80))
            while True:
                try:
                    resp, addr = sock.recvfrom(1024)
                    if len(resp) >= 0x40:
                        devtype = struct.unpack_from('<H', resp, 0x34)[0]
                        mac = bytes(reversed(resp[0x3A:0x40]))
                        devices.append((addr[0], mac, devtype))
                except OSError:
                    break
        finally:
            sock.close()

        return devices

    def auth(self):
        """Authenticate with the Broadlink device. Gets session key and device ID."""
        if not self.ip:
            # Try discovery first
            print("[BL] No IP configured, running discovery...")
            devices = self.discover()
            if not devices:
                raise OSError("No Broadlink devices found")
            self.ip, self.mac, self.devtype = devices[0]
            print(f"[BL] Found device at {self.ip} (type=0x{self.devtype:04x})")

        # Build auth payload (0x50 = 80 bytes)
        payload = bytearray(0x50)
        payload[0x04:0x14] = bytes([0x31] * 16)
        payload[0x1E] = 0x01
        payload[0x2D] = 0x01
        payload[0x30:0x36] = b'Test 1'

        # Reset to initial key for auth
        self.aes_key = INITIAL_KEY
        self.device_id = 0

        resp = self._send_packet(0x0065, payload)

        # Extract device ID and new AES key
        self.device_id = struct.unpack_from('<I', resp, 0x00)[0]
        self.aes_key = resp[0x04:0x14]
        self.authed = True
        print(f"[BL] Authenticated (id=0x{self.device_id:08x})")

    def ensure_connected(self):
        """Authenticate if not already done"""
        if not self.authed:
            self.auth()

    def _rm4_send(self, command, data=b''):
        """Send an RM4 Mini command (wraps with length prefix).

        RM4 Mini uses: struct.pack('<HI', len(data)+4, command) + data
        """
        inner = struct.pack('<HI', len(data) + 4, command) + data
        return self._send_packet(0x006A, inner)

    def send_data(self, ir_data):
        """Transmit IR data through the Broadlink.

        Args:
            ir_data: bytes in Broadlink IR format (from pulses_to_broadlink)
        """
        for attempt in range(self.retries):
            try:
                self.ensure_connected()
                self._rm4_send(0x02, ir_data)
                return True
            except OSError as e:
                print(f"[BL] Send attempt {attempt + 1} failed: {e}")
                self.authed = False  # Force re-auth on next attempt
                if attempt < self.retries - 1:
                    time.sleep(1)  # Longer delay for Broadlink to wake
        return False

    def ping(self):
        """Lightweight keepalive — re-auth to prevent Broadlink sleep."""
        try:
            self.auth()
        except OSError as e:
            print(f"[BL] Keepalive failed: {e}")
            self.authed = False

    def enter_learning(self):
        """Put the Broadlink into IR learning mode."""
        self.ensure_connected()
        self._rm4_send(0x03)
        print("[BL] Learning mode active")

    def check_data(self):
        """Check if IR data has been captured during learning.

        Returns:
            bytes of IR data if captured, None otherwise.
        """
        self.ensure_connected()
        try:
            resp = self._rm4_send(0x04)
            if resp and len(resp) > 6:
                p_len = struct.unpack_from('<H', resp, 0)[0]
                if p_len > 6:
                    ir_data = resp[0x06:p_len + 2]
                    if len(ir_data) > 0 and ir_data[0] == IR_MARKER:
                        return bytes(ir_data)
            return None
        except OSError:
            return None

    def check_sensors(self):
        """Read temperature and humidity from HTS2 sensor cable.

        Returns:
            tuple (temp_celsius, humidity_percent) or None on failure.
        """
        for attempt in range(self.retries):
            try:
                self.ensure_connected()
                resp = self._rm4_send(0x24)
                if resp and len(resp) >= 10:  # 6-byte wrapper + 4 sensor bytes
                    p_len = struct.unpack_from('<H', resp, 0)[0]
                    data = resp[0x06:p_len + 2]
                    if len(data) >= 4:
                        temp = struct.unpack_from('<bb', data, 0)
                        temp_c = temp[0] + temp[1] / 100.0
                        humidity = data[2] + data[3] / 100.0
                        return (temp_c, humidity)
                return None
            except OSError as e:
                print(f"[BL] Sensor read attempt {attempt + 1} failed: {e}")
                self.authed = False
                if attempt < self.retries - 1:
                    time.sleep(1)
        return None

    def get_status(self):
        """Get Broadlink connection status for API"""
        return {
            'ip': self.ip,
            'authed': self.authed,
            'device_id': f'0x{self.device_id:08x}' if self.device_id else None,
            'devtype': f'0x{self.devtype:04x}'
        }
