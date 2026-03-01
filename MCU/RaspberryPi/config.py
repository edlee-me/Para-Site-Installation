"""
Configuration for 8 relays + 8 dimmers.
Adjust pin numbers to match your wiring.

- Raspberry Pi Pico: GPIO 0–22 are safe; avoid 23–28 (flash, etc.).
- Full Raspberry Pi (BCM): use BCM numbers, e.g. 17, 27, 22, ...
"""

# --- Connection mode: "serial" (Pico over USB) or "network" (Pi with WiFi/Ethernet) ---
# Use "serial" when Pico is connected to Mac/PC via USB; use "network" when running on Pi with network.
CONNECTION_MODE = "serial"

# --- Network (only for CONNECTION_MODE == "network") ---
UDP_LISTEN_PORT = 9000

# --- Relay pins: 8 outputs, on/off ---
# Pico example: GP0–GP7. Use a relay board with optocouplers.
RELAY_PINS = [0, 1, 2, 3, 4, 5, 6, 7]

# --- Dimmer pins: 8 PWM outputs, 0–100% ---
# Pico: any GPIO supports PWM. Example: GP8–GP15.
DIMMER_PINS = [8, 9, 10, 11, 12, 13, 14, 15]

# PWM frequency for dimmers (Hz). 1000 typical for LED; some AC dimmers use 50–200 Hz.
DIMMER_PWM_FREQ = 1000

# Number of channels
NUM_RELAYS = 8
NUM_DIMMERS = 8
