#!/usr/bin/env python3
"""Generate long input texts (2-3 pages) for each voice and convert via /tts/sync.

Usage:
    python backend/scripts/generate_and_convert.py

Outputs saved to `backend/converted_outputs/` and inputs to `backend/test_inputs/`.
"""
import os
import sys
import time
import requests
from pathlib import Path

# Ensure repo root is on sys.path so `backend` package imports work when
# running this script directly from the project root or via CI.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.voice_catalog import list_available_voices

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
INPUT_DIR = Path("backend/test_inputs")
OUTPUT_DIR = Path("backend/converted_outputs")
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Simple generator functions to create ~800-1000 word texts per language.
EN_PARAGRAPH = (
    "This is a sample paragraph intended to form part of a longer document. "
    "It explores the topic in a clear and accessible way, providing examples, "
    "context, and a narrative flow that gradually deepens understanding. "
)

HI_SAMPLE = (
    "यह एक नमूना पैराग्राफ़ है जो एक लंबे दस्तावेज़ का हिस्सा बनने के लिए बनाया गया है। "
    "यह विषय की व्याख्या सरल शब्दों में करता है और उदाहरणों के माध्यम से समझ बढ़ाता है। "
)

# Build a multi-paragraph document of approx 800-1000 words.
def build_text(language_code: str) -> str:
    paras = []
    if language_code.startswith("en"):
        # create ~10-13 paragraphs of 80-100 words
        for i in range(12):
            paras.append(EN_PARAGRAPH * 8 + f"(Section {i+1})\n")
    elif language_code.startswith("hi"):
        for i in range(12):
            paras.append(HI_SAMPLE * 8 + f"(अनुभाग {i+1})\n")
    else:
        # fallback to English-like filler
        for i in range(12):
            paras.append(EN_PARAGRAPH * 8 + f"(Section {i+1})\n")
    return "\n\n".join(paras)


def convert_text(voice_id: str, text: str, out_path: Path) -> bool:
    payload = {"text": text, "voice": voice_id}
    url = f"{BACKEND_URL.rstrip('/')}/tts/sync"
    try:
        resp = requests.post(url, json=payload, timeout=120)
    except Exception as e:
        print(f"Request failed for {voice_id}: {e}")
        return False
    if resp.status_code != 200:
        print(f"Conversion failed for {voice_id}: {resp.status_code} - {resp.text}")
        return False
    out_path.write_bytes(resp.content)
    print(f"Saved: {out_path} ({len(resp.content)} bytes)")
    return True


def main():
    voices = list_available_voices()
    if not voices:
        print("No available voices found in voice_catalog.")
        return
    results = []
    for v in voices:
        vid = v["id"]
        lang = v.get("language", "en_US")
        print(f"\nGenerating input for {vid} ({lang})")
        text = build_text(lang)
        in_file = INPUT_DIR / f"input_{vid}.txt"
        in_file.write_text(text, encoding="utf-8")
        print(f"Wrote input to: {in_file}")
        out_file = OUTPUT_DIR / f"converted_{vid}.wav"
        ok = convert_text(vid, text, out_file)
        results.append((vid, ok, out_file if ok else None))
        time.sleep(1)
    print("\nSummary:")
    for vid, ok, path in results:
        print(f" - {vid}: {'OK' if ok else 'FAILED'}" + (f" -> {path}" if path else ""))

if __name__ == '__main__':
    main()
