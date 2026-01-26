"""Scan local Piper model folders and update DynamoDB voice availability.

This module looks for folders containing `.onnx` files under `./piper_models`
and `/models` (the latter is useful when the backend is running in-container
and the host `./piper_models` is mounted to `/models`). For each discovered
model folder it will upsert a voice record with `engine='piper'`,
`available=True` and `model_path` set to the folder path. Any existing voice
records with `engine=='piper'` that are not present on disk will be marked
`available=False`.
"""
from __future__ import annotations

import os
from typing import Iterable

from ..mongo_db import list_voices, get_voice, put_voice


def _candidate_paths() -> Iterable[str]:
    # prefer mounted /models (container) then repository-local backend/piper_models
    yield "/models"
    # when run from repo root, backend/piper_models will be at ./backend/piper_models
    yield os.path.join(os.getcwd(), "backend", "piper_models")
    # fallback to legacy top-level piper_models if present
    yield os.path.join(os.getcwd(), "piper_models")


def _folder_has_onnx(path: str) -> bool:
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(".onnx"):
                return True
    return False


def sync_piper_models(paths: Iterable[str] | None = None) -> dict:
    """Scan provided paths (or defaults) and update the DynamoDB `voices` table.

    Returns a summary dict with counts for created/updated/disabled voices.
    """
    if paths is None:
        paths = list(_candidate_paths())

    discovered = set()
    created_or_updated = 0

    for base in paths:
        if not base:
            continue
        if not os.path.exists(base):
            continue
        try:
            # Walk and find .onnx files anywhere under base. Support both
            # per-voice directories and flat downloads where .onnx files sit
            # at the repository root.
            for root, _, files in os.walk(base):
                for f in files:
                    if not f.lower().endswith(".onnx"):
                        continue
                    onnx_path = os.path.join(root, f)
                    # derive voice id from filename (strip extension)
                    voice_id = os.path.splitext(f)[0]
                    discovered.add(voice_id)
                    model_path = os.path.abspath(root)
                    existing = get_voice(voice_id) or {}
                    voice = dict(existing)
                    voice.update(
                        {
                            "id": voice_id,
                            "engine": "piper",
                            "available": True,
                            "model_path": model_path,
                        }
                    )
                    put_voice(voice)
                    created_or_updated += 1
        except Exception:
            # ignore individual path errors; continue scanning others
            continue

    # disable any piper voices not discovered
    disabled = 0
    try:
        all_voices = list_voices()
        for v in all_voices:
            if v.get("engine") == "piper":
                vid = v.get("id")
                if vid not in discovered:
                    v["available"] = False
                    put_voice(v)
                    disabled += 1
    except Exception:
        # if DynamoDB/listing fails, just return partial summary
        pass

    return {"found": len(discovered), "created_or_updated": created_or_updated, "disabled": disabled}


if __name__ == "__main__":
    import json

    summary = sync_piper_models()
    print(json.dumps(summary, indent=2))
import os
from typing import List

from ..mongo_db import list_voices, get_voice, put_voice


def _find_models(root_paths: List[str]) -> dict:
    """Return mapping voice_id -> (model_path, onnx_filename) for found models."""
    found = {}
    for root in root_paths:
        if not root:
            continue
        if not os.path.exists(root):
            continue
        for name in os.listdir(root):
            folder = os.path.join(root, name)
            if not os.path.isdir(folder):
                continue
            # find any .onnx file inside
            onnx_files = [f for f in os.listdir(folder) if f.endswith('.onnx')]
            if not onnx_files:
                continue
            # prefer the first .onnx
            onnx = onnx_files[0]
            # prefer using /models path in model_path to match Piper container mount
            # if the root contains 'piper_models' we will construct /models/<name>/<onnx>
            if os.path.abspath(root).endswith('piper_models') or os.path.abspath(root).endswith('piper_models\\'):
                model_path = f"/models/{name}/{onnx}"
            else:
                model_path = os.path.join(root, name, onnx)
            found[name] = (model_path, onnx)
    return found


def sync_piper_models():
    """Scan local piper model directories and update DynamoDB voice records.

    Behavior:
    - Scan possible model locations (./piper_models, /models)
    - For each discovered model folder, insert or update a voice entry with
      engine='piper', model_path set, available=True
    - For existing voices in DynamoDB with engine=='piper' but missing on disk,
      set available=False
    """
    # possible locations in order of preference
    candidates = [
        '/models',
        os.path.join(os.getcwd(), 'backend', 'piper_models'),
        os.path.join(os.getcwd(), 'piper_models'),
        os.path.join(os.path.dirname(os.getcwd()), 'piper_models'),
    ]

    found = _find_models(candidates)

    # update or create voice entries for found models
    present_ids = set()
    for vid, (model_path, onnx) in found.items():
        present_ids.add(vid)
        existing = get_voice(vid) or {}
        # preserve display_name and language if present
        voice = {
            'id': vid,
            'engine': 'piper',
            'language': existing.get('language', vid.split('-')[0] if '-' in vid else existing.get('language', 'unknown')),
            'display_name': existing.get('display_name', vid),
            'model_path': model_path,
            'supports_alignments': existing.get('supports_alignments', False),
            'available': True,
        }
        put_voice(voice)

    # mark piper voices not present as unavailable
    all_voices = list_voices()
    for v in all_voices:
        if v.get('engine') != 'piper':
            continue
        vid = v.get('id')
        if vid not in present_ids:
            v['available'] = False
            put_voice(v)

    return True
