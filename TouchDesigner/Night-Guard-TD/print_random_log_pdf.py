"""
Print a random PDF from the logs folder (e.g. Night-Guard-TD/logs).
For use from TouchDesigner: run with project venv Python, cwd = project root.

  .venv/bin/python Night-Guard-TD/print_random_log_pdf.py [--print-epson] [--no-rotate-180] [--printer NAME]
"""

import argparse
import os
import random
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")


def _rotate_pdf_180(pdf_path, output_path=None):
    """Rotate all pages of a PDF 180 degrees. Requires pypdf.
    If output_path is None, rotate in place. Otherwise write to output_path (e.g. temp file).
    Returns output_path or pdf_path on success, None on failure.
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("Rotation skipped: install pypdf (pip install pypdf)", file=sys.stderr)
        return None
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
            writer.pages[-1].rotate(180)
        dest = output_path if output_path else pdf_path
        if not output_path:
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
        else:
            with open(dest, "wb") as f:
                writer.write(f)
        print("PDF rotated 180°: {}".format(dest))
        return dest
    except Exception as e:
        print("PDF rotation failed: {}".format(e), file=sys.stderr)
        return None


def _lp_epson_pdf(pdf_path, orientation="portrait", media="Custom.241x90mm", resolution="360dpi", printer="EPSON_LQ_635K", wait=False):
    opts = [
        "lp", "-d", printer,
        "-o", "fit-to-page", "-o", "media=Custom.241x90mm",
    ]
    if resolution:
        opts.extend(["-o", "resolution={}".format(resolution)])
    # if orientation and orientation.lower() == "landscape":
    #     opts.extend(["-o", "landscape"])
    else:
        opts.extend(["-o", "portrait"])
    opts.append(pdf_path)
    if wait:
        subprocess.run(opts, check=False)
    else:
        subprocess.Popen(opts)


def main():
    parser = argparse.ArgumentParser(description="Pick a random PDF from logs and print it.")
    parser.add_argument(
        "--logs-dir",
        default=DEFAULT_LOGS_DIR,
        help="Folder containing entry_*.pdf files. Default: Night-Guard-TD/logs.",
    )
    parser.add_argument(
        "--print-epson",
        action="store_true",
        help="Send to Epson printer (EPSON_LQ_635K) via lp.",
    )
    parser.add_argument(
        "--printer", "-p",
        default="EPSON_LQ_635K",
        help="Printer name for lp -d. Default: EPSON_LQ_635K.",
    )
    parser.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="Print orientation.",
    )
    parser.add_argument(
        "--media",
        default="A4",
        help="Media size for lp -o media=.",
    )
    parser.add_argument(
        "--rotate-180",
        dest="rotate_180",
        action="store_true",
        default=True,
        help="Rotate the PDF 180° before printing (default).",
    )
    parser.add_argument(
        "--no-rotate-180",
        dest="rotate_180",
        action="store_false",
        help="Do not rotate the PDF before printing.",
    )
    args = parser.parse_args()

    logs_dir = os.path.abspath(args.logs_dir)

    if not os.path.isdir(logs_dir):
        print("Error: logs directory not found: {}".format(logs_dir), file=sys.stderr)
        return 1

    # Only pick from log-entry PDFs (entry_*.pdf), not rule_*.pdf or others
    pdfs = [f for f in os.listdir(logs_dir) if f.lower().endswith(".pdf") and f.startswith("entry_")]
    if not pdfs:
        print("Error: no entry_*.pdf files in {}".format(logs_dir), file=sys.stderr)
        return 1

    chosen = random.choice(pdfs)
    pdf_path = os.path.join(logs_dir, chosen)
    to_print = pdf_path
    temp_rotated = None

    if args.print_epson and args.rotate_180:
        temp_rotated = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        result = _rotate_pdf_180(pdf_path, output_path=temp_rotated)
        if result:
            to_print = result
        else:
            if temp_rotated and os.path.isfile(temp_rotated):
                try:
                    os.unlink(temp_rotated)
                except Exception:
                    pass
            return 1

    if args.print_epson:
        try:
            # When printing a temp (rotated) file, wait for lp to finish so we don't delete it before lp reads it
            _lp_epson_pdf(
                to_print,
                orientation=args.orientation,
                media=args.media,
                resolution="360dpi",
                printer=args.printer,
                wait=(temp_rotated is not None),
            )
            print("Printing: {}".format(chosen))
        except Exception as e:
            print("Error printing: {}".format(e), file=sys.stderr)
            if temp_rotated and os.path.isfile(temp_rotated):
                try:
                    os.unlink(temp_rotated)
                except Exception:
                    pass
            return 1
        finally:
            if temp_rotated and os.path.isfile(temp_rotated):
                try:
                    os.unlink(temp_rotated)
                except Exception:
                    pass
    else:
        print("Selected (not printing): {}".format(pdf_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
