"""
Query Context Service

提供查询会话上下文管理服务，支持用户偏好学习和会话历史追踪。

Author: kaichuan
Date: 2025-11-25
"""

from typing import Dict, List, Optional
import time
from uuid import uuid4

from app.core.common.singleton import Singleton
from app.core.dal.dao.query_session_dao import QuerySessionDao
from app.core.dal.dao.query_history_dao import QueryHistoryDao
from app.core.dal.do.query_session_do import QuerySessionDo
from app.core.dal.do.query_history_do import QueryHistoryDo
from app.core.dal.database import DbSession


class QueryContextService(metaclass=Singleton):
    """Query Context Service

    管理查询会话的上下文信息，包括用户偏好、会话状态和查询历史。
    """

    def __init__(self):
        """初始化服务"""
        session = DbSession()
        self._session_dao = QuerySessionDao(session)
        self._history_dao = QueryHistoryDao(session)

    def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        initial_context: Optional[Dict] = None
    ) -> QuerySessionDo:
        """创建新的查询会话

        Args:
            user_id: 用户标识符
            session_id: 会话标识符（可选，不提供则自动生成）
            initial_context: 初始上下文数据（可选）

        Returns:
            创建的会话对象
        """
        if session_id is None:
            session_id = f"session_{uuid4().hex}"

        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "context_data": initial_context or {},
            "last_active_at": int(time.time()),
            "is_active": True,
        }

        return self._session_dao.create(**session_data)

    def get_session(self, session_id: str) -> Optional[QuerySessionDo]:
        """获取会话信息

        Args:
            session_id: 会话标识符

        Returns:
            会话对象，如果不存在则返回 None
        """
        return self._session_dao.get_by_session_id(session_id)

    def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> QuerySessionDo:
        """获取或创建会话

        Args:
            user_id: 用户标识符
            session_id: 会话标识符（可选）

        Returns:
            会话对象
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session

        return self.create_session(user_id, session_id)

    def update_context(
        self,
        session_id: str,
        context_updates: Dict
    ) -> QuerySessionDo:
        """更新会话上下文

        Args:
            session_id: 会话标识符
            context_updates: 上下文更新数据

        Returns:
            更新后的会话对象
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 合并上下文数据
        current_context = session.context_data or {}
        merged_context = {**current_context, **context_updates}

        return self._session_dao.update_context(session_id, merged_context)

    def get_user_preferences(self, session_id: str) -> Dict:
        """获取用户偏好设置

        Args:
            session_id: 会话标识符

        Returns:
            用户偏好字典
        """
        session = self.get_session(session_id)
        if not session or not session.context_data:
            return {}

        return session.context_data.get("user_preferences", {})

    def update_user_preferences(
        self,
        session_id: str,
        preferences: Dict
    ) -> QuerySessionDo:
        """更新用户偏好设置

        Args:
            session_id: 会话标识符
            preferences: 偏好设置

        Returns:
            更新后的会话对象
        """
        return self.update_context(
            session_id,
            {"user_preferences": preferences}
        )

    def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = 10
    ) -> List[QueryHistoryDo]:
        """获取会话的查询历史

        Args:
            session_id: 会话标识符
            limit: 返回记录数限制

        Returns:
            查询历史列表
        """
        return self._history_dao.get_by_session(session_id, limit)

    def get_relevant_history(
        self,
        query_text: str,
        limit: int = 5
    ) -> List[QueryHistoryDo]:
        """获取相关的历史查询

        Args:
            query_text: 当前查询文本
            limit: 返回记录数限制

        Returns:
            相似查询列表
        """
        return self._history_dao.find_similar_queries(query_text, limit)

    def save_query(
        self,
        session_id: str,
        user_id: str,
        query_text: str,
        query_cypher: Optional[str] = None,
        query_intention: Optional[Dict] = None,
        complexity_analysis: Optional[Dict] = None,
        path_patterns: Optional[Dict] = None,
        validation_result: Optional[Dict] = None,
        result_data: Optional[Dict] = None,
        result_count: Optional[int] = None,
        success: bool = False,
        error_message: Optional[str] = None,
        latency_ms: Optional[int] = None,
        token_usage: Optional[Dict] = None,
        agents_executed: Optional[List[str]] = None
    ) -> QueryHistoryDo:
        """保存查询记录

        Args:
            session_id: 会话标识符
            user_id: 用户标识符
            query_text: 查询文本
            query_cypher: 生成的 Cypher（可选）
            query_intention: 查询意图分析（可选）
            complexity_analysis: 复杂度分析（可选）
            path_patterns: 路径模式分析（可选）
            validation_result: 验证结果（可选）
            result_data: 结果数据（可选）
            result_count: 结果记录数（可选）
            success: 是否成功
            error_message: 错误信息（可选）
            latency_ms: 执行延迟（可选）
            token_usage: Token 使用统计（可选）
            agents_executed: 执行的 Agent 列表（可选）

        Returns:
            创建的查询历史对象
        """
        query_data = {
            "session_id": session_id,
            "user_id": user_id,
            "query_text": query_text,
            "query_cypher": query_cypher,
            "query_intention": query_intention,
            "complexity_analysis": complexity_analysis,
            "path_patterns": path_patterns,
            "validation_result": validation_result,
            "result_data": result_data,
            "result_count": result_count,
            "success": success,
            "error_message": error_message,
            "latency_ms": latency_ms,
            "token_usage": token_usage,
            "agents_executed": agents_executed,
        }

        return self._history_dao.create(**query_data)

    def get_session_statistics(self, session_id: str) -> Dict:
        """获取会话统计信息

        Args:
            session_id: 会话标识符

        Returns:
            统计信息字典
        """
        history = self._history_dao.get_by_session(session_id)

        if not history:
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "success_rate": 0.0,
                "average_latency_ms": None,
            }

        total = len(history)
        successful = sum(1 for h in history if h.success)
        latencies = [h.latency_ms for h in history if h.latency_ms is not None]

        return {
            "total_queries": total,
            "successful_queries": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_latency_ms": (
                sum(latencies) / len(latencies) if latencies else None
            ),
        }

    def deactivate_session(self, session_id: str) -> QuerySessionDo:
        """停用会话

        Args:
            session_id: 会话标识符

        Returns:
            更新后的会话对象
        """
        return self._session_dao.deactivate_session(session_id)

    def get_active_sessions(self, user_id: str) -> List[QuerySessionDo]:
        """获取用户的所有活跃会话

        Args:
            user_id: 用户标识符

        Returns:
            活跃会话列表
        """
        return self._session_dao.get_active_sessions_by_user(user_id)
