from __future__ import annotations

from pydantic import BaseModel


class ToolPolicy(BaseModel):
    allow: list[str] = ["read", "exec", "process"]
    deny: list[str] = ["write", "edit", "apply_patch", "browser", "canvas"]

    def is_allowed(self, tool_name: str) -> bool:
        if tool_name in self.deny:
            return False
        if not self.allow:
            return True
        return tool_name in self.allow
