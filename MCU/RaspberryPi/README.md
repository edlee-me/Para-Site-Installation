# Raspberry Pi Pico – 8 Relays + 8 Dimmers (MicroPython)

Control **8 relays** and **8 dimmer modules** from **TouchDesigner**. Two connection options:

| Setup | When to use |
|-------|-------------|
| **USB (Pico ↔ Mac)** | Pico connected to the same Mac that runs TouchDesigner. No WiFi needed. |
| **Network (Pi with WiFi)** | Pico or Pi on the network; TouchDesigner sends OSC to the device’s IP. |

In both cases TouchDesigner uses the **OSC Out CHOP**; the only difference is whether a **bridge** on the Mac turns OSC into serial (USB) or the device receives OSC directly (network).

---

## Protocol

### OSC (used by TouchDesigner in both setups)

| Address | Type | Meaning | Example |
|---------|------|---------|---------|
| `/relay/1` … `/relay/8` | int | Relay off (0) or on (1) | `/relay/1` `1` |
| `/dimmer/1` … `/dimmer/8` | float | Dimmer 0.0–1.0 | `/dimmer/3` `0.75` |

### Serial (USB only, Pico side)

When using USB, the Mac bridge converts OSC into **one line per command**:

- `R,<1-8>,<0|1>` — relay index 1–8, 0 or 1  
- `D,<1-8>,<0.0-1.0>` — dimmer index 1–8, 0.0–1.0  

Example: `R,1,1` then `D,3,0.75`

---

## Option A: Pico connected to Mac via USB (no WiFi)

**Flow:** TouchDesigner (OSC) → Mac bridge (UDP → serial) → Pico (USB) → relays/dimmers

### 1. Pico (MicroPython)

1. Copy to the Pico: `config.py`, `main_serial.py`.
2. Edit `config.py`: set `RELAY_PINS` and `DIMMER_PINS` to your GPIO numbers (Pico: 0–22).
3. Run on the Pico: copy `main_serial.py` to the Pico as `main.py` so it runs on boot (or run once with `mpremote run main_serial.py`). Then **unplug/replug** or reset so the Pico is not in REPL mode. The Mac can then open the Pico’s USB serial port for the bridge.

### 2. Mac – bridge (OSC → serial)

1. Install Python deps:  
   `pip install -r host/requirements.txt`  
   (or `pip install pyserial`)
2. With the Pico plugged in via USB, run:

   ```bash
   python3 host/osc_to_serial_bridge.py
   ```

   The script finds the Pico’s serial port (e.g. `/dev/cu.usbmodem101`) and listens for OSC on **UDP port 9000**.  
   To force a port:  
   `python3 host/osc_to_serial_bridge.py /dev/cu.usbmodem101`

### 3. TouchDesigner

1. Add an **OSC Out CHOP**.
2. **Network Address:** `127.0.0.1` (same machine as the bridge).
3. **Port:** `9000`.
4. Feed channels named `relay/1` … `relay/8`, `dimmer/1` … `dimmer/8`; use **32-bit int** for relays and **32-bit float** for dimmers.

No WiFi or router needed; everything goes over USB and localhost.

---

## Option C: TouchDesigner Serial DAT (no bridge)

You can **skip the bridge** by having TouchDesigner talk to the Arduino (or Pico) directly over serial.

- Use a **Serial DAT** (not the Serial CHOP): it opens the COM/serial port and has a **send()** method so you can send any string (e.g. `R,1,1\n`, `D,3,0.75\n`).
- The **Serial CHOP** sends fixed script strings per channel and can’t easily include the current value (e.g. dimmer 0.75), so it’s not a good fit for this protocol.
- Drive the Serial DAT from a **CHOP Execute DAT** (or similar) that watches your 16 channels and, when values change, builds the line and calls `op('serial1').send('R,1,1', terminator='\n')`.

**Steps:**

1. Add a **Serial DAT**. Set **Port** to your Arduino’s port (e.g. `COM3` on Windows, `/dev/cu.usbmodem*` on Mac). Set **Baud Rate** to `115200`.
2. Create a CHOP with 16 channels: `relay1`…`relay8`, `dimmer1`…`dimmer8` (values 0/1 for relays, 0.0–1.0 for dimmers).
3. Add a **CHOP Execute DAT** with that CHOP as the **Execute** source. In the **onValueChange** callback (or **onFrameStart** if you prefer), call the script below so it sends only when values change (e.g. keep a stored state and send `R,i,v` or `D,i,v` when different).

