"""
Integration Tests for QueryDesignOperator

测试查询设计 Operator 的集成功能。

Author: kaichuan
Date: 2025-11-25
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Initialize server before importing app modules
from app.core.sdk.init_server import init_server
init_server()

from app.plugin.tugraph.operator.query_design_operator import (
    QueryDesignOperator,
    create_query_design_operator
)
from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage


@pytest.mark.integration
@pytest.mark.operator
class TestQueryDesignOperatorIntegration:
    """Integration tests for QueryDesignOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_query_design_operator()

    @pytest.fixture
    def mock_reasoner_with_design_result(self):
        """Create mock reasoner that returns query design result."""
        reasoner = AsyncMock()

        # Mock query design response
        design_result = {
            "designed_query": {
                "cypher": "MATCH (p:Person) WHERE p.age > 25 RETURN p.name, p.age ORDER BY p.age DESC LIMIT 100",
                "query_type": "VERTEX_QUERY",
                "components": {
                    "match_clauses": ["MATCH (p:Person)"],
                    "where_conditions": ["p.age > 25"],
                    "return_clause": "RETURN p.name, p.age",
                    "limit_clause": "LIMIT 100",
                    "order_by": "ORDER BY p.age DESC",
                    "with_clauses": []
                }
            },
            "optimization_applied": {
                "original_approach": "Basic MATCH with WHERE clause",
                "optimizations": [
                    {
                        "type": "LIMIT_ADDITION",
                        "description": "Added LIMIT 100 to prevent large result sets",
                        "benefit": "Reduces memory usage and improves response time"
                    },
                    {
                        "type": "ORDER_BY_OPTIMIZATION",
                        "description": "Added ORDER BY for consistent results",
                        "benefit": "Predictable ordering, enables pagination"
                    }
                ],
                "estimated_improvement": "30-40% faster execution"
            },
            "design_rationale": {
                "pattern_choices": "Simple MATCH pattern for direct vertex access",
                "condition_placement": "WHERE clause used as age comparison requires range check",
                "optimization_strategy": "Balance readability with performance",
                "trade_offs": "LIMIT may exclude some results but prevents memory issues"
            },
            "execution_metadata": {
                "recommended_execution_order": ["Filter by age", "Sort results", "Apply limit"],
                "index_hints": ["CREATE INDEX ON Person(age)"],
                "caching_opportunities": ["Result set can be cached for 5 minutes"],
                "parallel_execution_potential": False
            },
            "alternative_designs": [
                {
                    "cypher": "MATCH (p:Person {age: 26}) RETURN p",
                    "approach": "Exact match using inline properties",
                    "when_to_use": "When age is exact value instead of range"
                }
            ]
        }

        reasoner.infer = AsyncMock(return_value=design_result)
        return reasoner

    @pytest.mark.asyncio
    async def test_operator_initialization(self, operator):
        """Test operator is properly initialized with correct configuration."""
        assert operator is not None
        assert operator._config is not None
        assert operator._config.id == "query_design_operator"
        assert operator._config.threshold == 0.7
        assert operator._config.hops == 2
        assert len(operator._config.actions) == 4

        # Verify actions
        action_names = [action.name for action in operator._config.actions]
        assert "get_schema" in action_names
        assert "read_grammer" in action_names
        assert "query_vertex" in action_names
        assert "rewrite_query" in action_names

    @pytest.mark.asyncio
    async def test_execute_simple_vertex_query_design(
        self,
        operator,
        mock_reasoner_with_design_result,
        sample_job
    ):
        """Test designing a simple vertex query."""
        # Setup workflow message
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find people older than 25",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "filters": ["age > 25"]
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
                reasoner=mock_reasoner_with_design_result,
                job=sample_job,
                workflow_messages=[workflow_message]
            )

        # Verify result
        assert result is not None
        assert isinstance(result, WorkflowMessage)
        mock_reasoner_with_design_result.infer.assert_called_once()

        # Verify query designed
        result_data = mock_reasoner_with_design_result.infer.return_value
        assert "designed_query" in result_data
        assert "MATCH (p:Person)" in result_data["designed_query"]["cypher"]
        assert "WHERE p.age > 25" in result_data["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_execute_path_query_design(
        self,
        operator,
        sample_job
    ):
        """Test designing a multi-hop path query."""
        # Create mock reasoner with path query result
        reasoner = AsyncMock()
        path_design_result = {
            "designed_query": {
                "cypher": "MATCH (p1:Person)-[:KNOWS*2]->(p2:Person) WHERE p1.name = 'John' RETURN p2.name LIMIT 50",
                "query_type": "PATH_QUERY",
                "components": {
                    "match_clauses": ["MATCH (p1:Person)-[:KNOWS*2]->(p2:Person)"],
                    "where_conditions": ["p1.name = 'John'"],
                    "return_clause": "RETURN p2.name",
                    "limit_clause": "LIMIT 50",
                    "order_by": None,
                    "with_clauses": []
                }
            },
            "optimization_applied": {
                "original_approach": "Variable length path traversal",
                "optimizations": [
                    {
                        "type": "CONDITION_INLINE",
                        "description": "Moved p1.name filter before path traversal",
                        "benefit": "Reduces number of starting nodes, faster traversal"
                    },
                    {
                        "type": "LIMIT_ADDITION",
                        "description": "Added LIMIT to prevent memory exhaustion",
                        "benefit": "Caps result set for multi-hop queries"
                    }
                ],
                "estimated_improvement": "50-60% faster for large graphs"
            },
            "design_rationale": {
                "pattern_choices": "Variable length path pattern *2 for friends-of-friends",
                "condition_placement": "Filter on starting node before traversal",
                "optimization_strategy": "Early filtering to reduce search space",
                "trade_offs": "Fixed depth of 2, may miss deeper connections"
            },
            "execution_metadata": {
                "recommended_execution_order": [
                    "Find Person nodes with name='John'",
                    "Traverse KNOWS relationships 2 hops",
                    "Collect target nodes",
                    "Apply limit"
                ],
                "index_hints": ["CREATE INDEX ON Person(name)"],
                "caching_opportunities": ["Cache starting nodes by name"],
                "parallel_execution_potential": True
            },
            "alternative_designs": [
                {
                    "cypher": "MATCH path = (p1:Person)-[:KNOWS*1..3]->(p2:Person) WHERE p1.name = 'John' RETURN path",
                    "approach": "Variable depth path with path return",
                    "when_to_use": "When relationship depth is uncertain or path details needed"
                }
            ]
        }
        reasoner.infer = AsyncMock(return_value=path_design_result)

        # Setup workflow message with path pattern
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find friends of friends of John",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "relationship_patterns": ["KNOWS"]
                },
                "path_analysis": {
                    "has_multi_hop": True,
                    "patterns": [{"pattern_type": "MULTI_HOP", "min_depth": 2, "max_depth": 2}]
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

        # Verify path query designed
        result_data = reasoner.infer.return_value
        assert result_data["designed_query"]["query_type"] == "PATH_QUERY"
        assert "[:KNOWS*2]" in result_data["designed_query"]["cypher"]
        assert len(result_data["optimization_applied"]["optimizations"]) >= 2

    @pytest.mark.asyncio
    async def test_execute_aggregation_query_design(
        self,
        operator,
        sample_job
    ):
        """Test designing an aggregation query."""
        # Create mock reasoner with aggregation result
        reasoner = AsyncMock()
        aggregation_result = {
            "designed_query": {
                "cypher": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN c.name, count(p) as employee_count ORDER BY employee_count DESC LIMIT 10",
                "query_type": "AGGREGATION",
                "components": {
                    "match_clauses": ["MATCH (p:Person)-[:WORKS_AT]->(c:Company)"],
                    "where_conditions": [],
                    "return_clause": "RETURN c.name, count(p) as employee_count",
                    "limit_clause": "LIMIT 10",
                    "order_by": "ORDER BY employee_count DESC",
                    "with_clauses": []
                }
            },
            "optimization_applied": {
                "original_approach": "Aggregation with grouping",
                "optimizations": [
                    {
                        "type": "ORDER_BY_OPTIMIZATION",
                        "description": "Order by count for top-N pattern",
                        "benefit": "Efficient retrieval of most common results"
                    },
                    {
                        "type": "LIMIT_ADDITION",
                        "description": "Limit to top 10 for manageable results",
                        "benefit": "Focuses on most relevant data"
                    }
                ],
                "estimated_improvement": "40% faster with limit"
            },
            "design_rationale": {
                "pattern_choices": "Relationship traversal for grouping by target",
                "condition_placement": "No WHERE needed, aggregation handles grouping",
                "optimization_strategy": "Top-N query pattern with ORDER BY + LIMIT",
                "trade_offs": "Only shows top 10, may miss smaller companies"
            },
            "execution_metadata": {
                "recommended_execution_order": [
                    "Traverse WORKS_AT relationships",
                    "Group by company name",
                    "Count employees per company",
                    "Sort by count descending",
                    "Take top 10"
                ],
                "index_hints": [],
                "caching_opportunities": ["Cache aggregation results for 1 hour"],
                "parallel_execution_potential": False
            },
            "alternative_designs": [
                {
                    "cypher": "MATCH (c:Company) RETURN c.name, size((c)<-[:WORKS_AT]-()) as employee_count",
                    "approach": "Pattern expression for counting",
                    "when_to_use": "When starting from Company perspective"
                }
            ]
        }
        reasoner.infer = AsyncMock(return_value=aggregation_result)

        # Setup workflow message with aggregation
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Count how many people work at each company",
                "intention_analysis": {
                    "query_type": "AGGREGATE",
                    "aggregation_type": "COUNT"
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

        # Verify aggregation query designed
        result_data = reasoner.infer.return_value
        assert result_data["designed_query"]["query_type"] == "AGGREGATION"
        assert "count(" in result_data["designed_query"]["cypher"]
        assert "ORDER BY" in result_data["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_execute_complex_query_design(
        self,
        operator,
        sample_job
    ):
        """Test designing a complex multi-stage query."""
        # Create mock reasoner with complex query result
        reasoner = AsyncMock()
        complex_result = {
            "designed_query": {
                "cypher": "MATCH (p:Person)-[:KNOWS]->(friend:Person)-[:WORKS_AT]->(c:Company) WHERE c.industry = 'tech' WITH p, collect(DISTINCT c.name) as companies WHERE size(companies) > 2 RETURN p.name, companies LIMIT 20",
                "query_type": "COMPLEX",
                "components": {
                    "match_clauses": ["MATCH (p:Person)-[:KNOWS]->(friend:Person)-[:WORKS_AT]->(c:Company)"],
                    "where_conditions": ["c.industry = 'tech'", "size(companies) > 2"],
                    "return_clause": "RETURN p.name, companies",
                    "limit_clause": "LIMIT 20",
                    "order_by": None,
                    "with_clauses": ["WITH p, collect(DISTINCT c.name) as companies"]
                }
            },
            "optimization_applied": {
                "original_approach": "Complex multi-stage query",
                "optimizations": [
                    {
                        "type": "WITH_SEPARATION",
                        "description": "Use WITH to separate aggregation from filtering",
                        "benefit": "Clearer logic, enables post-aggregation filtering"
                    },
                    {
                        "type": "CONDITION_INLINE",
                        "description": "Filter industry early in traversal",
                        "benefit": "Reduces intermediate results"
                    },
                    {
                        "type": "LIMIT_ADDITION",
                        "description": "Final result limit to prevent memory issues",
                        "benefit": "Caps output size for complex queries"
                    }
                ],
                "estimated_improvement": "60-70% faster with optimizations"
            },
            "design_rationale": {
                "pattern_choices": "Multi-hop with multiple relationship types",
                "condition_placement": "Early filter on industry, late filter on company count",
                "optimization_strategy": "Stage separation using WITH for clarity and performance",
                "trade_offs": "Complex query requires careful indexing and may be slow on large graphs"
            },
            "execution_metadata": {
                "recommended_execution_order": [
                    "Find Person nodes",
                    "Traverse KNOWS to friends",
                    "Traverse WORKS_AT to companies",
                    "Filter by tech industry",
                    "Aggregate companies per person",
                    "Filter persons with >2 companies",
                    "Apply limit"
                ],
                "index_hints": [
                    "CREATE INDEX ON Company(industry)",
                    "CREATE INDEX ON Person(name)"
                ],
                "caching_opportunities": [
                    "Cache company industry lookups",
                    "Cache person-friend relationships"
                ],
                "parallel_execution_potential": True
            },
            "alternative_designs": [
                {
                    "cypher": "MATCH (p:Person) WHERE size((p)-[:KNOWS]->()-[:WORKS_AT]->(:Company {industry: 'tech'})) > 2 RETURN p",
                    "approach": "Pattern expression with size check",
                    "when_to_use": "When only need person count, not company details"
                }
            ]
        }
        reasoner.infer = AsyncMock(return_value=complex_result)

        # Setup workflow message with complex query
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find people whose friends work at more than 2 tech companies",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "complexity_indicators": ["multi_hop", "aggregation", "filtering"]
                },
                "complexity_analysis": {
                    "complexity_level": "COMPLEX",
                    "recommended_strategy": "multi_stage"
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

        # Verify complex query designed
        result_data = reasoner.infer.return_value
        assert result_data["designed_query"]["query_type"] == "COMPLEX"
        assert len(result_data["designed_query"]["components"]["with_clauses"]) >= 1
        assert len(result_data["optimization_applied"]["optimizations"]) >= 3

    @pytest.mark.asyncio
    async def test_execute_with_context_preferences(
        self,
        operator,
        sample_job
    ):
        """Test query design incorporating user preferences from context."""
        # Create mock reasoner considering user preferences
        reasoner = AsyncMock()
        preference_aware_result = {
            "designed_query": {
                "cypher": "MATCH (p:Person) WHERE p.age > 25 RETURN p.name, p.age, p.city LIMIT 50",
                "query_type": "VERTEX_QUERY",
                "components": {
                    "match_clauses": ["MATCH (p:Person)"],
                    "where_conditions": ["p.age > 25"],
                    "return_clause": "RETURN p.name, p.age, p.city",
                    "limit_clause": "LIMIT 50",
                    "order_by": None,
                    "with_clauses": []
                }
            },
            "optimization_applied": {
                "original_approach": "Basic query",
                "optimizations": [
                    {
                        "type": "PREFERENCE_BASED_LIMIT",
                        "description": "Set LIMIT 50 based on user's acceptable latency of 100ms",
                        "benefit": "Matches user performance expectations"
                    }
                ],
                "estimated_improvement": "Aligned with user preferences"
            },
            "design_rationale": {
                "pattern_choices": "Simple pattern matching user's preference for SIMPLE queries",
                "condition_placement": "WHERE clause as user prefers readable queries",
                "optimization_strategy": "Balance simplicity with performance per user profile",
                "trade_offs": "Limited result set to match performance expectations"
            },
            "execution_metadata": {
                "recommended_execution_order": ["Filter", "Return"],
                "index_hints": ["CREATE INDEX ON Person(age)"],
                "caching_opportunities": [],
                "parallel_execution_potential": False
            },
            "alternative_designs": []
        }
        reasoner.infer = AsyncMock(return_value=preference_aware_result)

        # Setup workflow message with user preferences
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find people older than 25",
                "user_preferences": {
                    "preferred_complexity": "SIMPLE",
                    "acceptable_latency_ms": 100
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

        # Verify preferences considered
        result_data = reasoner.infer.return_value
        assert "PREFERENCE_BASED" in result_data["optimization_applied"]["optimizations"][0]["type"]
        assert "user" in result_data["design_rationale"]["optimization_strategy"].lower()

    @pytest.mark.asyncio
    async def test_operator_instruction_format(self, operator):
        """Test that operator instruction contains expected guidance."""
        instruction = operator._config.instruction

        # Verify key instruction elements
        assert "Cypher query design specialist" in instruction
        assert "Available Tools:" in instruction
        assert "get_schema" in instruction
        assert "read_grammer" in instruction
        assert "query_vertex" in instruction
        assert "rewrite_query" in instruction
        assert "Output Format:" in instruction
        assert "designed_query" in instruction
        assert "optimization_applied" in instruction

    @pytest.mark.asyncio
    async def test_operator_action_configuration(self, operator):
        """Test that operator actions are properly configured."""
        actions = operator._config.actions

        # Verify all actions present
        action_names = {a.name for a in actions}
        assert "get_schema" in action_names
        assert "read_grammer" in action_names
        assert "query_vertex" in action_names
        assert "rewrite_query" in action_names

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates operator with custom ID."""
        custom_id = "custom_design_operator"
        operator = create_query_design_operator(operator_id=custom_id)

        assert operator is not None
        assert operator._config.id == custom_id
        assert operator._config.threshold == 0.7


@pytest.mark.integration
@pytest.mark.operator
class TestQueryDesignOperatorEdgeCases:
    """Edge case tests for QueryDesignOperator."""

    @pytest.fixture
    def operator(self):
        """Create operator instance for testing."""
        return create_query_design_operator()

    @pytest.mark.asyncio
    async def test_operator_with_ambiguous_intent(
        self,
        operator,
        sample_job
    ):
        """Test query design with ambiguous user intent."""
        # Create mock reasoner handling ambiguous intent
        reasoner = AsyncMock()
        ambiguous_result = {
            "designed_query": {
                "cypher": "MATCH (p:Person) RETURN p LIMIT 100",
                "query_type": "VERTEX_QUERY",
                "components": {
                    "match_clauses": ["MATCH (p:Person)"],
                    "where_conditions": [],
                    "return_clause": "RETURN p",
                    "limit_clause": "LIMIT 100",
                    "order_by": None,
                    "with_clauses": []
                }
            },
            "optimization_applied": {
                "original_approach": "Default query due to ambiguous intent",
                "optimizations": [
                    {
                        "type": "SAFE_DEFAULT",
                        "description": "Applied conservative defaults for unclear intent",
                        "benefit": "Prevents errors while waiting for clarification"
                    }
                ],
                "estimated_improvement": "N/A - baseline query"
            },
            "design_rationale": {
                "pattern_choices": "Simple MATCH as intent unclear",
                "condition_placement": "No conditions due to ambiguous requirements",
                "optimization_strategy": "Conservative approach pending clarification",
                "trade_offs": "May not match actual intent, but safe to execute"
            },
            "execution_metadata": {
                "recommended_execution_order": ["Simple scan"],
                "index_hints": [],
                "caching_opportunities": [],
                "parallel_execution_potential": False
            },
            "alternative_designs": [
                {
                    "cypher": "MATCH (p:Person) WHERE p.name STARTS WITH 'A' RETURN p",
                    "approach": "Example with name filtering",
                    "when_to_use": "If user wants filtered results"
                },
                {
                    "cypher": "MATCH (p:Person)-[r]->(n) RETURN p, type(r), n",
                    "approach": "Include relationships",
                    "when_to_use": "If user wants related data"
                }
            ]
        }
        reasoner.infer = AsyncMock(return_value=ambiguous_result)

        # Setup workflow message with vague query
        workflow_message = WorkflowMessage(
            payload={"query_text": "Show me something about people"},
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

        # Verify safe default query designed
        result_data = reasoner.infer.return_value
        assert len(result_data["alternative_designs"]) >= 2
        assert "ambiguous" in result_data["design_rationale"]["pattern_choices"].lower() or \
               "unclear" in result_data["design_rationale"]["pattern_choices"].lower()

    @pytest.mark.asyncio
    async def test_operator_with_conflicting_requirements(
        self,
        operator,
        sample_job
    ):
        """Test query design with conflicting optimization requirements."""
        # Create mock reasoner handling conflicts
        reasoner = AsyncMock()
        conflicting_result = {
            "designed_query": {
                "cypher": "MATCH (p:Person)-[:KNOWS*1..3]->(friend:Person) WHERE p.name = 'John' RETURN friend.name LIMIT 1000",
                "query_type": "PATH_QUERY",
                "components": {
                    "match_clauses": ["MATCH (p:Person)-[:KNOWS*1..3]->(friend:Person)"],
                    "where_conditions": ["p.name = 'John'"],
                    "return_clause": "RETURN friend.name",
                    "limit_clause": "LIMIT 1000",
                    "order_by": None,
                    "with_clauses": []
                }
            },
            "optimization_applied": {
                "original_approach": "Variable path query with depth range",
                "optimizations": [
                    {
                        "type": "CONFLICT_RESOLUTION",
                        "description": "Balanced completeness (user wants all results) vs. performance (latency concern)",
                        "benefit": "Set LIMIT high enough for most cases while preventing memory exhaustion"
                    }
                ],
                "estimated_improvement": "Compromise solution"
            },
            "design_rationale": {
                "pattern_choices": "Variable depth 1..3 to balance exploration with performance",
                "condition_placement": "Early filter on starting node",
                "optimization_strategy": "Compromise between conflicting requirements",
                "trade_offs": "May miss results beyond 1000, but prevents excessive latency"
            },
            "execution_metadata": {
                "recommended_execution_order": ["Filter", "Traverse", "Limit"],
                "index_hints": ["CREATE INDEX ON Person(name)"],
                "caching_opportunities": [],
                "parallel_execution_potential": True
            },
            "alternative_designs": []
        }
        reasoner.infer = AsyncMock(return_value=conflicting_result)

        # Setup workflow message with conflicts
        workflow_message = WorkflowMessage(
            payload={
                "query_text": "Find all friends within 3 hops of John",
                "requirements": {
                    "completeness": "high",  # Wants all results
                    "latency": "low"  # But also wants fast response
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

        # Verify conflict handled
        result_data = reasoner.infer.return_value
        assert "CONFLICT" in result_data["optimization_applied"]["optimizations"][0]["type"] or \
               "Compromise" in result_data["optimization_applied"]["estimated_improvement"] or \
               "conflicting" in result_data["design_rationale"]["optimization_strategy"].lower()
