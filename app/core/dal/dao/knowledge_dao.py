from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import DAO
from app.core.dal.model.knowledge_model import (
    FileModel,
    GraphDBModel,
    KbToFileModel,
    KnowledgeBaseModel,
)


class KnowledgeBaseDAO(DAO[KnowledgeBaseModel]):
    """Knowledge Base Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(KnowledgeBaseModel, session)


class FileDAO(DAO[FileModel]):
    """File Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(FileModel, session)


class KBToFileDAO(DAO[KbToFileModel]):
    """Knowledge Base to File Data Access Object"""

    # TODO：not defined very clear

    def __init__(self, session: SqlAlchemySession):
        super().__init__(KbToFileModel, session)


class GraphDbDAO(DAO[GraphDBModel]):
    """Graph Database Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(GraphDBModel, session)
