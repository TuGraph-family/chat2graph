"""
Query Complexity Analysis Operator

分析查询复杂度并推荐执行策略的 Operator。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional

from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.toolkit.action import Action


class QueryComplexityAnalysisOperator(Operator):
    """Operator for analyzing query complexity and recommending execution strategies.

    This operator orchestrates complexity analysis using QueryComplexityAnalyzer
    and IndexRecommender tools to determine optimal query execution approach.

    Workflow:
        1. Analyze query complexity (entity count, relationship depth, features)
        2. Recommend indexes for optimization
        3. Determine execution strategy (direct, optimized, multi-stage)
        4. Generate optimization hints
    """

    def __init__(self, operator_id: Optional[str] = None):
        """Initialize QueryComplexityAnalysisOperator.

        Args:
            operator_id (str, optional): Custom operator ID
        """
        instruction = """You are a query complexity analysis specialist for TuGraph.

Your task is to analyze the complexity of natural language queries and provide:
1. Complexity assessment (SIMPLE, MODERATE, COMPLEX)
2. Complexity score and detailed metrics
3. Recommended execution strategy
4. Index recommendations for optimization
5. Performance optimization hints

Available Tools:
- analyze_complexity: Analyze query complexity with multiple dimensions
- recommend_indexes: Suggest indexes based on query patterns

Input Format:
- Natural language query
- Optional: Intention analysis result

Output Format:
{
    "complexity_analysis": {
        "complexity_level": "SIMPLE|MODERATE|COMPLEX",
        "complexity_score": 0.0-1.0,
        "entity_count": int,
        "relationship_depth": int,
        "has_temporal": bool,
        "has_spatial": bool,
        "has_aggregations": bool,
        "has_variable_length": bool,
        "recommended_strategy": "strategy description",
        "optimization_hints": ["hint1", "hint2"]
    },
    "index_recommendations": {
        "recommendations": [
            {
                "vertex_type": "string",
                "property_name": "string",
                "index_type": "btree|fulltext|spatial",
                "priority": "HIGH|MEDIUM|LOW",
                "estimated_benefit": "string",
                "reason": "string"
            }
        ],
        "total_count": int
    },
    "execution_recommendation": {
        "approach": "direct|optimized|multi_stage",
        "rationale": "explanation",
        "estimated_performance": "LOW|MEDIUM|HIGH|CRITICAL"
    }
}

Guidelines:
1. Always analyze complexity first to understand query characteristics
2. Recommend indexes only for frequently used properties
3. For COMPLEX queries, suggest multi-stage execution with caching
4. Provide actionable optimization hints
5. Consider both current query and potential future patterns
"""

        # Define actions (tools) for this operator
        actions = [
            Action(
                name="analyze_complexity",
                description="Analyze natural language query complexity",
                namespace="tugraph.query_planning"
            ),
            Action(
                name="recommend_indexes",
                description="Recommend indexes based on query patterns",
                namespace="tugraph.query_planning"
            ),
        ]

        config = OperatorConfig(
            instruction=instruction,
            actions=actions,
            id=operator_id or "query_complexity_analysis_operator",
            output_schema="complexity_analysis_result",
            threshold=0.7,
            hops=1
        )

        super().__init__(config=config)


def create_query_complexity_analysis_operator(
    operator_id: Optional[str] = None
) -> QueryComplexityAnalysisOperator:
    """Factory function to create QueryComplexityAnalysisOperator.

    Args:
        operator_id (str, optional): Custom operator ID

    Returns:
        QueryComplexityAnalysisOperator: Configured operator instance

    Example:
        operator = create_query_complexity_analysis_operator()
        result = await operator.execute(reasoner, job, workflow_messages)
    """
    return QueryComplexityAnalysisOperator(operator_id=operator_id)
