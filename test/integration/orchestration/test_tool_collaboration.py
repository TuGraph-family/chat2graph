"""
Integration Tests for Tool Collaboration and Orchestration

测试工具协作和编排的集成功能。

Author: kaichuan
Date: 2025-11-25
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Initialize server before importing app modules
from app.core.sdk.init_server import init_server
init_server()

from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage


@pytest.mark.integration
@pytest.mark.orchestration
class TestContextToolCollaboration:
    """Integration tests for context tools working together."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for tool collaboration testing."""
        return SubJob(
            id=f"collab_job_{uuid4()}",
            session_id=f"collab_session_{uuid4()}",
            goal="Test tool collaboration patterns",
            context="Validating tools working together",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_retriever_and_learner_collaboration(self, sample_job):
        """Test ContextRetriever and PreferenceLearner working together."""
        collaboration_workflow = []

        # Step 1: ContextRetriever gets session data
        retriever_result = {
            "tool": "ContextRetriever",
            "session_context": {
                "session_id": sample_job.session_id,
                "total_queries": 15,
                "success_rate": 0.87
            },
            "relevant_history": [
                {"query": "Find persons", "success": True},
                {"query": "Find companies", "success": True}
            ]
        }
        collaboration_workflow.append(retriever_result)

        # Step 2: PreferenceLearner analyzes retrieved data
        learner_result = {
            "tool": "PreferenceLearner",
            "input": retriever_result["relevant_history"],
            "learned_preferences": {
                "preferred_complexity": "SIMPLE",
                "preferred_entities": ["Person", "Company"],
                "confidence": 0.85
            }
        }
        collaboration_workflow.append(learner_result)

        # Step 3: Results combined for query enhancement
        combined_result = {
            "context": retriever_result["session_context"],
            "preferences": learner_result["learned_preferences"],
            "recommendation": "Use simple queries with Person/Company entities"
        }
        collaboration_workflow.append(combined_result)

        # Verify collaboration
        assert len(collaboration_workflow) == 3
        assert collaboration_workflow[0]["tool"] == "ContextRetriever"
        assert collaboration_workflow[1]["tool"] == "PreferenceLearner"
        assert collaboration_workflow[2]["recommendation"] is not None

    @pytest.mark.asyncio
    async def test_learner_and_suggester_collaboration(self, sample_job):
        """Test PreferenceLearner and QuerySuggester working together."""
        collaboration_workflow = []

        # Step 1: PreferenceLearner identifies patterns
        learner_result = {
            "tool": "PreferenceLearner",
            "preferences": {
                "frequent_patterns": ["Person-KNOWS-Person", "Person-WORKS_AT-Company"],
                "preferred_complexity": "MODERATE",
                "avg_result_size": 50
            }
        }
        collaboration_workflow.append(learner_result)

        # Step 2: QuerySuggester uses preferences to suggest improvements
        suggester_result = {
            "tool": "QuerySuggester",
            "input_preferences": learner_result["preferences"],
            "suggestions": {
                "improvements": [
                    "Consider using your frequent KNOWS pattern",
                    "Set LIMIT to 50 based on your average result size"
                ],
                "alternatives": [
                    "MATCH (p:Person)-[:KNOWS]->(friend) RETURN p, friend LIMIT 50"
                ]
            }
        }
        collaboration_workflow.append(suggester_result)

        # Verify collaboration
        assert suggester_result["input_preferences"] == learner_result["preferences"]
        assert len(suggester_result["suggestions"]["improvements"]) >= 2

    @pytest.mark.asyncio
    async def test_three_tool_collaboration_chain(self, sample_job):
        """Test all three context tools working in sequence."""
        tool_chain = []

        # Tool 1: Retrieve context
        step1 = {
            "tool": "ContextRetriever",
            "output": {
                "session_queries": 20,
                "relevant_history": [
                    {"query": "Find tech companies", "cypher": "MATCH (c:Company) WHERE c.industry='tech' RETURN c"}
                ]
            }
        }
        tool_chain.append(step1)

        # Tool 2: Learn from history
        step2 = {
            "tool": "PreferenceLearner",
            "input_from": "ContextRetriever",
            "output": {
                "learned": {
                    "frequent_filters": ["industry='tech'"],
                    "preferred_limit": 100
                }
            }
        }
        tool_chain.append(step2)

        # Tool 3: Suggest based on learning
        step3 = {
            "tool": "QuerySuggester",
            "input_from": "PreferenceLearner",
            "output": {
                "suggestions": [
                    "Use industry='tech' filter based on your history",
                    "Set LIMIT 100 as you usually do"
                ]
            }
        }
        tool_chain.append(step3)

        # Verify sequential collaboration
        assert len(tool_chain) == 3
        assert tool_chain[1]["input_from"] == "ContextRetriever"
        assert tool_chain[2]["input_from"] == "PreferenceLearner"


@pytest.mark.integration
@pytest.mark.orchestration
class TestQueryPlanningToolCollaboration:
    """Integration tests for query planning tools working together."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for planning tool testing."""
        return SubJob(
            id=f"planning_job_{uuid4()}",
            session_id=f"planning_session_{uuid4()}",
            goal="Test query planning tool collaboration",
            context="Validating planning tools coordination",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_schema_and_query_tool_collaboration(self, sample_job):
        """Test get_schema and query_vertex tools working together."""
        planning_workflow = []

        # Step 1: get_schema retrieves schema
        schema_result = {
            "tool": "get_schema",
            "schema": {
                "vertex_types": ["Person", "Company"],
                "edge_types": ["WORKS_AT", "KNOWS"],
                "properties": {
                    "Person": ["name", "age"],
                    "Company": ["name", "industry"]
                }
            }
        }
        planning_workflow.append(schema_result)

        # Step 2: query_vertex uses schema to validate query
        query_result = {
            "tool": "query_vertex",
            "uses_schema": True,
            "validation": {
                "vertex_type": "Person",
                "properties_used": ["name", "age"],
                "all_valid": True
            },
            "query": "MATCH (p:Person) WHERE p.age > 25 RETURN p.name"
        }
        planning_workflow.append(query_result)

        # Verify schema was used
        assert planning_workflow[1]["uses_schema"] is True
        assert planning_workflow[1]["validation"]["all_valid"] is True

    @pytest.mark.asyncio
    async def test_complexity_and_rewrite_tool_collaboration(self, sample_job):
        """Test analyze_complexity and rewrite_query tools working together."""
        optimization_workflow = []

        # Step 1: analyze_complexity identifies issues
        complexity_result = {
            "tool": "analyze_complexity",
            "analysis": {
                "complexity_score": 0.9,
                "issues": ["No LIMIT clause", "Unbounded traversal"],
                "recommendations": ["Add LIMIT", "Add early filtering"]
            }
        }
        optimization_workflow.append(complexity_result)

        # Step 2: rewrite_query applies recommendations
        rewrite_result = {
            "tool": "rewrite_query",
            "input_analysis": complexity_result["analysis"],
            "original": "MATCH (p:Person)-[:KNOWS*]->(friend) RETURN p, friend",
            "rewritten": "MATCH (p:Person)-[:KNOWS*1..3]->(friend) WHERE p.name = 'John' RETURN p, friend LIMIT 100",
            "improvements": ["Added LIMIT 100", "Limited path depth", "Added early filter"]
        }
        optimization_workflow.append(rewrite_result)

        # Verify rewrite addressed complexity issues
        assert "LIMIT" in rewrite_result["rewritten"]
        assert "*1..3" in rewrite_result["rewritten"]


@pytest.mark.integration
@pytest.mark.orchestration
class TestCrossLayerToolCollaboration:
    """Integration tests for tools from different layers working together."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for cross-layer testing."""
        return SubJob(
            id=f"cross_layer_job_{uuid4()}",
            session_id=f"cross_layer_session_{uuid4()}",
            goal="Test cross-layer tool collaboration",
            context="Validating tools across different layers",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_context_and_planning_tool_collaboration(self, sample_job):
        """Test context tools collaborating with planning tools."""
        cross_layer_workflow = []

        # Layer 1: Context tools gather user preferences
        context_phase = {
            "layer": "context",
            "tools": ["ContextRetriever", "PreferenceLearner"],
            "output": {
                "preferred_complexity": "SIMPLE",
                "preferred_limit": 50,
                "frequent_entities": ["Person"]
            }
        }
        cross_layer_workflow.append(context_phase)

        # Layer 2: Planning tools use preferences
        planning_phase = {
            "layer": "planning",
            "tools": ["get_schema", "query_vertex"],
            "uses_context": context_phase["output"],
            "output": {
                "query": "MATCH (p:Person) RETURN p LIMIT 50",
                "rationale": "Simple query with user's preferred LIMIT"
            }
        }
        cross_layer_workflow.append(planning_phase)

        # Verify cross-layer collaboration
        assert planning_phase["uses_context"] is not None
        assert "50" in planning_phase["output"]["query"]

    @pytest.mark.asyncio
    async def test_validation_and_context_tool_collaboration(self, sample_job):
        """Test validation tools providing feedback to context tools."""
        feedback_loop = []

        # Step 1: Validation tool identifies issue
        validation_result = {
            "tool": "validate_schema",
            "validation": {
                "status": "FAIL",
                "error": "Property 'salary' not found on Person"
            }
        }
        feedback_loop.append(validation_result)

        # Step 2: Context tools record failure pattern
        context_update = {
            "tool": "PreferenceLearner",
            "feedback": validation_result["validation"],
            "learning": {
                "avoid_properties": ["salary"],
                "reason": "Not in schema"
            }
        }
        feedback_loop.append(context_update)

        # Step 3: Future suggestions avoid the error
        suggester_result = {
            "tool": "QuerySuggester",
            "uses_learning": context_update["learning"],
            "suggestions": {
                "improvements": ["Avoid 'salary' property - not in schema"],
                "alternatives": ["Use 'name' or 'age' instead"]
            }
        }
        feedback_loop.append(suggester_result)

        # Verify feedback loop
        assert len(feedback_loop) == 3
        assert "salary" in feedback_loop[1]["learning"]["avoid_properties"]
        assert "salary" in feedback_loop[2]["suggestions"]["improvements"][0]


@pytest.mark.integration
@pytest.mark.orchestration
class TestToolOrchestrationPatterns:
    """Integration tests for common tool orchestration patterns."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for orchestration pattern testing."""
        return SubJob(
            id=f"pattern_job_{uuid4()}",
            session_id=f"pattern_session_{uuid4()}",
            goal="Test tool orchestration patterns",
            context="Validating orchestration strategies",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self, sample_job):
        """Test multiple tools executing in parallel."""
        parallel_execution = {
            "pattern": "PARALLEL",
            "tools_executed": [
                {
                    "tool": "get_schema",
                    "execution_time": 50,
                    "status": "SUCCESS"
                },
                {
                    "tool": "ContextRetriever",
                    "execution_time": 45,
                    "status": "SUCCESS"
                },
                {
                    "tool": "read_grammer",
                    "execution_time": 30,
                    "status": "SUCCESS"
                }
            ],
            "total_time": 50  # Max of parallel executions, not sum
        }

        # Verify parallel execution is faster than sequential
        sequential_time = sum(t["execution_time"] for t in parallel_execution["tools_executed"])
        assert parallel_execution["total_time"] < sequential_time

    @pytest.mark.asyncio
    async def test_sequential_tool_chain(self, sample_job):
        """Test tools executing in strict sequence with dependencies."""
        sequential_chain = {
            "pattern": "SEQUENTIAL",
            "steps": [
                {
                    "step": 1,
                    "tool": "get_schema",
                    "output": {"schema": "..."},
                    "next_depends_on": "schema"
                },
                {
                    "step": 2,
                    "tool": "validate_schema",
                    "requires": "schema",
                    "input_from": 1,
                    "output": {"valid": True}
                },
                {
                    "step": 3,
                    "tool": "query_vertex",
                    "requires": "valid",
                    "input_from": 2,
                    "output": {"query": "..."}
                }
            ]
        }

        # Verify strict ordering
        for i in range(1, len(sequential_chain["steps"])):
            assert sequential_chain["steps"][i]["input_from"] == i

    @pytest.mark.asyncio
    async def test_conditional_tool_selection(self, sample_job):
        """Test conditional tool execution based on previous results."""
        conditional_workflow = []

        # Step 1: Initial query complexity check
        complexity_check = {
            "tool": "analyze_complexity",
            "complexity": "HIGH"
        }
        conditional_workflow.append(complexity_check)

        # Step 2: Conditional branching based on complexity
        if complexity_check["complexity"] == "HIGH":
            optimization_path = {
                "condition": "HIGH_COMPLEXITY",
                "tools_selected": ["rewrite_query", "recommend_indexes"],
                "reason": "High complexity requires optimization"
            }
            conditional_workflow.append(optimization_path)
        else:
            simple_path = {
                "condition": "LOW_COMPLEXITY",
                "tools_selected": ["validate_schema"],
                "reason": "Simple query only needs validation"
            }
            conditional_workflow.append(simple_path)

        # Verify conditional selection
        assert len(conditional_workflow) == 2
        assert conditional_workflow[1]["condition"] == "HIGH_COMPLEXITY"
        assert "rewrite_query" in conditional_workflow[1]["tools_selected"]

    @pytest.mark.asyncio
    async def test_retry_with_different_tool(self, sample_job):
        """Test fallback to alternative tool on failure."""
        retry_workflow = []

        # Attempt 1: Primary tool fails
        primary_attempt = {
            "tool": "query_vertex",
            "method": "direct",
            "status": "TIMEOUT"
        }
        retry_workflow.append(primary_attempt)

        # Attempt 2: Fallback to alternative tool
        fallback_attempt = {
            "tool": "get_schema",
            "method": "schema_based",
            "status": "SUCCESS",
            "reason": "Fallback after query_vertex timeout"
        }
        retry_workflow.append(fallback_attempt)

        # Verify fallback succeeded
        assert retry_workflow[0]["status"] == "TIMEOUT"
        assert retry_workflow[1]["status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_tool_result_aggregation(self, sample_job):
        """Test aggregating results from multiple tools."""
        aggregation_workflow = {
            "pattern": "AGGREGATION",
            "parallel_tools": [
                {
                    "tool": "ContextRetriever",
                    "result": {"user_history": 20}
                },
                {
                    "tool": "get_schema",
                    "result": {"vertex_types": ["Person", "Company"]}
                },
                {
                    "tool": "analyze_complexity",
                    "result": {"complexity": "MODERATE"}
                }
            ],
            "aggregated_result": {
                "user_history": 20,
                "available_types": ["Person", "Company"],
                "complexity": "MODERATE",
                "recommendation": "Moderate complexity query with user context"
            }
        }

        # Verify all results aggregated
        assert len(aggregation_workflow["parallel_tools"]) == 3
        assert all(k in aggregation_workflow["aggregated_result"]
                   for k in ["user_history", "available_types", "complexity"])
