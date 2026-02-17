#!/usr/bin/env python3
"""Test Whynter ARC-14SH IR protocol via Broadlink RM4 Mini"""

import broadlink
import struct

# Whynter ARC-14SH IR Protocol timings (from ESPHome)
HEADER_MARK = 8000
HEADER_SPACE = 4000
BIT_MARK = 600
ONE_SPACE = 1600
ZERO_SPACE = 550


def reverse_bits(byte_val):
    """Reverse bits of an 8-bit value"""
    result = 0
    for i in range(8):
        if byte_val & (1 << i):
            result |= 1 << (7 - i)
    return result


def encode_whynter(power=False, mode='cool', fan='high', temp_f=72):
    """Build 32-bit Whynter command"""
    cmd = 0x12 << 24  # Command header

    # Fan speed (bits 22-20)
    fan_map = {'high': 0b001, 'med': 0b010, 'low': 0b100, 'auto': 0b000}
    cmd |= fan_map.get(fan, 0) << 20

    # Mode (bits 19-16)
    mode_map = {'fan': 0b0001, 'dehum': 0b0010, 'heat': 0b0100, 'cool': 0b1000}
    cmd |= mode_map.get(mode, 0b1000) << 16

    # Fahrenheit (bit 10)
    cmd |= 1 << 10

    # Power (bit 8)
    if power:
        cmd |= 1 << 8

    # Temperature (bits 7-0, bit-reversed)
    cmd |= reverse_bits(temp_f) & 0xFF

    return cmd


def command_to_pulses(cmd):
    """Convert 32-bit command to IR pulse timings (microseconds)"""
    pulses = [HEADER_MARK, HEADER_SPACE]
    for i in range(31, -1, -1):
        pulses.append(BIT_MARK)
        if (cmd >> i) & 1:
            pulses.append(ONE_SPACE)
        else:
            pulses.append(ZERO_SPACE)
    pulses.append(BIT_MARK)  # Final mark
    return pulses


def pulses_to_broadlink(timings_us):
    """Convert microsecond pulses to Broadlink IR format"""
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
    packet[0] = 0x26  # IR marker
    packet[1] = 0x00  # no repeat
    struct.pack_into('<H', packet, 2, len(data))
    packet.extend(data)
    return bytes(packet)


if __name__ == '__main__':
    import sys

    power = '--on' in sys.argv
    mode = 'cool'
    fan = 'high'
    temp = 72

    for arg in sys.argv[1:]:
        if arg.startswith('--mode='):
            mode = arg.split('=')[1]
        elif arg.startswith('--fan='):
            fan = arg.split('=')[1]
        elif arg.startswith('--temp='):
            temp = int(arg.split('=')[1])

    action = "ON" if power else "OFF"
    print(f"Whynter {action}: mode={mode}, fan={fan}, temp={temp}F")

    cmd = encode_whynter(power=power, mode=mode, fan=fan, temp_f=temp)
    print(f"Command: 0x{cmd:08X}")
    print(f"Binary:  {cmd:032b}")

    pulses = command_to_pulses(cmd)
    print(f"Pulses: {len(pulses)} values")

    bl_data = pulses_to_broadlink(pulses)
    print(f"Broadlink data: {len(bl_data)} bytes")

    dev = broadlink.hello("192.168.71.155")
    dev.auth()
    print("Authenticated, sending...")
    dev.send_data(bl_data)
    print(f"Sent! Whynter should be {action}.")
