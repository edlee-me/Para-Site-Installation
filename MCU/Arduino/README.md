# Arduino + RobotDyn AC dimmer (RBDDimmer)

Use **Arduino** (or ESP32/ESP8266) instead of Raspberry Pi Pico when you have **RobotDyn 4ch AC dimmer** modules. The [RBDDimmer](https://github.com/RobotDynOfficial/RBDDimmer) library only supports Arduino/ESP, not Pico.

## Arduino Mega: 8 relays + 8 dimmers (default)

The sketch is set up for **Mega** by default:

| Pin   | Use |
|-------|-----|
| D2    | Zero-cross input (from RobotDyn dimmer module) |
| D3–D10| Dimmer 1–8 outputs → two RobotDyn 4ch modules (or one 4ch + spare) |
| 22, 24, 26, 28, 30, 32, 34, 36 | Relay 1–8 outputs |

Choose **Board: Arduino Mega 2560** in the IDE and upload.

---

## Arduino UNO: 4 relays + 4 dimmers

**UNO has limited pins:** D0/D1 = USB serial, D2 = zero-cross (fixed). That leaves 11 pins — **not enough for 8+8**. For UNO, edit the sketch: set `NUM_RELAYS` and `NUM_DIMMERS` to **4**, and use:

| Pin    | Use |
|--------|-----|
| D2     | Zero-cross |
| D3–D6  | Dimmer 1–4 |
| D7–D10 | Relay 1–4 |

## Can I use only Arduino?

**Yes.** Same flow:

**TouchDesigner** → **OSC Out CHOP** → **Bridge (Mac)** → **USB serial** → **Arduino** → relays + RobotDyn dimmers

- Install the Arduino sketch in this folder.
- Connect the Arduino to the Mac via USB.
- Run the same bridge: `python3 host/osc_to_serial_bridge.py --only-changed`
- Point the bridge at the Arduino’s serial port (or let it auto-detect; may need to specify the port).

## Hardware

- **Relays:** 8 digital outputs (configurable in the sketch).
- **Dimmers:** RobotDyn AC dimmer module(s). You need:
  - **Zero-cross (ZC) input** from the AC dimmer board → one Arduino input pin (e.g. **D2** on Mega/UNO).
  - **DIM/PSM outputs** from the Arduino → dimmer board trigger inputs. Use the pins listed in the [RBDDimmer README](https://github.com/RobotDynOfficial/RBDDimmer) for your board (e.g. Mega: D3–D10; **D2 is fixed as ZC** on AVR).

| Board     | Zero-cross | This sketch |
|-----------|------------|-------------|
| **Mega**  | D2 (fixed) | **8 relays** (22,24,…,36) + **8 dimmers** (D3–D10) — default |
| UNO       | D2 (fixed) | 4 relays + 4 dimmers (edit NUM_* and pin arrays) |
| ESP32     | Your choice | 8+8 (set pin arrays and ZERO_CROSS_PIN) |

## Setup

1. Install **RBDDimmer** in Arduino IDE: **Sketch → Include Library → Manage Libraries** → search “RBDDimmer” (RobotDyn).
2. Open `relay_dimmer_serial/relay_dimmer_serial.ino`.
3. Set `RELAY_PINS`, `DIMMER_PINS`, and `ZERO_CROSS_PIN` to match your wiring. For Mega/UNO, ZC is D2.
4. Upload to the board. Set **Tools → Port** to the Arduino’s USB port.
5. On the Mac, run the bridge (same as for Pico). If the Arduino appears as a different serial device, pass the port:  
   `python3 host/osc_to_serial_bridge.py /dev/cu.usbmodem*` (or the correct port).

## Serial protocol (same as Pico)

- `R,<1-8>,<0|1>` — relay on/off  
- `D,<1-8>,<0.0-1.0>` — dimmer 0–100% (sketch converts to 0–100 for `setPower()`)

So the existing TouchDesigner patch and bridge work unchanged; only the device on the other end of USB is the Arduino instead of the Pico.


Serial CHOP vs Serial DAT
Serial CHOP – Sends a fixed script string per channel when that channel changes. You can’t put the current value (e.g. 0.75) into the string, so you can’t send D,3,0.75 properly. Not a good fit for this.
Serial DAT – Opens the serial port and has send(text, terminator='\n'). You can build any string (e.g. R,1,1, D,3,0.75) in a script and send it. Use this.
No-bridge setup
Serial DAT
Create a Serial DAT.
Set Port to the Arduino’s port (e.g. COM3 on Windows, /dev/cu.usbmodem… on Mac).
Set Baud Rate to 115200.
Turn it on (Active).
CHOP with your 16 channels
Same as now: e.g. relay1…relay8 (0/1), dimmer1…dimmer8 (0.0–1.0).
CHOP Execute DAT
Create a CHOP Execute DAT.
Set Execute to the CHOP above.
In the onValueChange callback, paste the script that builds R,<i>,<v> or D,<i>,<v> and calls the Serial DAT’s send().
That way TouchDesigner sends the same protocol (R,1,1, D,3,0.75, etc.) directly over serial; the Arduino sketch is unchanged and the bridge is no longer needed.