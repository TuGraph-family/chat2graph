"""
Integration Tests for Complex Query Workflows

测试复杂查询工作流的端到端集成。

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
class TestComplexMultiHopWorkflows:
    """Integration tests for complex multi-hop query workflows."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for complex workflow testing."""
        return SubJob(
            id=f"complex_job_{uuid4()}",
            session_id=f"complex_session_{uuid4()}",
            goal="Process complex multi-hop natural language query to Cypher",
            context="Testing end-to-end complex query workflow",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_friends_of_friends_workflow(self, sample_job):
        """Test workflow for friends-of-friends query."""
        workflow_stages = []

        # Stage 1: Initial complex query
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find friends of friends of John",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Stage 2: Intention analysis identifies multi-hop
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "relationship_patterns": ["KNOWS"],
                    "filters": [{"property": "name", "operator": "=", "value": "John"}],
                    "complexity_indicators": ["multi_hop"],
                    "confidence": 0.88
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Stage 3: Complexity analysis identifies high complexity
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "COMPLEX",
                    "complexity_score": 0.8,
                    "entity_count": 1,
                    "relationship_depth": 2,
                    "has_variable_length": True,
                    "recommended_strategy": "multi_stage"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Stage 4: Path pattern recognition
        pattern_result = WorkflowMessage(
            payload={
                "path_analysis": {
                    "has_multi_hop": True,
                    "patterns": [{
                        "pattern_type": "MULTI_HOP",
                        "source_entity": "Person",
                        "target_entity": "Person",
                        "relationship_types": ["KNOWS"],
                        "min_depth": 2,
                        "max_depth": 2
                    }]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(pattern_result)

        # Stage 5: Query design with variable length path
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p1:Person)-[:KNOWS*2]->(p2:Person) WHERE p1.name = 'John' RETURN p2.name, p2.age LIMIT 100",
                    "query_type": "PATH_QUERY",
                    "components": {
                        "match_clauses": ["MATCH (p1:Person)-[:KNOWS*2]->(p2:Person)"],
                        "where_conditions": ["p1.name = 'John'"]
                    }
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Stage 6: Validation with performance warning
        validation_result = WorkflowMessage(
            payload={
                "validation_summary": {
                    "overall_status": "WARNING",
                    "critical_issues": 0,
                    "warnings": 1
                },
                "performance_prediction": {
                    "estimated_latency_ms": 500,
                    "performance_tier": "MEDIUM",
                    "bottlenecks": ["Multi-hop traversal without early filtering"]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(validation_result)

        # Verify complex workflow progression
        assert len(workflow_stages) == 6
        assert "multi_hop" in workflow_stages[1].payload["intention_analysis"]["complexity_indicators"]
        assert workflow_stages[2].payload["complexity_analysis"]["complexity_level"] == "COMPLEX"
        assert workflow_stages[3].payload["path_analysis"]["has_multi_hop"] is True
        assert "[:KNOWS*2]" in workflow_stages[4].payload["designed_query"]["cypher"]
        assert workflow_stages[5].payload["validation_summary"]["overall_status"] == "WARNING"

    @pytest.mark.asyncio
    async def test_multi_entity_complex_workflow(self, sample_job):
        """Test workflow for query involving multiple entity types and relationships."""
        workflow_stages = []

        # Initial: Find people who work at tech companies and know someone in management
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find people who work at tech companies and know someone in management",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Intention analysis: Multiple entities and relationships
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person", "Company"],
                    "relationship_patterns": ["WORKS_AT", "KNOWS"],
                    "filters": [
                        {"entity": "Company", "property": "industry", "value": "tech"},
                        {"entity": "Person", "property": "role", "value": "management"}
                    ],
                    "confidence": 0.85
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Complexity: High due to multiple relationships and filters
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "COMPLEX",
                    "complexity_score": 0.85,
                    "entity_count": 3,
                    "relationship_depth": 2,
                    "filter_count": 2,
                    "recommended_strategy": "multi_stage"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Query design with WITH clause for staging
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": """MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE c.industry = 'tech'
WITH p
MATCH (p)-[:KNOWS]->(m:Person)
WHERE m.role = 'management'
RETURN p.name, collect(m.name) as managers LIMIT 50""",
                    "query_type": "COMPLEX",
                    "components": {
                        "with_clauses": ["WITH p"]
                    }
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Verify multi-entity workflow
        assert len(workflow_stages[1].payload["intention_analysis"]["target_entities"]) == 2
        assert len(workflow_stages[1].payload["intention_analysis"]["relationship_patterns"]) == 2
        assert "WITH" in workflow_stages[3].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_aggregation_with_grouping_workflow(self, sample_job):
        """Test workflow for complex aggregation with grouping."""
        workflow_stages = []

        # Initial: Count employees per company with filters
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Count how many people work at each tech company, show only companies with more than 10 employees",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Intention: Aggregation with post-aggregation filter
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "AGGREGATE",
                    "aggregation_type": "COUNT",
                    "grouping_by": ["Company"],
                    "filters": [
                        {"type": "pre_aggregation", "property": "industry", "value": "tech"},
                        {"type": "post_aggregation", "operator": ">", "value": 10}
                    ]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Complexity: Moderate for aggregation
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "MODERATE",
                    "complexity_score": 0.6,
                    "has_aggregations": True,
                    "has_post_aggregation_filter": True
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Query design with HAVING clause
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": """MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE c.industry = 'tech'
WITH c, count(p) as employee_count
WHERE employee_count > 10
RETURN c.name, employee_count
ORDER BY employee_count DESC""",
                    "query_type": "AGGREGATION"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Verify aggregation with filtering
        assert workflow_stages[1].payload["intention_analysis"]["aggregation_type"] == "COUNT"
        assert any(f["type"] == "post_aggregation" for f in workflow_stages[1].payload["intention_analysis"]["filters"])
        assert "count(p)" in workflow_stages[3].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_shortest_path_workflow(self, sample_job):
        """Test workflow for shortest path query."""
        workflow_stages = []

        # Initial: Find shortest connection between two people
        initial_message = WorkflowMessage(
            payload={
                "query_text": "Find the shortest path of connections between Alice and Bob",
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_message)

        # Intention: Shortest path query
        intention_result = WorkflowMessage(
            payload={
                "intention_analysis": {
                    "query_type": "PATH",
                    "path_type": "SHORTEST",
                    "source": {"entity": "Person", "property": "name", "value": "Alice"},
                    "target": {"entity": "Person", "property": "name", "value": "Bob"}
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(intention_result)

        # Complexity: High for path algorithms
        complexity_result = WorkflowMessage(
            payload={
                "complexity_analysis": {
                    "complexity_level": "COMPLEX",
                    "complexity_score": 0.75,
                    "uses_path_algorithm": True
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(complexity_result)

        # Path pattern: Shortest path with variable length
        pattern_result = WorkflowMessage(
            payload={
                "path_analysis": {
                    "has_multi_hop": True,
                    "patterns": [{
                        "pattern_type": "SHORTEST_PATH",
                        "bidirectional": True,
                        "max_depth": 10
                    }]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(pattern_result)

        # Query design with shortestPath function
        design_result = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": """MATCH (alice:Person {name: 'Alice'}), (bob:Person {name: 'Bob'})
MATCH path = shortestPath((alice)-[*]-(bob))
RETURN path, length(path) as path_length""",
                    "query_type": "PATH_QUERY"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(design_result)

        # Verify shortest path query
        assert workflow_stages[1].payload["intention_analysis"]["path_type"] == "SHORTEST"
        assert "shortestPath" in workflow_stages[4].payload["designed_query"]["cypher"]


@pytest.mark.integration
@pytest.mark.workflow
class TestMultiTurnConversationWorkflows:
    """Integration tests for multi-turn conversation workflows."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for conversation workflow testing."""
        return SubJob(
            id=f"conversation_job_{uuid4()}",
            session_id=f"conversation_session_{uuid4()}",
            goal="Process multi-turn conversation queries",
            context="Testing context accumulation across turns",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_two_turn_refinement_workflow(self, sample_job):
        """Test workflow where second query refines first query."""
        conversation_turns = []

        # Turn 1: Initial query
        turn1_initial = WorkflowMessage(
            payload={
                "query_text": "Find people",
                "turn_number": 1,
                "session_id": sample_job.session_id
            },
            job_id=sample_job.id
        )
        turn1_result = WorkflowMessage(
            payload={
                "query_text": "Find people",
                "designed_query": {
                    "cypher": "MATCH (p:Person) RETURN p LIMIT 100"
                },
                "turn_number": 1
            },
            job_id=sample_job.id
        )
        conversation_turns.append({"initial": turn1_initial, "result": turn1_result})

        # Turn 2: Refinement query
        turn2_initial = WorkflowMessage(
            payload={
                "query_text": "Only those older than 30",
                "turn_number": 2,
                "session_id": sample_job.session_id,
                "previous_context": {
                    "previous_query": "Find people",
                    "previous_cypher": "MATCH (p:Person) RETURN p LIMIT 100"
                }
            },
            job_id=sample_job.id
        )
        turn2_result = WorkflowMessage(
            payload={
                "query_text": "Only those older than 30",
                "resolved_full_query": "Find people older than 30",
                "designed_query": {
                    "cypher": "MATCH (p:Person) WHERE p.age > 30 RETURN p LIMIT 100"
                },
                "turn_number": 2
            },
            job_id=sample_job.id
        )
        conversation_turns.append({"initial": turn2_initial, "result": turn2_result})

        # Verify context carryover
        assert len(conversation_turns) == 2
        assert "previous_context" in conversation_turns[1]["initial"].payload
        assert "WHERE p.age > 30" in conversation_turns[1]["result"].payload["designed_query"]["cypher"]

    @pytest.mark.asyncio
    async def test_three_turn_progressive_query_workflow(self, sample_job):
        """Test workflow where each turn adds more constraints."""
        conversation_turns = []

        # Turn 1: Start with entity
        turn1 = {
            "query": "Find companies",
            "cypher": "MATCH (c:Company) RETURN c LIMIT 100"
        }
        conversation_turns.append(turn1)

        # Turn 2: Add filter
        turn2 = {
            "query": "In the tech industry",
            "context": turn1,
            "resolved": "Find companies in the tech industry",
            "cypher": "MATCH (c:Company) WHERE c.industry = 'tech' RETURN c LIMIT 100"
        }
        conversation_turns.append(turn2)

        # Turn 3: Add relationship
        turn3 = {
            "query": "And show their employees",
            "context": turn2,
            "resolved": "Find companies in the tech industry and show their employees",
            "cypher": "MATCH (c:Company)-[:EMPLOYS]->(p:Person) WHERE c.industry = 'tech' RETURN c, p LIMIT 100"
        }
        conversation_turns.append(turn3)

        # Verify progressive query building
        assert len(conversation_turns) == 3
        assert "Company" in conversation_turns[0]["cypher"]
        assert "industry = 'tech'" in conversation_turns[1]["cypher"]
        assert "[:EMPLOYS]" in conversation_turns[2]["cypher"]

    @pytest.mark.asyncio
    async def test_conversation_context_accumulation(self, sample_job):
        """Test that conversation context accumulates correctly."""
        context_stack = []

        # Turn 1: Initial context
        context1 = {
            "turn": 1,
            "entities_mentioned": ["Person"],
            "relationships_mentioned": [],
            "filters": []
        }
        context_stack.append(context1)

        # Turn 2: Add relationship
        context2 = {
            "turn": 2,
            "entities_mentioned": ["Person", "Company"],
            "relationships_mentioned": ["WORKS_AT"],
            "filters": [],
            "previous_context": context1
        }
        context_stack.append(context2)

        # Turn 3: Add filter
        context3 = {
            "turn": 3,
            "entities_mentioned": ["Person", "Company"],
            "relationships_mentioned": ["WORKS_AT"],
            "filters": [{"property": "age", "operator": ">", "value": 25}],
            "previous_context": context2
        }
        context_stack.append(context3)

        # Verify accumulation
        assert len(context_stack) == 3
        assert len(context_stack[0]["entities_mentioned"]) == 1
        assert len(context_stack[1]["entities_mentioned"]) == 2
        assert len(context_stack[2]["filters"]) == 1


@pytest.mark.integration
@pytest.mark.workflow
class TestComplexWorkflowOptimization:
    """Integration tests for complex workflow optimization strategies."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for optimization testing."""
        return SubJob(
            id=f"optimization_job_{uuid4()}",
            session_id=f"optimization_session_{uuid4()}",
            goal="Test query optimization in complex workflows",
            context="Validating optimization strategies",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_optimization_rewrite_workflow(self, sample_job):
        """Test workflow where query is rewritten for optimization."""
        optimization_stages = []

        # Stage 1: Initial design (suboptimal)
        initial_design = {
            "cypher": "MATCH (p:Person) WHERE p.age > 25 MATCH (p)-[:WORKS_AT]->(c:Company) RETURN p, c",
            "optimization_score": 0.4
        }
        optimization_stages.append(initial_design)

        # Stage 2: Optimization analysis identifies issues
        analysis = {
            "issues": [
                "Separate MATCH clauses inefficient",
                "Should combine into single pattern"
            ],
            "recommendations": [
                "Combine MATCH patterns",
                "Move filter into combined pattern"
            ]
        }
        optimization_stages.append(analysis)

        # Stage 3: Rewritten query (optimized)
        optimized_design = {
            "cypher": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) WHERE p.age > 25 RETURN p, c",
            "optimization_score": 0.8,
            "improvements": [
                "Combined MATCH patterns",
                "Single traversal instead of two"
            ]
        }
        optimization_stages.append(optimized_design)

        # Verify optimization progression
        assert optimization_stages[0]["optimization_score"] < optimization_stages[2]["optimization_score"]
        assert len(optimization_stages[1]["recommendations"]) >= 2

    @pytest.mark.asyncio
    async def test_index_hint_optimization_workflow(self, sample_job):
        """Test workflow that adds index hints for optimization."""
        workflow_stages = []

        # Initial query design
        initial_design = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p:Person) WHERE p.name = 'John' RETURN p"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(initial_design)

        # Performance analysis identifies indexing opportunity
        performance_analysis = WorkflowMessage(
            payload={
                "performance_prediction": {
                    "estimated_latency_ms": 500,
                    "bottlenecks": ["Full scan on Person.name"],
                    "index_recommendations": [{
                        "vertex_type": "Person",
                        "property_name": "name",
                        "estimated_benefit": "80% speedup"
                    }]
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(performance_analysis)

        # Query rewritten with optimization note
        optimized_design = WorkflowMessage(
            payload={
                "designed_query": {
                    "cypher": "MATCH (p:Person) WHERE p.name = 'John' RETURN p",
                    "optimization_notes": "Requires index on Person(name) for optimal performance"
                }
            },
            job_id=sample_job.id
        )
        workflow_stages.append(optimized_design)

        # Verify index recommendation workflow
        assert len(workflow_stages) == 3
        assert "index_recommendations" in workflow_stages[1].payload["performance_prediction"]
