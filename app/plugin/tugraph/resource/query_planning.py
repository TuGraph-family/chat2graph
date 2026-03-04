"""
Query Planning Tools

提供查询复杂度分析、索引推荐和查询重写工具。

Author: kaichuan
Date: 2025-11-25
"""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from app.core.toolkit.tool import Tool
from app.core.service.graph_db_service import GraphDbService


@dataclass
class ComplexityMetrics:
    """复杂度分析指标"""
    entity_count: int
    relationship_depth: int
    has_temporal: bool
    has_spatial: bool
    has_aggregations: bool
    has_variable_length: bool
    complexity_score: float
    complexity_level: str  # SIMPLE, MODERATE, COMPLEX


class QueryComplexityAnalyzer(Tool):
    """Tool for analyzing natural language query complexity."""

    # 关键词定义
    TEMPORAL_KEYWORDS = [
        'year', 'month', 'day', 'date', 'time', 'when', 'during',
        'before', 'after', 'between', 'since', 'until', 'recent',
        'last', 'past', 'ago', 'yesterday', 'today', 'tomorrow',
        '年', '月', '日', '时间', '何时', '之前', '之后', '最近'
    ]

    SPATIAL_KEYWORDS = [
        'location', 'place', 'where', 'near', 'around', 'within',
        'distance', 'km', 'mile', 'city', 'country', 'region',
        '位置', '地点', '哪里', '附近', '周围', '城市', '国家'
    ]

    AGGREGATION_KEYWORDS = [
        'count', 'sum', 'average', 'mean', 'max', 'min', 'total',
        'how many', 'number of', 'all', 'every', 'each',
        '计数', '总和', '平均', '最大', '最小', '多少', '所有'
    ]

    MULTI_HOP_KEYWORDS = [
        'through', 'via', 'connected', 'related', 'path', 'chain',
        'friend of friend', 'transitive', 'indirect', 'ancestor',
        'descendant', 'upstream', 'downstream',
        '通过', '连接', '相关', '路径', '链', '间接'
    ]

    def __init__(self):
        super().__init__(
            name=self.analyze_complexity.__name__,
            description=self.analyze_complexity.__doc__ or "",
            function=self.analyze_complexity,
        )
        self.complexity_weights = {
            'entity_count': 0.15,
            'relationship_depth': 0.25,
            'temporal': 0.15,
            'spatial': 0.15,
            'aggregations': 0.15,
            'variable_length': 0.15
        }

    async def analyze_complexity(
        self,
        query: str,
        intention_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Analyze the complexity of a natural language query.

        Args:
            query (str): The natural language query to analyze
            intention_analysis (dict, optional): Optional intention analysis result containing:
                - object_vertex_types (list): List of entity types
                - query_conditions (list): List of query conditions

        Returns:
            str: JSON string containing complexity analysis:
                - complexity_level (str): SIMPLE, MODERATE, or COMPLEX
                - entity_count (int): Number of entities involved
                - relationship_depth (int): Depth of relationship traversal
                - has_temporal_constraints (bool): Whether query has temporal constraints
                - has_spatial_constraints (bool): Whether query has spatial constraints
                - has_aggregations (bool): Whether query has aggregations
                - has_variable_length (bool): Whether query has variable-length paths
                - complexity_score (float): Numerical complexity score (0-1)
                - recommended_strategy (str): Recommended execution strategy
                - optimization_hints (list): List of optimization suggestions
                - index_recommendations (list): List of recommended indexes

        Example:
            result = await analyze_complexity(
                query="Find friends of friends of John in last year",
                intention_analysis={"object_vertex_types": ["Person"]}
            )
        """
        query_lower = query.lower()

        # 提取实体数量
        entity_count = self._estimate_entity_count(query, intention_analysis)

        # 检测关系深度
        relationship_depth = self._estimate_relationship_depth(query_lower)

        # 检测特性
        has_temporal = self._has_feature(query_lower, self.TEMPORAL_KEYWORDS)
        has_spatial = self._has_feature(query_lower, self.SPATIAL_KEYWORDS)
        has_aggregations = self._has_feature(query_lower, self.AGGREGATION_KEYWORDS)
        has_variable_length = self._has_feature(query_lower, self.MULTI_HOP_KEYWORDS)

        # 计算复杂度分数
        score = self._calculate_complexity_score(
            entity_count=entity_count,
            relationship_depth=relationship_depth,
            has_temporal=has_temporal,
            has_spatial=has_spatial,
            has_aggregations=has_aggregations,
            has_variable_length=has_variable_length
        )

        # 分类复杂度等级
        if score < 0.3:
            level = "SIMPLE"
        elif score < 0.6:
            level = "MODERATE"
        else:
            level = "COMPLEX"

        metrics = ComplexityMetrics(
            entity_count=entity_count,
            relationship_depth=relationship_depth,
            has_temporal=has_temporal,
            has_spatial=has_spatial,
            has_aggregations=has_aggregations,
            has_variable_length=has_variable_length,
            complexity_score=score,
            complexity_level=level
        )

        # 生成策略建议
        strategy = self._recommend_strategy(metrics)

        result = {
            **asdict(metrics),
            **strategy
        }

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _estimate_entity_count(
        self,
        query: str,
        intention: Optional[Dict[str, Any]] = None
    ) -> int:
        """估算查询涉及的实体数量"""
        if intention and 'object_vertex_types' in intention:
            return len(intention['object_vertex_types'])

        # 回退：统计大写单词（启发式方法）
        entities = re.findall(r'\b[A-Z][a-z]+\b', query)
        return max(1, len(set(entities)))

    def _estimate_relationship_depth(self, query: str) -> int:
        """估算关系遍历深度"""
        # 查找多跳指示器
        if any(keyword in query for keyword in self.MULTI_HOP_KEYWORDS):
            # 统计连接词
            chain_count = sum(query.count(word) for word in ['through', 'via', 'to', 'of', '通过', '到'])
            return min(5, max(2, chain_count))

        # 默认单跳
        return 1

    def _has_feature(self, query: str, keywords: List[str]) -> bool:
        """检查查询是否包含特定特性关键词"""
        return any(keyword in query for keyword in keywords)

    def _calculate_complexity_score(
        self,
        entity_count: int,
        relationship_depth: int,
        has_temporal: bool,
        has_spatial: bool,
        has_aggregations: bool,
        has_variable_length: bool
    ) -> float:
        """计算加权复杂度分数 (0-1)"""
        score = 0.0

        # 实体数量贡献（归一化到 0-1）
        entity_score = min(1.0, entity_count / 5.0)
        score += entity_score * self.complexity_weights['entity_count']

        # 关系深度贡献（归一化到 0-1）
        depth_score = min(1.0, relationship_depth / 4.0)
        score += depth_score * self.complexity_weights['relationship_depth']

        # 特性贡献（二元）
        if has_temporal:
            score += self.complexity_weights['temporal']
        if has_spatial:
            score += self.complexity_weights['spatial']
        if has_aggregations:
            score += self.complexity_weights['aggregations']
        if has_variable_length:
            score += self.complexity_weights['variable_length']

        return min(1.0, score)

    def _recommend_strategy(self, metrics: ComplexityMetrics) -> Dict[str, Any]:
        """基于复杂度推荐执行策略"""
        strategy = {
            "recommended_strategy": "",
            "optimization_hints": [],
            "index_recommendations": []
        }

        if metrics.complexity_level == "SIMPLE":
            strategy["recommended_strategy"] = "Direct execution with VertexQuerier"
            strategy["optimization_hints"] = [
                "使用属性索引进行过滤",
                "如果可能，限制结果集大小"
            ]

        elif metrics.complexity_level == "MODERATE":
            strategy["recommended_strategy"] = "Optimized Cypher with index hints"
            strategy["optimization_hints"] = [
                "使用 LIMIT 子句减少结果集",
                "考虑使用 WITH 存储中间结果",
                "为大型属性扫描添加索引提示"
            ]

            if metrics.has_temporal:
                strategy["optimization_hints"].append(
                    "在日期/时间属性上创建时间索引"
                )
                strategy["index_recommendations"].append({
                    "index_type": "temporal",
                    "target_property": "date/time properties",
                    "estimated_benefit": "high"
                })

            if metrics.relationship_depth > 1:
                strategy["optimization_hints"].append(
                    "考虑使用 shortestPath() 进行多跳查询"
                )

        else:  # COMPLEX
            strategy["recommended_strategy"] = "Multi-stage execution with caching"
            strategy["optimization_hints"] = [
                "将查询拆分为多个阶段",
                "缓存中间结果",
                "使用查询性能分析识别瓶颈",
                "考虑为频繁模式创建物化视图"
            ]

            if metrics.has_variable_length:
                strategy["optimization_hints"].append(
                    "为可变长度模式设置合理的深度限制"
                )

            if metrics.has_aggregations:
                strategy["optimization_hints"].append(
                    "尽早下推聚合操作"
                )

            if metrics.has_spatial:
                strategy["index_recommendations"].append({
                    "index_type": "spatial",
                    "target_property": "location properties",
                    "estimated_benefit": "high"
                })

        return strategy


class IndexRecommender(Tool):
    """Tool for recommending indexes based on query patterns."""

    def __init__(self):
        super().__init__(
            name=self.recommend_indexes.__name__,
            description=self.recommend_indexes.__doc__ or "",
            function=self.recommend_indexes,
        )

    async def recommend_indexes(
        self,
        graph_db_service: GraphDbService,
        vertex_types: List[str],
        query_conditions: List[Dict[str, str]],
        query_frequency: int = 1
    ) -> str:
        """Recommend indexes based on query patterns and current schema.

        Args:
            vertex_types (list): List of vertex types involved in the query
            query_conditions (list): List of query conditions with field names
            query_frequency (int, optional): How frequently this query pattern is used

        Returns:
            str: JSON string containing index recommendations:
                - recommendations (list): List of index recommendation objects:
                    - vertex_type (str): Target vertex type
                    - property_name (str): Property to index
                    - index_type (str): Type of index (btree, fulltext, spatial)
                    - priority (str): HIGH, MEDIUM, LOW
                    - estimated_benefit (str): Expected performance improvement
                    - reason (str): Why this index is recommended

        Example:
            result = await recommend_indexes(
                vertex_types=["Person", "Company"],
                query_conditions=[{"field": "name", "operator": "CONTAINS"}],
                query_frequency=100
            )
        """
        recommendations = []

        # 获取当前 schema
        try:
            query = "CALL dbms.graph.getGraphSchema()"
            store = graph_db_service.get_default_graph_db()
            schema_result = store.conn.run(query=query)
            import json
            schema = json.loads(schema_result[0][0])["schema"]
        except Exception as e:
            schema = []

        # 分析每个顶点类型和查询条件
        for vertex_type in vertex_types:
            # 提取该顶点类型的查询条件
            relevant_conditions = [
                cond for cond in query_conditions
                if 'field' in cond
            ]

            for condition in relevant_conditions:
                field = condition.get('field', '')
                operator = condition.get('operator', '=')

                # 根据操作符确定索引类型
                if operator in ['CONTAINS', 'STARTS WITH', 'ENDS WITH', 'REGEXP']:
                    index_type = "fulltext"
                    priority = "HIGH" if query_frequency > 10 else "MEDIUM"
                    benefit = "显著提升文本搜索性能"
                elif operator in ['<', '>', '<=', '>=']:
                    index_type = "btree"
                    priority = "HIGH" if query_frequency > 5 else "MEDIUM"
                    benefit = "加速范围查询"
                elif operator == '=':
                    index_type = "btree"
                    priority = "MEDIUM"
                    benefit = "提升等值查询性能"
                else:
                    index_type = "btree"
                    priority = "LOW"
                    benefit = "通用性能提升"

                recommendations.append({
                    "vertex_type": vertex_type,
                    "property_name": field,
                    "index_type": index_type,
                    "priority": priority,
                    "estimated_benefit": benefit,
                    "reason": f"频繁使用 {operator} 操作符查询 {field} 属性"
                })

        # 去重
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = (rec['vertex_type'], rec['property_name'], rec['index_type'])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)

        result = {
            "recommendations": unique_recommendations,
            "total_count": len(unique_recommendations)
        }

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)


class QueryRewriter(Tool):
    """Tool for rewriting queries for better performance."""

    def __init__(self):
        super().__init__(
            name=self.rewrite_query.__name__,
            description=self.rewrite_query.__doc__ or "",
            function=self.rewrite_query,
        )

    async def rewrite_query(
        self,
        cypher_query: str,
        optimization_goal: str = "performance"
    ) -> str:
        """Rewrite a Cypher query for better performance.

        Args:
            cypher_query (str): The original Cypher query
            optimization_goal (str, optional): Optimization goal:
                - "performance": Optimize for execution speed
                - "memory": Optimize for memory usage
                - "readability": Optimize for code clarity

        Returns:
            str: JSON string containing:
                - original_query (str): The original query
                - rewritten_query (str): The optimized query
                - optimizations_applied (list): List of optimizations applied
                - estimated_improvement (str): Expected performance improvement
                - explanation (str): Explanation of changes

        Example:
            result = await rewrite_query(
                cypher_query="MATCH (p:Person) WHERE p.age > 18 RETURN p",
                optimization_goal="performance"
            )
        """
        original = cypher_query.strip()
        rewritten = original
        optimizations = []
        improvements = []

        # 优化 1: 添加 LIMIT 如果没有
        if 'LIMIT' not in rewritten.upper() and 'RETURN' in rewritten.upper():
            if optimization_goal == "performance":
                rewritten = rewritten.rstrip(';') + ' LIMIT 1000'
                optimizations.append("添加 LIMIT 子句限制结果集")
                improvements.append("减少内存使用和数据传输")

        # 优化 2: 将 WHERE 条件移到 MATCH 模式中
        where_pattern = re.search(
            r'MATCH\s+\((\w+):(\w+)\)\s+WHERE\s+\1\.(\w+)\s*=\s*["\']?([^"\'\s;]+)["\']?',
            rewritten,
            re.IGNORECASE
        )
        if where_pattern and optimization_goal == "performance":
            var, label, prop, value = where_pattern.groups()
            # 重写为内联属性
            old_pattern = where_pattern.group(0)
            if value.isdigit():
                new_pattern = f"MATCH ({var}:{label} {{{prop}: {value}}})"
            else:
                new_pattern = f"MATCH ({var}:{label} {{{prop}: '{value}'}})"

            # 移除 WHERE 子句
            rewritten = rewritten.replace(old_pattern, new_pattern, 1)
            optimizations.append("将 WHERE 条件内联到 MATCH 模式")
            improvements.append("更早进行过滤，减少中间结果")

        # 优化 3: 使用 WITH 分离复杂查询
        if rewritten.count('MATCH') > 2 and 'WITH' not in rewritten.upper():
            if optimization_goal == "memory":
                optimizations.append("建议使用 WITH 子句分离查询阶段")
                improvements.append("减少内存峰值使用")

        # 优化 4: 添加 DISTINCT 消除重复
        if 'RETURN' in rewritten.upper() and 'DISTINCT' not in rewritten.upper():
            if ',' in rewritten.split('RETURN')[1]:  # 多个返回值
                optimizations.append("考虑添加 DISTINCT 消除重复结果")
                improvements.append("减少结果集大小")

        # 构建结果
        if not optimizations:
            optimizations.append("查询已经较优，无需重写")
            improvements.append("保持原查询")
            rewritten = original

        result = {
            "original_query": original,
            "rewritten_query": rewritten,
            "optimizations_applied": optimizations,
            "estimated_improvement": ", ".join(improvements),
            "explanation": "应用了 {} 个优化策略".format(len(optimizations))
        }

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
