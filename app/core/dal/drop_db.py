from app.core.dal.database import Do, engine
from app.core.dal.do.file_descriptor_do import FileDescriptorDo  # noqa: F401
from app.core.dal.do.graph_db_do import GraphDbDo  # noqa: F401
from app.core.dal.do.job_do import JobDo  # noqa: F401
from app.core.dal.do.knowledge_do import KnowledgeBaseDo  # noqa: F401
from app.core.dal.do.message_do import MessageDo  # noqa: F401
from app.core.dal.do.session_do import SessionDo  # noqa: F401


def drop_db() -> None:
    """Drop database tables."""
    Do.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    drop_db()
