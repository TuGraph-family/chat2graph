from typing import List, Optional
from uuid import uuid4

from app.core.common.singleton import Singleton
from app.core.dal.dao.seesion_dao import SessionDao
from app.core.dal.do.session_do import SessionDo
from app.core.model.session import Session


class SessionService(metaclass=Singleton):
    """Session service"""

    def __init__(self):
        self._session_dao: SessionDao = SessionDao.instance

    def create_session(self, name: str) -> Session:
        """Create the session by name.

        Args:
            name (str): Name of the session
        Returns:
            Session: Session object
        """
        # create the session
        result: SessionDo = self._session_dao.create(name=name)
        return Session(id=str(result.id), name=name, timestamp=int(result.timestamp))

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
        result = self._session_dao.get_by_id(id=session_id)
        if not result:
            raise ValueError(f"Session with ID {id} not found")
        return Session(
            id=str(result.id),
            name=str(result.name),
            timestamp=int(result.timestamp) if result.timestamp is not None else None,
        )

    def delete_session(self, id: str) -> None:
        """Delete the session by ID.

        Args:
            id (str): ID of the session
        """
        # delete the session
        session = self._session_dao.get_by_id(id=id)
        if not session:
            raise ValueError(f"Session with ID {id} not found")
        self._session_dao.delete(id=id)

    def update_session(self, id: str, name: Optional[str] = None) -> Session:
        """Update the session by ID.

        Args:
            id (str): ID of the session
            name (Optional[str]): New name for the session
        """
        # fetch the existing session
        session = self._session_dao.get_by_id(id=id)
        if not session:
            raise ValueError(f"Session with ID {id} not found")

        # update only if a new name is provided and it's different from the current name
        if name is not None and name != session.name:
            updated_session = self._session_dao.update(id=id, name=name)
            return Session(
                id=str(updated_session.id),
                name=str(updated_session.name),
                timestamp=int(updated_session.timestamp)
                if updated_session.timestamp is not None
                else None,
            )
        return Session(
            id=str(session.id),
            name=str(session.name),
            timestamp=int(session.timestamp) if session.timestamp is not None else None,
        )

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions.

        Returns:
            List[Session]: List of sessions
        """

        results = self._session_dao.get_all()
        return [
            Session(
                id=str(result.id),
                name=str(result.name),
                timestamp=int(result.timestamp) if result.timestamp is not None else None,
            )
            for result in results
        ]
