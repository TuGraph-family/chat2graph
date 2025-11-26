"""
Query Session Data Access Object

提供对 QuerySessionDo 的数据访问操作。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional
from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.query_session_do import QuerySessionDo


class QuerySessionDao(Dao[QuerySessionDo]):
    """Query Session DAO

    提供查询会话的数据访问方法。
    """

    def __init__(self, session: SqlAlchemySession):
        super().__init__(QuerySessionDo, session)

    def get_by_session_id(self, session_id: str) -> Optional[QuerySessionDo]:
        """根据会话 ID 获取会话记录

        Args:
            session_id: 会话标识符

        Returns:
            QuerySessionDo 对象，如果不存在则返回 None
        """
        results = self.filter_by(session_id=session_id)
        return results[0] if results else None

    def get_active_sessions_by_user(self, user_id: str) -> List[QuerySessionDo]:
        """获取用户的所有活跃会话

        Args:
            user_id: 用户标识符

        Returns:
            活跃会话列表
        """
        return (
            self.session.query(self._model)
            .filter(
                self._model.user_id == user_id,
                self._model.is_active == True
            )
            .order_by(self._model.last_active_at.desc())
            .all()
        )

    def deactivate_session(self, session_id: str) -> QuerySessionDo:
        """停用会话

        Args:
            session_id: 会话标识符

        Returns:
            更新后的 QuerySessionDo 对象
        """
        session = self.get_by_session_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return self.update(id=session.id, is_active=False)

    def update_context(
        self,
        session_id: str,
        context_data: dict
    ) -> QuerySessionDo:
        """更新会话上下文

        Args:
            session_id: 会话标识符
            context_data: 新的上下文数据

        Returns:
            更新后的 QuerySessionDo 对象
        """
        import time
        session = self.get_by_session_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return self.update(
            id=session.id,
            context_data=context_data,
            last_active_at=int(time.time())
        )
