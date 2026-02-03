import uuid
from datetime import datetime

class HistoryManager:
    def __init__(self):
        # In-memory storage: { session_id: [ {role, content, timestamp} ] }
        self.sessions = {}

    def create_session(self):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id

    def add_message(self, session_id, role, content):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_history(self, session_id):
        return self.sessions.get(session_id, [])

    def list_sessions(self):
        return [
            {
                "id": sid, 
                "message_count": len(msgs), 
                "last_message": msgs[-1]["content"] if msgs else "",
                "timestamp": msgs[-1]["timestamp"] if msgs else ""
            }
            for sid, msgs in self.sessions.items()
        ]
