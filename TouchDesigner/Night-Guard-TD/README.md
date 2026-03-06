# Night Guard – TouchDesigner Integration (Night-Guard-TD)

This folder is the **TouchDesigner-ready** version of the Night Guard system. The original, standalone version is in **`../Night-Guard/`** (backup).

Same logic as Night-Guard: interprets a CCTV-style image with the Gemini API and outputs a "phantom night guard" system log. This build adds:

- **CLI:** pass the image path as first argument (e.g. from TouchDesigner after capture).
- **Paths:** `keywords.txt`, `examples.txt`, and `exhibition_archive_log.txt` are resolved from this folder, so it runs correctly when launched from any working directory.
- **Optional:** `--print Printer_POS_80` sends the generated log text to the thermal printer via `lp`.

## File structure

- `night_guard.py` – main script (CLI + script-dir paths)
- `keywords.txt` – vocabulary bank
- `examples.txt` – few-shot style examples
- `exhibition_archive_log.txt` – created at runtime; logs appended here

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

The project has a venv at **`../.venv/`** with `google-genai` and `pillow` already installed. **Use that Python** when running the script (see CLI below). To recreate the venv:

```bash
cd /path/to/Para-Site-Installation && python3 -m venv .venv && .venv/bin/pip install google-genai pillow
```

## TouchDesigner: run after each capture

Use the **system Python** (or your venv) that has `google-genai` and `pillow`. In your capture callback (e.g. CHOP Execute DAT **onDone**), after saving the image and optionally printing it:

```python
import subprocess
night_guard_script = '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation/Night-Guard-TD/night_guard.py'
python_exe = '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation/.venv/bin/python'  # project venv (recommended)
subprocess.Popen([python_exe, night_guard_script, path, '--print', 'Printer_POS_80'])
```

- `path` = full path to the PNG you just saved.
- Replace `night_guard_script` with the actual path to this folder’s `night_guard.py` on the show machine.
- Omit `'--print', 'Printer_POS_80'` if you only want the log in `exhibition_archive_log.txt` and the console.

Optional: set `project.paths['nightguard']` to this folder and use `tdu.expandPath('nightguard://')` plus `os.path.join(..., 'night_guard.py')` instead of a hardcoded path.

**If the script doesn’t run from TouchDesigner:** use **absolute paths** and a fixed project root instead of `project.folder` (which can be wrong). Copy the callback from `TouchDesigner/timer_capture_onDone_reference.py` into your Timer CHOP Execute DAT’s `onDone`. It redirects the child process stdout/stderr to `Night-Guard-TD/td_nightguard_log.txt`, so all `print()` and errors from `night_guard.py` appear there (TouchDesigner has no console for the child). Do **not** use `shell=True`; keep the list form and `cwd=PROJECT_ROOT`. Do **not** use `stdout=subprocess.PIPE` unless you read from it—that hides output.

## CLI (no TouchDesigner)

**Use the project venv** so `google-genai` and `pillow` are found (plain `python3` will give `ModuleNotFoundError`):

```bash
cd /path/to/Para-Site-Installation
.venv/bin/python Night-Guard-TD/night_guard.py '/path/to/capture.png'
.venv/bin/python Night-Guard-TD/night_guard.py '/path/to/capture.png' --print Printer_POS_80
```

Example with your image:

```bash
cd /Users/ed/Documents/Projects/Para-Site/Para-Site-Installation
.venv/bin/python Night-Guard-TD/night_guard.py '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation/Night-Guard/Screenshot 2026-02-27 at 14.38.26.png'
```

Logs are appended to `exhibition_archive_log.txt` in the `Night-Guard-TD` folder.
