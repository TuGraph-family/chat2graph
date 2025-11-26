"""
Query History 持久化模型

此模型存储查询历史记录，包括自然语言查询、生成的 Cypher、
执行结果、性能指标等信息。

Author: kaichuan
Date: 2025-11-25
"""

from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Boolean, Integer, JSON, Index
from sqlalchemy.sql import func
from app.core.dal.database import Do


class QueryHistoryDo(Do):
    """Query History 持久化模型

    存储完整的查询执行历史，支持查询分析、模式挖掘和反馈学习。

    Attributes:
        id: 历史记录唯一标识符 (UUID)
        session_id: 关联的会话标识符
        user_id: 用户标识符
        query_text: 用户输入的自然语言查询
        query_cypher: 生成的 Cypher 查询语句
        query_intention: 查询意图分析结果（JSON 格式）
        complexity_analysis: 复杂度分析结果（JSON 格式）
        path_patterns: 路径模式分析结果（JSON 格式）
        validation_result: 验证结果详情（JSON 格式）
        result_data: 查询结果数据（摘要形式，JSON 格式）
        result_count: 结果记录数
        success: 查询是否成功执行
        error_message: 错误信息（如果失败）
        latency_ms: 执行延迟（毫秒）
        token_usage: Token 使用统计（JSON 格式）
        agents_executed: 执行的 Agent 列表（JSON 格式）
        created_at: 创建时间戳（Unix 时间）
    """

    __tablename__ = "query_history"

    # ==================== 基本信息 ====================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="历史记录唯一标识符 (UUID)"
    )

    session_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="关联的会话标识符"
    )

    user_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="用户标识符"
    )

    # ==================== 查询信息 ====================
    query_text = Column(
        Text,
        nullable=False,
        comment="用户输入的自然语言查询"
    )

    query_cypher = Column(
        Text,
        nullable=True,
        comment="生成的 Cypher 查询语句"
    )

    # ==================== 分析结果 ====================
    query_intention = Column(
        JSON,
        nullable=True,
        comment="查询意图分析结果（JSON 格式）"
    )

    complexity_analysis = Column(
        JSON,
        nullable=True,
        comment="复杂度分析结果（JSON 格式）"
    )

    path_patterns = Column(
        JSON,
        nullable=True,
        comment="路径模式分析结果（JSON 格式）"
    )

    validation_result = Column(
        JSON,
        nullable=True,
        comment="验证结果详情（JSON 格式）"
    )

    # ==================== 执行结果 ====================
    result_data = Column(
        JSON,
        nullable=True,
        comment="查询结果数据（摘要形式，JSON 格式）"
    )

    result_count = Column(
        Integer,
        nullable=True,
        comment="结果记录数"
    )

    success = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="查询是否成功执行"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息（如果失败）"
    )

    # ==================== 性能指标 ====================
    latency_ms = Column(
        Integer,
        nullable=True,
        comment="执行延迟（毫秒）"
    )

    token_usage = Column(
        JSON,
        nullable=True,
        comment="Token 使用统计（JSON 格式）"
    )

    agents_executed = Column(
        JSON,
        nullable=True,
        comment="执行的 Agent 列表（JSON 格式）"
    )

    # ==================== 元数据 ====================
    created_at = Column(
        BigInteger,
        server_default=func.strftime("%s", "now"),
        comment="创建时间戳（Unix 时间）"
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index('idx_query_history_session_id', 'session_id'),
        Index('idx_query_history_user_id', 'user_id'),
        Index('idx_query_history_created_at', 'created_at'),
        Index('idx_query_history_success', 'success'),
        Index('idx_query_history_user_success', 'user_id', 'success'),
        Index('idx_query_history_session_created', 'session_id', 'created_at'),
    )

    def __repr__(self):
        """字符串表示"""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"<QueryHistoryDo(id={self.id}, session={self.session_id}, "
            f"status={status}, latency={self.latency_ms}ms)>"
        )

    def to_dict(self):
        """转换为字典

        Returns:
            dict: 查询历史信息字典
        """
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query_text": self.query_text,
            "query_cypher": self.query_cypher,
            "query_intention": self.query_intention,
            "complexity_analysis": self.complexity_analysis,
            "path_patterns": self.path_patterns,
            "validation_result": self.validation_result,
            "result_data": self.result_data,
            "result_count": self.result_count,
            "success": self.success,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "token_usage": self.token_usage,
            "agents_executed": self.agents_executed,
            "created_at": self.created_at,
        }
