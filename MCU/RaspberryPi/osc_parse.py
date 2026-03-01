"""
Minimal OSC 1.0 message parser for MicroPython.
Handles messages with a single int or float argument (e.g. from TouchDesigner OSC Out CHOP).
"""

import struct


def _align4(length):
    """Return length padded to multiple of 4."""
    return (length + 3) & ~3


def parse_osc_message(data):
    """
    Parse one OSC message from byte string. Returns (address, value) or None.
    address is str like "/relay/1", value is int or float.
    """
    if len(data) < 8:
        return None
    # Address: null-terminated, 4-byte aligned
    end = data.find(b"\x00")
    if end < 0:
        return None
    address = data[:end].decode("utf-8", "ignore")
    addr_len = _align4(end + 1)
    if len(data) < addr_len + 4:
        return None
    type_tag_str = data[addr_len : addr_len + 4]
    # Type tag: ",i" or ",f" then optional padding
    if not type_tag_str.startswith(b","):
        return None
    type_char = type_tag_str[1:2]
    tag_len = _align4(type_tag_str.find(b"\x00") + 1 if b"\x00" in type_tag_str else 4)
    args_start = addr_len + tag_len
    if type_char == b"i":
        if len(data) < args_start + 4:
            return None
        (value,) = struct.unpack(">i", data[args_start : args_start + 4])
        return (address, value)
    if type_char == b"f":
        if len(data) < args_start + 4:
            return None
        (value,) = struct.unpack(">f", data[args_start : args_start + 4])
        return (address, value)
    return None
