#!/usr/bin/env python3
"""Test script for Piper and Parler TTS voices with long text."""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

# Long text for testing (2-3 pages)
LONG_TEXT = """
The history of artificial intelligence spans several decades and encompasses remarkable innovations. Artificial intelligence has evolved from theoretical concepts to practical applications that transform our daily lives. Machine learning algorithms power recommendation systems, natural language processing, and computer vision applications across industries. Deep neural networks have achieved impressive results in image recognition, language translation, and strategic game playing. The field continues to expand with advances in generative models, reinforcement learning, and autonomous systems.

The impact of AI on society is profound and multifaceted. In healthcare, machine learning assists in disease diagnosis, drug discovery, and personalized treatment planning. Educational platforms leverage AI to provide adaptive learning experiences tailored to individual students. Manufacturing facilities employ AI-powered robots and vision systems to enhance efficiency and precision. Financial institutions use AI algorithms for fraud detection, credit assessment, and algorithmic trading. Natural language processing enables seamless communication across language barriers through real-time translation services.

However, the rise of artificial intelligence also presents significant challenges and ethical considerations. Privacy concerns emerge as AI systems process vast amounts of personal data. Algorithmic bias can perpetuate discrimination in hiring decisions, loan approvals, and criminal justice systems. The automation of jobs raises questions about economic displacement and workforce retraining. Intellectual property rights become complex when AI systems generate creative content. Governance frameworks struggle to keep pace with rapid technological advancement while protecting fundamental human rights and values.

As we navigate the future of artificial intelligence, collaboration between technologists, policymakers, ethicists, and society is essential. Organizations worldwide are developing AI governance frameworks and ethical guidelines. International cooperation on AI standards and safety measures is gaining momentum. Educational institutions are expanding AI literacy programs to prepare the next generation. Investment in responsible AI research focuses on transparency, fairness, and human-centered design. The challenge ahead is ensuring that artificial intelligence benefits all of humanity while minimizing risks and respecting human dignity and autonomy in our increasingly AI-driven world.
"""

def test_piper_voice(voice_id: str, text: str):
    """Test Piper TTS voice."""
    print(f"\n{'='*60}")
    print(f"Testing Piper TTS: {voice_id}")
    print(f"{'='*60}")
    print(f"Text length: {len(text)} characters")
    
    try:
        response = requests.post(
            f"{BASE_URL}/tts/sync",
            json={"voice": voice_id, "text": text},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS")
            print(f"  Duration: {data['duration']:.2f} seconds")
            print(f"  Audio URL: {data['audio_url']}")
            print(f"  Engine: {data['engine']}")
            return True
        else:
            print(f"✗ ERROR: Status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return False

def test_parler_voice(voice_id: str, text: str):
    """Test Parler TTS voice."""
    print(f"\n{'='*60}")
    print(f"Testing Parler TTS: {voice_id}")
    print(f"{'='*60}")
    print(f"Text length: {len(text)} characters")
    
    try:
        response = requests.post(
            f"{BASE_URL}/tts/sync",
            json={"voice": voice_id, "text": text},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS")
            print(f"  Duration: {data.get('duration', 'N/A'):.2f} seconds" if isinstance(data.get('duration'), (int, float)) else f"  Duration: {data.get('duration', 'N/A')}")
            print(f"  Audio URL: {data.get('audio_url', 'N/A')}")
            print(f"  Engine: {data.get('engine', 'N/A')}")
            return True
        else:
            print(f"✗ ERROR: Status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("TTS VOICE API TEST - Piper & Parler")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Text length: {len(LONG_TEXT)} characters")
    
    results = {}
    
    # Test Piper voices (3 different voices)
    piper_voices = [
        "en_US-amy-medium",
        "en_US-lessac-high",
        "en_GB-alan-medium"
    ]
    
    print("\n\n### PIPER TTS TESTS ###")
    results['piper'] = {}
    for voice in piper_voices:
        results['piper'][voice] = test_piper_voice(voice, LONG_TEXT)
    
    # Test Parler voices (3 Indian regional languages)
    parler_voices = [
        "parler-hi-male",      # Hindi
        "parler-ta-female",    # Tamil
        "parler-te-male"       # Telugu
    ]
    
    print("\n\n### PARLER TTS TESTS ###")
    results['parler'] = {}
    for voice in parler_voices:
        results['parler'][voice] = test_parler_voice(voice, LONG_TEXT)
    
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    piper_success = sum(1 for v in results['piper'].values() if v)
    piper_total = len(results['piper'])
    
    parler_success = sum(1 for v in results['parler'].values() if v)
    parler_total = len(results['parler'])
    
    print(f"\nPiper TTS: {piper_success}/{piper_total} voices successful")
    print(f"Parler TTS: {parler_success}/{parler_total} voices successful")
    print(f"\nTotal: {piper_success + parler_success}/{piper_total + parler_total} successful")
    
    if piper_success == piper_total and parler_success == parler_total:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n⚠ Some tests failed - see details above")

if __name__ == "__main__":
    main()
