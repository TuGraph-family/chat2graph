from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.common.system_env import SystemEnv

# check if the system folder exists
system_path = SystemEnv.APP_ROOT + SystemEnv.SYSTEM_PATH
Path(system_path).mkdir(parents=True, exist_ok=True)

# engine and session factory
engine = create_engine(
    SystemEnv.DATABASE_URL,
    pool_size=SystemEnv.DATABASE_POOL_SIZE,
    max_overflow=SystemEnv.DATABASE_MAX_OVERFLOW,
    pool_timeout=SystemEnv.DATABASE_POOL_TIMEOUT,
    pool_recycle=SystemEnv.DATABASE_POOL_RECYCLE,
    pool_pre_ping=SystemEnv.DATABASE_POOL_PRE_PING,
)
DbSession = sessionmaker(autocommit=False, autoflush=True, bind=engine)
Do: DeclarativeMeta = declarative_base()
