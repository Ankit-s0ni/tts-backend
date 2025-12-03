#!/usr/bin/env python3
"""Generate sample WAVs for the three hard-coded voices via the backend `/tts/sync` API.

Usage:
  python scripts/generate_samples.py --backend http://localhost:8000

This will POST the text inputs to `/tts/sync` with the appropriate `voice` field
and write WAV files into `backend/test_outputs/`.
"""
import os
import argparse
import requests

ROOT = os.path.dirname(os.path.dirname(__file__))
INPUT_DIR = os.path.join(ROOT, "test_inputs")
OUT_DIR = os.path.join(ROOT, "test_outputs")
os.makedirs(OUT_DIR, exist_ok=True)

SAMPLES = [
    ("en_US-lessac-medium", "english_2page.txt", "sample_en_US_lessac.wav"),
    ("hi_IN-rohan-medium", "hindi_rohan_2page.txt", "sample_hi_IN_rohan.wav"),
    ("hi_IN-priyamvada-medium", "hindi_priyamvada_2page.txt", "sample_hi_IN_priyamvada.wav"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    args = parser.parse_args()

    for voice_id, infile, outname in SAMPLES:
        path = os.path.join(INPUT_DIR, infile)
        if not os.path.isfile(path):
            print(f"Missing input: {path}, skipping {voice_id}")
            continue
        with open(path, "r", encoding="utf8") as fh:
            text = fh.read()

        payload = {"text": text, "voice": voice_id}
        print(f"Requesting voice={voice_id} from {args.backend}/tts/sync ...")
        resp = requests.post(f"{args.backend.rstrip('/')}/tts/sync", json=payload, timeout=300)
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code} {resp.text}")
            continue
        out_path = os.path.join(OUT_DIR, outname)
        with open(out_path, "wb") as fh:
            fh.write(resp.content)
        print(f"Wrote {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    main()
