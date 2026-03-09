# Night Guard with Perplexity API (simple alternative to Gemini / Azure)

Use **`night_guard_perplexity.py`** when Gemini isn’t available (e.g. Hong Kong) and you want to avoid Azure setup. Same behaviour: CCTV image → phantom night guard log → `exhibition_archive_log.txt` and optional print/PDF.

Docs: [Perplexity API – Getting started](https://docs.perplexity.ai/docs/getting-started/overview), [Image attachments](https://docs.perplexity.ai/docs/agent-api/image-attachments).

---

## 1. Get an API key

You already created one. If needed:

- Go to [Perplexity → Settings → API](https://www.perplexity.ai/settings/api) (or [API Portal](https://www.perplexity.ai/account/api)).
- Create an API key and copy it.

---

## 2. Install dependency

From the project root (or wherever your venv is):

```bash
# TouchDesigner venv
cd /path/to/Para-Site-Installation/TouchDesigner
.venv/bin/pip install perplexityai
```

Optional: `pillow` and `reportlab` (same as for the other Night Guard scripts) if not already installed.

---

## 3. Configure the API key (pick one)

### Option A – Environment variable (good for TouchDesigner)

```bash
export PERPLEXITY_API_KEY="pplx-xxxxxxxx"
```

Set this in the environment that runs the script (e.g. before starting TouchDesigner, or in your shell profile).

### Option B – File (good for local dev, keep out of git)

In the **`Night-Guard-TD`** folder, create **`perplexity_api_key.txt`** with your key on the first line (no quotes). This file is gitignored.

```
pplx-xxxxxxxxxxxxxxxx
```

### Option C – CLI

```bash
.venv/bin/python Night-Guard-TD/night_guard_perplexity.py /path/to/capture.png --api-key "pplx-xxxx"
```

---

## 4. Run the script

Same pattern as the Gemini version, but call the Perplexity script:

```bash
cd /path/to/Para-Site-Installation
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard_perplexity.py /path/to/capture.png
```

With Epson PDF print:

```bash
TouchDesigner/.venv/bin/python TouchDesigner/Night-Guard-TD/night_guard_perplexity.py /path/to/capture.png --print-epson --font ./Night-Guard-TD/AzeretMono-Variable.ttf
```

---

## 5. Use from TouchDesigner (timer callback)

In your Timer CHOP **onDone** (or wherever you run after capture), call the Perplexity script instead of the Gemini one:

```python
import os
import subprocess

PROJECT_ROOT = parent().par.Projectrootpath.eval()
script = os.path.join(PROJECT_ROOT, "Night-Guard-TD", "night_guard_perplexity.py")
python_exe = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
log_file = os.path.join(PROJECT_ROOT, "Night-Guard-TD", "td_nightguard_log.txt")

# path = full path to the PNG you just saved
cmd = [
    python_exe,
    script,
    path,
    "--print-epson",
    "--font", os.path.join(PROJECT_ROOT, "Night-Guard-TD", "AzeretMono-Variable.ttf"),
]
subprocess.Popen(
    cmd,
    cwd=PROJECT_ROOT,
    stdout=open(log_file, "a"),
    stderr=subprocess.STDOUT,
    shell=False,
)
```

Ensure **PERPLEXITY_API_KEY** is set in the environment that TouchDesigner uses (e.g. launch from a shell that has it, or set in TD’s environment).

---

## 6. Optional: change model

Default is **`openai/gpt-4o-mini`** (vision-capable, good balance of cost and quality). Override with:

- Env: `export PERPLEXITY_MODEL="openai/gpt-4o"`
- CLI: `--model openai/gpt-4o`

See [Agent API – Models](https://docs.perplexity.ai/docs/agent-api/models) for vision-capable options.

---

## 7. Summary

| Step | Action |
|------|--------|
| 1 | Get API key from [Perplexity API](https://www.perplexity.ai/settings/api). |
| 2 | `pip install perplexityai` in your venv. |
| 3 | Set **PERPLEXITY_API_KEY** or put key in **`perplexity_api_key.txt`** (first line). |
| 4 | Run `night_guard_perplexity.py <image>` or call it from TouchDesigner as above. |

Output is the same as with Gemini: log text in **`exhibition_archive_log.txt`**, and optional **`logs/entry_<ts>.txt`** / **`.pdf`** and Epson print.
