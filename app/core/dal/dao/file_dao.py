from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.file_do import FileDo


class FileDao(Dao[FileDo]):
    """File Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(FileDo, session)
