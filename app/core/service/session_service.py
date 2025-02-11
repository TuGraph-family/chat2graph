from typing import Dict, Optional

from app.core.model.session import Session
from app.core.common.singleton import Singleton
from app.plugin.sqlite.sqlite_model import Session as SqlSession, db
from app.server.common.api_tool import ParameterException, ServiceException


def get_all_sessions():
    """Get all sessions"""
    sessions = SqlSession.query.all()
    return [
        {"id": session.id, "created_at": session.created_at.isoformat(), "name": session.name}
        for session in sessions
    ]


def create_session(name=None):
    """Create a new session"""
    if name is None:
        raise ParameterException("Session name is required")
    new_session = SqlSession(name=name)
    try:
        db.session.add(new_session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ServiceException(f"Failed to create session: {str(e)}") from e
    return {
        "id": new_session.id,
        "created_at": new_session.created_at.isoformat(),
        "name": new_session.name,
    }


def get_session(session_id):
    """Get a session by ID"""
    session = SqlSession.query.get(session_id)
    if session is None:
        # TODO: fix the parameters
        raise ParameterException("Session not found", 404)
    return {"id": session.id, "created_at": session.created_at.isoformat(), "name": session.name}


def delete_session(session_id):
    """Delete a session by ID"""
    session = SqlSession.query.get(session_id)
    if session is None:
        # TODO: fix the parameters
        raise ParameterException("Session not found", 404)
    try:
        db.session.delete(session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ServiceException(f"Failed to delete session: {str(e)}") from e
    return {"message": "Session deleted successfully"}


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
