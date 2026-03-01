"""
MicroPython: 8 relays + 8 dimmers controlled via OSC from TouchDesigner.
Listens on UDP port for OSC messages: /relay/<1-8> int (0|1), /dimmer/<1-8> float (0.0-1.0).
"""

import socket
import machine
from config import (
    UDP_LISTEN_PORT,
    RELAY_PINS,
    DIMMER_PINS,
    DIMMER_PWM_FREQ,
    NUM_RELAYS,
    NUM_DIMMERS,
)
from osc_parse import parse_osc_message

# --- Hardware: relays (GPIO out) and dimmers (PWM) ---
relay_pins = []
dimmer_pwms = []


def setup_relays():
    for i in range(min(NUM_RELAYS, len(RELAY_PINS))):
        pin = machine.Pin(RELAY_PINS[i], machine.Pin.OUT)
        pin.off()
        relay_pins.append(pin)


def setup_dimmers():
    for i in range(min(NUM_DIMMERS, len(DIMMER_PINS))):
        pwm = machine.PWM(machine.Pin(DIMMER_PINS[i]))
        pwm.freq(DIMMER_PWM_FREQ)
        pwm.duty_u16(0)
        dimmer_pwms.append(pwm)


def set_relay(index, value):
    """index 0..7, value 0 or 1."""
    if 0 <= index < len(relay_pins):
        relay_pins[index].value(1 if value else 0)


def set_dimmer(index, value):
    """index 0..7, value 0.0..1.0 (float)."""
    if 0 <= index < len(dimmer_pwms):
        v = max(0.0, min(1.0, float(value)))
        duty = int(v * 65535)
        dimmer_pwms[index].duty_u16(duty)


def handle_osc(address, value):
    """Dispatch OSC address to relay or dimmer."""
    parts = address.strip("/").split("/")
    if len(parts) < 2:
        return
    kind, num_str = parts[0], parts[1]
    try:
        index = int(num_str)
    except ValueError:
        return
    if kind == "relay":
        set_relay(index - 1, 1 if value else 0)  # /relay/1 -> index 0
    elif kind == "dimmer":
        set_dimmer(index - 1, float(value))  # /dimmer/1 -> index 0


def run():
    setup_relays()
    setup_dimmers()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", UDP_LISTEN_PORT))
    print("Listening for OSC on port", UDP_LISTEN_PORT)
    print("  /relay/1..8  int 0|1")
    print("  /dimmer/1..8 float 0.0..1.0")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
        except OSError as e:
            if e.args[0] == 11:  # EAGAIN
                continue
            raise
        result = parse_osc_message(data)
        if result:
            address, value = result
            handle_osc(address, value)


if __name__ == "__main__":
    run()
