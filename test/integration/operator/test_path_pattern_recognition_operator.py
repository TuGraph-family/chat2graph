"""
Integration Tests for PathPatternRecognitionOperator

测试路径模式识别 Operator 的集成功能。

Author: kaichuan
Date: 2025-11-25
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Initialize server before importing app modules
from app.core.sdk.init_server import init_server
init_server()

from app.plugin.tugraph.operator.path_pattern_recognition_operator import (
    PathPatternRecognitionOperator,
    create_path_pattern_recognition_operator
)
from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage


@pytest.mark.integration
@pytest.mark.operator
class TestPathPatternRecognitionOperatorIntegration:
    """Integration tests for PathPatternRecognitionOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_path_pattern_recognition_operator()

    @pytest.fixture
    def mock_reasoner_with_pattern_result(self):
        """Create mock reasoner that returns path pattern recognition result."""
        reasoner = AsyncMock()

        # Mock path pattern recognition response
        pattern_result = {
            "path_analysis": {
                "has_multi_hop": True,
                "patterns": [
                    {
                        "pattern_type": "MULTI_HOP",
                        "source_entity": "Person",
                        "target_entity": "Person",
                        "relationship_types": ["KNOWS"],
                        "min_depth": 2,
                        "max_depth": 2,
                        "bidirectional": False,
                        "temporal_constraints": None,
                        "spatial_constraints": None
                    }
                ]
            },
            "temporal_conditions": None,
            "spatial_conditions": None,
            "combined_cypher_hints": {
                "path_pattern_cypher": "MATCH (p1:Person)-[:KNOWS*2]->(p2:Person)",
                "where_conditions": [],
                "recommended_functions": []
            }
        }

        reasoner.infer = AsyncMock(return_value=pattern_result)
        return reasoner

    @pytest.mark.asyncio
    async def test_operator_initialization(self, operator):
        """Test operator is properly initialized with correct configuration."""
        assert operator is not None
        assert operator._config is not None
        assert operator._config.id == "path_pattern_recognition_operator"
        assert operator._config.threshold == 0.7
        assert operator._config.hops == 1
        assert len(operator._config.actions) == 3

        # Verify actions
        action_names = [action.name for action in operator._config.actions]
        assert "recognize_patterns" in action_names
        assert "build_temporal_query" in action_names
        assert "build_spatial_query" in action_names

    @pytest.mark.asyncio
    async def test_execute_multi_hop_pattern_recognition(
        self,
        operator,
        mock_reasoner_with_pattern_result,
        sample_job
    ):
        """Test executing pattern recognition for multi-hop query."""
        # Setup workflow message with multi-hop query
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find friends of friends of John",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "relationship_patterns": ["KNOWS"]
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
                reasoner=mock_reasoner_with_pattern_result,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify result
        assert result is not None
        assert isinstance(result, WorkflowMessage)
        mock_reasoner_with_pattern_result.infer.assert_called_once()

        # Verify result contains pattern analysis
        result_data = mock_reasoner_with_pattern_result.infer.return_value
        assert "path_analysis" in result_data
        assert result_data["path_analysis"]["has_multi_hop"] is True
        assert len(result_data["path_analysis"]["patterns"]) == 1

    @pytest.mark.asyncio
    async def test_execute_temporal_pattern_recognition(
        self,
        operator,
        sample_job
    ):
        """Test executing pattern recognition with temporal constraints."""
        # Create mock reasoner with temporal result
        reasoner = AsyncMock()
        temporal_result = {
            "path_analysis": {
                "has_multi_hop": False,
                "patterns": [
                    {
                        "pattern_type": "DIRECT",
                        "source_entity": "Person",
                        "target_entity": "Company",
                        "relationship_types": ["WORKS_AT"],
                        "min_depth": 1,
                        "max_depth": 1,
                        "bidirectional": False,
                        "temporal_constraints": {
                            "property": "since",
                            "operator": ">",
                            "value": 1640995200  # 2022-01-01
                        },
                        "spatial_constraints": None
                    }
                ]
            },
            "temporal_conditions": {
                "cypher_condition": "r.since > 1640995200",
                "cypher_function": "timestamp()",
                "start_timestamp": 1640995200,
                "end_timestamp": None,
                "explanation": "Filter relationships started after 2022-01-01"
            },
            "spatial_conditions": None,
            "combined_cypher_hints": {
                "path_pattern_cypher": "MATCH (p:Person)-[r:WORKS_AT]->(c:Company)",
                "where_conditions": ["r.since > 1640995200"],
                "recommended_functions": ["timestamp()"]
            }
        }
        reasoner.infer = AsyncMock(return_value=temporal_result)

        # Setup workflow message with temporal query
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find people who joined companies after 2022",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "has_temporal": True
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

        # Verify temporal conditions are present
        result_data = reasoner.infer.return_value
        assert result_data["temporal_conditions"] is not None
        assert "cypher_condition" in result_data["temporal_conditions"]
        assert "since > 1640995200" in result_data["temporal_conditions"]["cypher_condition"]

    @pytest.mark.asyncio
    async def test_execute_shortest_path_pattern(
        self,
        operator,
        sample_job
    ):
        """Test executing pattern recognition for shortest path query."""
        # Create mock reasoner with shortest path result
        reasoner = AsyncMock()
        shortest_path_result = {
            "path_analysis": {
                "has_multi_hop": True,
                "patterns": [
                    {
                        "pattern_type": "SHORTEST_PATH",
                        "source_entity": "Person",
                        "target_entity": "Person",
                        "relationship_types": ["KNOWS", "WORKS_AT"],
                        "min_depth": 1,
                        "max_depth": 5,
                        "bidirectional": True,
                        "temporal_constraints": None,
                        "spatial_constraints": None
                    }
                ]
            },
            "temporal_conditions": None,
            "spatial_conditions": None,
            "combined_cypher_hints": {
                "path_pattern_cypher": "MATCH path = shortestPath((p1:Person)-[*1..5]-(p2:Person))",
                "where_conditions": [],
                "recommended_functions": ["shortestPath()"]
            }
        }
        reasoner.infer = AsyncMock(return_value=shortest_path_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find the shortest path between Alice and Bob"
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

        # Verify shortest path pattern
        result_data = reasoner.infer.return_value
        patterns = result_data["path_analysis"]["patterns"]
        assert patterns[0]["pattern_type"] == "SHORTEST_PATH"
        assert patterns[0]["bidirectional"] is True
        assert "shortestPath()" in result_data["combined_cypher_hints"]["recommended_functions"]

    @pytest.mark.asyncio
    async def test_execute_variable_length_pattern(
        self,
        operator,
        sample_job
    ):
        """Test executing pattern recognition for variable-length path."""
        # Create mock reasoner with variable length result
        reasoner = AsyncMock()
        var_length_result = {
            "path_analysis": {
                "has_multi_hop": True,
                "patterns": [
                    {
                        "pattern_type": "VARIABLE_LENGTH",
                        "source_entity": "Person",
                        "target_entity": "Company",
                        "relationship_types": ["KNOWS", "WORKS_AT"],
                        "min_depth": 1,
                        "max_depth": 3,
                        "bidirectional": False,
                        "temporal_constraints": None,
                        "spatial_constraints": None
                    }
                ]
            },
            "temporal_conditions": None,
            "spatial_conditions": None,
            "combined_cypher_hints": {
                "path_pattern_cypher": "MATCH (p:Person)-[:KNOWS|WORKS_AT*1..3]->(c:Company)",
                "where_conditions": [],
                "recommended_functions": []
            }
        }
        reasoner.infer = AsyncMock(return_value=var_length_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find companies connected to John within 3 steps"
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

        # Verify variable length pattern
        result_data = reasoner.infer.return_value
        patterns = result_data["path_analysis"]["patterns"]
        assert patterns[0]["pattern_type"] == "VARIABLE_LENGTH"
        assert patterns[0]["min_depth"] == 1
        assert patterns[0]["max_depth"] == 3

    @pytest.mark.asyncio
    async def test_operator_instruction_format(self, operator):
        """Test that operator instruction contains expected guidance."""
        instruction = operator._config.instruction

        # Verify key instruction elements
        assert "path pattern recognition specialist" in instruction
        assert "Available Tools:" in instruction
        assert "recognize_patterns" in instruction
        assert "build_temporal_query" in instruction
        assert "build_spatial_query" in instruction
        assert "Output Format:" in instruction
        assert "path_analysis" in instruction

    @pytest.mark.asyncio
    async def test_operator_action_configuration(self, operator):
        """Test that operator actions are properly configured."""
        actions = operator._config.actions

        # Verify all actions present
        action_names = {a.name for a in actions}
        assert "recognize_patterns" in action_names
        assert "build_temporal_query" in action_names
        assert "build_spatial_query" in action_names

        # Verify namespaces
        for action in actions:
            assert action.namespace == "tugraph.multi_hop_reasoning"

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates operator with custom ID."""
        custom_id = "custom_pattern_operator"
        operator = create_path_pattern_recognition_operator(operator_id=custom_id)

        assert operator is not None
        assert operator._config.id == custom_id


@pytest.mark.integration
@pytest.mark.operator
class TestPathPatternRecognitionOperatorEdgeCases:
    """Edge case tests for PathPatternRecognitionOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_path_pattern_recognition_operator()

    @pytest.mark.asyncio
    async def test_operator_with_no_patterns(
        self,
        operator,
        sample_job
    ):
        """Test operator handling when no patterns are recognized."""
        # Create mock reasoner with no patterns
        reasoner = AsyncMock()
        no_pattern_result = {
            "path_analysis": {
                "has_multi_hop": False,
                "patterns": []
            },
            "temporal_conditions": None,
            "spatial_conditions": None,
            "combined_cypher_hints": {
                "path_pattern_cypher": None,
                "where_conditions": [],
                "recommended_functions": []
            }
        }
        reasoner.infer = AsyncMock(return_value=no_pattern_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={"query_text": "Invalid query with no clear pattern"},
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
        assert len(result_data["path_analysis"]["patterns"]) == 0

    @pytest.mark.asyncio
    async def test_operator_with_complex_multi_pattern(
        self,
        operator,
        sample_job
    ):
        """Test operator with multiple different path patterns."""
        # Create mock reasoner with multiple patterns
        reasoner = AsyncMock()
        multi_pattern_result = {
            "path_analysis": {
                "has_multi_hop": True,
                "patterns": [
                    {
                        "pattern_type": "DIRECT",
                        "source_entity": "Person",
                        "target_entity": "Company",
                        "relationship_types": ["WORKS_AT"],
                        "min_depth": 1,
                        "max_depth": 1
                    },
                    {
                        "pattern_type": "MULTI_HOP",
                        "source_entity": "Company",
                        "target_entity": "Technology",
                        "relationship_types": ["USES"],
                        "min_depth": 1,
                        "max_depth": 2
                    }
                ]
            },
            "temporal_conditions": None,
            "spatial_conditions": None,
            "combined_cypher_hints": {
                "path_pattern_cypher": "MATCH (p:Person)-[:WORKS_AT]->(c:Company)-[:USES*1..2]->(t:Technology)",
                "where_conditions": [],
                "recommended_functions": []
            }
        }
        reasoner.infer = AsyncMock(return_value=multi_pattern_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find technologies used by companies where people work"
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

        # Verify multiple patterns handled
        result_data = reasoner.infer.return_value
        assert len(result_data["path_analysis"]["patterns"]) == 2
