"""
Query Pattern Data Access Object

提供对 QueryPatternDo 的数据访问操作。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional
from sqlalchemy.orm import Session as SqlAlchemySession
from sqlalchemy import desc

from app.core.dal.dao.dao import Dao
from app.core.dal.do.query_pattern_do import QueryPatternDo


class QueryPatternDao(Dao[QueryPatternDo]):
    """Query Pattern DAO

    提供查询模式的数据访问方法。
    """

    def __init__(self, session: SqlAlchemySession):
        super().__init__(QueryPatternDo, session)

    def get_by_signature(self, pattern_signature: str) -> Optional[QueryPatternDo]:
        """根据模式签名获取模式记录

        Args:
            pattern_signature: 模式签名

        Returns:
            QueryPatternDo 对象，如果不存在则返回 None
        """
        results = self.filter_by(pattern_signature=pattern_signature)
        return results[0] if results else None

    def get_by_type(
        self,
        pattern_type: str,
        limit: Optional[int] = None
    ) -> List[QueryPatternDo]:
        """获取指定类型的模式

        Args:
            pattern_type: 模式类型
            limit: 返回记录数限制

        Returns:
            模式列表，按频次倒序
        """
        query = (
            self.session.query(self._model)
            .filter(self._model.pattern_type == pattern_type)
            .order_by(desc(self._model.frequency))
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_top_patterns(
        self,
        limit: int = 10,
        min_frequency: int = 1
    ) -> List[QueryPatternDo]:
        """获取最常用的模式

        Args:
            limit: 返回记录数限制
            min_frequency: 最小频次阈值

        Returns:
            模式列表，按频次倒序
        """
        return (
            self.session.query(self._model)
            .filter(self._model.frequency >= min_frequency)
            .order_by(desc(self._model.frequency))
            .limit(limit)
            .all()
        )

    def increment_frequency(
        self,
        pattern_signature: str
    ) -> QueryPatternDo:
        """增加模式使用频次

        Args:
            pattern_signature: 模式签名

        Returns:
            更新后的 QueryPatternDo 对象
        """
        pattern = self.get_by_signature(pattern_signature)
        if not pattern:
            raise ValueError(f"Pattern {pattern_signature} not found")

        new_frequency = pattern.frequency + 1
        return self.update(id=pattern.id, frequency=new_frequency)

    def update_statistics(
        self,
        pattern_signature: str,
        success: bool,
        latency_ms: Optional[int] = None,
        token_usage: Optional[int] = None
    ) -> QueryPatternDo:
        """更新模式统计信息

        Args:
            pattern_signature: 模式签名
            success: 是否成功
            latency_ms: 执行延迟（可选）
            token_usage: Token 使用量（可选）

        Returns:
            更新后的 QueryPatternDo 对象
        """
        pattern = self.get_by_signature(pattern_signature)
        if not pattern:
            raise ValueError(f"Pattern {pattern_signature} not found")

        # 更新成功率（增量计算）
        total_executions = pattern.frequency
        current_successes = pattern.success_rate * (total_executions - 1)
        new_successes = current_successes + (1 if success else 0)
        new_success_rate = new_successes / total_executions if total_executions > 0 else 0

        update_data = {
            "success_rate": new_success_rate
        }

        # 更新平均延迟（增量计算）
        if latency_ms is not None and pattern.avg_latency_ms is not None:
            new_avg_latency = (
                (pattern.avg_latency_ms * (total_executions - 1) + latency_ms)
                / total_executions
            )
            update_data["avg_latency_ms"] = new_avg_latency
        elif latency_ms is not None:
            update_data["avg_latency_ms"] = float(latency_ms)

        # 更新平均 Token 使用量（增量计算）
        if token_usage is not None and pattern.avg_token_usage is not None:
            new_avg_tokens = (
                (pattern.avg_token_usage * (total_executions - 1) + token_usage)
                / total_executions
            )
            update_data["avg_token_usage"] = int(new_avg_tokens)
        elif token_usage is not None:
            update_data["avg_token_usage"] = token_usage

        return self.update(id=pattern.id, **update_data)
