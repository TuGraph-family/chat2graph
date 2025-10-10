from app.core.common.logger import Chat2GraphLogger
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.dal.init_db import init_db
from app.core.service.service_factory import ServiceFactory


def init_server():
    """Initialize the server by setting up the database and service factory."""
    # initialize logging
    Chat2GraphLogger()

    # initialize the database
    init_db()

    # initialize the DAO factory with a database session
    DaoFactory.initialize(DbSession())

    # initialize the service factory
    ServiceFactory.initialize()
