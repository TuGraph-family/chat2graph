"""
Query Validation Operator

全面验证查询的 Schema 合规性、语义正确性、性能和安全性的 Operator。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Optional

from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.toolkit.action import Action


class QueryValidationOperator(Operator):
    """Operator for comprehensive query validation.

    This operator orchestrates validation tools to ensure queries are:
    1. Schema-compliant
    2. Semantically correct
    3. Performance-efficient
    4. Security-safe

    Workflow:
        1. Validate against graph schema
        2. Check semantic correctness
        3. Predict performance characteristics
        4. Scan for security vulnerabilities
        5. Generate validation report with recommendations
    """

    def __init__(self, operator_id: Optional[str] = None):
        """Initialize QueryValidationOperator.

        Args:
            operator_id (str, optional): Custom operator ID
        """
        instruction = """You are a comprehensive query validation specialist for TuGraph.

Your task is to validate Cypher queries across multiple dimensions:
1. Schema Compliance: Verify vertex types and properties exist
2. Semantic Correctness: Check logic, variables, and intent alignment
3. Performance: Predict execution time and resource usage
4. Security: Scan for injection risks and dangerous operations

Available Tools:
- validate_schema: Validate query against graph schema
- check_semantics: Check semantic correctness and logic
- predict_performance: Predict performance characteristics
- scan_security: Scan for security vulnerabilities

Input Format:
- Cypher query (generated or user-provided)
- Graph database service instance
- Optional: Query intention, complexity analysis, query source

Output Format:
{
    "validation_summary": {
        "overall_status": "PASS|WARNING|FAIL",
        "critical_issues": int,
        "warnings": int,
        "recommendations": int
    },
    "schema_validation": {
        "is_valid": bool,
        "errors": ["error1", "error2"],
        "warnings": ["warning1"],
        "suggestions": ["suggestion1"],
        "severity": "INFO|WARNING|ERROR|CRITICAL"
    },
    "semantic_validation": {
        "is_semantically_valid": bool,
        "semantic_issues": ["issue1"],
        "logic_warnings": ["warning1"],
        "intention_alignment": {...},
        "recommendations": ["rec1"]
    },
    "performance_prediction": {
        "estimated_latency_ms": int,
        "estimated_memory_mb": int,
        "performance_tier": "LOW|MEDIUM|HIGH|CRITICAL",
        "bottlenecks": ["bottleneck1"],
        "optimization_opportunities": ["opt1"]
    },
    "security_scan": {
        "is_safe": bool,
        "vulnerabilities": [...],
        "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
        "recommendations": ["rec1"]
    },
    "final_recommendation": {
        "action": "APPROVE|APPROVE_WITH_WARNINGS|REJECT|REQUIRE_MODIFICATION",
        "rationale": "explanation",
        "required_changes": ["change1", "change2"],
        "priority_order": ["highest priority issue", "..."]
    }
}

Guidelines:
1. Schema validation is mandatory - must pass for query to execute
2. Semantic issues should be addressed before optimization
3. Performance warnings are advisory but critical tier needs attention
4. Security issues take highest priority - reject unsafe queries
5. Provide clear, actionable recommendations
6. Order issues by severity and impact
7. Consider the query source (user_input has higher security scrutiny)
"""

        # Define actions (tools) for this operator
        actions = [
            Action(
                name="validate_schema",
                description="Validate Cypher query against graph schema",
                namespace="tugraph.query_validation"
            ),
            Action(
                name="check_semantics",
                description="Check semantic correctness of Cypher query",
                namespace="tugraph.query_validation"
            ),
            Action(
                name="predict_performance",
                description="Predict query performance characteristics",
                namespace="tugraph.query_validation"
            ),
            Action(
                name="scan_security",
                description="Scan query for security vulnerabilities",
                namespace="tugraph.query_validation"
            ),
        ]

        config = OperatorConfig(
            instruction=instruction,
            actions=actions,
            id=operator_id or "query_validation_operator",
            output_schema="validation_report",
            threshold=0.8,  # Higher threshold for validation
            hops=1
        )

        super().__init__(config=config)


def create_query_validation_operator(
    operator_id: Optional[str] = None
) -> QueryValidationOperator:
    """Factory function to create QueryValidationOperator.

    Args:
        operator_id (str, optional): Custom operator ID

    Returns:
        QueryValidationOperator: Configured operator instance

    Example:
        operator = create_query_validation_operator()
        result = await operator.execute(reasoner, job, workflow_messages)
    """
    return QueryValidationOperator(operator_id=operator_id)
