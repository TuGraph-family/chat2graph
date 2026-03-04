"""
Query Pattern 持久化模型

此模型存储查询模式库，用于模式识别、查询推荐和性能优化。

Author: kaichuan
Date: 2025-11-25
"""

from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Integer, Float, JSON, Index
from sqlalchemy.sql import func
from app.core.dal.database import Do


class QueryPatternDo(Do):
    """Query Pattern 持久化模型

    存储查询模式的元数据和统计信息，支持模式匹配和查询优化。

    Attributes:
        id: 模式记录唯一标识符 (UUID)
        pattern_type: 模式类型
            - 'DIRECT': 直接查询
            - 'MULTI_HOP': 多跳查询
            - 'AGGREGATION': 聚合查询
            - 'TEMPORAL': 时间查询
            - 'SPATIAL': 空间查询
            - 'PATTERN_MATCH': 模式匹配
        pattern_template: 参数化的查询模板
        pattern_signature: 模式签名（用于快速匹配）
        example_queries: 示例自然语言查询（JSON 数组）
        cypher_template: 参数化的 Cypher 模板
        frequency: 使用频次统计
        success_rate: 成功率（0-1）
        avg_latency_ms: 平均执行延迟（毫秒）
        avg_token_usage: 平均 Token 消耗
        metadata: 额外的元数据（JSON 格式）
        created_at: 创建时间戳（Unix 时间）
        updated_at: 更新时间戳（Unix 时间）
    """

    __tablename__ = "query_pattern"

    # ==================== 基本信息 ====================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="模式记录唯一标识符 (UUID)"
    )

    pattern_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="模式类型"
    )

    pattern_template = Column(
        Text,
        nullable=False,
        comment="参数化的查询模板"
    )

    pattern_signature = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="模式签名（用于快速匹配）"
    )

    # ==================== 示例和模板 ====================
    example_queries = Column(
        JSON,
        nullable=True,
        comment="示例自然语言查询（JSON 数组）"
    )

    cypher_template = Column(
        Text,
        nullable=True,
        comment="参数化的 Cypher 模板"
    )

    # ==================== 统计信息 ====================
    frequency = Column(
        Integer,
        nullable=False,
        default=0,
        comment="使用频次统计"
    )

    success_rate = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="成功率（0-1）"
    )

    avg_latency_ms = Column(
        Float,
        nullable=True,
        comment="平均执行延迟（毫秒）"
    )

    avg_token_usage = Column(
        Integer,
        nullable=True,
        comment="平均 Token 消耗"
    )

    # ==================== 元数据 ====================
    pattern_metadata = Column(
        JSON,
        nullable=True,
        comment="额外的元数据（JSON 格式）"
    )

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

    # ==================== 索引 ====================
    __table_args__ = (
        Index('idx_pattern_type', 'pattern_type'),
        Index('idx_pattern_signature', 'pattern_signature'),
        Index('idx_frequency', 'frequency'),
        Index('idx_success_rate', 'success_rate'),
        Index('idx_type_frequency', 'pattern_type', 'frequency'),
    )

    def __repr__(self):
        """字符串表示"""
        return (
            f"<QueryPatternDo(id={self.id}, type={self.pattern_type}, "
            f"frequency={self.frequency}, success_rate={self.success_rate:.2f})>"
        )

    def to_dict(self):
        """转换为字典

        Returns:
            dict: 模式信息字典
        """
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "pattern_template": self.pattern_template,
            "pattern_signature": self.pattern_signature,
            "example_queries": self.example_queries,
            "cypher_template": self.cypher_template,
            "frequency": self.frequency,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_token_usage": self.avg_token_usage,
            "pattern_metadata": self.pattern_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
