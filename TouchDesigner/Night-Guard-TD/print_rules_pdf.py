"""
Generate PDFs from rule_1.txt through rule_5.txt and print each to the Epson (one by one).
Uses night_guard_perplexity.py --pdf-only with --print-epson --print-epson-rotate-180.

Run from project root:
  .venv/bin/python TouchDesigner/Night-Guard-TD/print_rules_pdf.py [--no-print]
"""

import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Project root: parent of TouchDesigner
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

RULES = ["rule_1.txt", "rule_2.txt", "rule_3.txt", "rule_4.txt", "rule_5.txt"]


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF from each rule_N.txt and print to Epson (one by one)."
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Generate PDFs only, do not send to printer.",
    )
    parser.add_argument(
        "--project-root",
        default=PROJECT_ROOT,
        help="Project root (default: parent of TouchDesigner).",
    )
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)
    python_exe = os.path.join(project_root, ".venv", "bin", "python")
    night_guard_script = os.path.join(project_root, "TouchDesigner", "Night-Guard-TD", "night_guard_perplexity.py")
    logs_dir = os.path.join(project_root, "TouchDesigner", "Night-Guard-TD", "logs")
    font_path = os.path.join(project_root, "TouchDesigner", "Night-Guard-TD", "AzeretMono-Variable.ttf")

    if not os.path.isfile(python_exe):
        print("Error: venv Python not found:", python_exe, file=sys.stderr)
        return 1
    if not os.path.isfile(night_guard_script):
        print("Error: night_guard_perplexity.py not found:", night_guard_script, file=sys.stderr)
        return 1
    if not os.path.isdir(logs_dir):
        print("Error: logs dir not found:", logs_dir, file=sys.stderr)
        return 1

    print_opt = [] if args.no_print else ["--print-epson", "--print-epson-rotate-180"]
    cmd_base = [
        python_exe,
        night_guard_script,
        "--pdf-only",
        None,  # path to rule_N.txt
        "--font",
        font_path,
    ] + print_opt

    for name in RULES:
        rule_path = os.path.join(logs_dir, name)
        if not os.path.isfile(rule_path):
            print("Skip (not found):", rule_path)
            continue
        cmd = cmd_base.copy()
        cmd[3] = rule_path
        print("---", name, "---")
        ret = subprocess.run(cmd, cwd=project_root)
        if ret.returncode != 0:
            print("Failed:", name, "return code", ret.returncode, file=sys.stderr)
            return ret.returncode
        print("Done:", name)

    print("All rules done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
