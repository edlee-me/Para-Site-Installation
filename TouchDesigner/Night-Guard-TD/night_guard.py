from google import genai
from google.genai import types
from PIL import Image
import time
import sys
import os
import re
import argparse
import subprocess

# Base directory: where this script lives (so it works when run from TouchDesigner or any cwd)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# 1. 讀取外部設定檔的函數
def load_text_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請確認檔案是否存在。")
        sys.exit()


def get_keywords_and_examples():
    keywords_path = os.path.join(SCRIPT_DIR, "keywords.txt")
    examples_path = os.path.join(SCRIPT_DIR, "examples.txt")
    return load_text_file(keywords_path), load_text_file(examples_path)


# 2. 組合 System Prompt (將變數動態塞入)
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

# VOCABULARY BANK
Weave in 2–4 of these words naturally, but don't force them:
{keywords_data}

# EXAMPLES FOR STYLE REFERENCE (FEW-SHOT PROMPTING)
{examples_data}
"""


def _wrap_line(line, width=70):
    """Word-wrap a single line to max `width` chars; returns list of lines."""
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
    """Split text at [HUMIDITY ...]; wrap the rest (body) to max_chars per line."""
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


def _text_to_pdf(text, pdf_path, font_path=None):
    """Create a one-page PDF from the text string (240x80mm, 14pt, line height 1.5). font_path: optional .ttf/.otf for custom font."""
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
    margin = 5 * mm
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=(page_w, page_h),
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    font_size = 11
    style.fontSize = font_size
    style.leading = font_size * 1.2  # line height 1.5
    if font_path and os.path.isfile(font_path):
        try:
            font_name = "CustomBody"
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            style.fontName = font_name
        except Exception as e:
            print("Custom font failed ({}), using default: {}".format(font_path, e))
    # Preserve line breaks; Paragraph uses <br/> for newlines
    paragraph = Paragraph(text.replace("\n", "<br/>"), style)
    doc.build([paragraph])


def _lp_epson_pdf(pdf_path, orientation="portrait", media="A4", resolution="360dpi"):
    """Send PDF to EPSON_LQ_635K. orientation: 'portrait' or 'landscape'."""
    opts = [
        "lp",
        "-d",
        "EPSON_LQ_635K",
        "-o",
        "fit-to-page",
        "-o",
        "media={}".format(media),
    ]
    if resolution:
        opts.extend(["-o", "Resolution={}".format(resolution)])
    if orientation and orientation.lower() == "landscape":
        opts.extend(["-o", "landscape"])
    else:
        opts.extend(["-o", "portrait"])
    opts.append(pdf_path)
    subprocess.Popen(opts)


# 3. 模擬熱敏印表機輸出 + 寫入日誌 + 可選真實列印
def simulate_thermal_printer(
    text,
    log_path,
    print_to_printer=None,
    print_epson=False,
    print_epson_orientation="portrait",
    pdf_font_path=None,
):
    text = _wrap_text_after_humidity(text, max_chars=70)
    print("\n" + "=" * 40)
    print("🖨️  模擬熱敏印表機啟動中...")
    print("=" * 40 + "\n")

    # 逐行印出，模擬機械吐紙的物理延遲感
    lines = text.split("\n")
    for line in lines:
        print(line)
        time.sleep(0.6)  # 每行停頓 0.6 秒

    print("\n" + "=" * 40)
    print("🖨️  列印完成。")
    print("=" * 40 + "\n")

    # 將生成的日誌寫入本地檔案，作為數位備份
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

    # 將此則 log 文字單獨存成一個檔案（一個 capture 一個檔）
    logs_dir = os.path.join(SCRIPT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    single_txt = os.path.join(logs_dir, "entry_{}.txt".format(ts))
    with open(single_txt, "w", encoding="utf-8") as f:
        f.write(text)
    # 同則 log 另存為 PDF（由字串直接產生，列印較清晰）
    single_pdf = os.path.join(logs_dir, "entry_{}.pdf".format(ts))
    _text_to_pdf(text, single_pdf, font_path=pdf_font_path)

    # 可選：將文字送到實體熱敏印表機 (macOS lp)。優先送 PDF，若無則送 .txt
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
            print(f"實體列印失敗: {e}")

    # 可選：將 PDF 送到 EPSON_LQ_635K，fit-to-page
    if print_epson and os.path.isfile(single_pdf):
        try:
            _lp_epson_pdf(single_pdf, orientation=print_epson_orientation, media="A4", resolution="360dpi")
        except Exception as e:
            print(f"EPSON 列印失敗: {e}")


def _normalize_key(key):
    """Strip whitespace, newlines, and optional quotes so the key is sent exactly as intended."""
    if not key:
        return None
    key = key.strip().strip("\"'")
    key = key.split("\n")[0].strip().strip("\"'")
    if key.startswith("\ufeff"):
        key = key[1:]
    return key if key else None


def _resolve_api_key(api_key=None):
    """Resolve API key from: argument, GEMINI_API_KEY env, or local api_key.txt (gitignored)."""
    k = _normalize_key(api_key)
    if k:
        return k
    k = _normalize_key(os.environ.get("GEMINI_API_KEY"))
    if k:
        return k
    for name in ("api_key.txt", ".api_key"):
        path = os.path.join(SCRIPT_DIR, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                raw = f.read()
            k = _normalize_key(raw)
            if k:
                return k
    return None


# 4. 主程式區塊 (可從 TouchDesigner 呼叫，傳入 image_path)
def main(
    image_path,
    api_key=None,
    print_to_printer=None,
    print_epson=False,
    print_epson_orientation="portrait",
    pdf_font_path=None,
):
    key = _resolve_api_key(api_key)
    if not key:
        print(
            "Error: No Gemini API key. Set GEMINI_API_KEY, use --api-key, or create Night-Guard-TD/api_key.txt with your key (see api_key.txt.example)."
        )
        sys.exit(1)
    client = genai.Client(api_key=key)

    keywords_data, examples_data = get_keywords_and_examples()
    system_instruction = build_system_instruction(keywords_data, examples_data)

    try:
        cctv_image = Image.open(image_path)
    except FileNotFoundError:
        print(f"找不到圖片：{image_path}，請確認檔名與路徑。")
        return

    print("系統運作中，正在分析監控畫面...")

    # 真實時間，供 log 標頭使用
    real_log_header = "[LOG ENTRY: {} / TIME: {}]".format(
        time.strftime("%Y-%m-%d"), time.strftime("%H:%M")
    )
    user_message = (
        "Please generate a system log based on this CCTV feed. Use this exact line as the first log line: "
        + real_log_header
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[user_message, cctv_image],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=1.5,
            ),
        )
    except Exception as e:
        err = str(e).lower()
        if (
            "api key" in err
            or "invalid_argument" in err
            or "invalid" in err
            or "401" in err
            or "403" in err
        ):
            print(
                "API key was rejected. Get a valid Gemini key at https://aistudio.google.com/apikey"
            )
            print(
                "Then put it in Night-Guard-TD/api_key.txt (one line, no quotes) or set GEMINI_API_KEY."
            )
        raise

    clean_text = response.text.strip()
    # 將輸出中的 [LOG ENTRY: ... / TIME: ...] 替換為真實時間
    clean_text = re.sub(
        r"\[LOG ENTRY:\s*[^\]]+?\]",
        real_log_header,
        clean_text,
        count=1,
    )
    log_path = os.path.join(SCRIPT_DIR, "exhibition_archive_log.txt")
    simulate_thermal_printer(
        clean_text,
        log_path,
        print_to_printer=print_to_printer,
        print_epson=print_epson,
        print_epson_orientation=print_epson_orientation,
        pdf_font_path=pdf_font_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Night Guard: interpret CCTV image and write system log."
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        default=None,
        help="Path to the captured image (e.g. from TouchDesigner).",
    )
    parser.add_argument(
        "--print",
        "-p",
        dest="printer",
        metavar="PRINTER",
        help="Send the generated log to this printer (e.g. Printer_POS_80).",
    )
    parser.add_argument(
        "--api-key", default=None, help="Gemini API key (or set GEMINI_API_KEY)."
    )
    parser.add_argument(
        "--pdf-only",
        metavar="LOG_FILE",
        help="Create a PDF from an existing log text file. Output: same path with .pdf extension.",
    )
    parser.add_argument(
        "--print-epson",
        action="store_true",
        help="Create PDF and print it to EPSON_LQ_635K with fit-to-page (and --pdf-only: print the created PDF).",
    )
    parser.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="Print orientation for Epson (default: portrait).",
    )
    parser.add_argument(
        "--font",
        metavar="PATH",
        default=None,
        help="Path to a .ttf or .otf font for the generated PDF (uses default if not set).",
    )
    args = parser.parse_args()

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
        )
        if os.path.isfile(pdf_path):
            print("Created:", pdf_path)
            if args.print_epson:
                _lp_epson_pdf(
                    pdf_path,
                    orientation=args.orientation,
                    media="Custom.240x80mm",
                    resolution=None,
                )
        sys.exit(0)

    if not args.image_path:
        parser.error("image_path required unless --pdf-only is used")
    main(
        args.image_path,
        api_key=args.api_key,
        print_to_printer=args.printer,
        print_epson=args.print_epson,
        print_epson_orientation=args.orientation,
        pdf_font_path=args.font,
    )
