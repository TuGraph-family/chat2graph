"""
Query Session 持久化模型

此模型存储用户的查询会话信息，包括会话上下文、用户偏好等。
用于实现上下文感知的查询生成。

Author: kaichuan
Date: 2025-11-25
"""

from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Boolean, JSON, Index
from sqlalchemy.sql import func
from app.core.dal.database import Do


class QuerySessionDo(Do):
    """Query Session 持久化模型

    存储用户查询会话的上下文信息，支持跨会话的用户偏好学习。

    Attributes:
        id: 会话记录唯一标识符 (UUID)
        user_id: 用户标识符
        session_id: 会话标识符（唯一）
        context_data: 会话上下文数据（JSON 格式）
            - user_preferences: 用户偏好设置
            - session_state: 会话状态信息
            - recent_queries: 最近查询摘要
        created_at: 创建时间戳（Unix 时间）
        updated_at: 更新时间戳（Unix 时间）
        last_active_at: 最后活跃时间戳
        is_active: 是否为活跃会话
    """

    __tablename__ = "query_session"

    # ==================== 基本信息 ====================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="会话记录唯一标识符 (UUID)"
    )

    user_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="用户标识符"
    )

    session_id = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="会话标识符（唯一）"
    )

    # ==================== 上下文数据 ====================
    context_data = Column(
        JSON,
        nullable=True,
        comment="会话上下文数据（JSON 格式）"
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

    last_active_at = Column(
        BigInteger,
        nullable=True,
        comment="最后活跃时间戳"
    )

    is_active = Column(
        Boolean,
        default=True,
        comment="是否为活跃会话"
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index('idx_query_session_user_session', 'user_id', 'session_id'),
        Index('idx_query_session_session_id', 'session_id'),
        Index('idx_query_session_created_at', 'created_at'),
        Index('idx_query_session_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self):
        """字符串表示"""
        return (
            f"<QuerySessionDo(id={self.id}, session_id={self.session_id}, "
            f"user_id={self.user_id}, active={self.is_active})>"
        )

    def to_dict(self):
        """转换为字典

        Returns:
            dict: 会话信息字典
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context_data": self.context_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_active_at": self.last_active_at,
            "is_active": self.is_active,
        }
