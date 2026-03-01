"""
MicroPython for Raspberry Pi Pico: 8 relays + 8 dimmers via USB serial.
Connect Pico to Mac/PC with USB. A bridge on the computer receives OSC from
TouchDesigner and sends text commands over the serial link.

Serial protocol (one command per line):
  R,<1-8>,<0|1>     relay: index 1-8, 0=off 1=on
  D,<1-8>,<0.0-1.0> dimmer: index 1-8, 0.0-1.0 = 0-100%
Example: R,1,1  D,3,0.75
"""

import sys
import machine
from config import (
    RELAY_PINS,
    DIMMER_PINS,
    DIMMER_PWM_FREQ,
    NUM_RELAYS,
    NUM_DIMMERS,
)

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
    if 0 <= index < len(relay_pins):
        relay_pins[index].value(1 if value else 0)


def set_dimmer(index, value):
    if 0 <= index < len(dimmer_pwms):
        v = max(0.0, min(1.0, float(value)))
        dimmer_pwms[index].duty_u16(int(v * 65535))


def handle_line(line):
    line = line.strip()
    if not line:
        return
    parts = line.split(",")
    if len(parts) != 3:
        return
    cmd, a, b = parts[0].upper(), parts[1].strip(), parts[2].strip()
    try:
        index = int(a)
        if cmd == "R":
            val = int(b)
            print("relay {} = {}".format(index, val))
            set_relay(index - 1, val)
        elif cmd == "D":
            val = float(b)
            print("dimmer {} = {}".format(index, val))
            set_dimmer(index - 1, val)
    except (ValueError, IndexError):
        pass


def run():
    setup_relays()
    setup_dimmers()
    print("Serial relay/dimmer ready. Commands: R,<1-8>,<0|1>  D,<1-8>,<0.0-1.0>")

    buf = ""
    while True:
        c = sys.stdin.read(1)
        if not c:
            continue
        if c in ("\n", "\r"):
            if buf:
                handle_line(buf)
                buf = ""
        else:
            buf += c
            if len(buf) > 64:
                buf = ""


if __name__ == "__main__":
    run()
