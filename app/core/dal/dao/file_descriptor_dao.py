from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.file_descriptor_do import FileDescriptorDo


class FileDescriptorDao(Dao[FileDescriptorDo]):
    """File descriptor Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(FileDescriptorDo, session)
