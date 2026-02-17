#!/usr/bin/env python3
"""Test Whynter IR with ARC-110WD timings (pre-header + 2850/2850 header)"""

import broadlink
import struct

# ARC-110WD timings (IRremoteESP8266)
PRE_MARK = 750
PRE_SPACE = 750
HEADER_MARK = 2850
HEADER_SPACE = 2850
BIT_MARK = 750
ONE_SPACE = 2150
ZERO_SPACE = 750


def reverse_bits(byte_val):
    result = 0
    for i in range(8):
        if byte_val & (1 << i):
            result |= 1 << (7 - i)
    return result


def encode_whynter(power=False, mode='cool', fan='high', temp_f=72):
    cmd = 0x12 << 24
    fan_map = {'high': 0b001, 'med': 0b010, 'low': 0b100, 'auto': 0b000}
    cmd |= fan_map.get(fan, 0) << 20
    mode_map = {'fan': 0b0001, 'dehum': 0b0010, 'heat': 0b0100, 'cool': 0b1000}
    cmd |= mode_map.get(mode, 0b1000) << 16
    cmd |= 1 << 10  # Fahrenheit
    if power:
        cmd |= 1 << 8
    cmd |= reverse_bits(temp_f) & 0xFF
    return cmd


def command_to_pulses(cmd):
    # Pre-header
    pulses = [PRE_MARK, PRE_SPACE]
    # Header
    pulses.extend([HEADER_MARK, HEADER_SPACE])
    # 32 data bits MSB first
    for i in range(31, -1, -1):
        pulses.append(BIT_MARK)
        if (cmd >> i) & 1:
            pulses.append(ONE_SPACE)
        else:
            pulses.append(ZERO_SPACE)
    pulses.append(BIT_MARK)  # Final mark
    return pulses


def pulses_to_broadlink(timings_us):
    US_PER_UNIT = 1000000.0 / 32768.0
    data = bytearray()
    for us in timings_us:
        units = int(us / US_PER_UNIT + 0.5)
        if units > 255:
            data.append(0x00)
            data.append((units >> 8) & 0xFF)
            data.append(units & 0xFF)
        else:
            data.append(units)
    packet = bytearray(4)
    packet[0] = 0x26
    packet[1] = 0x00
    struct.pack_into('<H', packet, 2, len(data))
    packet.extend(data)
    return bytes(packet)


if __name__ == '__main__':
    cmd = encode_whynter(power=False, mode='cool', fan='high', temp_f=72)
    print(f"ARC-110WD timings - POWER OFF")
    print(f"Command: 0x{cmd:08X}")

    pulses = command_to_pulses(cmd)
    print(f"Pulses: {len(pulses)} values (with pre-header)")

    bl_data = pulses_to_broadlink(pulses)
    print(f"Broadlink data: {len(bl_data)} bytes")

    dev = broadlink.hello("192.168.71.155")
    dev.auth()
    print("Sending with ARC-110WD timings...")
    dev.send_data(bl_data)
    print("Sent!")
