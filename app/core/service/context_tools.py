"""
Context Management Tools

提供上下文管理工具，包括上下文检索、偏好学习和查询建议。

Author: kaichuan
Date: 2025-11-25
"""

import json
from typing import Any, Dict, List, Optional
from collections import Counter

from app.core.toolkit.tool import Tool
from app.core.service.query_context_service import QueryContextService


class ContextRetriever(Tool):
    """Tool for retrieving relevant context from query history."""

    def __init__(self):
        super().__init__(
            name=self.retrieve_context.__name__,
            description=self.retrieve_context.__doc__ or "",
            function=self.retrieve_context,
        )
        self._context_service = QueryContextService.instance

    async def retrieve_context(
        self,
        session_id: str,
        current_query: str,
        context_type: str = "all",
        max_items: int = 5
    ) -> str:
        """Retrieve relevant context from query history and session state.

        Args:
            session_id (str): Session identifier
            current_query (str): Current query text for relevance matching
            context_type (str, optional): Type of context to retrieve:
                - "all": All context types (default)
                - "history": Previous queries
                - "preferences": User preferences
                - "patterns": Similar query patterns
                - "statistics": Session statistics
            max_items (int, optional): Maximum number of items to return

        Returns:
            str: JSON string containing context information:
                - session_context (dict): Current session state and preferences
                - relevant_history (list): Similar previous queries
                - query_patterns (list): Matching query patterns
                - session_statistics (dict): Session performance metrics
                - recommendations (list): Context-based recommendations

        Example:
            result = await retrieve_context(
                session_id="session_123",
                current_query="Find all Person nodes",
                context_type="all",
                max_items=5
            )
        """
        context = {}

        try:
            # 1. 获取会话上下文
            if context_type in ["all", "session", "preferences"]:
                session = self._context_service.get_session(session_id)
                if session:
                    context["session_context"] = {
                        "user_id": session.user_id,
                        "session_id": session.session_id,
                        "is_active": session.is_active,
                        "last_active_at": session.last_active_at,
                        "context_data": session.context_data or {}
                    }

                    # 提取用户偏好
                    preferences = self._context_service.get_user_preferences(session_id)
                    context["user_preferences"] = preferences

            # 2. 检索相关历史
            if context_type in ["all", "history"]:
                relevant_queries = self._context_service.get_relevant_history(
                    current_query,
                    limit=max_items
                )
                context["relevant_history"] = [
                    {
                        "query_text": q.query_text,
                        "query_cypher": q.query_cypher,
                        "success": q.success,
                        "latency_ms": q.latency_ms,
                        "created_at": q.created_at
                    }
                    for q in relevant_queries
                ]

            # 3. 获取会话统计
            if context_type in ["all", "statistics"]:
                stats = self._context_service.get_session_statistics(session_id)
                context["session_statistics"] = stats

            # 4. 生成基于上下文的建议
            recommendations = self._generate_context_recommendations(
                context,
                current_query
            )
            context["recommendations"] = recommendations

        except Exception as e:
            context["error"] = f"检索上下文时发生错误: {str(e)}"
            context["recommendations"] = ["请检查 session_id 是否有效"]

        return json.dumps(context, ensure_ascii=False, indent=2)

    def _generate_context_recommendations(
        self,
        context: Dict[str, Any],
        current_query: str
    ) -> List[str]:
        """基于上下文生成建议"""
        recommendations = []

        # 基于历史成功率的建议
        stats = context.get("session_statistics", {})
        success_rate = stats.get("success_rate", 1.0)
        if success_rate < 0.5:
            recommendations.append("当前会话成功率较低，建议简化查询或检查语法")

        # 基于相似查询的建议
        relevant_history = context.get("relevant_history", [])
        if relevant_history:
            successful_similar = [q for q in relevant_history if q.get("success")]
            if successful_similar:
                recommendations.append(
                    f"找到 {len(successful_similar)} 个相似的成功查询，可参考其模式"
                )

        # 基于用户偏好的建议
        preferences = context.get("user_preferences", {})
        if preferences.get("prefer_simple_queries"):
            recommendations.append("用户偏好简单查询，建议使用直接的 MATCH 模式")

        return recommendations


