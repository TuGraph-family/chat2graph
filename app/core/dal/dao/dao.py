import threading
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import DeclarativeBase, Session as SqlAlchemySession

from app.core.common.singleton import Singleton

T = TypeVar("T", bound=DeclarativeBase)


class Dao(Generic[T], metaclass=Singleton):
    """Data Access Object"""

    # thread local storage
    _thread_local = threading.local()

    def __init__(self, model: Type[T], session: SqlAlchemySession):
        self._model: Type[T] = model
        self._engine: Any = session.get_bind()

    @property
    def session(self) -> SqlAlchemySession:
        """get the SQLAlchemy session"""
        if not hasattr(self._thread_local, "session"):
            self._thread_local.session = SqlAlchemySession(self._engine)
        return self._thread_local.session

    def create(self, **kwargs: Any) -> T:
        """Create a new object."""
        obj = self._model(**kwargs)
        try:
            self.session.add(obj)
            self.session.commit()
            return obj
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_id(self, id: str) -> Optional[T]:
        """Get an object by ID."""
        return self.session.query(self._model).get(id)

    def filter_by(self, **kwargs: Any) -> List[T]:
        """Filter objects."""
        return self.session.query(self._model).filter_by(**kwargs).all()

    def get_all(self) -> List[T]:
        """Get all objects."""
        return self.session.query(self._model).all()

    def update(self, id: str, **kwargs: Any) -> T:
        """Update an object."""
        obj = self.get_by_id(id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            self.session.commit()
            return obj
        raise ValueError(f"Object with ID {id} not found")

    def delete(self, id: str) -> Optional[T]:
        """Delete an object."""
        obj = self.get_by_id(id)
        try:
            if obj:
                self.session.delete(obj)
                self.session.commit()
            return obj
        except Exception as e:
            self.session.rollback()
            raise e