Example script to paste into the CHOP Execute DAT (adjust `serial1` and the CHOP path to your names):

```python
# In CHOP Execute DAT: set Execute to your source CHOP (16 channels: relay1..relay8, dimmer1..dimmer8).
# Call this from onValueChange or onFrameStart.

def onValueChange(channel, sampleIndex, val, prev):
    serial = op('serial1')  # your Serial DAT
    if not serial.par.active or serial.par.port == '':
        return
    name = channel.name
    if name.startswith('relay'):
        i = int(name.replace('relay', ''))
        serial.send('R,{},{}'.format(i, 1 if val else 0), terminator='\n')
    elif name.startswith('dimmer'):
        i = int(name.replace('dimmer', ''))
        serial.send('D,{},{}'.format(i, max(0, min(1, float(val)))), terminator='\n')
```

To send only when a value actually changes, use **onValueChange** (it fires when that channel’s value changes). The Arduino/Pico code stays the same; no bridge needed.

---

## Option B: Device on the network (WiFi / Ethernet)

Use this when the board has network (e.g. Raspberry Pi with WiFi, or Pico W with WiFi).

**Flow:** TouchDesigner (OSC) → UDP → device (MicroPython) → relays/dimmers

1. On the device, use `main.py` (and `osc_parse.py`, `config.py`). Set `CONNECTION_MODE = "network"` if you use it, and set `UDP_LISTEN_PORT` (e.g. 9000).
2. Run `main.py` on the device so it listens on that port.
3. In TouchDesigner, set **OSC Out CHOP** to the device’s **IP** and the same port (e.g. 9000).

---

## TouchDesigner – channel names

The OSC Out CHOP sends one message per channel; the **channel name** becomes the OSC address.

- Use channel names: `relay/1`, `relay/2`, … `relay/8`, `dimmer/1`, … `dimmer/8`  
  so that messages are `/relay/1`, `/relay/2`, … `/dimmer/8`.
- Set **Base Address** to `/` if needed so the full address is exactly `/relay/1`, etc.
- Relays: **32-bit integer** (0 or 1).  
- Dimmers: **32-bit float** (0.0–1.0).

---

## Arduino instead of Pico (RobotDyn AC dimmer)

If you use **RobotDyn 4ch AC dimmer** modules, the [RBDDimmer](https://github.com/RobotDynOfficial/RBDDimmer) library supports **Arduino, ESP32, ESP8266** only — **not Raspberry Pi Pico**. For that hardware you can use **only Arduino**: same bridge and TouchDesigner setup; the Arduino runs the sketch in `arduino/relay_dimmer_serial/` and speaks the same serial protocol (`R,1,1`, `D,1,0.75`). See `arduino/README.md`.

---

## Files

| File | Role |
|------|------|
| `config.py` | Relay/dimmer GPIO pins, PWM frequency. |
| `main_serial.py` | Pico over **USB serial**: reads `R,*,*` / `D,*,*` and drives GPIO/PWM. |
| `main.py` | Device on **network**: UDP OSC server (for Pi/Pico W with network). |
| `osc_parse.py` | Minimal OSC parser (for `main.py`). |
| `host/osc_to_serial_bridge.py` | **Mac/PC**: receives OSC on UDP 9000, forwards to Pico or Arduino over USB serial. |
| `host/requirements.txt` | Python deps for the bridge (`pyserial`). |
| `arduino/relay_dimmer_serial/` | Arduino sketch for 8 relays + 8 dimmers (RobotDyn RBDDimmer); same serial protocol. |
| `arduino/README.md` | Arduino setup and pinout for RobotDyn AC dimmer. |
| `touchdesigner/serial_send_example.py` | Example script for Serial DAT + CHOP Execute (no bridge). |

---

## Hardware notes

- **Relays:** Use a 3.3 V–compatible relay module (e.g. 8-channel with optocouplers). Do not drive heavy loads directly from the Pico.
- **Dimmers:** AC dimmer modules typically need 0–100% PWM; set `DIMMER_PWM_FREQ` in `config.py` (e.g. 50–1000 Hz) to match your module.
- **Pico pins:** Avoid GP23–28 (used for flash etc.). Use GP0–22 for relays and dimmers.
