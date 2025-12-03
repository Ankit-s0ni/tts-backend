#!/usr/bin/env python3
import sys
import json
from app.dynamo import get_job_item

job_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
item = get_job_item(job_id)
print(json.dumps(item, indent=2, default=str))
