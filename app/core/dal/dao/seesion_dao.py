from sqlalchemy.orm import Session as SessionType

from app.core.dal.dao.dao import DAO
from app.core.dal.model.session_model import SessionModel


class SessionDAO(DAO[SessionModel]):
    """Session Data Access Object"""

    def __init__(self, session: SessionType):
        super().__init__(SessionModel, session)