class PreferenceLearner(Tool):
    """Tool for learning and updating user preferences."""

    def __init__(self):
        super().__init__(
            name=self.learn_preferences.__name__,
            description=self.learn_preferences.__doc__ or "",
            function=self.learn_preferences,
        )
        self._context_service = QueryContextService.instance

    async def learn_preferences(
        self,
        session_id: str,
        learning_mode: str = "auto"
    ) -> str:
        """Learn user preferences from query history and feedback.

        Args:
            session_id (str): Session identifier
            learning_mode (str, optional): Learning mode:
                - "auto": Automatic learning from history (default)
                - "explicit": Only use explicit feedback
                - "hybrid": Combine both approaches

        Returns:
            str: JSON string containing learned preferences:
                - preferences (dict): Updated user preferences
                - confidence (dict): Confidence scores for each preference
                - learning_summary (dict): Summary of learning process
                - preference_updates (list): List of updated preferences
                - recommendations (list): Preference-based recommendations

        Example:
            result = await learn_preferences(
                session_id="session_123",
                learning_mode="auto"
            )
        """
        preferences = {}
        confidence_scores = {}
        updates = []
        summary = {
            "queries_analyzed": 0,
            "patterns_identified": 0,
            "preferences_learned": 0
        }

        try:
            # 获取会话历史
            history = self._context_service.get_session_history(
                session_id,
                limit=50
            )
            summary["queries_analyzed"] = len(history)

            if not history:
                return json.dumps({
                    "preferences": {},
                    "confidence": {},
                    "learning_summary": summary,
                    "preference_updates": [],
                    "recommendations": ["需要更多查询历史来学习偏好"]
                }, ensure_ascii=False, indent=2)

            # 1. 学习查询复杂度偏好
            complexity_pref = self._learn_complexity_preference(history)
            if complexity_pref:
                preferences["preferred_complexity"] = complexity_pref["level"]
                confidence_scores["complexity"] = complexity_pref["confidence"]
                updates.append(f"学习到复杂度偏好: {complexity_pref['level']}")

            # 2. 学习查询模式偏好
            pattern_pref = self._learn_pattern_preference(history)
            if pattern_pref:
                preferences["preferred_patterns"] = pattern_pref["patterns"]
                confidence_scores["patterns"] = pattern_pref["confidence"]
                updates.append(f"识别到 {len(pattern_pref['patterns'])} 个常用模式")
                summary["patterns_identified"] = len(pattern_pref["patterns"])

            # 3. 学习数据偏好
            data_pref = self._learn_data_preference(history)
            if data_pref:
                preferences["preferred_vertex_types"] = data_pref["vertex_types"]
                preferences["preferred_result_size"] = data_pref["result_size"]
                confidence_scores["data"] = data_pref["confidence"]
                updates.append(f"学习到数据偏好: {', '.join(data_pref['vertex_types'][:3])}")

            # 4. 学习性能偏好
            perf_pref = self._learn_performance_preference(history)
            if perf_pref:
                preferences["acceptable_latency_ms"] = perf_pref["threshold"]
                confidence_scores["performance"] = perf_pref["confidence"]
                updates.append(f"学习到性能偏好: {perf_pref['threshold']}ms 延迟阈值")

            # 更新会话偏好
            if preferences:
                self._context_service.update_user_preferences(
                    session_id,
                    preferences
                )
                summary["preferences_learned"] = len(preferences)

            # 生成建议
            recommendations = self._generate_preference_recommendations(
                preferences,
                confidence_scores
            )

        except Exception as e:
            return json.dumps({
                "error": f"学习偏好时发生错误: {str(e)}",
                "preferences": {},
                "recommendations": ["请检查会话数据完整性"]
            }, ensure_ascii=False, indent=2)

        return json.dumps({
            "preferences": preferences,
            "confidence": confidence_scores,
            "learning_summary": summary,
            "preference_updates": updates,
            "recommendations": recommendations
        }, ensure_ascii=False, indent=2)

    def _learn_complexity_preference(self, history: List) -> Optional[Dict[str, Any]]:
        """学习查询复杂度偏好"""
        if not history:
            return None

        # 统计成功查询的复杂度分布
        successful_queries = [q for q in history if q.success]
        if not successful_queries:
            return None

        complexity_counts = Counter()
        for query in successful_queries:
            if query.complexity_analysis:
                level = query.complexity_analysis.get("complexity_level")
                if level:
                    complexity_counts[level] += 1

        if not complexity_counts:
            return None

        # 最常见的复杂度
        preferred_level = complexity_counts.most_common(1)[0][0]
        confidence = complexity_counts[preferred_level] / len(successful_queries)

        return {
            "level": preferred_level,
            "confidence": confidence
        }

    def _learn_pattern_preference(self, history: List) -> Optional[Dict[str, Any]]:
        """学习查询模式偏好"""
        if not history:
            return None

        # 统计查询模式
        pattern_counts = Counter()
        for query in history:
            if query.success and query.path_patterns:
                patterns = query.path_patterns.get("patterns", [])
                for pattern in patterns:
                    pattern_type = pattern.get("pattern_type")
                    if pattern_type:
                        pattern_counts[pattern_type] += 1

        if not pattern_counts:
            return None

        # 最常用的模式（前 3 个）
        top_patterns = [p[0] for p in pattern_counts.most_common(3)]
        confidence = sum(pattern_counts.values()) / len(history)

        return {
            "patterns": top_patterns,
            "confidence": min(1.0, confidence)
        }

    def _learn_data_preference(self, history: List) -> Optional[Dict[str, Any]]:
        """学习数据偏好"""
        if not history:
            return None

        # 统计常用顶点类型
        vertex_type_counts = Counter()
        result_sizes = []

        for query in history:
            if query.success:
                # 从意图分析提取顶点类型
                if query.query_intention:
                    vertex_types = query.query_intention.get("object_vertex_types", [])
                    vertex_type_counts.update(vertex_types)

                # 统计结果集大小
                if query.result_count is not None:
                    result_sizes.append(query.result_count)

        if not vertex_type_counts:
            return None

        # 最常用的顶点类型（前 5 个）
        top_vertex_types = [v[0] for v in vertex_type_counts.most_common(5)]

        # 平均结果集大小
        avg_result_size = int(sum(result_sizes) / len(result_sizes)) if result_sizes else 100

        confidence = len(result_sizes) / len(history)

        return {
            "vertex_types": top_vertex_types,
            "result_size": avg_result_size,
            "confidence": confidence
        }

    def _learn_performance_preference(self, history: List) -> Optional[Dict[str, Any]]:
        """学习性能偏好"""
        if not history:
            return None

        # 统计成功查询的延迟
        latencies = [
            q.latency_ms for q in history
            if q.success and q.latency_ms is not None
        ]

        if not latencies:
            return None

        # 75th 百分位作为可接受延迟
        sorted_latencies = sorted(latencies)
        p75_index = int(len(sorted_latencies) * 0.75)
        threshold = sorted_latencies[p75_index]

        confidence = len(latencies) / len(history)

        return {
            "threshold": threshold,
            "confidence": confidence
        }

    def _generate_preference_recommendations(
        self,
        preferences: Dict[str, Any],
        confidence_scores: Dict[str, float]
    ) -> List[str]:
        """生成基于偏好的建议"""
        recommendations = []

        # 复杂度建议
        if "preferred_complexity" in preferences:
            level = preferences["preferred_complexity"]
            recommendations.append(f"建议保持 {level} 复杂度的查询以获得最佳体验")

        # 模式建议
        if "preferred_patterns" in preferences:
            patterns = preferences["preferred_patterns"]
            recommendations.append(f"建议使用熟悉的模式: {', '.join(patterns)}")

        # 性能建议
        if "acceptable_latency_ms" in preferences:
            threshold = preferences["acceptable_latency_ms"]
            recommendations.append(f"建议优化查询以保持延迟在 {threshold}ms 以内")

        # 低置信度警告
        low_confidence = [k for k, v in confidence_scores.items() if v < 0.3]
        if low_confidence:
            recommendations.append(
                f"偏好学习置信度较低: {', '.join(low_confidence)}，需要更多数据"
            )

        return recommendations


