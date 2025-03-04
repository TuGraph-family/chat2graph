from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session as SessionType

from app.core.model.sql_model import File, GraphDB, KBToFile, KnowledgeBase, Message, Session

T = TypeVar("T")


class DAO(Generic[T]):
    """Data Access Object"""

    def __init__(self, model: Type[T], session: SessionType):
        self._model: Type[T] = model
        self._session: SessionType = session

    def create(self, **kwargs: Any) -> T:
        """Create a new object."""
        obj = self._model(**kwargs)
        self._session.add(obj)
        self._session.commit()
        return obj

    def get_by_id(self, id: str) -> Optional[T]:
        """Get an object by ID."""
        return self._session.query(self._model).get(id)

    def filter_by(self, **kwargs: Any) -> List[T]:
        """Filter objects."""
        return self._session.query(self._model).filter_by(**kwargs).all()

    def get_all(self) -> List[T]:
        """Get all objects."""
        return self._session.query(self._model).all()

    def update(self, id: str, **kwargs: Any) -> Optional[T]:
        """Update an object."""
        obj = self.get_by_id(id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            self._session.commit()
        return obj

    def delete(self, id: str) -> Optional[T]:
        """Delete an object."""
        obj = self.get_by_id(id)
        if obj:
            self._session.delete(obj)
            self._session.commit()
        return obj


class SessionDAO(DAO[Session]):
    """Session Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(Session, session)


class MessageDAO(DAO[Message]):
    """Message Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(Message, session)


class KnowledgeBaseDAO(DAO[KnowledgeBase]):
    """Knowledge Base Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(KnowledgeBase, session)


class FileDAO(DAO[File]):
    """File Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(File, session)


class KBToFileDAO(DAO[KBToFile]):
    """Knowledge Base to File Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(KBToFile, session)


class GraphDbDAO(DAO[GraphDB]):
    """Graph Database Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(GraphDB, session)
