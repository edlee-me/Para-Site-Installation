# Night Guard – TouchDesigner Integration (Night-Guard-TD)

This folder is the **TouchDesigner-ready** version of the Night Guard system. The original, standalone version is in **`../Night-Guard/`** (backup).

Same logic as Night-Guard: interprets a CCTV-style image with the Gemini API and outputs a "phantom night guard" system log. **If Gemini is unavailable (e.g. in Hong Kong), use Perplexity:** see **`night_guard_perplexity.py`** and **`SETUP_PERPLEXITY.md`**. This build adds:

- **CLI:** pass the image path as first argument (e.g. from TouchDesigner after capture).
- **Paths:** `keywords.txt`, `examples.txt`, and `exhibition_archive_log.txt` are resolved from this folder, so it runs correctly when launched from any working directory.
- **Optional:** `--print Printer_POS_80` sends the generated log text to the thermal printer via `lp`.

## File structure

- `night_guard.py` – main script (CLI + script-dir paths; can write PDF from the log text if reportlab is installed)
- `keywords.txt` – vocabulary bank
- `examples.txt` – few-shot style examples
- `exhibition_archive_log.txt` – created at runtime; logs appended here
- `logs/` – one `entry_<timestamp>.txt` and one `entry_<timestamp>.pdf` per run (PDF optional, needs reportlab)

## API key (keep it out of git)

Provide your Gemini API key in one of these ways (never commit the key):

1. **Local file (recommended for development)**  
   In this folder, create `api_key.txt` with your key on the first line. It is gitignored.  
   Copy `api_key.txt.example` to `api_key.txt` and paste your key.

2. **Environment variable**  
   Set `GEMINI_API_KEY` (e.g. in your shell profile or TouchDesigner’s environment):
   ```bash
   export GEMINI_API_KEY='your-key-here'
   ```

3. **CLI**  
   Pass it when you run the script: `--api-key 'your-key-here'`  
   (Avoid on shared machines; env or file is safer.)

If no key is set, the script exits with a clear error.

## Setup

The project has a venv at **`TouchDesigner/.venv/`** with `google-genai`, `pillow`, and `reportlab` installed. **Use that Python** when running the script (see CLI below). To recreate the venv:

```bash
cd /path/to/Para-Site-Installation/TouchDesigner && python3 -m venv .venv && .venv/bin/pip install google-genai pillow reportlab
```

**PDF output:** Each log is also saved as a PDF (same text, A4). reportlab is installed in `TouchDesigner/.venv`. If it were missing, the script would still write `.txt` only.

## TouchDesigner: run after each capture

Use the **system Python** (or your venv) that has `google-genai` and `pillow`. In your capture callback (e.g. CHOP Execute DAT **onDone**), after saving the image and optionally printing it:

```python
import subprocess
night_guard_script = '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation/Night-Guard-TD/night_guard.py'
python_exe = '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation/TouchDesigner/.venv/bin/python'  # TouchDesigner venv
subprocess.Popen([python_exe, night_guard_script, path, '--print', 'Printer_POS_80'])
```

- `path` = full path to the PNG you just saved.
- Replace `night_guard_script` with the actual path to this folder’s `night_guard.py` on the show machine.
- Omit `'--print', 'Printer_POS_80'` if you only want the log in `exhibition_archive_log.txt` and the console.

Optional: set `project.paths['nightguard']` to this folder and use `tdu.expandPath('nightguard://')` plus `os.path.join(..., 'night_guard.py')` instead of a hardcoded path.

**If the script doesn’t run from TouchDesigner:** use **absolute paths** and a fixed project root instead of `project.folder` (which can be wrong). Copy the callback from `TouchDesigner/timer_capture_onDone_reference.py` into your Timer CHOP Execute DAT’s `onDone`. It redirects the child process stdout/stderr to `Night-Guard-TD/td_nightguard_log.txt`, so all `print()` and errors from `night_guard.py` appear there (TouchDesigner has no console for the child). Do **not** use `shell=True`; keep the list form and `cwd=PROJECT_ROOT`. Do **not** use `stdout=subprocess.PIPE` unless you read from it—that hides output.

## CLI (no TouchDesigner)

**Use the TouchDesigner venv** so `google-genai` and `pillow` are found (plain `python3` will give `ModuleNotFoundError`):

```bash
cd /path/to/Para-Site-Installation
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard.py '/path/to/capture.png'
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard.py '/path/to/capture.png' --print Printer_POS_80
```

Example with your image:

```bash
cd /Users/ed/Documents/Projects/Para-Site/Para-Site-Installation
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard.py '/path/to/capture.png'
```

Logs are appended to `exhibition_archive_log.txt` in the `Night-Guard-TD` folder.

### Create a PDF from any log file

To turn an existing log `.txt` file into a PDF (same path, `.pdf` extension), use `--pdf-only`. Requires `reportlab` in the venv.

```bash
cd /path/to/Para-Site-Installation
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard.py --pdf-only TouchDesigner/Night-Guard-TD/logs/entry_1772813814265.txt
```

Output: `TouchDesigner/Night-Guard-TD/logs/entry_1772813814265.pdf`

**Create PDF and print on EPSON_LQ_635K (fit-to-page, A4, 360dpi):**

```bash
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard.py '/path/to/capture.png' --print-epson
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard.py --pdf-only path/to/log.txt --print-epson
```
