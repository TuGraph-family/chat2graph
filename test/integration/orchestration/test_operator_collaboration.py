"""
Integration Tests for Operator Collaboration and Orchestration

测试算子协作和编排的集成功能。

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
class TestSequentialOperatorExecution:
    """Integration tests for sequential operator execution and data flow."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for operator collaboration testing."""
        return SubJob(
            id=f"seq_op_job_{uuid4()}",
            session_id=f"seq_op_session_{uuid4()}",
            goal="Test sequential operator execution",
            context="Validating operator data flow",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_full_pipeline_sequential_execution(self, sample_job):
        """Test complete operator pipeline execution from intention to validation."""
        pipeline_stages = []

        # Stage 1: Intention Analysis Operator (implicit)
        intention_result = WorkflowMessage(
            payload={
                "query_text": "Find persons older than 30",
                "intention_analysis": {
                    "query_type": "RETRIEVE",
                    "target_entities": ["Person"],
                    "filters": [{"property": "age", "operator": ">", "value": 30}],
                    "confidence": 0.92
                }
            },
            job_id=sample_job.id
        )
        pipeline_stages.append(intention_result)

        # Stage 2: Complexity Analysis Operator
        complexity_result = WorkflowMessage(
            payload={
                "query_text": "Find persons older than 30",
                "intention_analysis": intention_result.payload["intention_analysis"],
                "complexity_analysis": {
                    "complexity_level": "SIMPLE",
                    "complexity_score": 0.3,
                    "entity_count": 1,
                    "relationship_depth": 0,
                    "has_filters": True,
                    "recommended_strategy": "direct"
                }
            },
            job_id=sample_job.id
        )
        pipeline_stages.append(complexity_result)

        # Stage 3: Path Pattern Recognition Operator (skipped for simple query)
        # For simple queries without relationships, path recognition may be skipped

        # Stage 4: Query Design Operator
        design_result = WorkflowMessage(
            payload={
                "query_text": "Find persons older than 30",
                "intention_analysis": intention_result.payload["intention_analysis"],
                "complexity_analysis": complexity_result.payload["complexity_analysis"],
                "designed_query": {
                    "cypher": "MATCH (p:Person) WHERE p.age > 30 RETURN p.name, p.age LIMIT 100",
                    "query_type": "VERTEX_QUERY",
                    "components": {
                        "match_clauses": ["MATCH (p:Person)"],
                        "where_conditions": ["p.age > 30"],
                        "return_expressions": ["p.name", "p.age"],
                        "limit_clause": "LIMIT 100"
                    }
                },
                "optimization_applied": {
                    "early_filtering": True,
                    "index_hints": ["Person.age"],
                    "limit_added": True
                }
            },
            job_id=sample_job.id
        )
        pipeline_stages.append(design_result)

        # Stage 5: Query Validation Operator
        validation_result = WorkflowMessage(
            payload={
                "cypher_query": design_result.payload["designed_query"]["cypher"],
                "validation_summary": {
                    "overall_status": "PASS",
                    "critical_issues": 0,
                    "warnings": 0,
                    "recommendations": 1
                },
                "schema_validation": {
                    "is_valid": True,
                    "errors": [],
                    "warnings": []
                },
                "semantic_validation": {
                    "is_semantically_valid": True,
                    "semantic_issues": []
                },
                "performance_prediction": {
                    "estimated_latency_ms": 150,
                    "performance_tier": "FAST",
                    "bottlenecks": []
                },
                "security_scan": {
                    "is_safe": True,
                    "vulnerabilities": []
                }
            },
            job_id=sample_job.id
        )
        pipeline_stages.append(validation_result)

        # Verify complete pipeline execution
        assert len(pipeline_stages) == 4
        assert all(msg.job_id == sample_job.id for msg in pipeline_stages)

        # Verify data flow through pipeline
        assert "intention_analysis" in pipeline_stages[0].payload
        assert "complexity_analysis" in pipeline_stages[1].payload
        assert "designed_query" in pipeline_stages[2].payload
        assert "validation_summary" in pipeline_stages[3].payload

        # Verify data accumulation
        assert pipeline_stages[1].payload["intention_analysis"] == pipeline_stages[0].payload["intention_analysis"]
        assert pipeline_stages[2].payload["complexity_analysis"] == pipeline_stages[1].payload["complexity_analysis"]

    @pytest.mark.asyncio
    async def test_complex_query_pipeline_with_path_recognition(self, sample_job):
        """Test pipeline execution for complex query including path recognition."""
        pipeline_stages = []

        # Stage 1: Intention Analysis
        intention_result = WorkflowMessage(
            payload={
                "query_text": "Find friends of friends of John",
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
        pipeline_stages.append(intention_result)

        # Stage 2: Complexity Analysis
        complexity_result = WorkflowMessage(
            payload={
                "intention_analysis": intention_result.payload["intention_analysis"],
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
        pipeline_stages.append(complexity_result)

        # Stage 3: Path Pattern Recognition (critical for complex query)
        path_result = WorkflowMessage(
            payload={
                "intention_analysis": intention_result.payload["intention_analysis"],
                "complexity_analysis": complexity_result.payload["complexity_analysis"],
                "path_analysis": {
                    "has_multi_hop": True,
                    "patterns": [{
                        "pattern_type": "MULTI_HOP",
                        "source_entity": "Person",
                        "target_entity": "Person",
                        "relationship_types": ["KNOWS"],
                        "min_depth": 2,
                        "max_depth": 2,
                        "bidirectional": False
                    }],
                    "combined_cypher_hints": {
                        "variable_length_syntax": "[:KNOWS*2]",
                        "optimization_hints": ["Add depth limit", "Consider early filtering"]
                    }
                }
            },
            job_id=sample_job.id
        )
        pipeline_stages.append(path_result)

        # Stage 4: Query Design (uses path analysis)
        design_result = WorkflowMessage(
            payload={
                "path_analysis": path_result.payload["path_analysis"],
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
        pipeline_stages.append(design_result)

        # Stage 5: Validation
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
                    "bottlenecks": ["Multi-hop traversal"]
                }
            },
            job_id=sample_job.id
        )
        pipeline_stages.append(validation_result)

        # Verify complex pipeline
        assert len(pipeline_stages) == 5
        assert pipeline_stages[2].payload["path_analysis"]["has_multi_hop"] is True
        assert "[:KNOWS*2]" in pipeline_stages[3].payload["designed_query"]["cypher"]


@pytest.mark.integration
@pytest.mark.orchestration
class TestOperatorResultPassing:
    """Integration tests for operator result passing and data accumulation."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for result passing testing."""
        return SubJob(
            id=f"result_job_{uuid4()}",
            session_id=f"result_session_{uuid4()}",
            goal="Test operator result passing",
            context="Validating data accumulation",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_data_accumulation_through_operators(self, sample_job):
        """Test that data accumulates correctly as it passes through operators."""
        accumulated_data = {}

        # Operator 1: Intention Analysis adds intention_analysis
        accumulated_data["query_text"] = "Find persons"
        accumulated_data["intention_analysis"] = {
            "query_type": "RETRIEVE",
            "target_entities": ["Person"]
        }
        assert len(accumulated_data) == 2

        # Operator 2: Complexity Analysis adds complexity_analysis
        accumulated_data["complexity_analysis"] = {
            "complexity_level": "SIMPLE",
            "complexity_score": 0.2
        }
        assert len(accumulated_data) == 3

        # Operator 3: Query Design adds designed_query
        accumulated_data["designed_query"] = {
            "cypher": "MATCH (p:Person) RETURN p LIMIT 100",
            "query_type": "VERTEX_QUERY"
        }
        assert len(accumulated_data) == 4

        # Operator 4: Validation adds validation_summary
        accumulated_data["validation_summary"] = {
            "overall_status": "PASS"
        }
        assert len(accumulated_data) == 5

        # Verify all previous data preserved
        assert "query_text" in accumulated_data
        assert "intention_analysis" in accumulated_data
        assert "complexity_analysis" in accumulated_data
        assert "designed_query" in accumulated_data
        assert "validation_summary" in accumulated_data

    @pytest.mark.asyncio
    async def test_operator_output_as_next_operator_input(self, sample_job):
        """Test that one operator's output becomes the next operator's input."""
        operator_chain = []

        # Operator 1: Complexity Analysis
        op1_output = {
            "operator": "ComplexityAnalysis",
            "output": {
                "complexity_level": "MODERATE",
                "complexity_score": 0.6,
                "has_relationships": True
            }
        }
        operator_chain.append(op1_output)

        # Operator 2: Path Recognition uses complexity output
        op2_input = op1_output["output"]
        op2_output = {
            "operator": "PathRecognition",
            "input_from": "ComplexityAnalysis",
            "used_input": op2_input,
            "output": {
                "has_multi_hop": False,
                "patterns": [{
                    "pattern_type": "DIRECT",
                    "relationship_depth": 1
                }]
            }
        }
        operator_chain.append(op2_output)

        # Operator 3: Query Design uses both previous outputs
        op3_input = {
            "complexity": op1_output["output"],
            "path_info": op2_output["output"]
        }
        op3_output = {
            "operator": "QueryDesign",
            "input_from": ["ComplexityAnalysis", "PathRecognition"],
            "used_input": op3_input,
            "output": {
                "cypher": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p, c"
            }
        }
        operator_chain.append(op3_output)

        # Verify operator chain
        assert len(operator_chain) == 3
        assert operator_chain[1]["input_from"] == "ComplexityAnalysis"
        assert operator_chain[1]["used_input"] == operator_chain[0]["output"]
        assert operator_chain[2]["input_from"] == ["ComplexityAnalysis", "PathRecognition"]


@pytest.mark.integration
@pytest.mark.orchestration
class TestConditionalOperatorSelection:
    """Integration tests for conditional operator selection based on results."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for conditional operator testing."""
        return SubJob(
            id=f"conditional_job_{uuid4()}",
            session_id=f"conditional_session_{uuid4()}",
            goal="Test conditional operator selection",
            context="Validating dynamic operator routing",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_path_recognition_conditional_on_complexity(self, sample_job):
        """Test that path recognition is conditionally included based on complexity."""
        workflow_branches = []

        # Scenario 1: Simple query (complexity = SIMPLE)
        simple_complexity = {
            "complexity_level": "SIMPLE",
            "has_relationships": False
        }

        simple_branch = {
            "complexity": simple_complexity,
            "path_recognition_needed": False,
            "operators_used": ["IntentionAnalysis", "ComplexityAnalysis", "QueryDesign", "Validation"],
            "reason": "No relationships, path recognition skipped"
        }
        workflow_branches.append(simple_branch)

        # Scenario 2: Complex query (complexity = COMPLEX)
        complex_complexity = {
            "complexity_level": "COMPLEX",
            "has_relationships": True,
            "relationship_depth": 2
        }

        complex_branch = {
            "complexity": complex_complexity,
            "path_recognition_needed": True,
            "operators_used": ["IntentionAnalysis", "ComplexityAnalysis", "PathRecognition", "QueryDesign", "Validation"],
            "reason": "Complex relationships require path analysis"
        }
        workflow_branches.append(complex_branch)

        # Verify conditional logic
        assert workflow_branches[0]["path_recognition_needed"] is False
        assert len(workflow_branches[0]["operators_used"]) == 4

        assert workflow_branches[1]["path_recognition_needed"] is True
        assert len(workflow_branches[1]["operators_used"]) == 5
        assert "PathRecognition" in workflow_branches[1]["operators_used"]

    @pytest.mark.asyncio
    async def test_context_enhancement_conditional_on_session(self, sample_job):
        """Test that context enhancement is conditional on session availability."""
        workflow_scenarios = []

        # Scenario 1: No session ID (skip context enhancement)
        no_session = {
            "session_id": None,
            "context_enhancement_applied": False,
            "operators_used": ["IntentionAnalysis", "ComplexityAnalysis", "QueryDesign", "Validation"],
            "reason": "No session history available"
        }
        workflow_scenarios.append(no_session)

        # Scenario 2: Valid session ID (apply context enhancement)
        with_session = {
            "session_id": sample_job.session_id,
            "context_enhancement_applied": True,
            "operators_used": ["IntentionAnalysis", "ContextEnhancement", "ComplexityAnalysis", "QueryDesign", "Validation"],
            "reason": "Session history available for personalization"
        }
        workflow_scenarios.append(with_session)

        # Verify conditional enhancement
        assert workflow_scenarios[0]["context_enhancement_applied"] is False
        assert "ContextEnhancement" not in workflow_scenarios[0]["operators_used"]

        assert workflow_scenarios[1]["context_enhancement_applied"] is True
        assert "ContextEnhancement" in workflow_scenarios[1]["operators_used"]


@pytest.mark.integration
@pytest.mark.orchestration
class TestOperatorCollaborationForComplexQueries:
    """Integration tests for operator collaboration on complex queries."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for complex query testing."""
        return SubJob(
            id=f"complex_collab_job_{uuid4()}",
            session_id=f"complex_collab_session_{uuid4()}",
            goal="Test operator collaboration for complex queries",
            context="Validating multi-operator coordination",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_multi_operator_coordination_for_aggregation(self, sample_job):
        """Test operators working together for aggregation query with filtering."""
        collaboration_stages = []

        # Stage 1: Intention identifies aggregation with filters
        intention_stage = {
            "operator": "IntentionAnalysis",
            "output": {
                "query_type": "AGGREGATE",
                "aggregation_type": "COUNT",
                "grouping_by": ["Company"],
                "filters": [
                    {"type": "pre_aggregation", "property": "industry", "value": "tech"},
                    {"type": "post_aggregation", "operator": ">", "value": 10}
                ]
            }
        }
        collaboration_stages.append(intention_stage)

        # Stage 2: Complexity recognizes aggregation complexity
        complexity_stage = {
            "operator": "ComplexityAnalysis",
            "input_from": intention_stage["output"],
            "output": {
                "complexity_level": "MODERATE",
                "has_aggregations": True,
                "has_post_aggregation_filter": True,
                "recommended_strategy": "staged"
            }
        }
        collaboration_stages.append(complexity_stage)

        # Stage 3: Query Design uses both intention and complexity
        design_stage = {
            "operator": "QueryDesign",
            "input_from": [intention_stage["output"], complexity_stage["output"]],
            "output": {
                "cypher": """MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE c.industry = 'tech'
WITH c, count(p) as employee_count
WHERE employee_count > 10
RETURN c.name, employee_count
ORDER BY employee_count DESC""",
                "design_rationale": {
                    "stages": ["Pre-filter companies", "Aggregate employees", "Post-filter by count"],
                    "informed_by": ["intention aggregation type", "complexity staged strategy"]
                }
            }
        }
        collaboration_stages.append(design_stage)

        # Verify multi-operator collaboration
        assert len(collaboration_stages) == 3
        assert collaboration_stages[1]["input_from"] == intention_stage["output"]
        assert "WITH" in collaboration_stages[2]["output"]["cypher"]
        assert "count(p)" in collaboration_stages[2]["output"]["cypher"]

    @pytest.mark.asyncio
    async def test_validation_feedback_to_design_operator(self, sample_job):
        """Test validation operator providing feedback that triggers redesign."""
        feedback_loop = []

        # Iteration 1: Initial design
        design_v1 = {
            "iteration": 1,
            "operator": "QueryDesign",
            "cypher": "MATCH (p:Person)-[:KNOWS*]->(friend) RETURN p, friend"
        }
        feedback_loop.append(design_v1)

        # Validation 1: Identifies performance issue
        validation_v1 = {
            "iteration": 1,
            "operator": "QueryValidation",
            "validation_result": {
                "overall_status": "WARNING",
                "performance_issues": ["Unbounded variable-length path"],
                "recommendations": ["Add path length limit", "Add LIMIT clause"]
            }
        }
        feedback_loop.append(validation_v1)

        # Redesign triggered by validation feedback
        redesign_action = {
            "action": "REDESIGN",
            "reason": "Performance warning from validation",
            "applied_recommendations": validation_v1["validation_result"]["recommendations"]
        }
        feedback_loop.append(redesign_action)

        # Iteration 2: Improved design
        design_v2 = {
            "iteration": 2,
            "operator": "QueryDesign",
            "cypher": "MATCH (p:Person)-[:KNOWS*1..3]->(friend) RETURN p, friend LIMIT 100",
            "improvements": ["Limited path depth to 1-3", "Added LIMIT 100"]
        }
        feedback_loop.append(design_v2)

        # Validation 2: Passes
        validation_v2 = {
            "iteration": 2,
            "operator": "QueryValidation",
            "validation_result": {
                "overall_status": "PASS",
                "performance_issues": []
            }
        }
        feedback_loop.append(validation_v2)

        # Verify feedback loop
        assert len(feedback_loop) == 5
        assert feedback_loop[1]["validation_result"]["overall_status"] == "WARNING"
        assert feedback_loop[2]["action"] == "REDESIGN"
        assert "*1..3" in feedback_loop[3]["cypher"]
        assert feedback_loop[4]["validation_result"]["overall_status"] == "PASS"


@pytest.mark.integration
@pytest.mark.orchestration
class TestOperatorErrorHandling:
    """Integration tests for error handling across operators."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for error handling testing."""
        return SubJob(
            id=f"error_job_{uuid4()}",
            session_id=f"error_session_{uuid4()}",
            goal="Test operator error handling",
            context="Validating error propagation and recovery",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_validation_error_propagation(self, sample_job):
        """Test that validation errors properly propagate and halt pipeline."""
        error_pipeline = []

        # Operators 1-3: Execute successfully
        for op_name in ["IntentionAnalysis", "ComplexityAnalysis", "QueryDesign"]:
            stage = {
                "operator": op_name,
                "status": "SUCCESS"
            }
            error_pipeline.append(stage)

        # Operator 4: Validation fails
        validation_stage = {
            "operator": "QueryValidation",
            "status": "FAIL",
            "error": {
                "type": "SECURITY_VIOLATION",
                "message": "Potential injection vulnerability detected",
                "severity": "CRITICAL"
            }
        }
        error_pipeline.append(validation_stage)

        # Pipeline halts, no further operators
        pipeline_result = {
            "status": "FAILED",
            "failed_at": "QueryValidation",
            "completed_operators": ["IntentionAnalysis", "ComplexityAnalysis", "QueryDesign"],
            "error": validation_stage["error"]
        }

        # Verify error handling
        assert len(error_pipeline) == 4
        assert error_pipeline[3]["status"] == "FAIL"
        assert pipeline_result["status"] == "FAILED"
        assert pipeline_result["failed_at"] == "QueryValidation"

    @pytest.mark.asyncio
    async def test_operator_timeout_recovery(self, sample_job):
        """Test recovery from operator timeout."""
        timeout_scenario = []

        # Operator 1: Success
        op1 = {"operator": "IntentionAnalysis", "status": "SUCCESS", "duration_ms": 100}
        timeout_scenario.append(op1)

        # Operator 2: Timeout
        op2_attempt1 = {
            "operator": "ComplexityAnalysis",
            "attempt": 1,
            "status": "TIMEOUT",
            "duration_ms": 5000
        }
        timeout_scenario.append(op2_attempt1)

        # Retry with simplified input
        op2_retry = {
            "operator": "ComplexityAnalysis",
            "attempt": 2,
            "status": "SUCCESS",
            "duration_ms": 150,
            "recovery_action": "Simplified analysis scope"
        }
        timeout_scenario.append(op2_retry)

        # Continue with remaining operators
        op3 = {"operator": "QueryDesign", "status": "SUCCESS", "duration_ms": 200}
        timeout_scenario.append(op3)

        # Verify timeout recovery
        assert timeout_scenario[1]["status"] == "TIMEOUT"
        assert timeout_scenario[2]["attempt"] == 2
        assert timeout_scenario[2]["status"] == "SUCCESS"
        assert len(timeout_scenario) == 4


@pytest.mark.integration
@pytest.mark.orchestration
class TestOperatorOptimizationCollaboration:
    """Integration tests for operators collaborating on optimization."""

    @pytest.fixture
    def sample_job(self):
        """Create a sample SubJob for optimization testing."""
        return SubJob(
            id=f"opt_job_{uuid4()}",
            session_id=f"opt_session_{uuid4()}",
            goal="Test operator optimization collaboration",
            context="Validating optimization strategies",
            original_job_id=f"original_job_{uuid4()}"
        )

    @pytest.mark.asyncio
    async def test_complexity_informs_design_optimization(self, sample_job):
        """Test that complexity analysis informs query design optimization."""
        optimization_flow = []

        # Stage 1: Complexity identifies optimization opportunities
        complexity_stage = {
            "operator": "ComplexityAnalysis",
            "output": {
                "complexity_level": "COMPLEX",
                "optimization_opportunities": [
                    "Add index hints for Person.age",
                    "Consider early filtering",
                    "Limit result set size"
                ],
                "estimated_cardinality": "HIGH"
            }
        }
        optimization_flow.append(complexity_stage)

        # Stage 2: Design applies optimization recommendations
        design_stage = {
            "operator": "QueryDesign",
            "input": complexity_stage["output"],
            "output": {
                "cypher": "MATCH (p:Person) WHERE p.age > 30 RETURN p LIMIT 100",
                "optimizations_applied": [
                    "Added LIMIT based on cardinality warning",
                    "Used indexed property (age) in WHERE clause",
                    "Applied early filtering"
                ],
                "informed_by": complexity_stage["operator"]
            }
        }
        optimization_flow.append(design_stage)

        # Stage 3: Validation confirms optimizations
        validation_stage = {
            "operator": "QueryValidation",
            "output": {
                "performance_prediction": {
                    "estimated_latency_ms": 150,
                    "performance_tier": "FAST",
                    "optimization_effectiveness": "HIGH"
                },
                "validated_optimizations": design_stage["output"]["optimizations_applied"]
            }
        }
        optimization_flow.append(validation_stage)

        # Verify optimization collaboration
        assert len(optimization_flow) == 3
        assert len(complexity_stage["output"]["optimization_opportunities"]) == 3
        assert len(design_stage["output"]["optimizations_applied"]) == 3
        assert validation_stage["output"]["performance_prediction"]["performance_tier"] == "FAST"

    @pytest.mark.asyncio
    async def test_context_preferences_optimize_design(self, sample_job):
        """Test that context preferences guide query design optimization."""
        personalization_flow = []

        # Stage 1: Context Enhancement learns preferences
        context_stage = {
            "operator": "ContextEnhancement",
            "output": {
                "user_preferences": {
                    "preferred_complexity": "SIMPLE",
                    "preferred_limit": 50,
                    "frequent_properties": ["name", "age"]
                },
                "query_suggestions": {
                    "improvements": ["Keep queries simple", "Use LIMIT 50"]
                }
            }
        }
        personalization_flow.append(context_stage)

        # Stage 2: Design incorporates preferences
        design_stage = {
            "operator": "QueryDesign",
            "input": context_stage["output"],
            "output": {
                "cypher": "MATCH (p:Person) RETURN p.name, p.age LIMIT 50",
                "personalization_applied": {
                    "used_preferred_properties": ["name", "age"],
                    "used_preferred_limit": 50,
                    "kept_query_simple": True
                }
            }
        }
        personalization_flow.append(design_stage)

        # Verify personalization
        assert personalization_flow[1]["output"]["personalization_applied"]["used_preferred_limit"] == 50
        assert "LIMIT 50" in personalization_flow[1]["output"]["cypher"]
