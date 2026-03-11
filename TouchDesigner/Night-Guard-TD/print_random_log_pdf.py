"""
Print a random PDF from the logs folder (e.g. Night-Guard-TD/logs).
For use from TouchDesigner: run with project venv Python, cwd = project root.

  .venv/bin/python Night-Guard-TD/print_random_log_pdf.py [--print-epson] [--printer NAME]
"""

import argparse
import os
import random
import subprocess
import sys


def _lp_epson_pdf(pdf_path, orientation="portrait", media="Custom.241x80mm", resolution="360dpi", printer="EPSON_LQ_635K"):
    opts = [
        "lp", "-d", printer,
        "-o", "fit-to-page", "-o", "media=Custom.241x80mm",
    ]
    if resolution:
        opts.extend(["-o", "resolution={}".format(resolution)])
    # if orientation and orientation.lower() == "landscape":
    #     opts.extend(["-o", "landscape"])
    else:
        opts.extend(["-o", "portrait"])
    opts.append(pdf_path)
    print(opts)
    # return
    subprocess.Popen(opts)


def main():
    parser = argparse.ArgumentParser(description="Pick a random PDF from logs and print it.")
    parser.add_argument(
        "--logs-dir",
        default=None,
        help="Folder containing entry_*.pdf files. Default: logs/ next to this script.",
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
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.abspath(args.logs_dir) if args.logs_dir else os.path.join(script_dir, "logs")

    if not os.path.isdir(logs_dir):
        print("Error: logs directory not found: {}".format(logs_dir), file=sys.stderr)
        return 1

    pdfs = [f for f in os.listdir(logs_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        print("Error: no PDF files in {}".format(logs_dir), file=sys.stderr)
        return 1

    chosen = random.choice(pdfs)
    pdf_path = os.path.join(logs_dir, chosen)

    if args.print_epson:
        try:
            _lp_epson_pdf(
                pdf_path,
                orientation=args.orientation,
                media=args.media,
                resolution="360dpi",
                printer=args.printer,
            )
            print("Printing: {}".format(chosen))
        except Exception as e:
            print("Error printing: {}".format(e), file=sys.stderr)
            return 1
    else:
        print("Selected (not printing): {}".format(pdf_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
