"""Check what's available in Piper voices repo."""
from huggingface_hub import list_repo_tree

repo = "rhasspy/piper-voices"
print(f"Listing {repo} top directories...\n")

try:
    # List everything, sort by path
    items = list(list_repo_tree(repo, recursive=False))
    paths = set()
    for item in items:
        path = item.path
        if "/" in path:
            top_dir = path.split("/")[0]
            paths.add(top_dir)
    
    for p in sorted(paths):
        print(f"  {p}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

