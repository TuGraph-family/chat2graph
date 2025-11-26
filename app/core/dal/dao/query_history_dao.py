"""
Query History Data Access Object

提供对 QueryHistoryDo 的数据访问操作。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional
from sqlalchemy.orm import Session as SqlAlchemySession
from sqlalchemy import desc, func

from app.core.dal.dao.dao import Dao
from app.core.dal.do.query_history_do import QueryHistoryDo


class QueryHistoryDao(Dao[QueryHistoryDo]):
    """Query History DAO

    提供查询历史的数据访问方法。
    """

    def __init__(self, session: SqlAlchemySession):
        super().__init__(QueryHistoryDo, session)

    def get_by_session(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[QueryHistoryDo]:
        """获取会话的查询历史

        Args:
            session_id: 会话标识符
            limit: 返回记录数限制

        Returns:
            查询历史列表，按时间倒序
        """
        query = (
            self.session.query(self._model)
            .filter(self._model.session_id == session_id)
            .order_by(desc(self._model.created_at))
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_successful_queries(
        self,
        user_id: str,
        limit: Optional[int] = 10
    ) -> List[QueryHistoryDo]:
        """获取用户的成功查询历史

        Args:
            user_id: 用户标识符
            limit: 返回记录数限制

        Returns:
            成功查询历史列表
        """
        query = (
            self.session.query(self._model)
            .filter(
                self._model.user_id == user_id,
                self._model.success == True
            )
            .order_by(desc(self._model.created_at))
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def find_similar_queries(
        self,
        query_text: str,
        limit: int = 5
    ) -> List[QueryHistoryDo]:
        """查找相似的历史查询

        Args:
            query_text: 查询文本
            limit: 返回记录数限制

        Returns:
            相似查询列表
        """
        # 简单的文本相似度匹配，后续可以使用向量相似度
        search_terms = query_text.lower().split()

        query = (
            self.session.query(self._model)
            .filter(self._model.success == True)
        )

        # 对每个词进行模糊匹配
        for term in search_terms:
            query = query.filter(
                func.lower(self._model.query_text).like(f"%{term}%")
            )

        return query.order_by(desc(self._model.created_at)).limit(limit).all()

    def get_statistics(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> dict:
        """获取查询统计信息

        Args:
            user_id: 用户标识符（可选）
            start_time: 开始时间戳（可选）
            end_time: 结束时间戳（可选）

        Returns:
            统计信息字典
        """
        query = self.session.query(self._model)

        if user_id:
            query = query.filter(self._model.user_id == user_id)

        if start_time:
            query = query.filter(self._model.created_at >= start_time)

        if end_time:
            query = query.filter(self._model.created_at <= end_time)

        total_count = query.count()
        success_count = query.filter(self._model.success == True).count()

        # 计算平均延迟
        avg_latency = (
            query.filter(
                self._model.success == True,
                self._model.latency_ms.isnot(None)
            )
            .with_entities(func.avg(self._model.latency_ms))
            .scalar()
        )

        return {
            "total_queries": total_count,
            "successful_queries": success_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "average_latency_ms": float(avg_latency) if avg_latency else None,
        }
