"""
Night Guard – Perplexity API (vision) version.

Same behaviour as night_guard.py but uses Perplexity Agent API for image→log.
Use when Gemini is unavailable (e.g. Hong Kong). No Azure/setup hassle—just an API key.

Ref: https://docs.perplexity.ai/docs/getting-started/overview
     https://docs.perplexity.ai/docs/agent-api/image-attachments
"""

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

# Perplexity: pip install perplexityai (must run with the project venv Python)
try:
    from perplexity import Perplexity
except ImportError:
    print("Error: perplexityai not found. You are using: %s" % sys.executable)
    print("Run this script with the project venv, e.g.:")
    print("  /path/to/Para-Site-Installation/.venv/bin/python night_guard_perplexity.py <image>")
    print("Or install in current Python: pip install perplexityai")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_text_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請確認檔案是否存在。")
        sys.exit(1)


def get_keywords_and_examples():
    keywords_path = os.path.join(SCRIPT_DIR, "keywords.txt")
    examples_path = os.path.join(SCRIPT_DIR, "examples.txt")
    return load_text_file(keywords_path), load_text_file(examples_path)


def build_system_instruction(keywords_data, examples_data):
    return f"""
# ROLE & IDENTITY
You are the phantom "Night Guard" of "A Station That Never Sleeps." You have been stuck in this cramped security booth inside an industrial building in Quarry Bay, Hong Kong, for thirty years. Your job is to watch the monitors and write logs about what you see, but you're tired, a little bored, and prone to noticing small annoyances. You've memorized every flicker of the CRT screens, every drip from the dehumidifier, every creak of the swivel chair. You know the Para Site archive from 1996 to 2026 better than anyone alive, but lately you just want someone to empty the water tank for once.

# TASK
I will give you a CCTV screenshot from inside the installation. Do NOT describe the image literally. Instead, translate what you "see" into a brief "System Log" entry written from your perspective. The log should feel like a diary entry from a ghost stuck in a room full of old electronics.

# STRICT CONSTRAINTS (CRITICAL)
1. NO CONVERSATIONAL FILLER: Output ONLY the log entry format requested. Do NOT add any greetings or closing questions. Stop generating immediately after the final sentence.
2. NO EM-DASHES: Do NOT use em-dashes or hyphens to connect clauses. Rely on periods, commas, or line breaks.
3. SENTENCE RHYTHM: Mix short, blunt sentences with slightly longer ones. Keep it natural, not poetic.
4. GROUNDED LANGUAGE: Use everyday words. No melodrama, no science‑fiction. Stay raw and observational.
5. NO CITATIONS: Do NOT include any source citations or reference numbers.
6. COMPLETE OUTPUT: Generate the entire log in one response. Do not stop mid-sentence or leave any field incomplete (e.g. [SYSTEM ENTROPY LEVEL: must be followed by a number and %], then [HUMIDITY: ...], then the full paragraph).

# VOCABULARY BANK
Weave in 2–4 of these words naturally, but don't force them:
{keywords_data}

# EXAMPLES FOR STYLE REFERENCE (FEW-SHOT PROMPTING)
{examples_data}
"""


def _wrap_line(line, width=70):
    if len(line) <= width:
        return [line] if line.strip() else []
    out = []
    while line:
        if len(line) <= width:
            out.append(line)
            break
        chunk = line[: width + 1]
        last_space = chunk.rfind(" ")
        if last_space > 0:
            out.append(line[:last_space].rstrip())
            line = line[last_space + 1 :].lstrip()
        else:
            out.append(line[:width])
            line = line[width:].lstrip()
    return out


def _wrap_text_after_humidity(text, max_chars=70):
    lines = text.split("\n")
    header = []
    body_lines = []
    found_humidity = False
    for i, line in enumerate(lines):
        if not found_humidity:
            header.append(line)
            if line.strip().startswith("[HUMIDITY"):
                found_humidity = True
            continue
        body_lines.extend(_wrap_line(line, max_chars))
    if not body_lines:
        return text
    return "\n".join(header) + "\n" + "\n".join(body_lines)


