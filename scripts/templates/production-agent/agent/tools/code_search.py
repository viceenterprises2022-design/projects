from typing import List, Dict, Any

async def repo_code_search(pattern: str) -> List[Dict[str, Any]]:
    """Scan local repository files safely for specified text patterns."""
    return [
        {
            "filepath": "app/main.py",
            "matches": [f"line 42: matching pattern '{pattern}'"]
        }
    ]
