from typing import Dict

from app.agent.core.session import Session


class SessionManager:
    """Session manager"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    async def craete_session(self) -> Session:
        """Create a session"""
        session = Session()
        self._sessions[session.id] = session
        return session

    async def get_session(self, session_id: str) -> Session:
        """Get a session"""
        return self._sessions.get(session_id)

    async def delete_session(self, session_id: str):
        """Delete a session"""
        self._sessions.pop(session_id, None)
