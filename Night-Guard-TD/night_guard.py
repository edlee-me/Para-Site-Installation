from google import genai
from google.genai import types
from PIL import Image
import time
import sys
import os
import argparse
import subprocess

# Base directory: where this script lives (so it works when run from TouchDesigner or any cwd)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. 讀取外部設定檔的函數
def load_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
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

# 3. 模擬熱敏印表機輸出 + 寫入日誌 + 可選真實列印
def simulate_thermal_printer(text, log_path, print_to_printer=None):
    print("\n" + "="*40)
    print("🖨️  模擬熱敏印表機啟動中...")
    print("="*40 + "\n")
    
    # 逐行印出，模擬機械吐紙的物理延遲感
    lines = text.split('\n')
    for line in lines:
        print(line)
        time.sleep(0.6)  # 每行停頓 0.6 秒
        
    print("\n" + "="*40)
    print("🖨️  列印完成。")
    print("="*40 + "\n")
    
    # 將生成的日誌寫入本地檔案，作為數位備份
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

    # 可選：將文字送到實體熱敏印表機 (macOS lp)
    if print_to_printer:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
                tf.write(text)
                tmp_path = tf.name
            subprocess.Popen(['lp', '-d', print_to_printer, tmp_path])
            # Temp file left for OS to clean; lp reads it asynchronously
        except Exception as e:
            print(f"實體列印失敗: {e}")

def _normalize_key(key):
    """Strip whitespace, newlines, and optional quotes so the key is sent exactly as intended."""
    if not key:
        return None
    key = key.strip().strip('"\'')
    key = key.split("\n")[0].strip().strip('"\'')
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
def main(image_path, api_key=None, print_to_printer=None):
    key = _resolve_api_key(api_key)
    if not key:
        print("Error: No Gemini API key. Set GEMINI_API_KEY, use --api-key, or create Night-Guard-TD/api_key.txt with your key (see api_key.txt.example).")
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
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=["Please generate a system log based on this CCTV feed.", cctv_image],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=1.5,
            )
        )
    except Exception as e:
        err = str(e).lower()
        if "api key" in err or "invalid_argument" in err or "invalid" in err or "401" in err or "403" in err:
            print("API key was rejected. Get a valid Gemini key at https://aistudio.google.com/apikey")
            print("Then put it in Night-Guard-TD/api_key.txt (one line, no quotes) or set GEMINI_API_KEY.")
        raise

    clean_text = response.text.strip()
    log_path = os.path.join(SCRIPT_DIR, "exhibition_archive_log.txt")
    simulate_thermal_printer(clean_text, log_path, print_to_printer=print_to_printer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Night Guard: interpret CCTV image and write system log.")
    parser.add_argument("image_path", help="Path to the captured image (e.g. from TouchDesigner).")
    parser.add_argument("--print", "-p", dest="printer", metavar="PRINTER",
                        help="Send the generated log to this printer (e.g. Printer_POS_80).")
    parser.add_argument("--api-key", default=None, help="Gemini API key (or set GEMINI_API_KEY).")
    args = parser.parse_args()
    main(args.image_path, api_key=args.api_key, print_to_printer=args.printer)
