from contextlib import contextmanager
from typing import Any, Generator, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import DeclarativeBase, Session as SqlAlchemySession

from app.core.common.singleton import Singleton
from app.core.dal.database import DbSession

T = TypeVar("T", bound=DeclarativeBase)


class Dao(Generic[T], metaclass=Singleton):
    """Data Access Object"""

    def __init__(self, model: Type[T], session: SqlAlchemySession):
        self._model: Type[T] = model
        self._session: SqlAlchemySession = session

    @property
    def session(self) -> SqlAlchemySession:
        """Get the session."""
        return self._session

    @contextmanager
    def new_session(self) -> Generator[SqlAlchemySession, None, None]:
        """Create a new session."""
        session = DbSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create(self, **kwargs: Any) -> T:
        """Create a new object."""
        with self.new_session() as s:
            obj = self._model(**kwargs)
            s.add(obj)
            s.commit()

            assert hasattr(obj, "id") and obj.id is not None, (
                "Object ID should not be None after commit"
            )
            result = self.get_by_id(obj.id)
            if result is None:
                raise ValueError(f"Failed to create {self._model.__name__}")
            return result

    def get_by_id(self, id: str) -> Optional[T]:
        """Get an object by ID."""
        return self.session.query(self._model).get(id)

    def filter_by(self, **kwargs: Any) -> List[T]:
        """Filter objects."""
        return self.session.query(self._model).filter_by(**kwargs).all()

    def get_all(self) -> List[T]:
        """Get all objects."""
        return self.session.query(self._model).all()

    def count(self) -> int:
        """Get count."""
        return self.session.query(self._model).count()

    def update(self, id: str, **kwargs: Any) -> T:
        """Update an object."""
        kwargs.pop("id", None)
        if len(kwargs) != 0:
            with self.new_session() as s:
                # add synchronize_session parameter to satisfy type checker
                s.query(self._model).filter_by(id=id).update(kwargs, synchronize_session=False)  # type: ignore[arg-type]

        result = self.get_by_id(id)
        if result is None:
            raise ValueError(f"{self._model.__name__} with id {id} not found")

        self.session.refresh(result)
        return result

    def delete(self, id: str):
        """Delete an object."""
        with self.new_session() as s:
            s.query(self._model).filter_by(id=id).delete()
