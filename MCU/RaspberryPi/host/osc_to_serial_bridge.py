#!/usr/bin/env python3
"""
Bridge: receive OSC from TouchDesigner (UDP) and forward to Pico over USB serial.

Run this on the Mac (or PC) with the Pico connected via USB.
TouchDesigner OSC Out CHOP → localhost:9000 → this script → /dev/cu.usbmodem* → Pico.

Usage:
  python3 osc_to_serial_bridge.py [serial_port] [--log]
  If serial_port is omitted, uses first detected USB serial (e.g. Pico).
  Use --log to print every OSC message and the serial line sent.
  Use --debug to print every UDP packet (and raw bytes when parse fails).
  Use --only-changed to forward to the Pico only when a value actually changes
  (ignores repeated identical values from TouchDesigner).
"""

import argparse
import socket
import struct
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Install pyserial: pip install pyserial")
    sys.exit(1)

# --- Config (match TouchDesigner and Pico) ---
UDP_PORT = 9000
BAUD = 115200


def align4(n):
    return (n + 3) & ~3


def parse_osc(data):
    """Parse one OSC message. Returns (address, value) or None. value is int or float."""
    if len(data) < 8:
        return None
    end = data.find(b"\x00")
    if end < 0:
        return None
    address = data[:end].decode("utf-8", "ignore")
    addr_len = align4(end + 1)
    if len(data) < addr_len + 4:
        return None
    type_tag = data[addr_len : addr_len + 4]
    if not type_tag.startswith(b","):
        return None
    tag_char = type_tag[1:2]
    tag_len = 4
    args_start = addr_len + tag_len
    if tag_char == b"i" and len(data) >= args_start + 4:
        (value,) = struct.unpack(">i", data[args_start : args_start + 4])
        return (address, value)
    if tag_char == b"f" and len(data) >= args_start + 4:
        (value,) = struct.unpack(">f", data[args_start : args_start + 4])
        return (address, value)
    return None


def extract_osc_messages(data):
    """
    Yield (address, value) for each OSC message in data.
    Handles raw messages and OSC bundles (#bundle).
    """
    if len(data) < 4:
        return
    if data.startswith(b"#bundle\x00"):
        # OSC bundle: 8-byte timetag, then [4-byte len][message]...
        pos = 16  # "#bundle\x00" (8) + timetag (8)
        while pos + 4 <= len(data):
            (msg_len,) = struct.unpack(">I", data[pos : pos + 4])
            pos += 4
            if pos + msg_len > len(data):
                break
            msg = data[pos : pos + msg_len]
            pos += msg_len
            result = parse_osc(msg)
            if result:
                yield result
    else:
        result = parse_osc(data)
        if result:
            yield result


def _parse_address(address):
    """Return (kind, index) e.g. ('relay', 1) or ('dimmer', 3). Supports /relay/1, /relay1, /dimmer/2, /dimmer2."""
    s = address.strip("/").replace("/", "")
    for kind in ("relay", "dimmer"):
        if s.startswith(kind):
            tail = s[len(kind) :].lstrip("_")
            if tail.isdigit():
                idx = int(tail)
                if 1 <= idx <= 8:
                    return (kind, idx)
    parts = address.strip("/").split("/")
    if len(parts) >= 2:
        try:
            idx = int(parts[-1])
            if parts[0] in ("relay", "dimmer") and 1 <= idx <= 8:
                return (parts[0], idx)
        except ValueError:
            pass
    return (None, None)


def osc_to_serial(address, value):
    """Convert OSC (address, value) to Pico serial line. Returns None or string like 'R,1,1'.
    Dimmer value can be 0-255 (normalized to 0.0-1.0) or 0.0-1.0.
    """
    kind, index = _parse_address(address)
    if kind is None:
        return None
    if kind == "relay":
        return f"R,{index},{1 if value else 0}"
    if kind == "dimmer":
        v = float(value)
        if v > 1.0:
            v = v / 255.0
        v = max(0.0, min(1.0, v))
        return f"D,{index},{v}"
    return None


def find_pico_port():
    """Return first USB serial port that looks like a Pico (vid/pid or name)."""
    for p in serial.tools.list_ports.comports():
        # Raspberry Pi Pico USB VID:PID = 2E8A:0005 (RP2040)
        if p.vid == 0x2E8A and p.pid == 0x0005:
            return p.device
        if "usbmodem" in (p.device or "") or "usbserial" in (p.device or ""):
            return p.device
    return None


