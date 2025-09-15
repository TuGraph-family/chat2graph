from app.core.common.system_env import SystemEnv
from app.core.dal.database import Do, engine
from app.core.dal.do.artifact_do import ArtifactDo
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
    print(f"System database url: {SystemEnv.DATABASE_URL}")

    # create tables in an order that respects potential dependencies
    Do.metadata.create_all(
        bind=engine,
        tables=[
            GraphDbDo.__table__,
            FileDescriptorDo.__table__,
            KnowledgeBaseDo.__table__,
            SessionDo.__table__,
            JobDo.__table__,
            MessageDo.__table__,
            ArtifactDo.__table__,
        ],
        checkfirst=True,
    )
