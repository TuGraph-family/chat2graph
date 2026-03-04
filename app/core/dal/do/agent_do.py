"""Agent Configuration Persistence Model.

This model stores Agent configuration information, not runtime instances.
Agent instances are reconstructed from configuration when needed.
"""

from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Boolean, JSON, Index
from sqlalchemy.sql import func
from app.core.dal.database import Do


class AgentDo(Do):
    """Agent Configuration Persistence Model.

    Stores Agent configuration information, supports both Leader and Expert types.
    Enables cross-restart persistence by storing configuration rather than instances.

    Attributes:
        id: Agent unique identifier (UUID)
        agent_type: Agent type, 'leader' or 'expert'
        name: Agent name (unique)
        description: Agent description
        reasoner_type: Reasoner type, e.g. 'DualModelReasoner', 'MonoModelReasoner'
        reasoner_config: Reasoner configuration parameters (JSON format)
        workflow_type: Workflow type (class name)
        workflow_config: Workflow configuration parameters (JSON format)
        leader_state_type: LeaderState type, only for leader
        created_at: Creation timestamp (Unix time)
        updated_at: Update timestamp (Unix time)
        is_active: Whether active
    """

    __tablename__ = "agent"

    # ==================== Basic Information ====================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Agent unique identifier (UUID)"
    )

    agent_type = Column(
        String(20),
        nullable=False,
        comment="Agent type: 'leader' or 'expert'"
    )

    name = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="Agent name (unique)"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Agent description"
    )

    # ==================== Configuration Information ====================
    reasoner_type = Column(
        String(50),
        nullable=False,
        comment="Reasoner type, e.g. 'DualModelReasoner', 'MonoModelReasoner'"
    )

    reasoner_config = Column(
        JSON,
        nullable=True,
        comment="Reasoner configuration parameters (JSON format)"
    )

    workflow_type = Column(
        String(100),
        nullable=False,
        comment="Workflow type (class name)"
    )

    workflow_config = Column(
        JSON,
        nullable=True,
        comment="Workflow configuration parameters (JSON format)"
    )

    # ==================== Leader Specific Fields ====================
    leader_state_type = Column(
        String(50),
        nullable=True,
        comment="LeaderState type, only for leader"
    )

    # ==================== Metadata ====================
    created_at = Column(
        BigInteger,
        server_default=func.strftime("%s", "now"),
        comment="Creation timestamp (Unix time)"
    )

    updated_at = Column(
        BigInteger,
        onupdate=func.strftime("%s", "now"),
        comment="Update timestamp (Unix time)"
    )

    is_active = Column(
        Boolean,
        default=True,
        comment="Whether active"
    )

    # ==================== Indexes ====================
    __table_args__ = (
        Index('idx_agent_type', 'agent_type'),
        Index('idx_agent_name', 'name'),
        Index('idx_is_active', 'is_active'),
        Index('idx_agent_type_active', 'agent_type', 'is_active'),
    )

    def __repr__(self):
        """String representation."""
        return (
            f"<AgentDo(id={self.id}, name={self.name}, "
            f"type={self.agent_type}, active={self.is_active})>"
        )

    def to_dict(self):
        """Convert to dictionary.

        Returns:
            dict: Agent configuration dictionary
        """
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "reasoner_type": self.reasoner_type,
            "reasoner_config": self.reasoner_config,
            "workflow_type": self.workflow_type,
            "workflow_config": self.workflow_config,
            "leader_state_type": self.leader_state_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
        }
