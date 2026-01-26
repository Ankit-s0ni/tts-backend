"""Check what voices the catalog finds."""
from app.voice_catalog import list_voices

voices = list_voices()
indian = [v for v in voices if any(x in v['id'] for x in ['hi_', 'te_', 'ta_', 'mr_', 'kn_'])]

print(f'Total voices: {len(voices)}')
print(f'Indian voices found: {len(indian)}')
print()

for v in sorted(indian, key=lambda x: x['id']):
    print(f"{v['id']:30} - {v.get('engine', '?')}")
