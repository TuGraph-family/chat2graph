from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.session_do import SessionDo


class SessionDao(Dao[SessionDo]):
    """Session Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(SessionDo, session)
