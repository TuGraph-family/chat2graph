from typing import List, Optional, cast
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
        return Session(
            id=str(result.id), name=name, timestamp=int(result.timestamp), latest_job_id=None
        )

    def save_session(self, session: Session) -> Session:
        """Save the session by ID."""
        session_do: SessionDo = self._session_dao.update(
            id=session.id,
            name=session.name,
            timestamp=session.timestamp,
            latest_job_id=session.latest_job_id,
        )
        return Session(
            id=str(session_do.id),
            name=cast(Optional[str], session_do.name),
            timestamp=cast(Optional[int], session_do.timestamp),
            latest_job_id=cast(Optional[str], session_do.latest_job_id),
        )

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
            name=cast(Optional[str], result.name),
            timestamp=cast(Optional[int], result.timestamp),
            latest_job_id=cast(Optional[str], result.latest_job_id),
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

    def update_session(self, session: Session) -> Session:
        """Update the session by ID."""
        updated_session_do: SessionDo = self._session_dao.update(
            id=session.id,
            name=session.name,
            timestamp=session.timestamp,
            latest_job_id=session.latest_job_id,
        )
        return Session(
            id=str(updated_session_do.id),
            name=cast(Optional[str], updated_session_do.name),
            timestamp=cast(Optional[int], updated_session_do.timestamp),
            latest_job_id=cast(Optional[str], updated_session_do.latest_job_id),
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
                name=cast(Optional[str], result.name),
                timestamp=cast(Optional[int], result.timestamp),
                latest_job_id=cast(Optional[str], result.latest_job_id),
            )
            for result in results
        ]

    def get_latest_job_id(self, session_id: str) -> str:
        """Get the latest job ID for a session.

        Args:
            session_id (str): ID of the session

        Returns:
            str: Latest job ID
        """
        session = self.get_session(session_id=session_id)
        if not session.latest_job_id:
            raise ValueError(f"Session with ID {session_id} has no latest job ID")
        return session.latest_job_id
