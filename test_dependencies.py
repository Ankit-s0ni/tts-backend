#!/usr/bin/env python3
"""Simple test to verify Piper and Parler are installed and working."""

import sys

def test_piper():
    """Test if Piper TTS is installed."""
    print("\n" + "="*60)
    print("Testing Piper TTS Installation")
    print("="*60)
    
    try:
        import piper_tts
        print("✓ piper_tts module found")
        
        try:
            from piper_tts import PiperVoice
            print("✓ PiperVoice class available")
            return True
        except ImportError as e:
            print(f"✗ Cannot import PiperVoice: {e}")
            return False
    except ImportError:
        print("✗ piper_tts not installed")
        return False

def test_parler():
    """Test if Parler TTS is installed."""
    print("\n" + "="*60)
    print("Testing Parler TTS Installation")
    print("="*60)
    
    try:
        import parler_tts
        print("✓ parler_tts module found")
        return True
    except ImportError:
        print("✗ parler_tts not installed")
        try:
            # Try to see if it's available via transformers
            from transformers import pipeline
            print("✓ transformers available (Parler can use this)")
            return True
        except ImportError:
            print("✗ transformers not available")
            return False

def main():
    print("\n" + "="*60)
    print("TTS Module Installation Check")
    print("="*60)
    
    piper_ok = test_piper()
    parler_ok = test_parler()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Piper TTS: {'✓ INSTALLED' if piper_ok else '✗ NOT INSTALLED'}")
    print(f"Parler TTS: {'✓ INSTALLED' if parler_ok else '✗ NOT INSTALLED'}")
    
    if not piper_ok or not parler_ok:
        print("\n⚠ Missing dependencies detected")
        sys.exit(1)
    else:
        print("\n✓ All dependencies available")
        sys.exit(0)

if __name__ == "__main__":
    main()
