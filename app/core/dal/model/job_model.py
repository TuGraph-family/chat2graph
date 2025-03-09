from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.sql.sqltypes import Integer

from app.core.common.system_env import SystemEnv
from app.core.dal.database import Base


class JobModel(Base):  # type: ignore
    """Job table for storing job information"""

    __tablename__ = "job"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    goal = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    session_id = Column(
        String(36), ForeignKey("session.id", use_alter=True, name="fk_job_session"), nullable=False
    )
    assigned_expert_name = Column(String(100), nullable=True)

    # sub job attributes
    output_schema = Column(Text, nullable=True)
    life_cycle = Column(Integer, default=SystemEnv.LIFE_CYCLE)

    reference_count = Column(Integer, default=0)
