"""Test Parler TTS API to understand correct usage."""
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import torch

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")
print("✓ Tokenizer loaded")

print("\nLoading model...")
model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-v1")
print("✓ Model loaded")

print("\nModel has methods:")
synth_methods = [m for m in dir(model) if 'synthesize' in m.lower() or 'generate' in m.lower()]
print(f"  Synthesis/Generate: {synth_methods}")

forward_methods = [m for m in dir(model) if 'forward' in m.lower()]
print(f"  Forward: {forward_methods}")

# Try synthesize if it exists
if hasattr(model, 'synthesize'):
    print("\n✓ Model has synthesize method")
    print("Synthesize signature:", model.synthesize.__doc__)


