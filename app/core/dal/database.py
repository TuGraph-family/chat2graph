from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.common.system_env import SystemEnv

# check if the instance folder exists
project_root = Path(__file__).parents[3]
instance_path = project_root / "instance"
instance_path.mkdir(exist_ok=True)

# engine and session factory
engine = create_engine(SystemEnv.DATABASE_URL)
DB = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: DeclarativeMeta = declarative_base()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
