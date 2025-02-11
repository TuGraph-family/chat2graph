from typing import Dict, Optional

from app.agent.core.session import Session
from app.common.singleton import Singleton


class SessionService(metaclass=Singleton):
    """Session manager"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def get_session(self, session_id: Optional[str] = None) -> Session:
        """Get the session, if not exists or session_id is None, create a new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        session = Session(id=session_id) if session_id else Session()
        self._sessions[session.id] = session
        return session

    def delete_session(self, session_id: str):
        """Delete a session"""
        self._sessions.pop(session_id, None)
