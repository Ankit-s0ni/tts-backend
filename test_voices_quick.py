#!/usr/bin/env python3
"""Test script for voice endpoint - check if voices are returned correctly."""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_voices_endpoint():
    """Test the /voices endpoint."""
    print("\n" + "="*60)
    print("Testing /voices Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/voices", timeout=10)
        
        if response.status_code == 200:
            voices = response.json()
            print(f"✓ Got {len(voices)} voices")
            
            # Group by engine
            piper = [v for v in voices if v.get('engine') == 'piper']
            parler = [v for v in voices if v.get('engine') == 'parler']
            
            print(f"\n  Piper voices: {len(piper)}")
            for v in piper[:3]:
                print(f"    - {v['id']} ({v['language']})")
            if len(piper) > 3:
                print(f"    ... and {len(piper)-3} more")
            
            print(f"\n  Parler voices: {len(parler)}")
            for v in parler[:3]:
                print(f"    - {v['id']} ({v['language']})")
            if len(parler) > 3:
                print(f"    ... and {len(parler)-3} more")
                
            return voices
        else:
            print(f"✗ ERROR: Status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return None

def test_piper_short_text():
    """Test Piper with very short text to avoid service issues."""
    print("\n" + "="*60)
    print("Testing Piper TTS - Short Text")
    print("="*60)
    
    text = "Hello world. This is a test."
    voice_id = "en_US-amy-medium"
    
    print(f"Voice: {voice_id}")
    print(f"Text: '{text}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/tts/sync",
            json={"voice": voice_id, "text": text},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS")
            print(f"  Duration: {data['duration']:.2f} seconds")
            print(f"  Engine: {data['engine']}")
            return True
        else:
            print(f"✗ ERROR: Status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return False

def test_parler_short_text():
    """Test Parler with very short text."""
    print("\n" + "="*60)
    print("Testing Parler TTS - Short Text")
    print("="*60)
    
    text = "Namaste. Yeh ek parikshan hai."  # Hindi text
    voice_id = "parler-hi-male"
    
    print(f"Voice: {voice_id}")
    print(f"Text: '{text}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/tts/sync",
            json={"voice": voice_id, "text": text},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS")
            print(f"  Duration: {data.get('duration', 'N/A')}")
            print(f"  Engine: {data.get('engine', 'N/A')}")
            return True
        else:
            print(f"✗ ERROR: Status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("TTS VOICE API - Quick Test")
    print("="*60)
    
    # First check voices
    voices = test_voices_endpoint()
    
    if voices:
        # Test Piper
        piper_ok = test_piper_short_text()
        
        # Test Parler
        parler_ok = test_parler_short_text()
        
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"Voices endpoint: ✓")
        print(f"Piper synthesis: {'✓' if piper_ok else '✗'}")
        print(f"Parler synthesis: {'✓' if parler_ok else '✗'}")

if __name__ == "__main__":
    main()
