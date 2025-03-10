from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.knowledge_do import KbToFileDo, KnowledgeBaseDo


class KnowledgeBaseDao(Dao[KnowledgeBaseDo]):
    """Knowledge Base Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(KnowledgeBaseDo, session)


class KBToFileDAO(Dao[KbToFileDo]):
    """Knowledge Base to File Data Access Object"""

    # TODO：not defined very clear

    def __init__(self, session: SqlAlchemySession):
        super().__init__(KbToFileDo, session)
