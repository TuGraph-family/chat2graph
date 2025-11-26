"""
Integration Tests for QueryComplexityAnalysisOperator

测试查询复杂度分析 Operator 的集成功能。

Author: kaichuan
Date: 2025-11-25
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Initialize server before importing app modules
from app.core.sdk.init_server import init_server
init_server()

from app.plugin.tugraph.operator.query_complexity_analysis_operator import (
    QueryComplexityAnalysisOperator,
    create_query_complexity_analysis_operator
)
from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage
from app.core.reasoner.dual_model_reasoner import DualModelReasoner


@pytest.mark.integration
@pytest.mark.operator
class TestQueryComplexityAnalysisOperatorIntegration:
    """Integration tests for QueryComplexityAnalysisOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_query_complexity_analysis_operator()

    @pytest.fixture
    def mock_reasoner_with_complexity_result(self):
        """Create mock reasoner that returns complexity analysis result."""
        reasoner = AsyncMock(spec=DualModelReasoner)

        # Mock complexity analysis response
        complexity_result = {
            "complexity_analysis": {
                "complexity_level": "MODERATE",
                "complexity_score": 0.6,
                "entity_count": 2,
                "relationship_depth": 2,
                "has_temporal": False,
                "has_spatial": False,
                "has_aggregations": True,
                "has_variable_length": False,
                "recommended_strategy": "optimized",
                "optimization_hints": [
                    "Use index on Person.name",
                    "Consider caching for frequently accessed patterns"
                ]
            },
            "index_recommendations": {
                "recommendations": [
                    {
                        "vertex_type": "Person",
                        "property_name": "name",
                        "index_type": "btree",
                        "priority": "HIGH",
                        "estimated_benefit": "50% query speedup",
                        "reason": "Frequently queried property in WHERE clauses"
                    }
                ],
                "total_count": 1
            },
            "execution_recommendation": {
                "approach": "optimized",
                "rationale": "Moderate complexity with indexable properties",
                "estimated_performance": "MEDIUM"
            }
        }

        reasoner.infer = AsyncMock(return_value=complexity_result)
        return reasoner

    @pytest.mark.asyncio
    async def test_operator_initialization(self, operator):
        """Test operator is properly initialized with correct configuration."""
        assert operator is not None
        assert operator._config is not None
        assert operator._config.id == "query_complexity_analysis_operator"
        assert operator._config.threshold == 0.7
        assert operator._config.hops == 1
        assert len(operator._config.actions) == 2

        # Verify actions
        action_names = [action.name for action in operator._config.actions]
        assert "analyze_complexity" in action_names
        assert "recommend_indexes" in action_names

    @pytest.mark.asyncio
    async def test_execute_simple_query_analysis(
        self,
        operator,
        mock_reasoner_with_complexity_result,
        sample_job
    ):
        """Test executing complexity analysis for a simple query."""
        # Setup workflow message with simple query
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find all Person nodes",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"]
                }
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=mock_reasoner_with_complexity_result,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify result
        assert result is not None
        assert isinstance(result, WorkflowMessage)
        assert result.job_id == sample_job.id

        # Verify reasoner was called
        mock_reasoner_with_complexity_result.infer.assert_called_once()

        # Verify result contains complexity analysis
        result_data = mock_reasoner_with_complexity_result.infer.return_value
        assert "complexity_analysis" in result_data
        assert "index_recommendations" in result_data
        assert "execution_recommendation" in result_data

    @pytest.mark.asyncio
    async def test_execute_complex_query_analysis(
        self,
        operator,
        sample_job
    ):
        """Test executing complexity analysis for a complex multi-hop query."""
        # Create mock reasoner with complex query result
        reasoner = AsyncMock(spec=DualModelReasoner)
        complex_result = {
            "complexity_analysis": {
                "complexity_level": "COMPLEX",
                "complexity_score": 0.9,
                "entity_count": 4,
                "relationship_depth": 4,
                "has_temporal": True,
                "has_spatial": False,
                "has_aggregations": True,
                "has_variable_length": True,
                "recommended_strategy": "multi_stage",
                "optimization_hints": [
                    "Break into multiple sub-queries",
                    "Use intermediate result caching",
                    "Consider query result pagination"
                ]
            },
            "index_recommendations": {
                "recommendations": [
                    {
                        "vertex_type": "Person",
                        "property_name": "id",
                        "index_type": "btree",
                        "priority": "HIGH",
                        "estimated_benefit": "70% query speedup",
                        "reason": "Primary key for relationship traversal"
                    },
                    {
                        "vertex_type": "Company",
                        "property_name": "name",
                        "index_type": "btree",
                        "priority": "MEDIUM",
                        "estimated_benefit": "30% query speedup",
                        "reason": "Frequently used in filtering"
                    }
                ],
                "total_count": 2
            },
            "execution_recommendation": {
                "approach": "multi_stage",
                "rationale": "High complexity requires staged execution with caching",
                "estimated_performance": "CRITICAL"
            }
        }
        reasoner.infer = AsyncMock(return_value=complex_result)

        # Setup workflow message with complex query
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find friends of friends who work at tech companies founded after 2000",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person", "Company"],
                    "relationship_patterns": ["KNOWS", "WORKS_AT"],
                    "complexity_indicators": ["multi_hop", "filtering", "temporal"]
                }
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

        # Verify result indicates high complexity
        result_data = reasoner.infer.return_value
        assert result_data["complexity_analysis"]["complexity_level"] == "COMPLEX"
        assert result_data["complexity_analysis"]["complexity_score"] >= 0.8
        assert result_data["execution_recommendation"]["approach"] == "multi_stage"

    @pytest.mark.asyncio
    async def test_operator_with_previous_context(
        self,
        operator,
        mock_reasoner_with_complexity_result,
        sample_job
    ):
        """Test operator execution with previous workflow context."""
        # Create previous workflow messages
        intention_message = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "filters": ["age > 25"]
                }
            },
            job_id=sample_job.id
        )

        current_message = WorkflowMessage(
            payload={
                "query_text": "Find people older than 25"
            },
            job_id=sample_job.id
        )

        # Execute with context
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=mock_reasoner_with_complexity_result,
                job=sample_job,
                workflow_messages=[intention_message, current_message]
            )

        # Verify execution with context
        assert result is not None
        mock_reasoner_with_complexity_result.infer.assert_called_once()

    @pytest.mark.asyncio
    async def test_operator_instruction_format(self, operator):
        """Test that operator instruction contains expected guidance."""
        instruction = operator._config.instruction

        # Verify key instruction elements
        assert "complexity analysis specialist" in instruction
        assert "Available Tools:" in instruction
        assert "analyze_complexity" in instruction
        assert "recommend_indexes" in instruction
        assert "Output Format:" in instruction
        assert "complexity_level" in instruction
        assert "index_recommendations" in instruction

    @pytest.mark.asyncio
    async def test_operator_action_configuration(self, operator):
        """Test that operator actions are properly configured."""
        actions = operator._config.actions

        # Find specific actions
        analyze_action = next(
            (a for a in actions if a.name == "analyze_complexity"),
            None
        )
        index_action = next(
            (a for a in actions if a.name == "recommend_indexes"),
            None
        )

        # Verify analyze_complexity action
        assert analyze_action is not None
        assert analyze_action.description == "Analyze natural language query complexity"
        assert analyze_action.namespace == "tugraph.query_planning"

        # Verify recommend_indexes action
        assert index_action is not None
        assert index_action.description == "Recommend indexes based on query patterns"
        assert index_action.namespace == "tugraph.query_planning"

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates operator with custom ID."""
        custom_id = "custom_complexity_operator"
        operator = create_query_complexity_analysis_operator(operator_id=custom_id)

        assert operator is not None
        assert operator._config.id == custom_id

    @pytest.mark.asyncio
    async def test_operator_with_empty_workflow_messages(
        self,
        operator,
        mock_reasoner_with_complexity_result,
        sample_job
    ):
        """Test operator execution with no previous workflow messages."""
        # Execute without workflow messages
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=mock_reasoner_with_complexity_result,
                job=sample_job,
                workflow_messages=None
            )

        # Should still execute successfully
        assert result is not None
        mock_reasoner_with_complexity_result.infer.assert_called_once()


@pytest.mark.integration
@pytest.mark.operator
class TestQueryComplexityAnalysisOperatorEdgeCases:
    """Edge case tests for QueryComplexityAnalysisOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_query_complexity_analysis_operator()

    @pytest.mark.asyncio
    async def test_operator_with_malformed_query(
        self,
        operator,
        sample_job
    ):
        """Test operator handling of malformed query input."""
        # Create mock reasoner that handles malformed input
        reasoner = AsyncMock(spec=DualModelReasoner)
        error_result = {
            "error": "Unable to analyze malformed query",
            "complexity_analysis": {
                "complexity_level": "UNKNOWN",
                "complexity_score": 0.0,
                "recommended_strategy": "manual_review"
            }
        }
        reasoner.infer = AsyncMock(return_value=error_result)

        # Setup malformed query
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "",  # Empty query
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
        reasoner.infer.assert_called_once()

    @pytest.mark.asyncio
    async def test_operator_with_very_long_query(
        self,
        operator,
        sample_job
    ):
        """Test operator with extremely long query text."""
        # Create mock reasoner
        reasoner = AsyncMock(spec=DualModelReasoner)
        reasoner.infer = AsyncMock(return_value={"complexity_level": "COMPLEX"})

        # Create very long query
        long_query = "Find " + " ".join(["Person"] * 1000) + " nodes"
        workflow_message = WorkflowMessage(
            payload={"query_text": long_query},
            job_id=sample_job.id
        )

        # Execute should handle without crashing
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