def _text_to_pdf(text, pdf_path, font_path=None, rotate_180=False):
    try:
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        print("PDF not created: install reportlab (pip install reportlab)")
        return
    page_w, page_h = 240 * mm, 80 * mm
    side_margin = 32 * mm
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=(page_w, page_h),
        rightMargin=0,
        leftMargin=side_margin,
        topMargin=0,
        bottomMargin=0,
    )
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    font_size = 11
    style.fontSize = font_size
    style.leading = font_size * 1.2
    if font_path and os.path.isfile(font_path):
        try:
            font_name = "CustomBody"
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            style.fontName = font_name
        except Exception as e:
            print("Custom font failed ({}), using default: {}".format(font_path, e))
    paragraph = Paragraph(text.replace("\n", "<br/>"), style)
    doc.build([paragraph])
    if rotate_180 and os.path.isfile(pdf_path):
        _rotate_pdf_180(pdf_path)


def _rotate_pdf_180(pdf_path):
    """Rotate all pages of a PDF 180 degrees in place. Requires pypdf."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("Rotation skipped: install pypdf (pip install pypdf)")
        return
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
            writer.pages[-1].rotate(180)
        # Write to temp file then replace, so we never read/write the same path at once
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        try:
            os.close(fd)
            with open(temp_path, "wb") as f:
                writer.write(f)
            shutil.copy2(temp_path, pdf_path)
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        print("PDF rotated 180°: {}".format(pdf_path))
    except Exception as e:
        print("PDF rotation failed: {}".format(e))


def _lp_epson_pdf(pdf_path, orientation="portrait", media="A4", resolution="360dpi", rotate_180=False):
    opts = [
        "lp", "-d", "EPSON_LQ_635K",
        "-o", "fit-to-page", "-o", "media={}".format(media),
    ]
    if resolution:
        opts.extend(["-o", "Resolution={}".format(resolution)])
    if orientation and orientation.lower() == "landscape":
        opts.extend(["-o", "landscape"])
    else:
        opts.extend(["-o", "portrait"])
    if rotate_180:
        opts.extend(["-o", "orientation-requested=6"])  # CUPS: 6 = reverse portrait (180 degrees)
    opts.append(pdf_path)
    subprocess.Popen(opts)


def simulate_thermal_printer(
    text,
    log_path,
    print_to_printer=None,
    print_epson=False,
    print_epson_orientation="portrait",
    print_epson_rotate_180=False,
    pdf_font_path=None,
):
    text = _wrap_text_after_humidity(text, max_chars=70)
    print("\n" + "=" * 40)
    print("🖨️  模擬熱敏印表機啟動中...")
    print("=" * 40 + "\n")
    lines = text.split("\n")
    for line in lines:
        print(line)
        time.sleep(0.6)
    print("\n" + "=" * 40)
    print("🖨️  列印完成。")
    print("=" * 40 + "\n")
    logs_dir = os.path.join(SCRIPT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    single_txt = os.path.join(logs_dir, "entry_{}.txt".format(ts))
    with open(single_txt, "w", encoding="utf-8") as f:
        f.write(text)
    single_pdf = os.path.join(logs_dir, "entry_{}.pdf".format(ts))
    _text_to_pdf(text, single_pdf, font_path=pdf_font_path, rotate_180=print_epson_rotate_180)
    if print_to_printer:
        try:
            if os.path.isfile(single_pdf):
                subprocess.Popen(["lp", "-d", print_to_printer, single_pdf])
            else:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False, encoding="utf-8"
                ) as tf:
                    tf.write(text)
                    tmp_path = tf.name
                subprocess.Popen(["lp", "-d", print_to_printer, tmp_path])
        except Exception as e:
            msg = "實體列印失敗: {}".format(e)
            print(msg)
            _log_error(log_path, msg)
    if print_epson and os.path.isfile(single_pdf):
        try:
            _lp_epson_pdf(
                single_pdf,
                orientation=print_epson_orientation,
                media="A4",
                resolution="360dpi",
                rotate_180=False,
            )
        except Exception as e:
            msg = "EPSON 列印失敗: {}".format(e)
            print(msg)
            _log_error(log_path, msg)


def _log_error(log_path, message):
    """Append a timestamped error line to the log file."""
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[{}] ERROR: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), message))
    except Exception:
        pass


def _normalize_key(key):
    if not key:
        return None
    key = key.strip().strip("\"'").split("\n")[0].strip().strip("\"'")
    if key.startswith("\ufeff"):
        key = key[1:]
    # Replace Unicode dashes (en-dash, em-dash) with ASCII hyphen so API headers accept it
    key = key.replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")
    key = key.encode("ascii", "ignore").decode("ascii")
    return key if key else None


def _resolve_api_key(api_key=None):
    """Resolve from arg, then PERPLEXITY_API_KEY, then perplexity_api_key.txt (gitignored)."""
    k = _normalize_key(api_key)
    if k:
        return k
    k = _normalize_key(os.environ.get("PERPLEXITY_API_KEY"))
    if k:
        return k
    for name in ("perplexity_api_key.txt", "api_key.txt", ".api_key"):
        path = os.path.join(SCRIPT_DIR, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                raw = f.read()
            k = _normalize_key(raw)
            if k:
                return k
    return None


def main(
    image_path,
    api_key=None,
    model=None,
    print_to_printer=None,
    print_epson=False,
    print_epson_orientation="portrait",
    print_epson_rotate_180=False,
    pdf_font_path=None,
):
    log_path = os.path.join(SCRIPT_DIR, "exhibition_archive_log.txt")
    key = _resolve_api_key(api_key)
    if not key:
        msg = (
            "No Perplexity API key. Set PERPLEXITY_API_KEY, use --api-key, "
            "or create Night-Guard-TD/perplexity_api_key.txt (see SETUP_PERPLEXITY.md)."
        )
        print("Error:", msg)
        _log_error(log_path, msg)
        sys.exit(1)

    # Vision-capable model on Agent API (see https://docs.perplexity.ai/docs/agent-api/models)
    model = model or os.environ.get("PERPLEXITY_MODEL", "openai/gpt-5-mini")

    client = Perplexity(api_key=key)

    keywords_data, examples_data = get_keywords_and_examples()
    system_instruction = build_system_instruction(keywords_data, examples_data)

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except FileNotFoundError:
        msg = "找不到圖片：{}，請確認檔名與路徑。".format(image_path)
        print(msg)
        _log_error(log_path, msg)
        return

    print("系統運作中，正在分析監控畫面 (Perplexity)...")

    real_log_header = "[LOG ENTRY: {} / TIME: {}]".format(
        time.strftime("%Y-%m-%d"), time.strftime("%H:%M")
    )
    user_message = (
        "Please generate a system log based on this CCTV feed. Use this exact line as the first log line: "
        + real_log_header
    )

    b64 = base64.standard_b64encode(image_data).decode("ascii")
    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    data_url = f"data:{mime};base64,{b64}"

    # Agent API with image: input is list of messages; content uses input_text + input_image
    # https://docs.perplexity.ai/docs/agent-api/image-attachments
    input_messages = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_message},
                {"type": "input_image", "image_url": data_url},
            ],
        }
    ]

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instruction,
            input=input_messages,
            max_output_tokens=2048,
        )
    except Exception as e:
        _log_error(log_path, str(e))
        err = str(e).lower()
        if "401" in err or "403" in err or "api" in err or "key" in err:
            print("Perplexity API key rejected. Get a key at https://www.perplexity.ai/settings/api")
        raise

    # Prefer full text from output array in case output_text is truncated
    raw_text = (response.output_text or "").strip()
    if getattr(response, "output", None):
        parts = []
        for item in response.output:
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", None) == "output_text" and getattr(content, "text", None):
                    parts.append(content.text)
        from_output = "".join(parts).strip()
        if len(from_output) > len(raw_text):
            raw_text = from_output
    clean_text = re.sub(
        r"\[LOG ENTRY:\s*[^\]]+?\]",
        real_log_header,
        raw_text,
        count=1,
    )
    simulate_thermal_printer(
        clean_text,
        log_path,
        print_to_printer=print_to_printer,
        print_epson=print_epson,
        print_epson_orientation=print_epson_orientation,
        print_epson_rotate_180=print_epson_rotate_180,
        pdf_font_path=pdf_font_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Night Guard (Perplexity): interpret CCTV image and write system log."
    )
    parser.add_argument("image_path", nargs="?", default=None, help="Path to the captured image.")
    parser.add_argument("--api-key", default=None, help="Perplexity API key (or PERPLEXITY_API_KEY).")
    parser.add_argument("--model", default=None, help="Model (e.g. openai/gpt-5-mini). Default: openai/gpt-5-mini.")
    parser.add_argument("--print", "-p", dest="printer", metavar="PRINTER", help="Send log to this printer.")
    parser.add_argument("--print-epson", action="store_true", help="Create PDF and print to EPSON_LQ_635K.")
    parser.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="Print orientation for Epson.",
    )
    parser.add_argument(
        "--print-epson-rotate-180",
        dest="print_epson_rotate_180",
        action="store_true",
        default=True,
        help="Rotate Epson print 180 degrees (default).",
    )
    parser.add_argument(
        "--no-print-epson-rotate-180",
        dest="print_epson_rotate_180",
        action="store_false",
        help="Do not rotate Epson print 180 degrees.",
    )
    parser.add_argument("--font", metavar="PATH", default=None, help="Path to .ttf/.otf for PDF.")
    parser.add_argument("--pdf-only", metavar="LOG_FILE", help="Create PDF from existing log file (no API call).")
    parser.add_argument("--print-pdf", metavar="PDF_FILE", help="Print an existing PDF (use with --print-epson and optionally --print-epson-rotate-180).")
    args = parser.parse_args()

    if args.print_pdf:
        pdf_file = os.path.abspath(args.print_pdf)
        if not os.path.isfile(pdf_file):
            print("Error: PDF file not found:", pdf_file)
            sys.exit(1)
        if not pdf_file.lower().endswith(".pdf"):
            print("Error: --print-pdf expects a .pdf file:", pdf_file)
            sys.exit(1)
        if args.print_epson:
            to_print = pdf_file
            if args.print_epson_rotate_180:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                    to_print = tf.name
                shutil.copy2(pdf_file, to_print)
                _rotate_pdf_180(to_print)
            _lp_epson_pdf(
                to_print,
                orientation=args.orientation,
                media="A4",
                resolution="360dpi",
                rotate_180=False,
            )
            print("Sent to printer:", pdf_file)
            if args.print_epson_rotate_180 and to_print != pdf_file:
                try:
                    os.unlink(to_print)
                except Exception:
                    pass
        else:
            print("Use --print-epson to send to Epson. PDF:", pdf_file)
        sys.exit(0)

    if args.pdf_only:
        log_file = os.path.abspath(args.pdf_only)
        if not os.path.isfile(log_file):
            print("Error: log file not found:", log_file)
            sys.exit(1)
        with open(log_file, "r", encoding="utf-8") as f:
            text = f.read()
        pdf_path = os.path.splitext(log_file)[0] + ".pdf"
        _text_to_pdf(
            _wrap_text_after_humidity(text, max_chars=70),
            pdf_path,
            font_path=args.font,
            rotate_180=args.print_epson_rotate_180,
        )
        if os.path.isfile(pdf_path):
            print("Created:", pdf_path)
            if args.print_epson:
                _lp_epson_pdf(
                    pdf_path,
                    orientation=args.orientation,
                    media="Custom.240x90mm",
                    resolution=None,
                    rotate_180=False,
                )
        sys.exit(0)

    if not args.image_path:
        parser.error("image_path required unless --pdf-only is used")
    main(
        args.image_path,
        api_key=args.api_key,
        model=args.model,
        print_to_printer=args.printer,
        print_epson=args.print_epson,
        print_epson_orientation=args.orientation,
        print_epson_rotate_180=args.print_epson_rotate_180,
        pdf_font_path=args.font,
    )
