from app.core.dal.database import Do, engine
from app.core.dal.do.file_descriptor_do import FileDescriptorDo
from app.core.dal.do.graph_db_do import GraphDbDo
from app.core.dal.do.job_do import JobDo
from app.core.dal.do.knowledge_do import KnowledgeBaseDo
from app.core.dal.do.message_do import MessageDo
from app.core.dal.do.session_do import SessionDo


def init_db() -> None:
    """Initialize database tables."""
    # Do.metadata.drop_all(bind=engine)

    # create tables in order
    GraphDbDo.__table__.create(engine, checkfirst=True)
    FileDescriptorDo.__table__.create(engine, checkfirst=True)
    KnowledgeBaseDo.__table__.create(engine, checkfirst=True)
    SessionDo.__table__.create(engine, checkfirst=True)
    JobDo.__table__.create(engine, checkfirst=True)
    MessageDo.__table__.create(engine, checkfirst=True)

    Do.metadata.create_all(bind=engine)
