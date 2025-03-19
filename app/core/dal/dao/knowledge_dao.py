from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.knowledge_do import KnowledgeBaseDo, FileToKBDo


class KnowledgeBaseDao(Dao[KnowledgeBaseDo]):
    """Knowledge Base Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(KnowledgeBaseDo, session)


class FileToKBDao(Dao[FileToKBDo]):
    """File to Knowledge Base Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(FileToKBDo, session)
