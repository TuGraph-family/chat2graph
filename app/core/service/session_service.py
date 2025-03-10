from datetime import datetime
from typing import Dict, List, Optional, cast
from uuid import uuid4

from app.core.common.singleton import Singleton
from app.core.common.util import utc_now
from app.core.dal.dao.seesion_dao import SessionDao
from app.core.dal.database import DB
from app.core.dal.do.session_do import SessionDo
from app.core.model.session import Session
from app.server.common.util import ServiceException


class SessionService(metaclass=Singleton):
    """Session service"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._dao = SessionDao(DB())

    def create_session(self, name: str) -> Session:
        """Create the session by name.

        Args:
            name (str): Name of the session
        Returns:
            Session: Session object
        """
        # create the session
        created_at = utc_now()
        result: SessionDo = self._dao.create(name=name, created_at=created_at)
        return Session(id=str(result.id), name=name, created_at=created_at)

    def get_session(self, session_id: Optional[str] = None) -> Session:
        """Get the session by ID. If ID is not provided, create a new session.
        If the session already exists, return the existing session.

        Args:
            id (Optional[str]): ID of the session
        Returns:
            Session: Session object
        """
        if not session_id:
            return self.create_session(name="Session " + str(uuid4()))
        # fetch the session
        result = self._dao.get_by_id(id=session_id)
        if not result:
            raise ServiceException(f"Session with ID {id} not found")
        return Session(
            id=str(result.id),
            name=str(result.name),
            created_at=cast(datetime, result.created_at),
        )

    def delete_session(self, id: str) -> None:
        """Delete the session by ID.

        Args:
            id (str): ID of the session
        """
        # delete the session
        session = self._dao.get_by_id(id=id)
        if not session:
            raise ServiceException(f"Session with ID {id} not found")
        self._dao.delete(id=id)

    def update_session(self, id: str, name: Optional[str] = None) -> Session:
        """Update the session by ID.

        Args:
            id (str): ID of the session
            name (Optional[str]): New name for the session
        """
        # fetch the existing session
        session = self._dao.get_by_id(id=id)
        if not session:
            raise ServiceException(f"Session with ID {id} not found")

        # update only if a new name is provided and it's different from the current name
        if name is not None and name != session.name:
            updated_session = self._dao.update(id=id, name=name)
            return Session(
                id=updated_session.id,
                name=updated_session.name,
                created_at=updated_session.created_at,
            )
        return Session(id=session.id, name=session.name, created_at=session.created_at)

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions.

        Returns:
            List[Session]: List of sessions
        """

        results = self._dao.get_all()
        return [
            Session(id=str(result.id), name=result.name, created_at=result.created_at)
            for result in results
        ]
