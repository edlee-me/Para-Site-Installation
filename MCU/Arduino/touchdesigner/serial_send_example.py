# TouchDesigner: send relay/dimmer over Serial DAT (no bridge)
#
# 1. Add a Serial DAT: set Port to your Arduino (e.g. COM3 or /dev/cu.usbmodem*), Baud 115200.
# 2. Have a CHOP with 16 channels: relay1..relay8 (0/1), dimmer1..dimmer8 (0.0-1.0).
# 3. Add a CHOP Execute DAT, set "Execute" to that CHOP.
# 4. Paste the function below into the CHOP Execute's onValueChange callback.
#    (Or use onFrameStart and track previous values to send only on change.)
#
# Replace 'serial1' with your Serial DAT name.

def onValueChange(channel, sampleIndex, val, prev):
    serial = op('serial1')
    if not serial.par.active or serial.par.port == '':
        return
    name = channel.name
    try:
        if name.startswith('relay'):
            i = int(name.replace('relay', ''))
            if 1 <= i <= 8:
                serial.send('R,{},{}'.format(i, 1 if val else 0), terminator='\n')
        elif name.startswith('dimmer'):
            i = int(name.replace('dimmer', ''))
            if 1 <= i <= 8:
                v = max(0.0, min(1.0, float(val)))
                serial.send('D,{},{}'.format(i, v), terminator='\n')
    except Exception:
        pass
