"""
Path Pattern Recognition Operator

识别复杂路径模式并构建时间/空间查询条件的 Operator。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional

from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.toolkit.action import Action


class PathPatternRecognitionOperator(Operator):
    """Operator for recognizing complex path patterns and building temporal/spatial queries.

    This operator orchestrates multi-hop reasoning tools to identify path patterns
    and construct appropriate temporal and spatial query conditions.

    Workflow:
        1. Recognize path patterns (direct, multi-hop, variable-length, shortest)
        2. Extract temporal constraints and build time conditions
        3. Extract spatial constraints and build location conditions
        4. Combine patterns and constraints into structured output
    """

    def __init__(self, operator_id: Optional[str] = None):
        """Initialize PathPatternRecognitionOperator.

        Args:
            operator_id (str, optional): Custom operator ID
        """
        instruction = """You are a path pattern recognition specialist for TuGraph.

Your task is to identify complex graph traversal patterns and build appropriate query conditions:
1. Recognize path patterns (DIRECT, MULTI_HOP, VARIABLE_LENGTH, SHORTEST_PATH, PATTERN_MATCH)
2. Extract and build temporal query conditions
3. Extract and build spatial query conditions
4. Combine all patterns and constraints into a unified structure

Available Tools:
- recognize_patterns: Identify path patterns from natural language
- build_temporal_query: Build Cypher temporal conditions from time expressions
- build_spatial_query: Build Cypher spatial conditions from location expressions

Input Format:
- Natural language query
- Optional: Intention analysis result

Output Format:
{
    "path_analysis": {
        "has_multi_hop": bool,
        "patterns": [
            {
                "pattern_type": "DIRECT|MULTI_HOP|VARIABLE_LENGTH|SHORTEST_PATH|PATTERN_MATCH",
                "source_entity": "string",
                "target_entity": "string",
                "relationship_types": ["string"],
                "min_depth": int,
                "max_depth": int,
                "bidirectional": bool,
                "temporal_constraints": {...},
                "spatial_constraints": {...}
            }
        ]
    },
    "temporal_conditions": {
        "cypher_condition": "string",
        "cypher_function": "string",
        "start_timestamp": int,
        "end_timestamp": int,
        "explanation": "string"
    },
    "spatial_conditions": {
        "cypher_condition": "string",
        "cypher_function": "string",
        "distance": float,
        "distance_unit": "km|mile|meter",
        "center_point": {...},
        "explanation": "string"
    },
    "combined_cypher_hints": {
        "path_pattern_cypher": "Cypher pattern template",
        "where_conditions": ["condition1", "condition2"],
        "recommended_functions": ["function1", "function2"]
    }
}

Guidelines:
1. Always recognize patterns first before building conditions
2. For temporal queries, use Unix timestamps for consistency
3. For spatial queries, use point() and distance() functions
4. Handle missing temporal/spatial expressions gracefully
5. Provide clear explanations for all generated conditions
6. Consider query complexity when recommending patterns
"""

        # Define actions (tools) for this operator
        actions = [
            Action(
                name="recognize_patterns",
                description="Recognize path patterns from natural language query",
                namespace="tugraph.multi_hop_reasoning"
            ),
            Action(
                name="build_temporal_query",
                description="Build temporal query conditions from time expressions",
                namespace="tugraph.multi_hop_reasoning"
            ),
            Action(
                name="build_spatial_query",
                description="Build spatial query conditions from location expressions",
                namespace="tugraph.multi_hop_reasoning"
            ),
        ]

        config = OperatorConfig(
            instruction=instruction,
            actions=actions,
            id=operator_id or "path_pattern_recognition_operator",
            output_schema="path_pattern_result",
            threshold=0.7,
            hops=1
        )

        super().__init__(config=config)


def create_path_pattern_recognition_operator(
    operator_id: Optional[str] = None
) -> PathPatternRecognitionOperator:
    """Factory function to create PathPatternRecognitionOperator.

    Args:
        operator_id (str, optional): Custom operator ID

    Returns:
        PathPatternRecognitionOperator: Configured operator instance

    Example:
        operator = create_path_pattern_recognition_operator()
        result = await operator.execute(reasoner, job, workflow_messages)
    """
    return PathPatternRecognitionOperator(operator_id=operator_id)