def alternate_port(port):
    """On macOS, try the other device node (cu <-> tty) for the same device."""
    if not port:
        return None
    if "/cu." in port:
        return port.replace("/cu.", "/tty.")
    if "/tty." in port:
        return port.replace("/tty.", "/cu.")
    return None


def open_serial(port, baud, retries=3):
    """Try to open port, optionally try alternate (cu/tty) and retry with delay."""
    for attempt in range(retries):
        for p in (port, alternate_port(port)):
            if not p:
                continue
            try:
                return serial.Serial(p, baud)
            except (serial.SerialException, OSError):
                pass
        if attempt < retries - 1:
            time.sleep(1.5)
    return None


def main():
    parser = argparse.ArgumentParser(description="OSC (TouchDesigner) to USB serial (Pico) bridge")
    parser.add_argument("port", nargs="?", help="Serial port (e.g. /dev/cu.usbmodem101). Auto-detect if omitted.")
    parser.add_argument("--udp", type=int, default=UDP_PORT, help=f"UDP port for OSC (default {UDP_PORT})")
    parser.add_argument("--log", "-l", action="store_true", help="Log every OSC message and serial line to stdout")
    parser.add_argument("--debug", "-d", action="store_true", help="Print every UDP packet; show raw bytes when parse fails")
    parser.add_argument("--only-changed", "-c", action="store_true", help="Send to Pico only when a channel value has changed")
    args = parser.parse_args()

    port = args.port or find_pico_port()
    if not port:
        print("No Pico serial port found. Plug in the Pico and try again, or pass the port:")
        print("  python3 osc_to_serial_bridge.py /dev/cu.usbmodem101")
        sys.exit(1)

    ser = open_serial(port, BAUD)
    if ser is None:
        print(f"Could not open {port} (tried cu and tty, 3 retries).")
        print()
        print("If you see 'Resource busy' and lsof shows nothing:")
        print("  • Unplug the Pico, wait 3 seconds, plug it back in, then run this again.")
        print("Otherwise:")
        print("  • Close Thonny, Arduino IDE, or any serial monitor.")
        print("  • Quit any mpremote session or terminal connected to the Pico.")
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", args.udp))
    print(f"OSC → Serial bridge: listening for OSC on UDP port {args.udp}, sending to {port} @ {BAUD}")
    print("TouchDesigner: set OSC Out CHOP to Address 127.0.0.1, Port", args.udp)
    if args.log:
        print("Logging: ON (every OSC message and serial line)")
    if args.debug:
        print("Debug: ON (every UDP packet; raw bytes if parse fails)")
    if args.only_changed:
        print("Only-changed: ON (forward to Pico only when value changes)")
    print("Dimmer values: 0-255 or 0.0-1.0. Addresses: /relay/1, /relay1, /dimmer/1, /dimmer1, etc.")
    if not (args.log or args.debug):
        print("Use --log to see incoming OSC and serial output.")

    # For --only-changed: store last serial line sent per address (compare what we actually send)
    last_sent = {}

    while True:
        data, addr = sock.recvfrom(1024)
        if args.debug:
            print(f"[UDP] {len(data)} bytes from {addr[0]}:{addr[1]}")

        got_any = False
        for address, value in extract_osc_messages(data):
            got_any = True
            line = osc_to_serial(address, value)
            if not line:
                if args.log or args.debug:
                    print(f"  OSC  {address}  {value!r}  →  (ignored)")
                continue
            if args.only_changed:
                if last_sent.get(address) == line:
                    if args.log or args.debug:
                        print(f"  (unchanged)  {address} = {value!r}  →  {line}")
                    continue
                last_sent[address] = line
            if args.log or args.debug:
                print(f"  OSC  {address}  {value!r}  →  serial: {line}")
            ser.write((line + "\n").encode("utf-8"))

        if args.debug and not got_any and len(data) > 0:
            # Show raw bytes so we can see what TD is sending
            preview = data[:80].hex()
            if len(data) > 80:
                preview += "..."
            try:
                ascii_preview = "".join(chr(b) if 32 <= b < 127 else "." for b in data[:60])
                print(f"  [unparsed] hex: {preview}")
                print(f"  [unparsed] ascii: {ascii_preview!r}")
            except Exception:
                print(f"  [unparsed] hex: {preview}")


if __name__ == "__main__":
    main()
