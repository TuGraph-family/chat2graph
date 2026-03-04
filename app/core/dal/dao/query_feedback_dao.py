"""
Query Feedback Data Access Object

提供对 QueryFeedbackDo 的数据访问操作。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List
from sqlalchemy.orm import Session as SqlAlchemySession
from sqlalchemy import desc, func

from app.core.dal.dao.dao import Dao
from app.core.dal.do.query_feedback_do import QueryFeedbackDo


class QueryFeedbackDao(Dao[QueryFeedbackDo]):
    """Query Feedback DAO

    提供查询反馈的数据访问方法。
    """

    def __init__(self, session: SqlAlchemySession):
        super().__init__(QueryFeedbackDo, session)

    def get_by_query_history(self, query_history_id: str) -> List[QueryFeedbackDo]:
        """获取指定查询的所有反馈

        Args:
            query_history_id: 查询历史记录 ID

        Returns:
            反馈列表
        """
        return (
            self.session.query(self._model)
            .filter(self._model.query_history_id == query_history_id)
            .order_by(desc(self._model.created_at))
            .all()
        )

    def get_by_user(
        self,
        user_id: str,
        feedback_type: str = None
    ) -> List[QueryFeedbackDo]:
        """获取用户的反馈记录

        Args:
            user_id: 用户标识符
            feedback_type: 反馈类型（可选）

        Returns:
            反馈列表
        """
        query = (
            self.session.query(self._model)
            .filter(self._model.user_id == user_id)
        )

        if feedback_type:
            query = query.filter(self._model.feedback_type == feedback_type)

        return query.order_by(desc(self._model.created_at)).all()

    def aggregate_feedback(
        self,
        query_history_id: str = None
    ) -> dict:
        """聚合反馈统计

        Args:
            query_history_id: 查询历史记录 ID（可选）

        Returns:
            聚合统计字典
        """
        query = self.session.query(self._model)

        if query_history_id:
            query = query.filter(
                self._model.query_history_id == query_history_id
            )

        total_count = query.count()

        # 统计各类型反馈数量
        feedback_counts = (
            query.with_entities(
                self._model.feedback_type,
                func.count(self._model.id)
            )
            .group_by(self._model.feedback_type)
            .all()
        )

        # 统计反馈值分布
        value_stats = (
            query.filter(self._model.feedback_value.isnot(None))
            .with_entities(
                func.sum(self._model.feedback_value),
                func.avg(self._model.feedback_value)
            )
            .first()
        )

        feedback_type_dist = {
            feedback_type: count
            for feedback_type, count in feedback_counts
        }

        return {
            "total_feedback": total_count,
            "feedback_type_distribution": feedback_type_dist,
            "total_value": int(value_stats[0]) if value_stats[0] else 0,
            "average_value": float(value_stats[1]) if value_stats[1] else 0.0,
        }
