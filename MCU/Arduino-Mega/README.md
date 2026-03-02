# Arduino Mega — 8 Relays + 8 Dimmers

Serial-controlled 8-channel relay module and 8-channel AC dimmer (two RobotDyn 4ch dimmer modules). Same protocol as the Pico build; driven from TouchDesigner via a bridge on the Mac over USB serial.

- **Board:** Arduino Mega 2560
- **Relays:** 8-channel 5V module
- **Dimmers:** 2× RobotDyn 4-channel AC dimmer (RBDDimmer library)

## Pinout (Mega 2560)

| Function        | Pins        | Notes |
|----------------|-------------|--------|
| Zero-cross (ZC) | **D21**     | INT0. For 2× 4ch dimmer modules, connect **both** modules’ ZC outputs to this one pin. |
| Relays         | **D54–D61** | One output per channel (grouped for wiring). |
| Dimmer outputs | **D4–D11**  | dimmer0→D11, dimmer1→D10, … dimmer7→D4. |

## Power

- **Do not** power the relay and dimmer modules from the Mega’s 5V pin. Total draw (e.g. all 8 relays on + 2 dimmer modules) can exceed what the board can safely supply.
- Use an **external 5V supply** (e.g. 2A) for the **8ch relay** and **both 4ch dimmer** modules.
- Connect the external supply **GND** to the Mega’s **GND** (common ground).
- Power the Mega via USB (for logic/serial) or barrel jack; its 5V pin is for the Mega only.

## Relay wiring (device ON when you send `1`)

Each relay has **COM**, **NO**, and **NC**:

| Coil state | COM ↔ NO   | COM ↔ NC   |
|------------|------------|------------|
| **OFF** (send 0) | Open      | Closed     |
| **ON** (send 1)  | **Closed** | Open       |

To have the **device turn ON when you send 1**:

- Use **COM** and **NO** for the device circuit; leave **NC** unused (or use for something that should be on when the relay is off).
- **Example (AC):** Line (hot) → **COM**, **NO** → device live; device neutral → Neutral. Send **1** → relay closes COM–NO → device ON.
- **Example (DC):** +V → **COM**, **NO** → device +; device − → GND. Send **1** → device ON.

So: **wire the load in series with COM and NO**; command `1` = relay energized = COM–NO closed = device on.

## Serial protocol

- **Baud:** 115200
- **Commands** (one per line, newline-terminated):
  - `R,<channel>,<0|1>` — relay (channel 1–8). `1` = on, `0` = off.
  - `D,<channel>,<0.0–1.0>` — dimmer (channel 1–8). Value is level 0–100%.

Examples:

- `R,1,1`  — relay 1 on  
- `R,1,0`  — relay 1 off  
- `D,1,0.75` — dimmer 1 at 75%

## Build and upload

```bash
pio run -t upload
```

Serial monitor:

```bash
pio device monitor -b 115200
```
