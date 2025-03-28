from typing import Optional

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.graph_db_do import GraphDbDo


class GraphDbDao(Dao[GraphDbDo]):
    """Graph Database Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(GraphDbDo, session)

    def get_by_default(self) -> Optional[GraphDbDo]:
        """Get an object by ID."""
        return self.session.query(self._model).filter_by(is_default_db=True).first()
