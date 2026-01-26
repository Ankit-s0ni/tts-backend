#!/usr/bin/env python3
"""Test Malayalam and Telugu voices"""

import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8001/tts/sync"
OUTPUT_DIR = Path("test_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Test cases with Malayalam and Telugu text
TESTS = [
    {
        "voice": "ml_IN-arjun-medium",
        "text": "നമസ്കാരം, ഞാൻ പ്രസന്നരാണ് നിങ്ങളുമായി സംസാരിക്കാൻ. ഈ മലയാളം സന്ദേശം നിങ്ങൾ കേൾക്കുകയാണ്.",
        "lang": "Malayalam (Male)"
    },
    {
        "voice": "ml_IN-meera-medium",
        "text": "നന്നായി, കൃത്യമായി സംസാരിക്കാൻ എനിക്കാഗ്രഹമുണ്ട്. പ്രകൃതിയുടെ സൗന്ദര്യം നിരവധിയാണ്.",
        "lang": "Malayalam (Female)"
    },
    {
        "voice": "te_IN-maya-medium",
        "text": "నమస్కారం, నేను మీకు ఆశ్చర్యకరమైన టెలుగు శബ్దాన్ని చూపించడానికి ఉత్సాహంగా ఉన్నాను.",
        "lang": "Telugu (Female - Maya)"
    },
    {
        "voice": "te_IN-padmavathi-medium",
        "text": "తెలుగు భాష చాలా సुందరమైనది, సాంస్కృతికంగా గভీరమైనది.",
        "lang": "Telugu (Female - Padmavathi)"
    },
    {
        "voice": "te_IN-venkatesh-medium",
        "text": "నేను సంతోషంగా ఉన్నాను ఈ టెలుగు భాషను మీకు సమర్పించడానికి.",
        "lang": "Telugu (Male - Venkatesh)"
    },
]

def test_voice(voice_id: str, text: str, lang: str) -> bool:
    """Test a single voice"""
    print(f"\n🎤 Testing {lang} ({voice_id})...")
    print(f"   Text: {text[:50]}...")
    
    try:
        start_time = time.time()
        response = requests.post(
            API_URL,
            json={"text": text, "voice": voice_id},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            audio_hex = data.get("audio")
            duration = data.get("duration", 0)
            
            if audio_hex:
                # Convert hex to audio file
                audio_bytes = bytes.fromhex(audio_hex)
                filename = OUTPUT_DIR / f"{voice_id}.wav"
                with open(filename, "wb") as f:
                    f.write(audio_bytes)
                
                print(f"   ✓ Success! Duration: {duration:.2f}s ({len(audio_bytes)} bytes)")
                print(f"   📁 Saved: {filename}")
                return True
            else:
                print(f"   ✗ No audio in response")
                return False
        else:
            print(f"   ✗ API error: {response.status_code}")
            print(f"      {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def main():
    print("🎙️ Testing New Indian Language Voices (Malayalam & Telugu)\n")
    print("="*60)
    
    success = 0
    for test in TESTS:
        if test_voice(test["voice"], test["text"], test["lang"]):
            success += 1
    
    print("\n" + "="*60)
    print(f"✅ {success}/{len(TESTS)} voices tested successfully")
    print(f"📂 Audio files saved to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    main()
