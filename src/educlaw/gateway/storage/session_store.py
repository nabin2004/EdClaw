from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time 

@dataclass
class Session:
    id: str
    messages: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def add_user_message(self, text: str):
        self.messages.append({
            "role":"user",
            "content": text
        })

    def add_assistant_message(self, text: str):
        self.messages.append({
            "role":"assistant",
            "content": text
        })
    
class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        
    def get(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(id=session_id)
        return self.sessions[session_id]
    