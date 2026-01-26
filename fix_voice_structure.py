#!/usr/bin/env python3
"""Fix nested directory structure for downloaded voices"""

import os
import shutil
from pathlib import Path

VOICES_DIR = Path(__file__).parent / "piper_models"

def fix_voice_structure(voice_dir_name: str) -> bool:
    """Fix nested directory structure for a voice.
    
    Before: piper_models/ml_IN-arjun-medium/ml/ml_IN/arjun/medium/ml_IN-arjun-medium.onnx
    After:  piper_models/ml_IN-arjun-medium/ml_IN-arjun-medium.onnx
    """
    voice_dir = VOICES_DIR / voice_dir_name
    
    if not voice_dir.exists():
        print(f"✗ Directory not found: {voice_dir}")
        return False
    
    # Find .onnx files in nested structure
    onnx_files = list(voice_dir.rglob("*.onnx"))
    json_files = list(voice_dir.rglob("*.onnx.json"))
    
    if not onnx_files:
        print(f"⚠ No .onnx files found in {voice_dir_name}")
        return False
    
    print(f"\n🔧 Fixing {voice_dir_name}...")
    
    # Move files to top level
    for onnx_file in onnx_files:
        dest_file = voice_dir / onnx_file.name
        if dest_file != onnx_file:
            print(f"  Moving: {onnx_file.relative_to(voice_dir)}")
            shutil.move(str(onnx_file), str(dest_file))
    
    for json_file in json_files:
        dest_file = voice_dir / json_file.name
        if dest_file != json_file:
            print(f"  Moving: {json_file.relative_to(voice_dir)}")
            shutil.move(str(json_file), str(dest_file))
    
    # Clean up empty nested directories
    try:
        for item in voice_dir.rglob("*"):
            if item.is_dir() and not list(item.iterdir()):
                item.rmdir()
    except:
        pass
    
    # Verify files are at top level
    onnx_at_top = list(voice_dir.glob("*.onnx"))
    if onnx_at_top:
        print(f"  ✓ {len(onnx_at_top)} .onnx files at top level")
        return True
    else:
        print(f"  ✗ No .onnx files at top level")
        return False

def main():
    """Fix all Indian language voice directories"""
    print("🎤 Piper Voice Directory Structure Fixer\n")
    
    voices_to_fix = [
        "ml_IN-arjun-medium",
        "ml_IN-meera-medium",
        "te_IN-maya-medium",
        "te_IN-padmavathi-medium",
        "te_IN-venkatesh-medium",
    ]
    
    success = 0
    for voice_dir in voices_to_fix:
        if fix_voice_structure(voice_dir):
            success += 1
    
    print(f"\n✅ Fixed {success}/{len(voices_to_fix)} voices")
    
    # List fixed voices
    print("\n📂 Voice structure after fix:")
    for voice_dir in VOICES_DIR.iterdir():
        if voice_dir.is_dir() and any(x in voice_dir.name for x in ["ml_IN", "te_IN"]):
            onnx_files = list(voice_dir.glob("*.onnx"))
            if onnx_files:
                print(f"  ✓ {voice_dir.name}")
                for f in onnx_files[:1]:  # Show first file
                    print(f"    └─ {f.name}")

if __name__ == "__main__":
    main()
