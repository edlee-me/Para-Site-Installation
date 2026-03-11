# Print image from Movie File In TOP to Printer_POS_80

Save the current frame of a Movie File In TOP to a file and send it to **Printer_POS_80** (or another `lp` printer).

## 1. One-shot: button or pulse

Use a **CHOP Execute DAT** or **Execute DAT** so that when a channel goes 0→1 (or on a pulse), you save the TOP and run `lp`.

### CHOP Execute DAT (e.g. on a pulse or button)

1. Create a **CHOP Execute DAT**.
2. Point it at a CHOP that goes 0→1 when you want to print (e.g. a Pulse CHOP, or a value from a button).
3. In **onOffToOn**, paste:

```python
import subprocess
import os

# Your Movie File In TOP
MOVIE_TOP = op('moviefilein1')   # change to your TOP path
PRINTER = 'Printer_POS_80'
MEDIA = 'Custom.80x100mm'       # or 'A4', etc.

def onOffToOn(channel, sampleIndex, val, prev):
    folder = project.folder or '/tmp'
    path = os.path.join(folder, 'print_frame.png')
    MOVIE_TOP.save(path)
    # Use subprocess.run so the file isn't removed before lp reads it
    subprocess.run([
        'lp', '-d', PRINTER,
        '-o', 'media=' + MEDIA,
        '-o', 'fit-to-page',
        path,
    ], check=False)
```

- Replace `op('moviefilein1')` with your Movie File In TOP (e.g. `op('moviefilein1')` or `op('project1/moviefilein1')`).
- Adjust `PRINTER` and `MEDIA` if needed (e.g. `Printer_POS_80`, `Custom.80x100mm`).

### Execute DAT (e.g. on frame, when a flag is set)

If you prefer to trigger from a Table DAT flag (like in [print_text_top_on_new_log.md](print_text_top_on_new_log.md)):

1. Create a **Table DAT** `print_frame_flag` with one cell. Set `[0,0]` to `1` when you want to print.
2. Create an **Execute DAT**, set **Run** to **On Frame**.
3. In **onFrameEnd**:

```python
import subprocess
import os

MOVIE_TOP = op('moviefilein1')
PRINT_FLAG = op('print_frame_flag')
PRINTER = 'Printer_POS_80'
MEDIA = 'Custom.80x100mm'

def onFrameEnd(frame):
    try:
        if int(PRINT_FLAG[0, 0].val or 0) != 1:
            return
        PRINT_FLAG[0, 0].val = 0
        folder = project.folder or '/tmp'
        path = os.path.join(folder, 'print_frame.png')
        MOVIE_TOP.save(path)
        subprocess.run([
            'lp', '-d', PRINTER,
            '-o', 'media=' + MEDIA,
            '-o', 'fit-to-page',
            path,
        ], check=False)
    except Exception:
        pass
```

## 2. Paths and printer name

- **TOP path:** Use the operator path to your Movie File In, e.g. `op('moviefilein1')` or `op('comp/moviefilein1')`.
- **Printer:** `Printer_POS_80` must exist in CUPS. List printers: `lpstat -p`. If your printer has a different name (e.g. `Printer_POS-80`), set `PRINTER` to that.
- **Media:** Common values: `Custom.80x100mm`, `Custom.80x60mm`, `A4`. Match what you use for that printer.

## 3. Why `subprocess.run` instead of `subprocess.Popen`

Using **`subprocess.run()`** blocks until `lp` exits, so the saved PNG still exists when the print daemon reads it. With **`Popen`**, the script can continue and the file might be overwritten or removed before the daemon opens it, giving "No such file or directory".

## 4. Optional: save as PDF then print

If your printer gives better results with PDF, save the TOP as PNG, convert to PDF (e.g. with a small script or img2pdf), then `lp` the PDF. See [print_text_top_on_new_log.md](print_text_top_on_new_log.md) for a PDF conversion example.
