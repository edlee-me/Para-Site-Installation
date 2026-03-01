from google import genai
from google.genai import types
from PIL import Image
import time
import sys
import os

# 1. 讀取外部設定檔的函數
def load_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請確認檔案是否存在。")
        sys.exit()

# 讀取剛剛建立的兩個 txt 檔案
keywords_data = load_text_file("keywords.txt")
examples_data = load_text_file("examples.txt")

# 2. 組合 System Prompt (將變數動態塞入)
system_instruction = f"""
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

# 3. 模擬熱敏印表機輸出的函數
def simulate_thermal_printer(text):
    print("\n" + "="*40)
    print("🖨️  模擬熱敏印表機啟動中...")
    print("="*40 + "\n")
    
    # 逐行印出，模擬機械吐紙的物理延遲感
    lines = text.split('\n')
    for line in lines:
        print(line)
        time.sleep(0.6) # 每行停頓 0.6 秒
        
    print("\n" + "="*40)
    print("🖨️  列印完成。")
    print("="*40 + "\n")
    
    # 同時將生成的日誌寫入本地檔案，作為數位備份
    with open("exhibition_archive_log.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

# 4. 主程式區塊
def main():
    # 請記得換回你的真實 API Key
    client = genai.Client(api_key="AIzaSyDSId5qVigEBx8DsbRVAVPwtPfNIBh1RG4")

    image_path = "Screenshot 2026-02-27 at 14.38.26.png"
    try:
        cctv_image = Image.open(image_path)
    except FileNotFoundError:
        print(f"找不到圖片：{image_path}，請確認檔名與路徑。")
        return

    print("系統運作中，正在分析監控畫面...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=["Please generate a system log based on this CCTV feed.", cctv_image],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.5,
        )
    )

    clean_text = response.text.strip()
    
    # 呼叫模擬印表機函數
    simulate_thermal_printer(clean_text)

if __name__ == "__main__":
    main()