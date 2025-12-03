#!/usr/bin/env python3
from app.voice_catalog import get_voice
import os
v=get_voice('en_US-lessac-medium')
print('voice entry:', v)
if v:
    p=v.get('model_path')
    print('model_path:', p)
    print('exists:', os.path.exists(p))
    print('cwd:', os.getcwd())
else:
    print('voice not found')
