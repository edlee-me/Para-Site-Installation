"""Read exhibition_archive_log.txt, split into entries, create one PDF per entry.
Uses same wrap + PDF logic as night_guard_perplexity (no Perplexity import).
Supports custom font via --font or default AzeretMono-Variable.ttf in this folder.
"""
import argparse
import os


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
    for line in lines:
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
    style.fontSize = 11
    style.leading = 11 * 1.2
    if font_path and os.path.isfile(font_path):
        try:
            font_name = "CustomBody"
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            style.fontName = font_name
        except Exception as e:
            print("Custom font failed ({}), using default: {}".format(font_path, e))
    paragraph = Paragraph(text.replace("\n", "<br/>"), style)
    doc.build([paragraph])


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FONT = os.path.join(SCRIPT_DIR, "AzeretMono-Variable.ttf")


def main():
    parser = argparse.ArgumentParser(description="Split exhibition_archive_log.txt and create one PDF per entry.")
    parser.add_argument("--font", "-f", default=DEFAULT_FONT, metavar="PATH", help="Path to .ttf/.otf for PDF. Default: AzeretMono-Variable.ttf in this folder.")
    parser.add_argument("--log", "-l", default=None, help="Path to log file. Default: exhibition_archive_log.txt in this folder.")
    args = parser.parse_args()

    log_path = os.path.abspath(args.log) if args.log else os.path.join(SCRIPT_DIR, "exhibition_archive_log.txt")
    if not os.path.isfile(log_path):
        print("Error: log file not found:", log_path)
        return 1

    font_path = os.path.abspath(args.font) if args.font else None
    if font_path and not os.path.isfile(font_path):
        print("Warning: font not found:", font_path, "(using default)")
        font_path = None

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("\n\n[LOG ENTRY:")
    entries = []
    if content.strip().startswith("[LOG ENTRY:"):
        entries.append(parts[0].strip())
    for p in parts[1:]:
        entries.append(("[LOG ENTRY:" + p).strip())

    logs_dir = os.path.join(SCRIPT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    for i, text in enumerate(entries):
        if not text.strip():
            continue
        wrapped = _wrap_text_after_humidity(text, max_chars=70)
        pdf_path = os.path.join(logs_dir, "entry_{:03d}.pdf".format(i + 1))
        _text_to_pdf(wrapped, pdf_path, font_path=font_path)
        print("Created", pdf_path)

    print("Done. {} PDFs in {}".format(len(entries), logs_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
