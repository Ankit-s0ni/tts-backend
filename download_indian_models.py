#!/usr/bin/env python3
"""Download missing Indian language Piper models from Hugging Face."""
import os
from pathlib import Path
import urllib.request
import json

# Use huggingface_hub if available, otherwise use direct URLs
try:
    from huggingface_hub import hf_hub_download
    HAS_HF_HUB = True
except ImportError:
    HAS_HF_HUB = False

# Models to download - using the correct repo structure
MODELS = [
    {
        "name": "te_IN-rama-medium",
        "repo": "rhasspy/piper-voices",
        "file": "te_IN/rama/medium/te_IN-rama-medium.onnx"
    },
    {
        "name": "ta_IN-lakshmis-medium",
        "repo": "rhasspy/piper-voices",
        "file": "ta_IN/lakshmi/medium/ta_IN-lakshmis-medium.onnx"
    },
    {
        "name": "mr_IN-aniruddh-medium",
        "repo": "rhasspy/piper-voices",
        "file": "mr_IN/aniruddh/medium/mr_IN-aniruddh-medium.onnx"
    },
    {
        "name": "kn_IN-sunitha-medium",
        "repo": "rhasspy/piper-voices",
        "file": "kn_IN/sunitha/medium/kn_IN-sunitha-medium.onnx"
    },
]

output_dir = Path("./piper_models")

print("=" * 60)
print("DOWNLOADING INDIAN LANGUAGE PIPER MODELS")
print("=" * 60)
print()

if not HAS_HF_HUB:
    print("Installing huggingface_hub...")
    os.system("pip install -q huggingface_hub")
    from huggingface_hub import hf_hub_download

for model in MODELS:
    voice_name = model["name"]
    model_dir = output_dir / voice_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_file = model_dir / f"{voice_name}.onnx"
    
    if model_file.exists():
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"✓ {voice_name:30} - already exists ({size_mb:.1f} MB)")
        continue
    
    print(f"⬇ {voice_name:30}", end=" ", flush=True)
    
    try:
        # Download using huggingface_hub
        path = hf_hub_download(
            repo_id=model["repo"],
            filename=model["file"],
            repo_type="model",
            local_dir=str(model_dir),
            local_dir_use_symlinks=False
        )
        
        # Move to expected location if needed
        if path != str(model_file):
            import shutil
            if Path(path).exists():
                shutil.move(path, model_file)
        
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"✓ ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"✗ {str(e)[:50]}")

print()
print("=" * 60)
print("Download complete!")
print("=" * 60)

