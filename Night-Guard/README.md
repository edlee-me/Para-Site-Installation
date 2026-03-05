# A Station That Never Sleeps (展場夜更) - Night Guard System

An autonomous monitoring and generative text system created for the Para Site 30th-anniversary exhibition, *Site-seeing* (2026). 

This Python-based system acts as a phantom "Night Guard." It continuously monitors the exhibition's live CCTV feed and translates the visual data into poetic, hauntological system logs using the Gemini API. These logs process the archival memory of Para Site (1996–2026), capturing the temporal slippage, displacement, and the physical presence of visitors before outputting them to a thermal printer.

## 📂 File Structure
- `night_guard.py`: The core Python script that handles image processing, API calls, and printer simulation.
- `keywords.txt`: A structured vocabulary bank categorizing system terms, spatial materials, and archival chronologies.
- `examples.txt`: Few-shot prompting examples to lock the AI's tone into a cold, factual, yet melancholic state.
- `cctv_sample.jpg`: A placeholder image for system testing.
- `exhibition_archive_log.txt`: The local text file where all generated logs are backed up.

## 🛠️ Setup Instructions (For Technician)

**1. Environment Setup**
Ensure the Mac Mini is running Python 3.10+ and install the required official Google GenAI SDK:
```bash
pip install google-genai pillow
```
