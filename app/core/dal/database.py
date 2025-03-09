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
# TODO: config the sqlalchemy settings in the .env file
engine = create_engine(
    SystemEnv.DATABASE_URL,
    pool_size=50,
    max_overflow=50,
    pool_timeout=60,
    pool_recycle=3600,
    pool_pre_ping=True,
)
DB = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: DeclarativeMeta = declarative_base()
