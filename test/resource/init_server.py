from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.dal.init_db import init_db
from app.core.service.service_factory import ServiceFactory


def init_server():
    """Initialize the server by setting up the database and service factory."""
    # Initialize the database
    init_db()
    
    # Initialize the DAO factory with a database session
    DaoFactory.initialize(DbSession())
    
    # Initialize the service factory
    ServiceFactory.initialize()
