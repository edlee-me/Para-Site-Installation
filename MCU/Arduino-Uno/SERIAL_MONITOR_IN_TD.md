# Monitoring Arduino serial while TouchDesigner has the port

Only one application can open the serial port. Since TouchDesigner must keep it open to send commands, **monitor the Arduino’s replies inside TouchDesigner** by reading from the same Serial DAT.

## In TouchDesigner

1. **Serial DAT** – The same operator you use to send (`serial2` or similar) can receive. Ensure it is set to the same port and **115200** baud.

2. **Read received data** – Use the Serial DAT’s **Receive** or **onReceive** (depending on your TD version):
   - **Receive DAT**: create a Receive DAT, set its **Serial** parameter to your Serial DAT. It will get lines (or bytes) the Arduino sends.
   - **Callbacks**: if your Serial DAT has an `onReceive` callback, append incoming bytes to a string, split on `\n`, and print each line (e.g. to a Text DAT or `debug()`).

3. **Display** – Route the received lines into a **Text DAT** or use `op('text_dat').par.text = newLine` (or append) so you can see `relay 1 = 1`, `dimmer 2 = 50`, etc. in the network.

4. **Alternative** – Use a **Serial CHOP** (if available) or any operator that reads from the Serial DAT; then you can inspect the stream in the viewer or feed it into a DAT for logging.

The Arduino sends one line per command (e.g. `relay 1 = 1` or `dimmer 2 = 75`). Parse by newline and show those lines in your TD UI so you get a live log without opening a separate serial monitor.
