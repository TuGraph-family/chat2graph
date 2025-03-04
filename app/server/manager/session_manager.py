from typing import Any, Dict, List, Optional, Tuple

from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.service.session_service import SessionService
from app.server.common.util import ServiceException


class SessionManager:
    """Session Manager class to handle business logic"""

    def __init__(self):
        self._session_service: SessionService = SessionService()
        self._knowledgebase_service: KnowledgeBaseService = KnowledgeBaseService()

    def create_session(self, name: str) -> Tuple[Dict[str, Any], str]:
        """Create a new session and return the response data.

        Args:
            name (str): Name of the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing session details and success message
        """
        try:
            session = self._session_service.create_session(name=name)
            knowledgebase = self._knowledgebase_service.create_knowledge_base(
                name=name, knowledge_type="private", session_id=session.id
            )
            data = {
                "id": session.id,
                "knowledgebase_id": knowledgebase.id,
                "name": session.name,
                "created_at": session.created_at.isoformat() if session.created_at else None,
            }
            return data, "Session created successfully"
        except Exception as e:
            raise ServiceException(f"Failed to create session: {str(e)}") from e

    def get_session(self, session_id: str) -> Tuple[Dict[str, Any], str]:
        """Get session details by ID.

        Args:
            session_id (str): ID of the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing session details and success message
        """
        try:
            session = self._session_service.get_session(session_id=session_id)
            data = {
                "id": session.id,
                "name": session.name,
                "created_at": session.created_at.isoformat() if session.created_at else None,
            }
            return data, "Session fetched successfully"
        except Exception as e:
            raise ServiceException(f"Failed to fetch session: {str(e)}") from e

    def delete_session(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Delete a session by ID.

        Args:
            id (str): ID of the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        try:
            self._session_service.delete_session(id=id)
            return {}, f"Session with ID {id} deleted successfully"
        except Exception as e:
            raise ServiceException(f"Failed to delete session: {str(e)}") from e

    def update_session(self, id: str, name: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
        """Update a session's name by ID.

        Args:
            id (str): ID of the session
            name (Optional[str]): New name for the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing updated session details and success message
        """
        try:
            session = self._session_service.update_session(id=id, name=name)
            data = {
                "id": session.id,
                "name": session.name,
                "created_at": session.created_at.isoformat() if session.created_at else None,
            }
            return data, "Session updated successfully"
        except Exception as e:
            raise ServiceException(f"Failed to update session: {str(e)}") from e

    def get_all_sessions(self) -> Tuple[List[dict], str]:
        """Get all sessions.

        Returns:
            Tuple[List[dict], str]: A tuple containing a list of session details and success message
        """
        try:
            sessions = self._session_service.get_all_sessions()
            session_list = [
                {
                    "id": session.id,
                    "name": session.name,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                }
                for session in sessions
            ]
            return session_list, "Get all sessions successfully"
        except Exception as e:
            raise ServiceException(f"Failed to fetch all sessions: {str(e)}") from e
