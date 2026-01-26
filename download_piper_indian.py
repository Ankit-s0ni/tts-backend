#!/usr/bin/env python3
"""Download Indian regional language voices from Piper on Hugging Face"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "rhasspy/piper-voices"
VOICES_DIR = Path(__file__).parent / "piper_models"

# Define Indian language voices available in Piper
INDIAN_VOICES = {
    "Malayalam": {
        "ml_IN-arjun": "Medium",
        "ml_IN-meera": "Medium",
    },
    "Telugu": {
        "te_IN-maya": "Medium",
        "te_IN-padmavathi": "Medium",
        "te_IN-venkatesh": "Medium",
    },
}

def download_voice(language_code: str, voice_name: str, quality: str = "medium") -> bool:
    """Download a single voice model from Hugging Face.
    
    Args:
        language_code: e.g., "ml_IN" or "te_IN"
        voice_name: e.g., "arjun" or "maya"
        quality: e.g., "medium" or "high"
    
    Returns:
        True if successful, False otherwise
    """
    # Create directory for voice
    voice_dir = VOICES_DIR / f"{language_code}-{voice_name}-{quality}"
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    # Build Hugging Face path
    # Path format: ml/ml_IN/arjun/medium/ml_IN-arjun-medium.onnx
    hf_path = f"{language_code.split('_')[0]}/{language_code}/{voice_name}/{quality}/{language_code}-{voice_name}-{quality}.onnx"
    
    print(f"\nDownloading {language_code}-{voice_name}-{quality}...")
    print(f"  HF path: {hf_path}")
    print(f"  Local dir: {voice_dir}")
    
    try:
        # Download .onnx model file
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=hf_path,
            repo_type="model",
            cache_dir=None,
            local_dir=str(voice_dir),
            local_dir_use_symlinks=False
        )
        print(f"  ✓ Downloaded model: {Path(model_path).name}")
        
        # Download .json config file
        json_hf_path = hf_path.replace(".onnx", ".onnx.json")
        json_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=json_hf_path,
            repo_type="model",
            cache_dir=None,
            local_dir=str(voice_dir),
            local_dir_use_symlinks=False
        )
        print(f"  ✓ Downloaded config: {Path(json_path).name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def main():
    """Download all available Indian language voices"""
    os.makedirs(VOICES_DIR, exist_ok=True)
    
    print(f"🎤 Piper Indian Language Voice Downloader")
    print(f"📁 Target directory: {VOICES_DIR}\n")
    
    # Count results
    total = 0
    success = 0
    
    for language, voices in INDIAN_VOICES.items():
        print(f"\n{'='*60}")
        print(f"📍 {language}")
        print(f"{'='*60}")
        
        for full_name, quality in voices.items():
            parts = full_name.split("-")
            lang_code = parts[0]  # e.g., "ml_IN"
            voice_name = parts[1]  # e.g., "arjun"
            
            total += 1
            if download_voice(lang_code, voice_name, quality.lower()):
                success += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Downloaded {success}/{total} voices successfully")
    print(f"{'='*60}")
    
    # List downloaded voices
    print("\n📂 Available voices in piper_models:")
    for item in sorted(VOICES_DIR.iterdir()):
        if item.is_dir() and "-" in item.name:
            model_file = list(item.glob("*.onnx"))
            if model_file:
                print(f"  ✓ {item.name}")

if __name__ == "__main__":
    main()
