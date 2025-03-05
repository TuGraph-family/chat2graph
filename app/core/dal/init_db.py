from app.core.dal.database import Base, engine
from app.core.dal.model.job_model import JobModel
from app.core.dal.model.message_model import MessageModel, agent_workflow_links
from app.core.dal.model.session_model import SessionModel


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.drop_all(bind=engine)

    # create tables in order
    SessionModel.__table__.create(engine, checkfirst=True)
    JobModel.__table__.create(engine, checkfirst=True)
    MessageModel.__table__.create(engine, checkfirst=True)
    agent_workflow_links.create(engine, checkfirst=True)

    Base.metadata.create_all(bind=engine)
