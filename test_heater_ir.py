#!/usr/bin/env python3
"""Test Dr. Heater NEC IR protocol via Broadlink RM4 Mini"""

import broadlink
import struct

# NEC Protocol timing (microseconds)
NEC_HEADER_MARK = 9000
NEC_HEADER_SPACE = 4500
NEC_BIT_MARK = 563
NEC_ONE_SPACE = 1688
NEC_ZERO_SPACE = 563

DEVICE_ADDR = 0x80
CMD_POWER = 0x1A


def nec_to_pulses(address, command):
    pulses = [NEC_HEADER_MARK, NEC_HEADER_SPACE]
    for byte_val in [address, (~address) & 0xFF, command, (~command) & 0xFF]:
        for bit in range(8):
            pulses.append(NEC_BIT_MARK)
            if byte_val & (1 << bit):
                pulses.append(NEC_ONE_SPACE)
            else:
                pulses.append(NEC_ZERO_SPACE)
    pulses.append(NEC_BIT_MARK)
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
    print(f"Dr. Heater POWER toggle (NEC addr=0x{DEVICE_ADDR:02X}, cmd=0x{CMD_POWER:02X})")

    pulses = nec_to_pulses(DEVICE_ADDR, CMD_POWER)
    print(f"Pulses: {len(pulses)} values")

    bl_data = pulses_to_broadlink(pulses)
    print(f"Broadlink data: {len(bl_data)} bytes")

    dev = broadlink.hello("192.168.71.155")
    dev.auth()
    print("Authenticated, sending POWER...")
    dev.send_data(bl_data)
    print("Sent! Check if Dr. Heater toggled.")
