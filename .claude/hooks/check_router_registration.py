#!/usr/bin/env python3
"""PostToolUse hook: warn if a backend router file was edited but isn't
registered in backend/app/main.py via app.include_router(...)."""
import json
import re
import sys
from pathlib import Path

def get_project_root() -> Path:
    cwd = Path.cwd()
    for p in [cwd, *cwd.parents]:
        if (p / ".claude").exists() or (p / "backend/app/main.py").exists():
            return p
    return cwd

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    normalized = file_path.replace("\\", "/")

    match = re.search(r"backend/app/routers/(\w+)\.py$", normalized)
    if not match or match.group(1) == "__init__":
        return

    module = match.group(1)
    project_root = get_project_root()
    main_py = project_root / "backend/app/main.py"
    if not main_py.exists():
        return

    content = main_py.read_text(encoding="utf-8", errors="ignore")
    if module not in content:
        print(json.dumps({
            "systemMessage": (
                f"Router file {file_path} was edited but '{module}' doesn't "
                "appear in backend/app/main.py — verify it's registered via "
                "app.include_router(...)."
            )
        }))

if __name__ == "__main__":
    main()
