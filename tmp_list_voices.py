#!/usr/bin/env python3
from app.dynamo import list_voices
import json
print(json.dumps(list_voices(), indent=2, default=str))
