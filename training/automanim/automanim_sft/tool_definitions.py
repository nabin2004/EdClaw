"""Shared tool schemas embedded in Gemma-4 system turns for AutoManim traces."""

AUTOMANIM_TOOL_DEFINITIONS: list[dict] = [
    {
        "function": {
            "name": "write",
            "description": "Writes content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        }
    },
    {
        "function": {
            "name": "safe_bash",
            "description": "Executes a shell command safely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                },
                "required": ["command"],
            },
        }
    },
    {
        "function": {
            "name": "read",
            "description": "Reads content from a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        }
    },
]
