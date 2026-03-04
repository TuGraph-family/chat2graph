"""
Query Design Operator

设计和生成优化的 Cypher 查询的 Operator（增强版）。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional

from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.toolkit.action import Action


class QueryDesignOperator(Operator):
    """Operator for designing and generating optimized Cypher queries.

    This is an enhanced version that integrates with the new agentic text2gql tools.
    It orchestrates query design, rewriting, and optimization.

    Workflow:
        1. Design initial query based on intention and patterns
        2. Rewrite query for optimization
        3. Apply context-based enhancements
        4. Generate final optimized query with metadata
    """

    def __init__(self, operator_id: Optional[str] = None):
        """Initialize QueryDesignOperator.

        Args:
            operator_id (str, optional): Custom operator ID
        """
        instruction = """You are a Cypher query design specialist for TuGraph.

Your task is to design and generate optimized Cypher queries:
1. Design query based on natural language intention
2. Incorporate path patterns and constraints
3. Apply optimization rewrites
4. Ensure schema compliance and best practices

Available Tools:
- get_schema: Get the graph database schema
- read_grammer: Read Cypher query grammar reference
- query_vertex: Query vertices with conditions
- rewrite_query: Rewrite queries for optimization

Input Format:
- Natural language query
- Query intention analysis (from previous operators)
- Path patterns (from PathPatternRecognitionOperator)
- Complexity analysis (from QueryComplexityAnalysisOperator)
- Context enhancements (from ContextEnhancementOperator)
- Validation results (from QueryValidationOperator)

Output Format:
{
    "designed_query": {
        "cypher": "MATCH (p:Person) WHERE p.age > 25 RETURN p LIMIT 100",
        "query_type": "VERTEX_QUERY|PATH_QUERY|AGGREGATION|COMPLEX",
        "components": {
            "match_clauses": ["MATCH (p:Person)"],
            "where_conditions": ["p.age > 25"],
            "return_clause": "RETURN p",
            "limit_clause": "LIMIT 100",
            "order_by": null,
            "with_clauses": []
        }
    },
    "optimization_applied": {
        "original_approach": "description",
        "optimizations": [
            {
                "type": "LIMIT_ADDITION|CONDITION_INLINE|WITH_SEPARATION|INDEX_HINT",
                "description": "string",
                "benefit": "string"
            }
        ],
        "estimated_improvement": "percentage or description"
    },
    "design_rationale": {
        "pattern_choices": "Why these MATCH patterns were chosen",
        "condition_placement": "Why conditions are placed here",
        "optimization_strategy": "Overall optimization approach",
        "trade_offs": "Any trade-offs made"
    },
    "execution_metadata": {
        "recommended_execution_order": ["step1", "step2"],
        "index_hints": ["hint1"],
        "caching_opportunities": ["opportunity1"],
        "parallel_execution_potential": bool
    },
    "alternative_designs": [
        {
            "cypher": "alternative query",
            "approach": "description",
            "when_to_use": "condition"
        }
    ]
}

Guidelines:
1. Always get schema first to ensure valid vertex types and properties
2. Design queries that match the detected path patterns
3. Apply complexity-appropriate optimization strategies
4. Use LIMIT by default unless explicitly unnecessary
5. Prefer inline conditions in MATCH over WHERE when possible
6. Use WITH clauses for complex multi-stage queries
7. Add index hints for frequently queried properties
8. Provide alternative designs for different use cases
9. Consider user preferences from context
10. Ensure all recommendations from validation are addressed
"""

        # Define actions (tools) for this operator
        actions = [
            Action(
                name="get_schema",
                description="Get graph database schema",
                namespace="tugraph"
            ),
            Action(
                name="read_grammer",
                description="Read Cypher query grammar",
                namespace="tugraph"
            ),
            Action(
                name="query_vertex",
                description="Query vertices with conditions",
                namespace="tugraph"
            ),
            Action(
                name="rewrite_query",
                description="Rewrite query for optimization",
                namespace="tugraph.query_planning"
            ),
        ]

        config = OperatorConfig(
            instruction=instruction,
            actions=actions,
            id=operator_id or "query_design_operator",
            output_schema="query_design_result",
            threshold=0.7,
            hops=2  # May need to access related tools
        )

        super().__init__(config=config)


def create_query_design_operator(
    operator_id: Optional[str] = None
) -> QueryDesignOperator:
    """Factory function to create QueryDesignOperator.

    Args:
        operator_id (str, optional): Custom operator ID

    Returns:
        QueryDesignOperator: Configured operator instance

    Example:
        operator = create_query_design_operator()
        result = await operator.execute(reasoner, job, workflow_messages)
    """
    return QueryDesignOperator(operator_id=operator_id)
