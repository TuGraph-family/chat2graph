"""
Agent 配置持久化模型

此模型存储 Agent 的配置信息，而非运行时实例。
Agent 实例在需要时根据配置重建。

Author: Issue #40 Implementation
Date: 2025-11-24
"""

from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Boolean, JSON, Index
from sqlalchemy.sql import func
from app.core.dal.database import Do


class AgentDo(Do):
    """Agent 配置持久化模型

    存储 Agent 的配置信息，支持 Leader 和 Expert 两种类型。
    通过存储配置而非实例，实现跨重启持久化。

    Attributes:
        id: Agent 唯一标识符 (UUID)
        agent_type: Agent 类型，'leader' 或 'expert'
        name: Agent 名称（唯一）
        description: Agent 描述信息
        reasoner_type: Reasoner 类型，如 'DualReasoner', 'MonoReasoner'
        reasoner_config: Reasoner 配置参数（JSON 格式）
        workflow_type: Workflow 类型（类名）
        workflow_config: Workflow 配置参数（JSON 格式）
        leader_state_type: LeaderState 类型，仅 leader 使用
        created_at: 创建时间戳（Unix 时间）
        updated_at: 更新时间戳（Unix 时间）
        is_active: 是否激活
    """

    __tablename__ = "agent"

    # ==================== 基本信息 ====================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Agent 唯一标识符 (UUID)"
    )

    agent_type = Column(
        String(20),
        nullable=False,
        comment="Agent 类型: 'leader' 或 'expert'"
    )

    name = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="Agent 名称（唯一）"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Agent 描述信息"
    )

    # ==================== 配置信息 ====================
    reasoner_type = Column(
        String(50),
        nullable=False,
        comment="Reasoner 类型，如 'DualReasoner', 'MonoReasoner'"
    )

    reasoner_config = Column(
        JSON,
        nullable=True,
        comment="Reasoner 配置参数（JSON 格式）"
    )

    workflow_type = Column(
        String(100),
        nullable=False,
        comment="Workflow 类型（类名）"
    )

    workflow_config = Column(
        JSON,
        nullable=True,
        comment="Workflow 配置参数（JSON 格式）"
    )

    # ==================== Leader 特定字段 ====================
    leader_state_type = Column(
        String(50),
        nullable=True,
        comment="LeaderState 类型，仅 leader 使用"
    )

    # ==================== 元数据 ====================
    created_at = Column(
        BigInteger,
        server_default=func.strftime("%s", "now"),
        comment="创建时间戳（Unix 时间）"
    )

    updated_at = Column(
        BigInteger,
        onupdate=func.strftime("%s", "now"),
        comment="更新时间戳（Unix 时间）"
    )

    is_active = Column(
        Boolean,
        default=True,
        comment="是否激活"
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index('idx_agent_type', 'agent_type'),
        Index('idx_agent_name', 'name'),
        Index('idx_is_active', 'is_active'),
        Index('idx_agent_type_active', 'agent_type', 'is_active'),
    )

    def __repr__(self):
        """字符串表示"""
        return (
            f"<AgentDo(id={self.id}, name={self.name}, "
            f"type={self.agent_type}, active={self.is_active})>"
        )

    def to_dict(self):
        """转换为字典

        Returns:
            dict: Agent 配置字典
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
