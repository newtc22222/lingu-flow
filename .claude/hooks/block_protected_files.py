#!/usr/bin/env python3
"""PreToolUse hook: block edits to .env files and lockfiles so they aren't
modified by accident. .env.example files are explicitly allowed."""
import json
import re
import sys

PROTECTED = [
    re.compile(r"(^|/)\.env(\.[^.]+)?$"),
    re.compile(r"(^|/)frontend/package-lock\.json$"),
]
ALLOWED_EXCEPTIONS = [
    re.compile(r"(^|/)\.env\.example$"),
]

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    normalized = file_path.replace("\\", "/")
    if not normalized:
        return

    if any(p.search(normalized) for p in ALLOWED_EXCEPTIONS):
        return

    if any(p.search(normalized) for p in PROTECTED):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{file_path} is a protected env/lockfile — edits are "
                    "blocked to avoid leaking secrets or corrupting the "
                    "lockfile. Ask the user to edit it directly if it's "
                    "genuinely needed."
                ),
            }
        }))

if __name__ == "__main__":
    main()
