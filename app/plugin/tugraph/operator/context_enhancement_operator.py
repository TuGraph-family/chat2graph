"""
Context Enhancement Operator

利用历史查询和用户偏好增强查询生成的 Operator。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional

from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.toolkit.action import Action


class ContextEnhancementOperator(Operator):
    """Operator for enhancing queries with contextual information.

    This operator leverages historical queries and learned user preferences
    to improve query generation through:
    1. Context retrieval from session history
    2. User preference learning from past behavior
    3. Query suggestions based on context
    4. Adaptive recommendations

    Workflow:
        1. Retrieve relevant context (history, preferences, statistics)
        2. Learn or update user preferences
        3. Generate context-aware query suggestions
        4. Provide personalized recommendations
    """

    def __init__(self, operator_id: Optional[str] = None):
        """Initialize ContextEnhancementOperator.

        Args:
            operator_id (str, optional): Custom operator ID
        """
        instruction = """You are a context-aware query enhancement specialist for TuGraph.

Your task is to leverage historical context and user preferences to enhance query generation:
1. Retrieve relevant context from session history
2. Learn and apply user preferences
3. Generate context-aware query improvements
4. Provide personalized suggestions

Available Tools:
- retrieve_context: Get relevant history, preferences, and statistics
- learn_preferences: Learn user preferences from query history
- suggest_queries: Generate context-based query suggestions

Input Format:
- Session ID
- Current query (natural language or Cypher)
- Optional: Learning mode, suggestion type

Output Format:
{
    "context_summary": {
        "session_info": {
            "user_id": "string",
            "session_id": "string",
            "is_active": bool,
            "total_queries": int,
            "success_rate": float
        },
        "relevant_history": [
            {
                "query_text": "string",
                "query_cypher": "string",
                "success": bool,
                "latency_ms": int
            }
        ],
        "user_preferences": {
            "preferred_complexity": "SIMPLE|MODERATE|COMPLEX",
            "preferred_patterns": ["DIRECT", "MULTI_HOP"],
            "preferred_vertex_types": ["Person", "Company"],
            "acceptable_latency_ms": int
        }
    },
    "preference_insights": {
        "complexity": {
            "level": "SIMPLE|MODERATE|COMPLEX",
            "confidence": 0.0-1.0
        },
        "patterns": {
            "top_patterns": ["DIRECT", "MULTI_HOP"],
            "confidence": 0.0-1.0
        },
        "performance": {
            "threshold_ms": int,
            "confidence": 0.0-1.0
        },
        "data": {
            "frequent_types": ["Person", "Company"],
            "avg_result_size": int,
            "confidence": 0.0-1.0
        }
    },
    "query_suggestions": {
        "improvements": [
            {
                "suggestion": "string",
                "rationale": "string",
                "confidence": 0.0-1.0
            }
        ],
        "alternatives": [
            {
                "query": "string",
                "rationale": "string",
                "confidence": 0.0-1.0
            }
        ],
        "completions": [
            {
                "completion": "string",
                "rationale": "string",
                "confidence": 0.0-1.0
            }
        ]
    },
    "enhancement_recommendations": {
        "apply_to_current_query": ["recommendation1", "recommendation2"],
        "general_best_practices": ["practice1", "practice2"],
        "personalization_opportunities": ["opportunity1", "opportunity2"]
    }
}

Guidelines:
1. Always retrieve context first to understand user patterns
2. Use auto learning mode by default for preference learning
3. Generate multiple types of suggestions (improvements, alternatives, completions)
4. Confidence scores should reflect data quality and quantity
5. Provide actionable recommendations based on context
6. Consider both immediate query needs and long-term user patterns
7. Balance personalization with query correctness
8. Warn if insufficient historical data for reliable learning
"""

        # Define actions (tools) for this operator
        actions = [
            Action(
                name="retrieve_context",
                description="Retrieve relevant context from query history",
                namespace="tugraph.context_tools"
            ),
            Action(
                name="learn_preferences",
                description="Learn user preferences from query history",
                namespace="tugraph.context_tools"
            ),
            Action(
                name="suggest_queries",
                description="Generate context-based query suggestions",
                namespace="tugraph.context_tools"
            ),
        ]

        config = OperatorConfig(
            instruction=instruction,
            actions=actions,
            id=operator_id or "context_enhancement_operator",
            output_schema="context_enhancement_result",
            threshold=0.6,  # Lower threshold - context is supplementary
            hops=1
        )

        super().__init__(config=config)


def create_context_enhancement_operator(
    operator_id: Optional[str] = None
) -> ContextEnhancementOperator:
    """Factory function to create ContextEnhancementOperator.

    Args:
        operator_id (str, optional): Custom operator ID

    Returns:
        ContextEnhancementOperator: Configured operator instance

    Example:
        operator = create_context_enhancement_operator()
        result = await operator.execute(reasoner, job, workflow_messages)
    """
    return ContextEnhancementOperator(operator_id=operator_id)
