"""
Query Feedback 持久化模型

此模型存储用户对查询结果的反馈信息，用于查询质量改进和学习优化。

Author: kaichuan
Date: 2025-11-25
"""

from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Integer, JSON, Index
from sqlalchemy.sql import func
from app.core.dal.database import Do


class QueryFeedbackDo(Do):
    """Query Feedback 持久化模型

    存储用户反馈信息，支持多种反馈类型，用于持续改进查询质量。

    Attributes:
        id: 反馈记录唯一标识符 (UUID)
        query_history_id: 关联的查询历史记录 ID
        user_id: 用户标识符
        feedback_type: 反馈类型
            - 'thumbs_up': 点赞
            - 'thumbs_down': 点踩
            - 'correction': 纠正
            - 'suggestion': 建议
        feedback_value: 反馈数值 (+1 为正面, -1 为负面, 0 为中性)
        correction_data: 纠正数据（JSON 格式）
            - corrected_query: 用户纠正后的查询
            - corrected_result: 用户期望的结果
        comment: 用户评论或建议
        created_at: 创建时间戳（Unix 时间）
    """

    __tablename__ = "query_feedback"

    # ==================== 基本信息 ====================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="反馈记录唯一标识符 (UUID)"
    )

    query_history_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="关联的查询历史记录 ID"
    )

    user_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="用户标识符"
    )

    # ==================== 反馈信息 ====================
    feedback_type = Column(
        String(50),
        nullable=False,
        comment="反馈类型: thumbs_up, thumbs_down, correction, suggestion"
    )

    feedback_value = Column(
        Integer,
        nullable=True,
        comment="反馈数值 (+1 正面, -1 负面, 0 中性)"
    )

    correction_data = Column(
        JSON,
        nullable=True,
        comment="纠正数据（JSON 格式）"
    )

    comment = Column(
        Text,
        nullable=True,
        comment="用户评论或建议"
    )

    # ==================== 元数据 ====================
    created_at = Column(
        BigInteger,
        server_default=func.strftime("%s", "now"),
        comment="创建时间戳（Unix 时间）"
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index('idx_query_feedback_history_id', 'query_history_id'),
        Index('idx_query_feedback_user_id', 'user_id'),
        Index('idx_query_feedback_type', 'feedback_type'),
        Index('idx_query_feedback_created_at', 'created_at'),
        Index('idx_query_feedback_value', 'feedback_value'),
    )

    def __repr__(self):
        """字符串表示"""
        return (
            f"<QueryFeedbackDo(id={self.id}, "
            f"query_id={self.query_history_id}, "
            f"type={self.feedback_type}, value={self.feedback_value})>"
        )

    def to_dict(self):
        """转换为字典

        Returns:
            dict: 反馈信息字典
        """
        return {
            "id": self.id,
            "query_history_id": self.query_history_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type,
            "feedback_value": self.feedback_value,
            "correction_data": self.correction_data,
            "comment": self.comment,
            "created_at": self.created_at,
        }
