from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, Float, String, Text
from sqlalchemy.sql.sqltypes import Integer

from app.core.common.system_env import SystemEnv
from app.core.common.type import JobStatus
from app.core.dal.database import Do
from app.core.model.job import JobType


class JobDo(Do):  # type: ignore
    """Job table for storing job information"""

    __tablename__ = "job"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    goal = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    session_id = Column(String(36), nullable=False)  # FK constraint

    # category
    category = Column(String(36), default=JobType.JOB.value)

    # job attributes
    assigned_expert_name = Column(String(100), nullable=True)
    dag = Column(JSON, nullable=True)

    # sub job attributes
    original_job_id = Column(String(36), nullable=True)
    expert_id = Column(String(36), nullable=True)
    output_schema = Column(Text, nullable=True)
    life_cycle = Column(Integer, default=SystemEnv.LIFE_CYCLE)
    is_legacy = Column(Boolean, default=False)
    thinking = Column(Text, nullable=True)

    # job result
    status = Column(String(36), default=JobStatus.CREATED.value)
    message_id = Column(String(36), nullable=True)  # FK constraint
    duration = Column(Float, default=0.0)
    tokens = Column(Integer, default=0)
