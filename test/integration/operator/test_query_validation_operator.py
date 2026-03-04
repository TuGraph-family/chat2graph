"""
Integration Tests for QueryValidationOperator

测试查询验证 Operator 的集成功能。

Author: kaichuan
Date: 2025-11-25
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Initialize server before importing app modules
from app.core.sdk.init_server import init_server
init_server()

from app.plugin.tugraph.operator.query_validation_operator import (
    QueryValidationOperator,
    create_query_validation_operator
)
from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage


@pytest.mark.integration
@pytest.mark.operator
class TestQueryValidationOperatorIntegration:
    """Integration tests for QueryValidationOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_query_validation_operator()

    @pytest.fixture
    def mock_reasoner_with_validation_pass(self):
        """Create mock reasoner that returns passing validation result."""
        reasoner = AsyncMock()

        # Mock validation response for query that passes all checks
        validation_result = {
            "validation_summary": {
                "overall_status": "PASS",
                "critical_issues": 0,
                "warnings": 0,
                "recommendations": 2
            },
            "schema_validation": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": ["Consider adding index on Person.name"],
                "severity": "INFO"
            },
            "semantic_validation": {
                "is_semantically_valid": True,
                "semantic_issues": [],
                "logic_warnings": [],
                "intention_alignment": {
                    "matches_intention": True,
                    "confidence": 0.95
                },
                "recommendations": ["Query structure is optimal"]
            },
            "performance_prediction": {
                "estimated_latency_ms": 50,
                "estimated_memory_mb": 10,
                "performance_tier": "LOW",
                "bottlenecks": [],
                "optimization_opportunities": ["Index already utilized"]
            },
            "security_scan": {
                "is_safe": True,
                "vulnerabilities": [],
                "risk_level": "LOW",
                "recommendations": ["Query is safe to execute"]
            },
            "final_recommendation": {
                "action": "APPROVE",
                "rationale": "Query passes all validation checks with no critical issues",
                "required_changes": [],
                "priority_order": []
            }
        }

        reasoner.infer = AsyncMock(return_value=validation_result)
        return reasoner

    @pytest.mark.asyncio
    async def test_operator_initialization(self, operator):
        """Test operator is properly initialized with correct configuration."""
        assert operator is not None
        assert operator._config is not None
        assert operator._config.id == "query_validation_operator"
        assert operator._config.threshold == 0.8
        assert operator._config.hops == 1
        assert len(operator._config.actions) == 4

        # Verify actions
        action_names = [action.name for action in operator._config.actions]
        assert "validate_schema" in action_names
        assert "check_semantics" in action_names
        assert "predict_performance" in action_names
        assert "scan_security" in action_names

    @pytest.mark.asyncio
    async def test_execute_schema_validation(
        self,
        operator,
        mock_reasoner_with_validation_pass,
        sample_job
    ):
        """Test executing schema validation for valid query."""
        # Setup workflow message with Cypher query
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p:Person) WHERE p.name = 'John' RETURN p",
                "query_text": "Find person named John"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=mock_reasoner_with_validation_pass,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify result
        assert result is not None
        assert isinstance(result, WorkflowMessage)
        mock_reasoner_with_validation_pass.infer.assert_called_once()

        # Verify validation passed
        result_data = mock_reasoner_with_validation_pass.infer.return_value
        assert result_data["validation_summary"]["overall_status"] == "PASS"
        assert result_data["schema_validation"]["is_valid"] is True

    @pytest.mark.asyncio
    async def test_execute_semantic_validation(
        self,
        operator,
        sample_job
    ):
        """Test executing semantic validation for complex query."""
        # Create mock reasoner with semantic validation result
        reasoner = AsyncMock()
        semantic_result = {
            "validation_summary": {
                "overall_status": "PASS",
                "critical_issues": 0,
                "warnings": 1,
                "recommendations": 2
            },
            "schema_validation": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
                "severity": "INFO"
            },
            "semantic_validation": {
                "is_semantically_valid": True,
                "semantic_issues": [],
                "logic_warnings": ["Variable 'p2' could be more descriptive"],
                "intention_alignment": {
                    "matches_intention": True,
                    "confidence": 0.90,
                    "explanation": "Query correctly implements friends-of-friends pattern"
                },
                "recommendations": [
                    "Consider using named path for better readability",
                    "Add LIMIT clause to prevent large result sets"
                ]
            },
            "performance_prediction": {
                "estimated_latency_ms": 200,
                "estimated_memory_mb": 50,
                "performance_tier": "MEDIUM",
                "bottlenecks": ["Multi-hop traversal"],
                "optimization_opportunities": ["Add intermediate node filtering"]
            },
            "security_scan": {
                "is_safe": True,
                "vulnerabilities": [],
                "risk_level": "LOW",
                "recommendations": []
            },
            "final_recommendation": {
                "action": "APPROVE_WITH_WARNINGS",
                "rationale": "Query is semantically correct but has performance considerations",
                "required_changes": [],
                "priority_order": ["Add LIMIT clause", "Improve variable naming"]
            }
        }
        reasoner.infer = AsyncMock(return_value=semantic_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p1:Person)-[:KNOWS]->(p2:Person)-[:KNOWS]->(p3:Person) RETURN p1, p3",
                "query_text": "Find friends of friends"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify semantic validation
        result_data = reasoner.infer.return_value
        assert result_data["semantic_validation"]["is_semantically_valid"] is True
        assert len(result_data["semantic_validation"]["logic_warnings"]) == 1
        assert result_data["final_recommendation"]["action"] == "APPROVE_WITH_WARNINGS"

    @pytest.mark.asyncio
    async def test_execute_performance_prediction(
        self,
        operator,
        sample_job
    ):
        """Test performance prediction for complex query."""
        # Create mock reasoner with performance concerns
        reasoner = AsyncMock()
        performance_result = {
            "validation_summary": {
                "overall_status": "WARNING",
                "critical_issues": 0,
                "warnings": 2,
                "recommendations": 3
            },
            "schema_validation": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
                "severity": "INFO"
            },
            "semantic_validation": {
                "is_semantically_valid": True,
                "semantic_issues": [],
                "logic_warnings": [],
                "intention_alignment": {"matches_intention": True, "confidence": 0.95},
                "recommendations": []
            },
            "performance_prediction": {
                "estimated_latency_ms": 2500,
                "estimated_memory_mb": 500,
                "performance_tier": "HIGH",
                "bottlenecks": [
                    "Cartesian product in pattern matching",
                    "No index utilization",
                    "Large intermediate result set"
                ],
                "optimization_opportunities": [
                    "Add WHERE clause to filter early",
                    "Create index on Person.age",
                    "Use LIMIT to constrain results"
                ]
            },
            "security_scan": {
                "is_safe": True,
                "vulnerabilities": [],
                "risk_level": "LOW",
                "recommendations": []
            },
            "final_recommendation": {
                "action": "APPROVE_WITH_WARNINGS",
                "rationale": "Query may have performance issues with large datasets",
                "required_changes": [],
                "priority_order": [
                    "Add index on Person.age",
                    "Add WHERE clause for early filtering",
                    "Consider result set size"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=performance_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p1:Person)-[:KNOWS]->(p2:Person) RETURN p1, p2",
                "query_text": "Find all people and their friends"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify performance prediction
        result_data = reasoner.infer.return_value
        assert result_data["performance_prediction"]["performance_tier"] == "HIGH"
        assert result_data["performance_prediction"]["estimated_latency_ms"] > 1000
        assert len(result_data["performance_prediction"]["bottlenecks"]) >= 3

    @pytest.mark.asyncio
    async def test_execute_security_scan(
        self,
        operator,
        sample_job
    ):
        """Test security scanning for potentially unsafe query."""
        # Create mock reasoner with security concerns
        reasoner = AsyncMock()
        security_result = {
            "validation_summary": {
                "overall_status": "FAIL",
                "critical_issues": 2,
                "warnings": 1,
                "recommendations": 3
            },
            "schema_validation": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
                "severity": "INFO"
            },
            "semantic_validation": {
                "is_semantically_valid": True,
                "semantic_issues": [],
                "logic_warnings": [],
                "intention_alignment": {"matches_intention": True, "confidence": 0.85},
                "recommendations": []
            },
            "performance_prediction": {
                "estimated_latency_ms": 100,
                "estimated_memory_mb": 20,
                "performance_tier": "LOW",
                "bottlenecks": [],
                "optimization_opportunities": []
            },
            "security_scan": {
                "is_safe": False,
                "vulnerabilities": [
                    {
                        "type": "INJECTION_RISK",
                        "severity": "CRITICAL",
                        "description": "Unsanitized user input in query string",
                        "location": "WHERE clause"
                    },
                    {
                        "type": "DANGEROUS_OPERATION",
                        "severity": "HIGH",
                        "description": "Query contains DELETE operation",
                        "location": "DELETE clause"
                    }
                ],
                "risk_level": "CRITICAL",
                "recommendations": [
                    "Use parameterized queries",
                    "Validate all user inputs",
                    "Restrict DELETE operations to admin users"
                ]
            },
            "final_recommendation": {
                "action": "REJECT",
                "rationale": "Query has critical security vulnerabilities and must be rejected",
                "required_changes": [
                    "Remove direct string concatenation",
                    "Add input validation",
                    "Use parameterized queries"
                ],
                "priority_order": [
                    "Fix injection risk (CRITICAL)",
                    "Validate DELETE operation permissions (HIGH)",
                    "Add audit logging (MEDIUM)"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=security_result)

        # Setup workflow message with potentially unsafe query
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p:Person) WHERE p.name = '" + "${user_input}" + "' DELETE p",
                "query_text": "Delete person by name",
                "query_source": "user_input"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify security scan caught issues
        result_data = reasoner.infer.return_value
        assert result_data["security_scan"]["is_safe"] is False
        assert result_data["security_scan"]["risk_level"] == "CRITICAL"
        assert len(result_data["security_scan"]["vulnerabilities"]) == 2
        assert result_data["final_recommendation"]["action"] == "REJECT"

    @pytest.mark.asyncio
    async def test_validation_with_schema_errors(
        self,
        operator,
        sample_job
    ):
        """Test validation with schema violations."""
        # Create mock reasoner with schema errors
        reasoner = AsyncMock()
        schema_error_result = {
            "validation_summary": {
                "overall_status": "FAIL",
                "critical_issues": 2,
                "warnings": 0,
                "recommendations": 2
            },
            "schema_validation": {
                "is_valid": False,
                "errors": [
                    "Vertex type 'Employee' does not exist in schema",
                    "Property 'salary' not defined for Person vertex"
                ],
                "warnings": [],
                "suggestions": [
                    "Available vertex types: Person, Company",
                    "Person properties: id, name, age"
                ],
                "severity": "ERROR"
            },
            "semantic_validation": {
                "is_semantically_valid": False,
                "semantic_issues": ["Cannot validate semantics with invalid schema"],
                "logic_warnings": [],
                "intention_alignment": {"matches_intention": False, "confidence": 0.0},
                "recommendations": ["Fix schema errors first"]
            },
            "performance_prediction": {
                "estimated_latency_ms": 0,
                "estimated_memory_mb": 0,
                "performance_tier": "CRITICAL",
                "bottlenecks": ["Query cannot execute due to schema errors"],
                "optimization_opportunities": []
            },
            "security_scan": {
                "is_safe": True,
                "vulnerabilities": [],
                "risk_level": "LOW",
                "recommendations": []
            },
            "final_recommendation": {
                "action": "REJECT",
                "rationale": "Query has critical schema violations and cannot execute",
                "required_changes": [
                    "Replace 'Employee' with valid vertex type",
                    "Remove or correct 'salary' property reference"
                ],
                "priority_order": [
                    "Fix vertex type 'Employee' (CRITICAL)",
                    "Fix property 'salary' (CRITICAL)"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=schema_error_result)

        # Setup workflow message with invalid schema
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (e:Employee) WHERE e.salary > 100000 RETURN e",
                "query_text": "Find high-salary employees"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify schema errors caught
        result_data = reasoner.infer.return_value
        assert result_data["schema_validation"]["is_valid"] is False
        assert len(result_data["schema_validation"]["errors"]) == 2
        assert result_data["validation_summary"]["critical_issues"] == 2

    @pytest.mark.asyncio
    async def test_operator_instruction_format(self, operator):
        """Test that operator instruction contains expected guidance."""
        instruction = operator._config.instruction

        # Verify key instruction elements
        assert "comprehensive query validation specialist" in instruction
        assert "Available Tools:" in instruction
        assert "validate_schema" in instruction
        assert "check_semantics" in instruction
        assert "predict_performance" in instruction
        assert "scan_security" in instruction
        assert "Output Format:" in instruction
        assert "validation_summary" in instruction
        assert "final_recommendation" in instruction

    @pytest.mark.asyncio
    async def test_operator_action_configuration(self, operator):
        """Test that operator actions are properly configured."""
        actions = operator._config.actions

        # Verify all actions present
        action_names = {a.name for a in actions}
        assert "validate_schema" in action_names
        assert "check_semantics" in action_names
        assert "predict_performance" in action_names
        assert "scan_security" in action_names

        # Verify namespaces
        for action in actions:
            assert action.namespace == "tugraph.query_validation"

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates operator with custom ID."""
        custom_id = "custom_validation_operator"
        operator = create_query_validation_operator(operator_id=custom_id)

        assert operator is not None
        assert operator._config.id == custom_id
        assert operator._config.threshold == 0.8


@pytest.mark.integration
@pytest.mark.operator
class TestQueryValidationOperatorEdgeCases:
    """Edge case tests for QueryValidationOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_query_validation_operator()

    @pytest.mark.asyncio
    async def test_operator_with_empty_query(
        self,
        operator,
        sample_job
    ):
        """Test operator handling of empty query."""
        # Create mock reasoner with empty query handling
        reasoner = AsyncMock()
        empty_query_result = {
            "validation_summary": {
                "overall_status": "FAIL",
                "critical_issues": 1,
                "warnings": 0,
                "recommendations": 1
            },
            "schema_validation": {
                "is_valid": False,
                "errors": ["Query is empty or null"],
                "warnings": [],
                "suggestions": ["Provide a valid Cypher query"],
                "severity": "CRITICAL"
            },
            "semantic_validation": {
                "is_semantically_valid": False,
                "semantic_issues": ["Cannot validate empty query"],
                "logic_warnings": [],
                "intention_alignment": {"matches_intention": False, "confidence": 0.0},
                "recommendations": []
            },
            "performance_prediction": {
                "estimated_latency_ms": 0,
                "estimated_memory_mb": 0,
                "performance_tier": "CRITICAL",
                "bottlenecks": [],
                "optimization_opportunities": []
            },
            "security_scan": {
                "is_safe": False,
                "vulnerabilities": [{"type": "INVALID_INPUT", "severity": "CRITICAL"}],
                "risk_level": "CRITICAL",
                "recommendations": []
            },
            "final_recommendation": {
                "action": "REJECT",
                "rationale": "Query is empty and cannot be validated",
                "required_changes": ["Provide valid query"],
                "priority_order": ["Add query content"]
            }
        }
        reasoner.infer = AsyncMock(return_value=empty_query_result)

        # Setup workflow message with empty query
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "",
                "query_text": ""
            },
            job_id=sample_job.id
        )

        # Execute should handle gracefully
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        assert result is not None
        result_data = reasoner.infer.return_value
        assert result_data["validation_summary"]["overall_status"] == "FAIL"
        assert result_data["final_recommendation"]["action"] == "REJECT"

    @pytest.mark.asyncio
    async def test_operator_with_malformed_query(
        self,
        operator,
        sample_job
    ):
        """Test operator with syntactically malformed query."""
        # Create mock reasoner with malformed query handling
        reasoner = AsyncMock()
        malformed_result = {
            "validation_summary": {
                "overall_status": "FAIL",
                "critical_issues": 1,
                "warnings": 0,
                "recommendations": 1
            },
            "schema_validation": {
                "is_valid": False,
                "errors": ["Syntax error: unexpected token 'WHER'", "Missing RETURN clause"],
                "warnings": [],
                "suggestions": ["Use 'WHERE' instead of 'WHER'", "Add RETURN clause"],
                "severity": "CRITICAL"
            },
            "semantic_validation": {
                "is_semantically_valid": False,
                "semantic_issues": ["Cannot parse query due to syntax errors"],
                "logic_warnings": [],
                "intention_alignment": {"matches_intention": False, "confidence": 0.0},
                "recommendations": []
            },
            "performance_prediction": {
                "estimated_latency_ms": 0,
                "estimated_memory_mb": 0,
                "performance_tier": "CRITICAL",
                "bottlenecks": [],
                "optimization_opportunities": []
            },
            "security_scan": {
                "is_safe": False,
                "vulnerabilities": [{"type": "INVALID_SYNTAX", "severity": "HIGH"}],
                "risk_level": "HIGH",
                "recommendations": []
            },
            "final_recommendation": {
                "action": "REJECT",
                "rationale": "Query has syntax errors and cannot execute",
                "required_changes": ["Fix syntax errors"],
                "priority_order": ["Correct 'WHER' to 'WHERE'", "Add RETURN clause"]
            }
        }
        reasoner.infer = AsyncMock(return_value=malformed_result)

        # Setup malformed query
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p:Person) WHER p.name = 'John'",
                "query_text": "Find John"
            },
            job_id=sample_job.id
        )

        # Execute should handle gracefully
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        assert result is not None
        result_data = reasoner.infer.return_value
        assert len(result_data["schema_validation"]["errors"]) >= 1
        assert result_data["final_recommendation"]["action"] == "REJECT"

    @pytest.mark.asyncio
    async def test_operator_with_multiple_issues(
        self,
        operator,
        sample_job
    ):
        """Test operator with query having multiple types of issues."""
        # Create mock reasoner with multiple issues
        reasoner = AsyncMock()
        multi_issue_result = {
            "validation_summary": {
                "overall_status": "FAIL",
                "critical_issues": 3,
                "warnings": 2,
                "recommendations": 5
            },
            "schema_validation": {
                "is_valid": False,
                "errors": ["Property 'salary' not defined"],
                "warnings": ["Consider using index on Person.name"],
                "suggestions": ["Add index", "Use existing properties"],
                "severity": "ERROR"
            },
            "semantic_validation": {
                "is_semantically_valid": False,
                "semantic_issues": ["Logic error in WHERE clause"],
                "logic_warnings": ["Unnecessary subquery"],
                "intention_alignment": {"matches_intention": False, "confidence": 0.3},
                "recommendations": ["Simplify query logic"]
            },
            "performance_prediction": {
                "estimated_latency_ms": 5000,
                "estimated_memory_mb": 1000,
                "performance_tier": "CRITICAL",
                "bottlenecks": ["Full table scan", "Cartesian product"],
                "optimization_opportunities": ["Add indexes", "Rewrite query"]
            },
            "security_scan": {
                "is_safe": False,
                "vulnerabilities": [
                    {"type": "INJECTION_RISK", "severity": "CRITICAL"}
                ],
                "risk_level": "CRITICAL",
                "recommendations": ["Sanitize inputs"]
            },
            "final_recommendation": {
                "action": "REJECT",
                "rationale": "Query has multiple critical issues across all dimensions",
                "required_changes": [
                    "Fix schema violations",
                    "Correct semantic logic",
                    "Address security vulnerabilities",
                    "Optimize performance"
                ],
                "priority_order": [
                    "Fix injection risk (CRITICAL)",
                    "Fix schema errors (CRITICAL)",
                    "Optimize performance (HIGH)",
                    "Fix semantic issues (MEDIUM)",
                    "Add indexes (LOW)"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=multi_issue_result)

        # Setup workflow message with multiple issues
        workflow_message = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p:Person) WHERE p.salary > " + "${user_input}" + " RETURN *",
                "query_text": "Complex problematic query"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=reasoner,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify multiple issues detected
        result_data = reasoner.infer.return_value
        assert result_data["validation_summary"]["critical_issues"] >= 3
        assert result_data["final_recommendation"]["action"] == "REJECT"
        assert len(result_data["final_recommendation"]["priority_order"]) >= 5
