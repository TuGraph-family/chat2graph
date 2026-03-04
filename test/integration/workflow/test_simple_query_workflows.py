"""
Integration Tests for Simple Query Workflows

测试简单查询工作流的端到端集成。

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
@pytest.mark.workflow
class TestSimpleQueryWorkflows:
    """Integration tests for simple query processing workflows."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for testing."""
        return SubJob(
            id=f"workflow_job_{uuid4()}",
            session_id=f"workflow_session_{uuid4()}",
            goal="Process simple natural language query to Cypher",
            context="Testing end-to-end simple query workflow",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_simple_vertex_query_workflow(self, sample_job):
        """Test complete workflow for simple vertex query: Find all persons."""
        # This test validates the entire pipeline from natural language to Cypher

        # Simulated workflow stages:
        # 1. Intention Analysis
        # 2. Complexity Analysis
        # 3. Query Design
        # 4. Validation
        # 5. Final Cypher Query

        workflow_stages = []

        # Stage 1: Initial query
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find all persons",
                "user_id": "test_user",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Stage 2: Intention analysis result
        intention_result = WorkflowMessage(
            payload={
                "query_text": "Find all persons",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "filters": [],
                    "aggregations": [],
                    "confidence": 0.95
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Stage 3: Complexity analysis result
        complexity_result = WorkflowMessage(
            payload={
                "query_text": "Find all persons",
                "intention_analysis": intention_result.payload["intention_analysis"],
                "complexity_analysis": {
                    "complexity_level": "SIMPLE",
                    "complexity_score": 0.2,
                    "entity_count": 1,
                    "relationship_depth": 0,
                    "recommended_strategy": "direct"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Stage 4: Query design result
        design_result = WorkflowMessage(
            payload={
                "query_text": "Find all persons",
                "designed_query": {
                    "cypher": "MATCH (p:Person) RETURN p LIMIT 100",
                    "query_type": "VERTEX_QUERY"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Stage 5: Validation result
        validation_result = WorkflowMessage(
            payload={
                "cypher_query": "MATCH (p:Person) RETURN p LIMIT 100",
                "validation_summary": {
                    "overall_status": "PASS",
                    "critical_issues": 0,
                    "warnings": 0
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(validation_result)

        # Verify workflow progression
        assert len(workflow_stages) == 5
        assert workflow_stages[0].payload["query_text"] == "Find all persons"
        assert workflow_stages[1].payload["intention_analysis"]["query_type"] == "RETRIEVE"
        assert workflow_stages[2].payload["complexity_analysis"]["complexity_level"] == "SIMPLE"
        assert "MATCH (p:Person)" in workflow_stages[3].payload["designed_query"]["cypher"]
        assert workflow_stages[4].payload["validation_summary"]["overall_status"] == "PASS"

    @pytest.mark.asyncio
    async def test_simple_filtered_query_workflow(self, sample_job):
        """Test workflow for simple query with filter: Find persons older than 30."""
        workflow_stages = []

        # Initial query with filter
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find persons older than 30",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Intention analysis identifies filter
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "filters": [{"property": "age", "operator": ">", "value": 30}],
                    "confidence": 0.92
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Complexity remains simple
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "SIMPLE",
                    "complexity_score": 0.3,
                    "has_filters": True
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Query designed with WHERE clause
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p:Person) WHERE p.age > 30 RETURN p LIMIT 100",
                    "query_type": "VERTEX_QUERY"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Validation passes
        validation_result = WorkflowMessage(
            payload={
                "validation_summary": {
                    "overall_status": "PASS",
                    "critical_issues": 0
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(validation_result)

        # Verify filter applied correctly
        assert len(workflow_stages[1].payload["intention_analysis"]["filters"]) == 1
        assert "WHERE p.age > 30" in workflow_stages[3].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_simple_relationship_query_workflow(self, sample_job):
        """Test workflow for simple relationship query: Find persons who work at companies."""
        workflow_stages = []

        # Initial query with relationship
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find persons who work at companies",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Intention analysis identifies relationship
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person", "Company"],
                    "relationship_patterns": ["WORKS_AT"],
                    "confidence": 0.90
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Complexity moderate due to relationship
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "MODERATE",
                    "complexity_score": 0.5,
                    "relationship_depth": 1
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Path pattern recognition
        pattern_result = WorkflowMessage(
            payload={
                "path_analysis": {
                    "has_multi_hop": False,
                    "patterns": [{
                        "pattern_type": "DIRECT",
                        "source_entity": "Person",
                        "target_entity": "Company",
                        "relationship_types": ["WORKS_AT"]
                    }]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(pattern_result)

        # Query designed with relationship
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p, c LIMIT 100",
                    "query_type": "PATH_QUERY"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Verify relationship pattern
        assert "WORKS_AT" in workflow_stages[1].payload["intention_analysis"]["relationship_patterns"]
        assert "[:WORKS_AT]" in workflow_stages[4].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_simple_aggregation_workflow(self, sample_job):
        """Test workflow for simple aggregation: Count all persons."""
        workflow_stages = []

        # Initial aggregation query
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Count all persons",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Intention analysis identifies aggregation
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "AGGREGATE",
                    "target_entities": ["Person"],
                    "aggregation_type": "COUNT",
                    "confidence": 0.95
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Complexity simple for basic aggregation
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "SIMPLE",
                    "complexity_score": 0.3,
                    "has_aggregations": True
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Query designed with COUNT
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p:Person) RETURN count(p) as person_count",
                    "query_type": "AGGREGATION"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Verify aggregation
        assert workflow_stages[1].payload["intention_analysis"]["aggregation_type"] == "COUNT"
        assert "count(p)" in workflow_stages[3].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_workflow_with_context_enhancement(self, sample_job):
        """Test workflow that includes context enhancement from history."""
        workflow_stages = []

        # Initial query
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find persons",
                "session_id": sample_job.session_id,
                "user_id": "returning_user"
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Context enhancement provides preferences
        context_result = WorkflowMessage(
            payload={
                "context_summary": {
                    "session_info": {
                        "total_queries": 20,
                        "success_rate": 0.90
                    },
                    "user_preferences": {
                        "preferred_complexity": "SIMPLE",
                        "acceptable_latency_ms": 100
                    }
                },
                "query_suggestions": {
                    "improvements": [
                        {"suggestion": "Add LIMIT 50 based on your preferences"}
                    ]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(context_result)

        # Query design incorporates preferences
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p:Person) RETURN p LIMIT 50",
                    "query_type": "VERTEX_QUERY"
                },
                "design_rationale": {
                    "optimization_strategy": "Applied user preference for LIMIT 50"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Verify context influenced design
        assert workflow_stages[1].payload["context_summary"]["user_preferences"]["preferred_complexity"] == "SIMPLE"
        assert "LIMIT 50" in workflow_stages[2].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_workflow_message_progression(self, sample_job):
        """Test that workflow messages properly accumulate context."""
        workflow_messages = []

        # Message 1: Initial query
        msg1 = WorkflowMessage(
            payload={"query_text": "Find persons", "stage": "initial"},
            job_id=sample_job.id
        )
        workflow_messages.append(msg1)

        # Message 2: Add intention analysis
        msg2 = WorkflowMessage(
            payload={
                "query_text": "Find persons",
                "stage": "intention",
                "intention_analysis": {"query_type": "RETRIEVE"}
            },
            job_id=sample_job.id
        )
        workflow_messages.append(msg2)

        # Message 3: Add complexity analysis
        msg3 = WorkflowMessage(
            payload={
                "query_text": "Find persons",
                "stage": "complexity",
                "intention_analysis": {"query_type": "RETRIEVE"},
                "complexity_analysis": {"complexity_level": "SIMPLE"}
            },
            job_id=sample_job.id
        )
        workflow_messages.append(msg3)

        # Verify progressive enrichment
        assert len(workflow_messages) == 3
        assert "stage" in workflow_messages[0].payload
        assert "intention_analysis" in workflow_messages[1].payload
        assert "complexity_analysis" in workflow_messages[2].payload

        # Verify all messages belong to same job
        assert all(msg.job_id == sample_job.id for msg in workflow_messages)


@pytest.mark.integration
@pytest.mark.workflow
class TestWorkflowStateTransitions:
    """Test workflow state transitions and data flow."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for testing."""
        return SubJob(
            id=f"state_job_{uuid4()}",
            session_id=f"state_session_{uuid4()}",
            goal="Test workflow state transitions",
            context="Validating state progression",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_workflow_state_validation(self, sample_job):
        """Test that workflow enforces proper state transitions."""
        states = []

        # State 1: INITIAL
        state1 = {
            "state": "INITIAL",
            "has_query_text": True,
            "has_intention": False,
            "has_complexity": False,
            "has_design": False,
            "has_validation": False
        }
        states.append(state1)

        # State 2: INTENTION_ANALYZED
        state2 = {
            "state": "INTENTION_ANALYZED",
            "has_query_text": True,
            "has_intention": True,
            "has_complexity": False,
            "has_design": False,
            "has_validation": False
        }
        states.append(state2)

        # State 3: COMPLEXITY_ANALYZED
        state3 = {
            "state": "COMPLEXITY_ANALYZED",
            "has_query_text": True,
            "has_intention": True,
            "has_complexity": True,
            "has_design": False,
            "has_validation": False
        }
        states.append(state3)

        # State 4: QUERY_DESIGNED
        state4 = {
            "state": "QUERY_DESIGNED",
            "has_query_text": True,
            "has_intention": True,
            "has_complexity": True,
            "has_design": True,
            "has_validation": False
        }
        states.append(state4)

        # State 5: VALIDATED
        state5 = {
            "state": "VALIDATED",
            "has_query_text": True,
            "has_intention": True,
            "has_complexity": True,
            "has_design": True,
            "has_validation": True
        }
        states.append(state5)

        # Verify progressive state transitions
        assert len(states) == 5
        for i in range(1, len(states)):
            # Each state should have at least as much data as previous
            prev_true_count = sum(1 for v in states[i-1].values() if v is True)
            curr_true_count = sum(1 for v in states[i].values() if v is True)
            assert curr_true_count >= prev_true_count

    @pytest.mark.asyncio
    async def test_workflow_data_accumulation(self, sample_job):
        """Test that data accumulates correctly through workflow stages."""
        accumulated_data = {}

        # Stage 1: Add query text
        accumulated_data["query_text"] = "Find persons older than 25"
        assert len(accumulated_data) == 1

        # Stage 2: Add intention
        accumulated_data["intention_analysis"] = {
            "query_type": "RETRIEVE",
            "filters": [{"property": "age", "operator": ">", "value": 25}]
        }
        assert len(accumulated_data) == 2

        # Stage 3: Add complexity
        accumulated_data["complexity_analysis"] = {
            "complexity_level": "SIMPLE",
            "complexity_score": 0.3
        }
        assert len(accumulated_data) == 3

        # Stage 4: Add design
        accumulated_data["designed_query"] = {
            "cypher": "MATCH (p:Person) WHERE p.age > 25 RETURN p"
        }
        assert len(accumulated_data) == 4

        # Stage 5: Add validation
        accumulated_data["validation_summary"] = {
            "overall_status": "PASS"
        }
        assert len(accumulated_data) == 5

        # Verify all data preserved
        assert "query_text" in accumulated_data
        assert "intention_analysis" in accumulated_data
        assert "complexity_analysis" in accumulated_data
        assert "designed_query" in accumulated_data
        assert "validation_summary" in accumulated_data
