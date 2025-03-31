from typing import Optional

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.graph_db_do import GraphDbDo


class GraphDbDao(Dao[GraphDbDo]):
    """Graph Database Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(GraphDbDo, session)

    def get_by_default(self) -> Optional[GraphDbDo]:
        """Get default graph db."""
        return self.session.query(self._model).filter_by(is_default_db=True).first()

    def set_as_default(self, id):
        """Set a graph db as default. If another db is already default, unset it. It is assumed that
        there is only one default db at a time."""
        default_db = self.get_by_default()
        if default_db and default_db.id == id:
            return

        obj = self.get_by_id(id)
        if not obj:
            return

        with self.new_session() as s:
            s.query(self._model).filter_by(id=default_db.id).update({"is_default_db": False})
            s.query(self._model).filter_by(id=id).update({"is_default_db": True})
