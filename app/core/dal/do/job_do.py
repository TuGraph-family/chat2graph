from uuid import uuid4

from sqlalchemy import Column, String, Text
from sqlalchemy.sql.sqltypes import Integer

from app.core.common.system_env import SystemEnv
from app.core.dal.database import Do


class JobDo(Do):  # type: ignore
    """Job table for storing job information"""

    __tablename__ = "job"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    goal = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    session_id = Column(String(36), nullable=False)  # FK constraint
    assigned_expert_name = Column(String(100), nullable=True)

    # sub job attributes
    output_schema = Column(Text, nullable=True)
    life_cycle = Column(Integer, default=SystemEnv.LIFE_CYCLE)

    reference_count = Column(Integer, default=0)