class QuerySuggester(Tool):
    """Tool for suggesting query improvements and alternatives."""

    def __init__(self):
        super().__init__(
            name=self.suggest_queries.__name__,
            description=self.suggest_queries.__doc__ or "",
            function=self.suggest_queries,
        )
        self._context_service = QueryContextService.instance

    async def suggest_queries(
        self,
        session_id: str,
        current_query: str,
        suggestion_type: str = "all"
    ) -> str:
        """Suggest query improvements and alternatives based on context.

        Args:
            session_id (str): Session identifier
            current_query (str): Current query text or intention
            suggestion_type (str, optional): Type of suggestions:
                - "all": All suggestion types (default)
                - "improvements": Query optimization suggestions
                - "alternatives": Alternative query approaches
                - "completions": Query completion suggestions
                - "corrections": Error corrections

        Returns:
            str: JSON string containing query suggestions:
                - improvements (list): Optimization suggestions
                - alternatives (list): Alternative query approaches
                - completions (list): Query completion suggestions
                - corrections (list): Error correction suggestions
                - confidence (dict): Confidence scores for suggestions
                - rationale (dict): Explanation for each suggestion

        Example:
            result = await suggest_queries(
                session_id="session_123",
                current_query="Find Person nodes",
                suggestion_type="all"
            )
        """
        suggestions = {
            "improvements": [],
            "alternatives": [],
            "completions": [],
            "corrections": []
        }
        confidence = {}
        rationale = {}

        try:
            # 获取会话偏好
            preferences = self._context_service.get_user_preferences(session_id)

            # 获取相关历史
            relevant_history = self._context_service.get_relevant_history(
                current_query,
                limit=3
            )

            # 1. 改进建议
            if suggestion_type in ["all", "improvements"]:
                improvements = self._suggest_improvements(
                    current_query,
                    preferences,
                    relevant_history
                )
                suggestions["improvements"] = improvements["suggestions"]
                confidence["improvements"] = improvements["confidence"]
                rationale["improvements"] = improvements["rationale"]

            # 2. 替代方案
            if suggestion_type in ["all", "alternatives"]:
                alternatives = self._suggest_alternatives(
                    current_query,
                    relevant_history
                )
                suggestions["alternatives"] = alternatives["suggestions"]
                confidence["alternatives"] = alternatives["confidence"]
                rationale["alternatives"] = alternatives["rationale"]

            # 3. 补全建议
            if suggestion_type in ["all", "completions"]:
                completions = self._suggest_completions(
                    current_query,
                    preferences
                )
                suggestions["completions"] = completions["suggestions"]
                confidence["completions"] = completions["confidence"]
                rationale["completions"] = completions["rationale"]

            # 4. 纠错建议
            if suggestion_type in ["all", "corrections"]:
                corrections = self._suggest_corrections(
                    current_query,
                    relevant_history
                )
                suggestions["corrections"] = corrections["suggestions"]
                confidence["corrections"] = corrections["confidence"]
                rationale["corrections"] = corrections["rationale"]

        except Exception as e:
            return json.dumps({
                "error": f"生成建议时发生错误: {str(e)}",
                "suggestions": suggestions
            }, ensure_ascii=False, indent=2)

        return json.dumps({
            "suggestions": suggestions,
            "confidence": confidence,
            "rationale": rationale
        }, ensure_ascii=False, indent=2)

    def _suggest_improvements(
        self,
        query: str,
        preferences: Dict[str, Any],
        history: List
    ) -> Dict[str, Any]:
        """建议查询改进"""
        improvements = []
        rationale_list = []

        # 基于偏好的改进
        if preferences.get("acceptable_latency_ms"):
            threshold = preferences["acceptable_latency_ms"]
            improvements.append(f"添加 LIMIT {threshold // 10} 以控制延迟")
            rationale_list.append("根据历史性能偏好建议")

        # 基于成功案例的改进
        if history:
            successful = [q for q in history if q.success]
            if successful:
                # 提取常见优化模式
                if all("LIMIT" in (q.query_cypher or "") for q in successful[:2]):
                    if "LIMIT" not in query.upper():
                        improvements.append("添加 LIMIT 子句（类似成功查询）")
                        rationale_list.append("参考历史成功查询模式")

        if not improvements:
            improvements.append("当前查询暂无明显改进点")
            rationale_list.append("查询已较优")

        return {
            "suggestions": improvements,
            "confidence": 0.7 if improvements else 0.3,
            "rationale": rationale_list
        }

    def _suggest_alternatives(
        self,
        query: str,
        history: List
    ) -> Dict[str, Any]:
        """建议替代查询方案"""
        alternatives = []
        rationale_list = []

        # 基于相似查询的替代方案
        if history:
            for q in history[:2]:
                if q.success and q.query_cypher:
                    alternatives.append(q.query_cypher)
                    rationale_list.append(
                        f"相似查询（延迟: {q.latency_ms}ms）"
                    )

        if not alternatives:
            alternatives.append("暂无可用的替代方案")
            rationale_list.append("需要更多历史数据")

        return {
            "suggestions": alternatives,
            "confidence": 0.6 if len(alternatives) > 1 else 0.3,
            "rationale": rationale_list
        }

    def _suggest_completions(
        self,
        query: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """建议查询补全"""
        completions = []
        rationale_list = []

        # 基于偏好的补全
        preferred_types = preferences.get("preferred_vertex_types", [])
        if preferred_types and len(query.split()) < 5:
            for vtype in preferred_types[:2]:
                completions.append(f"{query} of type {vtype}")
                rationale_list.append(f"基于常用类型 {vtype}")

        if not completions:
            completions.append("完整的查询，无需补全")
            rationale_list.append("查询已完整")

        return {
            "suggestions": completions,
            "confidence": 0.5,
            "rationale": rationale_list
        }

    def _suggest_corrections(
        self,
        query: str,
        history: List
    ) -> Dict[str, Any]:
        """建议查询纠错"""
        corrections = []
        rationale_list = []

        # 检查常见错误
        if query.count("(") != query.count(")"):
            corrections.append("括号不匹配，请检查语法")
            rationale_list.append("语法错误检测")

        # 基于失败案例的纠错
        failed = [q for q in history if not q.success]
        if failed:
            for q in failed[:1]:
                if q.error_message:
                    corrections.append(f"避免类似错误: {q.error_message}")
                    rationale_list.append("基于历史失败案例")

        if not corrections:
            corrections.append("未发现明显错误")
            rationale_list.append("查询语法正确")

        return {
            "suggestions": corrections,
            "confidence": 0.8 if corrections else 0.5,
            "rationale": rationale_list
        }
