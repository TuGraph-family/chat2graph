"""
Integration Tests for ContextEnhancementOperator

测试上下文增强 Operator 的集成功能。

Author: kaichuan
Date: 2025-11-25
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Initialize server before importing app modules
from app.core.sdk.init_server import init_server
init_server()

from app.plugin.tugraph.operator.context_enhancement_operator import (
    ContextEnhancementOperator,
    create_context_enhancement_operator
)
from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage


@pytest.mark.integration
@pytest.mark.operator
class TestContextEnhancementOperatorIntegration:
    """Integration tests for ContextEnhancementOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_context_enhancement_operator()

    @pytest.fixture
    def mock_reasoner_with_context_result(self):
        """Create mock reasoner that returns context enhancement result."""
        reasoner = AsyncMock()

        # Mock context enhancement response
        context_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "user123",
                    "session_id": "session456",
                    "is_active": True,
                    "total_queries": 15,
                    "success_rate": 0.87
                },
                "relevant_history": [
                    {
                        "query_text": "Find all persons",
                        "query_cypher": "MATCH (p:Person) RETURN p",
                        "success": True,
                        "latency_ms": 50
                    },
                    {
                        "query_text": "Find persons working at companies",
                        "query_cypher": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p, c",
                        "success": True,
                        "latency_ms": 120
                    }
                ],
                "user_preferences": {
                    "preferred_complexity": "MODERATE",
                    "preferred_patterns": ["DIRECT", "MULTI_HOP"],
                    "preferred_vertex_types": ["Person", "Company"],
                    "acceptable_latency_ms": 200
                }
            },
            "preference_insights": {
                "complexity": {
                    "level": "MODERATE",
                    "confidence": 0.85
                },
                "patterns": {
                    "top_patterns": ["DIRECT", "MULTI_HOP"],
                    "confidence": 0.90
                },
                "performance": {
                    "threshold_ms": 200,
                    "confidence": 0.80
                },
                "data": {
                    "frequent_types": ["Person", "Company"],
                    "avg_result_size": 50,
                    "confidence": 0.88
                }
            },
            "query_suggestions": {
                "improvements": [
                    {
                        "suggestion": "Add index on Person.name for faster lookup",
                        "rationale": "Based on your frequent queries on Person.name",
                        "confidence": 0.92
                    }
                ],
                "alternatives": [
                    {
                        "query": "MATCH (p:Person {name: 'John'}) RETURN p",
                        "rationale": "More efficient than WHERE clause for exact match",
                        "confidence": 0.85
                    }
                ],
                "completions": [
                    {
                        "completion": "RETURN p.name, p.age ORDER BY p.age DESC LIMIT 10",
                        "rationale": "Common pattern from your history",
                        "confidence": 0.78
                    }
                ]
            },
            "enhancement_recommendations": {
                "apply_to_current_query": [
                    "Use parameterized queries for better performance",
                    "Consider adding LIMIT clause to prevent large result sets"
                ],
                "general_best_practices": [
                    "Use indexes on frequently queried properties",
                    "Keep query complexity moderate for better performance"
                ],
                "personalization_opportunities": [
                    "Create custom views for frequently accessed data patterns",
                    "Set up query templates for common operations"
                ]
            }
        }

        reasoner.infer = AsyncMock(return_value=context_result)
        return reasoner

    @pytest.mark.asyncio
    async def test_operator_initialization(self, operator):
        """Test operator is properly initialized with correct configuration."""
        assert operator is not None
        assert operator._config is not None
        assert operator._config.id == "context_enhancement_operator"
        assert operator._config.threshold == 0.6
        assert operator._config.hops == 1
        assert len(operator._config.actions) == 3

        # Verify actions
        action_names = [action.name for action in operator._config.actions]
        assert "retrieve_context" in action_names
        assert "learn_preferences" in action_names
        assert "suggest_queries" in action_names

    @pytest.mark.asyncio
    async def test_execute_context_retrieval(
        self,
        operator,
        mock_reasoner_with_context_result,
        sample_job
    ):
        """Test executing context retrieval for query enhancement."""
        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find person named John",
                "session_id": "session456"
            },
            job_id=sample_job.id
        )

        # Execute operator
        with patch("app.core.service.toolkit_service.ToolkitService") as mock_toolkit:
            mock_toolkit.instance.recommend_tools_actions = MagicMock(
                return_value=([], operator._config.actions)
            )

            result = await operator.execute(
                reasoner=mock_reasoner_with_context_result,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify result
        assert result is not None
        assert isinstance(result, WorkflowMessage)
        mock_reasoner_with_context_result.infer.assert_called_once()

        # Verify context retrieved
        result_data = mock_reasoner_with_context_result.infer.return_value
        assert "context_summary" in result_data
        assert result_data["context_summary"]["session_info"]["total_queries"] == 15
        assert len(result_data["context_summary"]["relevant_history"]) == 2

    @pytest.mark.asyncio
    async def test_execute_preference_learning(
        self,
        operator,
        sample_job
    ):
        """Test preference learning from query history."""
        # Create mock reasoner with preference learning result
        reasoner = AsyncMock()
        preference_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "user789",
                    "session_id": "session789",
                    "is_active": True,
                    "total_queries": 50,
                    "success_rate": 0.92
                },
                "relevant_history": [],
                "user_preferences": {
                    "preferred_complexity": "COMPLEX",
                    "preferred_patterns": ["MULTI_HOP", "SHORTEST_PATH"],
                    "preferred_vertex_types": ["Person", "Company", "Technology"],
                    "acceptable_latency_ms": 500
                }
            },
            "preference_insights": {
                "complexity": {
                    "level": "COMPLEX",
                    "confidence": 0.95
                },
                "patterns": {
                    "top_patterns": ["MULTI_HOP", "SHORTEST_PATH", "AGGREGATION"],
                    "confidence": 0.93
                },
                "performance": {
                    "threshold_ms": 500,
                    "confidence": 0.90
                },
                "data": {
                    "frequent_types": ["Person", "Company", "Technology"],
                    "avg_result_size": 200,
                    "confidence": 0.94
                }
            },
            "query_suggestions": {
                "improvements": [],
                "alternatives": [],
                "completions": []
            },
            "enhancement_recommendations": {
                "apply_to_current_query": [
                    "User prefers complex queries - consider multi-hop patterns",
                    "Average result size is 200 - no need for strict LIMIT"
                ],
                "general_best_practices": [
                    "Continue using complex patterns as user is comfortable with them",
                    "Acceptable latency is 500ms - optimize for correctness over speed"
                ],
                "personalization_opportunities": [
                    "Create stored procedures for common multi-hop patterns",
                    "Set up monitoring for queries exceeding 500ms threshold"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=preference_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find friends of friends who work at tech companies",
                "session_id": "session789",
                "learning_mode": "auto"
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

        # Verify preference learning
        result_data = reasoner.infer.return_value
        assert result_data["preference_insights"]["complexity"]["level"] == "COMPLEX"
        assert result_data["preference_insights"]["complexity"]["confidence"] >= 0.90
        assert "MULTI_HOP" in result_data["preference_insights"]["patterns"]["top_patterns"]

    @pytest.mark.asyncio
    async def test_execute_query_suggestions(
        self,
        operator,
        sample_job
    ):
        """Test generating query suggestions based on context."""
        # Create mock reasoner with query suggestions
        reasoner = AsyncMock()
        suggestion_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "user456",
                    "session_id": "session456",
                    "is_active": True,
                    "total_queries": 30,
                    "success_rate": 0.85
                },
                "relevant_history": [
                    {
                        "query_text": "Find people aged 25",
                        "query_cypher": "MATCH (p:Person) WHERE p.age = 25 RETURN p",
                        "success": True,
                        "latency_ms": 80
                    }
                ],
                "user_preferences": {
                    "preferred_complexity": "SIMPLE",
                    "preferred_patterns": ["DIRECT"],
                    "preferred_vertex_types": ["Person"],
                    "acceptable_latency_ms": 100
                }
            },
            "preference_insights": {
                "complexity": {"level": "SIMPLE", "confidence": 0.82},
                "patterns": {"top_patterns": ["DIRECT"], "confidence": 0.85},
                "performance": {"threshold_ms": 100, "confidence": 0.80},
                "data": {"frequent_types": ["Person"], "avg_result_size": 20, "confidence": 0.83}
            },
            "query_suggestions": {
                "improvements": [
                    {
                        "suggestion": "Add index on Person.age",
                        "rationale": "Frequent filtering on age property",
                        "confidence": 0.88
                    },
                    {
                        "suggestion": "Use LIMIT 100 to prevent large result sets",
                        "rationale": "Based on acceptable latency threshold",
                        "confidence": 0.75
                    }
                ],
                "alternatives": [
                    {
                        "query": "MATCH (p:Person {age: 25}) RETURN p",
                        "rationale": "More efficient for exact match",
                        "confidence": 0.90
                    }
                ],
                "completions": [
                    {
                        "completion": "RETURN p.name, p.age ORDER BY p.name",
                        "rationale": "Common pattern in your queries",
                        "confidence": 0.80
                    },
                    {
                        "completion": "RETURN count(p) as total",
                        "rationale": "You often count results",
                        "confidence": 0.70
                    }
                ]
            },
            "enhancement_recommendations": {
                "apply_to_current_query": [
                    "Use exact match syntax for better performance",
                    "Add ORDER BY for consistent results"
                ],
                "general_best_practices": [
                    "Keep queries simple as per your preference",
                    "Use indexes on age property"
                ],
                "personalization_opportunities": [
                    "Create query template for age-based searches",
                    "Set up quick filters for common age ranges"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=suggestion_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find people aged 30",
                "session_id": "session456",
                "suggestion_type": "all"
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

        # Verify suggestions generated
        result_data = reasoner.infer.return_value
        assert len(result_data["query_suggestions"]["improvements"]) >= 2
        assert len(result_data["query_suggestions"]["alternatives"]) >= 1
        assert len(result_data["query_suggestions"]["completions"]) >= 2

    @pytest.mark.asyncio
    async def test_execute_with_insufficient_history(
        self,
        operator,
        sample_job
    ):
        """Test handling when insufficient historical data is available."""
        # Create mock reasoner with insufficient history warning
        reasoner = AsyncMock()
        insufficient_history_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "new_user",
                    "session_id": "new_session",
                    "is_active": True,
                    "total_queries": 2,
                    "success_rate": 1.0
                },
                "relevant_history": [],
                "user_preferences": {
                    "preferred_complexity": "UNKNOWN",
                    "preferred_patterns": [],
                    "preferred_vertex_types": [],
                    "acceptable_latency_ms": 0
                }
            },
            "preference_insights": {
                "complexity": {"level": "UNKNOWN", "confidence": 0.0},
                "patterns": {"top_patterns": [], "confidence": 0.0},
                "performance": {"threshold_ms": 0, "confidence": 0.0},
                "data": {"frequent_types": [], "avg_result_size": 0, "confidence": 0.0}
            },
            "query_suggestions": {
                "improvements": [],
                "alternatives": [],
                "completions": []
            },
            "enhancement_recommendations": {
                "apply_to_current_query": [
                    "WARNING: Insufficient historical data for reliable recommendations",
                    "Continue using default best practices"
                ],
                "general_best_practices": [
                    "Use indexes on frequently queried properties",
                    "Add LIMIT clauses to prevent large result sets",
                    "Start with simple queries and increase complexity as needed"
                ],
                "personalization_opportunities": [
                    "Need at least 10 queries to learn preferences",
                    "Continue querying to build personalized recommendations"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=insufficient_history_result)

        # Setup workflow message for new user
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find all companies",
                "session_id": "new_session"
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

        # Verify warning about insufficient data
        result_data = reasoner.infer.return_value
        assert result_data["context_summary"]["session_info"]["total_queries"] < 10
        assert result_data["preference_insights"]["complexity"]["confidence"] == 0.0
        assert "WARNING" in result_data["enhancement_recommendations"]["apply_to_current_query"][0]

    @pytest.mark.asyncio
    async def test_execute_personalization_recommendations(
        self,
        operator,
        sample_job
    ):
        """Test generating personalized recommendations."""
        # Create mock reasoner with personalization focus
        reasoner = AsyncMock()
        personalization_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "power_user",
                    "session_id": "power_session",
                    "is_active": True,
                    "total_queries": 200,
                    "success_rate": 0.95
                },
                "relevant_history": [],
                "user_preferences": {
                    "preferred_complexity": "COMPLEX",
                    "preferred_patterns": ["MULTI_HOP", "AGGREGATION", "SHORTEST_PATH"],
                    "preferred_vertex_types": ["Person", "Company", "Technology", "Location"],
                    "acceptable_latency_ms": 1000
                }
            },
            "preference_insights": {
                "complexity": {"level": "COMPLEX", "confidence": 0.98},
                "patterns": {"top_patterns": ["MULTI_HOP", "AGGREGATION"], "confidence": 0.96},
                "performance": {"threshold_ms": 1000, "confidence": 0.95},
                "data": {"frequent_types": ["Person", "Company"], "avg_result_size": 500, "confidence": 0.97}
            },
            "query_suggestions": {
                "improvements": [],
                "alternatives": [],
                "completions": []
            },
            "enhancement_recommendations": {
                "apply_to_current_query": [
                    "User is experienced - can handle complex query patterns",
                    "No need to simplify or add warnings for advanced features"
                ],
                "general_best_practices": [
                    "Continue using advanced patterns as they match your expertise",
                    "Consider creating custom functions for repeated complex operations"
                ],
                "personalization_opportunities": [
                    "Create stored procedures for your top 10 query patterns",
                    "Set up dashboards for frequently analyzed data",
                    "Configure custom shortcuts for multi-hop traversals",
                    "Enable advanced query optimization features",
                    "Set up automated data refresh for your common views"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=personalization_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Complex analytical query",
                "session_id": "power_session"
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

        # Verify personalization recommendations
        result_data = reasoner.infer.return_value
        assert result_data["context_summary"]["session_info"]["total_queries"] >= 200
        assert result_data["preference_insights"]["complexity"]["confidence"] >= 0.95
        assert len(result_data["enhancement_recommendations"]["personalization_opportunities"]) >= 5

    @pytest.mark.asyncio
    async def test_operator_instruction_format(self, operator):
        """Test that operator instruction contains expected guidance."""
        instruction = operator._config.instruction

        # Verify key instruction elements
        assert "context-aware query enhancement specialist" in instruction
        assert "Available Tools:" in instruction
        assert "retrieve_context" in instruction
        assert "learn_preferences" in instruction
        assert "suggest_queries" in instruction
        assert "Output Format:" in instruction
        assert "context_summary" in instruction
        assert "preference_insights" in instruction
        assert "query_suggestions" in instruction

    @pytest.mark.asyncio
    async def test_operator_action_configuration(self, operator):
        """Test that operator actions are properly configured."""
        actions = operator._config.actions

        # Verify all actions present
        action_names = {a.name for a in actions}
        assert "retrieve_context" in action_names
        assert "learn_preferences" in action_names
        assert "suggest_queries" in action_names

        # Verify namespaces
        for action in actions:
            assert action.namespace == "tugraph.context_tools"

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates operator with custom ID."""
        custom_id = "custom_context_operator"
        operator = create_context_enhancement_operator(operator_id=custom_id)

        assert operator is not None
        assert operator._config.id == custom_id
        assert operator._config.threshold == 0.6


@pytest.mark.integration
@pytest.mark.operator
class TestContextEnhancementOperatorEdgeCases:
    """Edge case tests for ContextEnhancementOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_context_enhancement_operator()

    @pytest.mark.asyncio
    async def test_operator_with_no_session_id(
        self,
        operator,
        sample_job
    ):
        """Test operator handling when no session ID provided."""
        # Create mock reasoner with no session handling
        reasoner = AsyncMock()
        no_session_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "unknown",
                    "session_id": "unknown",
                    "is_active": False,
                    "total_queries": 0,
                    "success_rate": 0.0
                },
                "relevant_history": [],
                "user_preferences": {
                    "preferred_complexity": "UNKNOWN",
                    "preferred_patterns": [],
                    "preferred_vertex_types": [],
                    "acceptable_latency_ms": 0
                }
            },
            "preference_insights": {
                "complexity": {"level": "UNKNOWN", "confidence": 0.0},
                "patterns": {"top_patterns": [], "confidence": 0.0},
                "performance": {"threshold_ms": 0, "confidence": 0.0},
                "data": {"frequent_types": [], "avg_result_size": 0, "confidence": 0.0}
            },
            "query_suggestions": {
                "improvements": [],
                "alternatives": [],
                "completions": []
            },
            "enhancement_recommendations": {
                "apply_to_current_query": ["No session context available"],
                "general_best_practices": ["Use default query patterns"],
                "personalization_opportunities": ["Create a session to enable context learning"]
            }
        }
        reasoner.infer = AsyncMock(return_value=no_session_result)

        # Setup workflow message without session ID
        workflow_message = WorkflowMessage(
            payload={"query_text": "Find all persons"},
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
        assert result_data["context_summary"]["session_info"]["session_id"] == "unknown"

    @pytest.mark.asyncio
    async def test_operator_with_conflicting_preferences(
        self,
        operator,
        sample_job
    ):
        """Test operator with conflicting user preference signals."""
        # Create mock reasoner with conflicting preferences
        reasoner = AsyncMock()
        conflicting_result = {
            "context_summary": {
                "session_info": {
                    "user_id": "user999",
                    "session_id": "session999",
                    "is_active": True,
                    "total_queries": 25,
                    "success_rate": 0.70
                },
                "relevant_history": [],
                "user_preferences": {
                    "preferred_complexity": "SIMPLE",
                    "preferred_patterns": ["DIRECT"],
                    "preferred_vertex_types": ["Person"],
                    "acceptable_latency_ms": 50
                }
            },
            "preference_insights": {
                "complexity": {
                    "level": "CONFLICTING",
                    "confidence": 0.40,
                    "note": "User requests simple queries but accepts complex results"
                },
                "patterns": {"top_patterns": ["DIRECT", "MULTI_HOP"], "confidence": 0.55},
                "performance": {"threshold_ms": 50, "confidence": 0.45},
                "data": {"frequent_types": ["Person"], "avg_result_size": 100, "confidence": 0.60}
            },
            "query_suggestions": {
                "improvements": [
                    {
                        "suggestion": "Clarify complexity preferences",
                        "rationale": "Your queries show mixed complexity patterns",
                        "confidence": 0.50
                    }
                ],
                "alternatives": [],
                "completions": []
            },
            "enhancement_recommendations": {
                "apply_to_current_query": [
                    "WARNING: Conflicting preference signals detected",
                    "Defaulting to simple query structure",
                    "Consider reviewing query history to establish clear patterns"
                ],
                "general_best_practices": [
                    "Use consistent query patterns for better learning",
                    "Provide feedback on query results to improve recommendations"
                ],
                "personalization_opportunities": [
                    "Need more consistent data to build reliable profile",
                    "Consider explicit preference configuration"
                ]
            }
        }
        reasoner.infer = AsyncMock(return_value=conflicting_result)

        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find data",
                "session_id": "session999"
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

        # Verify conflicting preferences handled
        result_data = reasoner.infer.return_value
        assert result_data["preference_insights"]["complexity"]["confidence"] < 0.70
        assert "WARNING" in result_data["enhancement_recommendations"]["apply_to_current_query"][0]
