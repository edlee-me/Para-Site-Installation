# Setting up Para-Site Installation on a new Mac

Use these steps when moving the project to a new machine (or setting it up from a fresh clone).

## 1. Prerequisites

- **macOS** (the project uses `lp` for printing; same steps apply on other Unix if you have Python 3 and CUPS).
- **Python 3** (3.10 or 3.11 recommended). On macOS, `python3` often stays at the system version (e.g. 3.9); use the version you installed explicitly:
  ```bash
  python3.11 --version   # if you installed 3.11 from python.org or Homebrew
  ```
  If needed, install from [python.org](https://www.python.org/downloads/) or Homebrew: `brew install python@3.11`. The new version is usually available as `python3.11`, not as `python` or `python3`.
- **TouchDesigner** installed (if you use the TD integration).
- **Perplexity API key** (for `night_guard_perplexity.py`, recommended).
- *(Optional)* **Gemini API key** if you also want to use `night_guard.py`.

## 2. Project location

Copy or clone the project to the new Mac, e.g.:

```text
/Users/yourname/Documents/Projects/Para-Site/Para-Site-Installation/
```

Paths in TouchDesigner callbacks and docs use this project root; adjust if your path is different.

## 3. Create the virtual environment and install libraries

The app expects a venv at **`TouchDesigner/.venv`** and uses its Python to run `night_guard.py` (Gemini) and/or `night_guard_perplexity.py` (Perplexity).

From the **project root** (parent of `TouchDesigner`). Use **the same Python you want in the venv** (e.g. 3.11). On macOS, `python3` may still be 3.9; use `python3.11` if you installed 3.11:

```bash
cd /path/to/Para-Site-Installation/TouchDesigner
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r Night-Guard-TD/requirements.txt -r Night-Guard-TD/requirements-perplexity.txt
```

If you don’t have `python3.11` in PATH, use the full path (e.g. from python.org: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3`, or Homebrew: `/opt/homebrew/bin/python3.11`). Or use `python3` if it already reports 3.10+:

```bash
python3 -m venv .venv
.venv/bin/pip install google-genai perplexityai pillow reportlab
```

**Check:**

```bash
.venv/bin/python -c "from google import genai; import perplexity; from PIL import Image; import reportlab; print('OK')"
```

If that prints `OK`, the venv is ready.

## 4. API keys (Night Guard)

You can use either or both backends:

- **Perplexity (recommended, `night_guard_perplexity.py`)**
  - Create the API key file (do not commit this file):
    ```bash
    cd /path/to/Para-Site-Installation/TouchDesigner/Night-Guard-TD
    cp perplexity_api_key.txt.example perplexity_api_key.txt
    ```
  - Edit `perplexity_api_key.txt` and put your Perplexity API key on the next line.
  - Alternatively, set the environment variable before running TouchDesigner or the script:
    ```bash
    export PERPLEXITY_API_KEY='your-key-here'
    ```

- **Gemini (optional, `night_guard.py`)**
  - Create the API key file:
    ```bash
    cd /path/to/Para-Site-Installation/TouchDesigner/Night-Guard-TD
    cp api_key.txt.example api_key.txt
    ```
  - Edit `api_key.txt` and put your Gemini API key on the first line.
  - Or set:
    ```bash
    export GEMINI_API_KEY='your-key-here'
    ```

## 5. TouchDesigner paths

If your project path on the new Mac is different from the old one, update:

- **Timer CHOP callbacks** (or any Execute DAT) that run `night_guard.py`: set `PROJECT_ROOT` and the paths to `night_guard.py` and `.venv/bin/python` to the new location.
- **README** and any docs that show example paths (e.g. `/Users/ed/...`) so they match the new machine.

## 6. Printing (optional)

- **Epson LQ-635K:** Install the driver and add the printer in **System Settings → Printers & Scanners**. The script uses `lp -d EPSON_LQ_635K`; the printer name must match.
- **Custom font for PDFs:** If you use `--font`, use a path that exists on the new Mac (e.g. `/Library/Fonts/` or a project font folder).

## 7. Quick test

From the project root:

```bash
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard_perplexity.py --help
```

Then run on a real image (no TD needed):

```bash
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard_perplexity.py /path/to/a/test.png
```

Check that `TouchDesigner/Night-Guard-TD/exhibition_archive_log.txt` and files in `TouchDesigner/Night-Guard-TD/logs/` are created. If you use `--print-epson`, ensure the Epson is set up and the printer name is correct.

## Summary

| Step | What |
|------|------|
| 1 | Python 3.10+ and TouchDesigner installed |
| 2 | Project copied to new Mac |
| 3 | `TouchDesigner/.venv` created and `pip install -r Night-Guard-TD/requirements.txt -r Night-Guard-TD/requirements-perplexity.txt` |
| 4 | `Night-Guard-TD/perplexity_api_key.txt` (and optionally `api_key.txt`) created with API keys |
| 5 | TouchDesigner callbacks updated with new project path |
| 6 | Printer (and optional font path) configured if needed |
| 7 | Test run with `.venv/bin/python ... night_guard_perplexity.py` |
