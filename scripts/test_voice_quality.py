#!/usr/bin/env python3
"""Quick test to verify voice quality and distinctness.

Tests the same text in English and Hindi with all 3 voices.
"""
import requests
import json
from pathlib import Path

BACKEND_URL = "http://localhost:8001"
OUTPUT_DIR = Path("backend/test_outputs/quality_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def test_voice(voice_id: str, text: str, filename: str):
    """Test a single voice with given text."""
    print(f"\n{'='*70}")
    print(f"Testing: {voice_id}")
    print(f"Text: {text[:50]}...")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/tts/sync",
            json={"text": text, "voice": voice_id},
            timeout=30
        )
        
        if response.status_code == 200:
            output_path = OUTPUT_DIR / filename
            output_path.write_bytes(response.content)
            size = len(response.content)
            print(f"✅ SUCCESS: Generated {size:,} bytes")
            print(f"📁 Saved to: {output_path}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("="*70)
    print("  Voice Quality Test Suite")
    print("="*70)
    print("ℹ️  This test uses the SAME text with all 3 voices to verify")
    print("ℹ️  that each voice produces distinct and correct audio.\n")
    
    # Test 1: English text with English voice (should be perfect)
    print("\n🔵 TEST 1: English text with English voice (baseline)")
    test_voice(
        "en_US-lessac-medium",
        "Hello! This is a test of the English voice model. The quick brown fox jumps over the lazy dog.",
        "quality_english_lessac.wav"
    )
    
    # Test 2: Hindi text with Hindi Rohan voice
    print("\n🔵 TEST 2: Hindi text with Hindi Rohan voice")
    test_voice(
        "hi_IN-rohan-medium",
        "नमस्ते! यह हिंदी आवाज़ मॉडल का एक परीक्षण है। यह रोहन की आवाज़ है।",
        "quality_hindi_rohan.wav"
    )
    
    # Test 3: Hindi text with Hindi Priyamvada voice
    print("\n🔵 TEST 3: Hindi text with Hindi Priyamvada voice")
    test_voice(
        "hi_IN-priyamvada-medium",
        "नमस्ते! यह हिंदी आवाज़ मॉडल का एक परीक्षण है। यह प्रियम्वदा की आवाज़ है।",
        "quality_hindi_priyamvada.wav"
    )
    
    # Test 4: Same English text with Hindi voice (to verify it's NOT using English model)
    print("\n🔵 TEST 4: English text with Hindi Rohan voice (should sound different/accented)")
    test_voice(
        "hi_IN-rohan-medium",
        "Hello! This is a test of the Hindi voice model speaking English text.",
        "quality_english_with_rohan.wav"
    )
    
    print("\n" + "="*70)
    print("✅ Quality test complete!")
    print(f"📁 All files saved to: {OUTPUT_DIR}")
    print("\n🎧 Listen to the files to verify:")
    print("   1. quality_english_lessac.wav - Should be clear English")
    print("   2. quality_hindi_rohan.wav - Should be Hindi (male voice)")
    print("   3. quality_hindi_priyamvada.wav - Should be Hindi (female voice)")
    print("   4. quality_english_with_rohan.wav - English with Hindi accent")
    print("="*70)

if __name__ == "__main__":
    main()
