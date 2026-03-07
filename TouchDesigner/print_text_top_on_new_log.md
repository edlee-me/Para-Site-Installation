# Print Text TOP when the log updates

Trigger printing **only when** the Text TOP’s content has changed (new log), not every frame.

## Idea

1. When the **log-watch script** writes new text to `latest_log`, set a **“print next frame”** flag.
2. An **Execute DAT** that runs every frame checks the flag. If it’s set, save the Text TOP, send to printer, then clear the flag.

That way the TOP has already updated with the new text before you save/print.

## Setup

### 1. Print-flag DAT

Create a **Table DAT** named `print_flag` (same network as your scripts). One cell is enough. The script will set `[0,0]` to `1` when a new log is stored; the Execute DAT script will set it back to `0` after printing.

### 2. Log-watch script (when you store new log)

After you update the Text DAT with the new log content, set the flag so the next frame will print:

```python
# Right after: TEXT_DAT.text = content
try:
    op('print_flag')[0, 0].val = 1
except Exception:
    pass
```

So in your timer callback that calls `grabAndStoreNewLog()`, inside `grabAndStoreNewLog()` after `TEXT_DAT.text = content`, add the two lines above (and ensure the Table DAT exists and is named `print_flag`, or change `op('print_flag')` to your DAT path).

### 3. Execute DAT to do the print

- Create an **Execute DAT**.
- Set **Run** to **On Frame** (so it runs every frame).
- In the **onFrameEnd** callback, paste the script below. Set `PRINT_TOP` to your Text TOP path and `PRINTER` to your printer name.

```python
import subprocess
import os

PRINT_TOP = op('text1')        # Your Text TOP that displays the log
PRINT_FLAG = op('print_flag')  # Table DAT with one cell
PRINTER = 'Printer_POS_80'

def onFrameEnd(frame):
    try:
        if int(PRINT_FLAG[0, 0].val or 0) != 1:
            return
        PRINT_FLAG[0, 0].val = 0
        path = os.path.join(project.folder or '/tmp', 'print_log.png')
        PRINT_TOP.save(path)
        subprocess.Popen(['lp', '-d', PRINTER, '-o', 'fit-to-page', path])
    except Exception:
        pass
```

- Each frame, after the network has cooked, this runs. If `print_flag[0,0]` is `1`, we clear it, save the Text TOP to a file, and run `lp`. The Text TOP will already show the new log because it cooks before Execute DAT callbacks run.

### 4. Paths

- If your Text TOP or `print_flag` DAT live in another component, use full paths, e.g. `op('project1/container1/text1')`, `op('project1/print_flag')`.

## Flow

1. Timer runs → log-watch finds new `entry_*.txt` → writes to `latest_log` Text DAT → sets `print_flag[0,0] = 1`.
2. Same frame or next frame the Text TOP cooks (it reads from `latest_log`).
3. Execute DAT **onFrameEnd** runs → sees flag 1 → clears flag → saves Text TOP → `lp` to printer.

Result: the TOP is printed only when it has just been updated with a new log.

---

## EPSON LQ-635K: resolution (fix blurry print)

This printer only accepts these resolutions (from `lpoptions -p EPSON_LQ_635K -l`):

- **Resolution/Resolution:** 60dpi 120x60dpi 180dpi 360x180dpi 360dpi

If you use an unsupported value (e.g. `300dpi`), the driver falls back to the default **120x60dpi** and the print looks blurry. Use a **supported** value:

```text
-o Resolution=360dpi
```

So in your `lp` call use **A4** and 360dpi:

```python
subprocess.Popen([
    "lp",
    "-d", "EPSON_LQ_635K",
    "-o", "fit-to-page",
    "-o", "resolution=360dpi",   # must be one of: 60dpi 120x60dpi 180dpi 360x180dpi 360dpi
    "-o", "media=A4",
    path,
])
```

To use custom size again: `media=Custom.WIDTHxHEIGHT` (e.g. `Custom.241x80mm`). Use **360dpi** for sharpest text; if the printer forces 360x180dpi for your media, use `Resolution=360x180dpi` instead.

---

## Print as PDF for clearer output

Many drivers render **PDF** much sharper than a raw PNG. Use this flow: save the Text TOP as PNG → convert PNG to PDF → send the PDF to the printer.

### 1. Install img2pdf (once)

In your project venv:

```bash
.venv/bin/pip install img2pdf
```

### 2. Helper script

The script **`TouchDesigner/scripts/png_to_pdf.py`** converts one PNG to a one-page PDF:

```bash
.venv/bin/python TouchDesigner/scripts/png_to_pdf.py print_log.png print_log.pdf
```

### 3. In your Execute DAT (or CHOP Execute) print callback

Save the TOP as PNG, convert to PDF, then print the PDF. Use **`subprocess.run`** for the conversion so the PDF exists before **`lp`**:

```python
import subprocess
import os

PRINT_TOP = op('text1')
PRINTER = 'EPSON_LQ_635K'
PROJECT_ROOT = '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation'  # or project.folder
VENV_PYTHON = os.path.join(PROJECT_ROOT, '.venv', 'bin', 'python')
PNG_TO_PDF = os.path.join(PROJECT_ROOT, 'TouchDesigner', 'scripts', 'png_to_pdf.py')

path_png = os.path.join(project.folder or '/tmp', 'print_log.png')
path_pdf = os.path.join(project.folder or '/tmp', 'print_log.pdf')
PRINT_TOP.save(path_png)
subprocess.run([VENV_PYTHON, PNG_TO_PDF, path_png, path_pdf], check=True)
subprocess.Popen(['lp', '-d', PRINTER, '-o', 'fit-to-page', '-o', 'media=A4', path_pdf])
```
