#!/usr/bin/env python3
"""Test Indian language Piper TTS voices."""
import requests
import json

BASE_URL = "http://localhost:8001"

# Test texts for different Indian languages
test_cases = [
    {
        "voice": "hi_IN-pratham-medium",
        "text": "नमस्ते। यह एक परीक्षण है।",
        "lang": "Hindi"
    },
    {
        "voice": "hi_IN-priyamvada-medium",
        "text": "नमस्ते। मैं प्रियमवादा हूँ।",
        "lang": "Hindi (Female)"
    },
    {
        "voice": "hi_IN-rohan-medium",
        "text": "नमस्ते दोस्त। आप कैसे हो?",
        "lang": "Hindi (Rohan)"
    },
    {
        "voice": "te_IN-rama-medium",
        "text": "నమస్కారం. ఇది ఒక పరీక్ష.",
        "lang": "Telugu"
    },
    {
        "voice": "ta_IN-lakshmis-medium",
        "text": "வணக்கம். இது ஒரு சோதனை.",
        "lang": "Tamil"
    },
    {
        "voice": "mr_IN-aniruddh-medium",
        "text": "नमस्कार. हे एक चाचणी आहे.",
        "lang": "Marathi"
    },
]

print("=" * 60)
print("INDIAN LANGUAGE PIPER TTS TEST")
print("=" * 60)

for i, test in enumerate(test_cases, 1):
    voice = test["voice"]
    text = test["text"]
    lang = test["lang"]
    
    print(f"\n{i}. {lang} ({voice})")
    print(f"   Text: {text[:50]}..." if len(text) > 50 else f"   Text: {text}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/tts/sync",
            json={"text": text, "voice": voice},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            duration = data.get("duration", 0)
            engine = data.get("engine", "unknown")
            print(f"   ✓ SUCCESS - Duration: {duration:.2f}s, Engine: {engine}")
            
            # Show audio data size
            if "audio" in data:
                audio_hex = data.get("audio", "")
                audio_bytes = len(audio_hex) // 2
                print(f"   Audio size: {audio_bytes / 1024:.1f} KB")
        else:
            print(f"   ✗ ERROR - Status {response.status_code}")
            print(f"   {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ EXCEPTION: {str(e)}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
