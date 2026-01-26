#!/usr/bin/env python3
"""Test Hindi and Telugu TTS synthesis with Piper."""
import requests
import json

base_url = "http://localhost:8001"

# Test Hindi
print("=" * 70)
print("Testing Hindi TTS Synthesis")
print("=" * 70)

hindi_voice = "hi_IN-rohan-medium"
hindi_text = "नमस्ते। यह एक परीक्षण है। कृपया सुनें।"  # "Hello. This is a test. Please listen."

print(f"\nVoice: {hindi_voice}")
print(f"Text: {hindi_text}")

response = requests.post(
    f"{base_url}/tts/sync",
    json={"text": hindi_text, "voice": hindi_voice}
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ SUCCESS")
    print(f"  Duration: {result['duration']:.2f} seconds")
    print(f"  Sample size: {len(result.get('audio', '')) // 2} bytes")
    print(f"  Voice: {result['voice_id']}")
else:
    print(f"✗ ERROR: {response.status_code}")
    print(f"  {response.json()}")

# Test Telugu
print("\n" + "=" * 70)
print("Testing Telugu TTS Synthesis")
print("=" * 70)

telugu_voice = "te_IN-rama-medium"
telugu_text = "నమస్కారం. ఇది ఒక పరీక్ష. దయచేసి వినండి."  # "Hello. This is a test. Please listen."

print(f"\nVoice: {telugu_voice}")
print(f"Text: {telugu_text}")

response = requests.post(
    f"{base_url}/tts/sync",
    json={"text": telugu_text, "voice": telugu_voice}
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ SUCCESS")
    print(f"  Duration: {result['duration']:.2f} seconds")
    print(f"  Sample size: {len(result.get('audio', '')) // 2} bytes")
    print(f"  Voice: {result['voice_id']}")
else:
    print(f"✗ ERROR: {response.status_code}")
    print(f"  {response.json()}")

# Test English for comparison
print("\n" + "=" * 70)
print("Testing English TTS Synthesis (for comparison)")
print("=" * 70)

english_voice = "en_US-lessac-medium"
english_text = "Hello world. This is a test of the English voice."

print(f"\nVoice: {english_voice}")
print(f"Text: {english_text}")

response = requests.post(
    f"{base_url}/tts/sync",
    json={"text": english_text, "voice": english_voice}
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ SUCCESS")
    print(f"  Duration: {result['duration']:.2f} seconds")
    print(f"  Sample size: {len(result.get('audio', '')) // 2} bytes")
    print(f"  Voice: {result['voice_id']}")
else:
    print(f"✗ ERROR: {response.status_code}")
    print(f"  {response.json()}")
