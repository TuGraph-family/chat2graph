"""
Unit tests for Context Management Tools

Tests all context management tools including ContextRetriever, PreferenceLearner, and QuerySuggester.

Author: kaichuan - Phase 2 Week 1
Date: 2025-11-25
"""

from uuid import uuid4
import time
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.service.context_tools import (
    ContextRetriever,
    PreferenceLearner,
    QuerySuggester
)
from app.core.service.query_context_service import QueryContextService


@pytest.fixture
def mock_context_service():
    """Create a mock QueryContextService for testing."""
    service = MagicMock(spec=QueryContextService)
    return service


@pytest.fixture
def sample_session_id():
    """Generate a sample session ID."""
    return f"session_{uuid4().hex}"


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID."""
    return f"user_{uuid4().hex}"


class TestContextRetriever:
    """Test ContextRetriever tool."""

    @pytest.fixture
    def context_retriever(self, mock_context_service):
        """Create ContextRetriever instance with mocked service."""
        retriever = ContextRetriever()
        retriever._context_service = mock_context_service
        return retriever

    @pytest.mark.asyncio
    async def test_retrieve_all_context(self, context_retriever, mock_context_service, sample_session_id, sample_user_id):
        """Test retrieving all context types."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session.user_id = sample_user_id
        mock_session.session_id = sample_session_id
        mock_session.is_active = True
        mock_session.last_active_at = int(time.time())
        mock_session.context_data = {"key": "value"}

        mock_context_service.get_session.return_value = mock_session
        mock_context_service.get_user_preferences.return_value = {"prefer_simple_queries": True}
        mock_context_service.get_relevant_history.return_value = []
        mock_context_service.get_session_statistics.return_value = {
            "total_queries": 10,
            "success_rate": 0.8
        }

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="all",
            max_items=5
        )

        # Verify
        result = json.loads(result_json)
        assert "session_context" in result
        assert result["session_context"]["user_id"] == sample_user_id
        assert result["session_context"]["session_id"] == sample_session_id
        assert "user_preferences" in result
        assert result["user_preferences"]["prefer_simple_queries"] is True
        assert "relevant_history" in result
        assert "session_statistics" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_retrieve_history_only(self, context_retriever, mock_context_service, sample_session_id):
        """Test retrieving only history context."""
        # Setup mock history
        mock_query = MagicMock()
        mock_query.query_text = "Find Person with age > 25"
        mock_query.query_cypher = "MATCH (p:Person) WHERE p.age > 25 RETURN p"
        mock_query.success = True
        mock_query.latency_ms = 150
        mock_query.created_at = int(time.time())

        mock_context_service.get_relevant_history.return_value = [mock_query]

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="history",
            max_items=5
        )

        # Verify
        result = json.loads(result_json)
        assert "relevant_history" in result
        assert len(result["relevant_history"]) == 1
        assert result["relevant_history"][0]["query_text"] == "Find Person with age > 25"
        assert result["relevant_history"][0]["success"] is True

        # Should not retrieve other context types
        assert "session_context" not in result or result.get("session_context") is None

    @pytest.mark.asyncio
    async def test_retrieve_preferences_only(self, context_retriever, mock_context_service, sample_session_id, sample_user_id):
        """Test retrieving only preferences context."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.user_id = sample_user_id
        mock_session.session_id = sample_session_id
        mock_session.is_active = True
        mock_session.last_active_at = int(time.time())
        mock_session.context_data = {}

        mock_context_service.get_session.return_value = mock_session
        mock_context_service.get_user_preferences.return_value = {
            "preferred_complexity": "simple",
            "acceptable_latency_ms": 200
        }

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="preferences",
            max_items=5
        )

        # Verify
        result = json.loads(result_json)
        assert "session_context" in result
        assert "user_preferences" in result
        assert result["user_preferences"]["preferred_complexity"] == "simple"
        assert result["user_preferences"]["acceptable_latency_ms"] == 200

    @pytest.mark.asyncio
    async def test_retrieve_statistics_only(self, context_retriever, mock_context_service, sample_session_id):
        """Test retrieving only statistics context."""
        # Setup mock statistics
        mock_context_service.get_session_statistics.return_value = {
            "total_queries": 25,
            "success_rate": 0.92,
            "avg_latency_ms": 180.5
        }

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="statistics",
            max_items=5
        )

        # Verify
        result = json.loads(result_json)
        assert "session_statistics" in result
        assert result["session_statistics"]["total_queries"] == 25
        assert result["session_statistics"]["success_rate"] == 0.92

    @pytest.mark.asyncio
    async def test_retrieve_with_error(self, context_retriever, mock_context_service, sample_session_id):
        """Test error handling in context retrieval."""
        # Setup mock to raise exception
        mock_context_service.get_session.side_effect = Exception("Database error")

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="all",
            max_items=5
        )

        # Verify error handling
        result = json.loads(result_json)
        assert "error" in result
        assert "Database error" in result["error"]
        assert "recommendations" in result
        assert "请检查 session_id 是否有效" in result["recommendations"]

    @pytest.mark.asyncio
    async def test_generate_recommendations_low_success_rate(self, context_retriever, mock_context_service, sample_session_id, sample_user_id):
        """Test recommendation generation for low success rate."""
        # Setup mock with low success rate
        mock_session = MagicMock()
        mock_session.user_id = sample_user_id
        mock_session.session_id = sample_session_id
        mock_session.is_active = True
        mock_session.last_active_at = int(time.time())
        mock_session.context_data = {}

        mock_context_service.get_session.return_value = mock_session
        mock_context_service.get_user_preferences.return_value = {}
        mock_context_service.get_relevant_history.return_value = []
        mock_context_service.get_session_statistics.return_value = {
            "total_queries": 10,
            "success_rate": 0.3  # Low success rate
        }

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="all",
            max_items=5
        )

        # Verify
        result = json.loads(result_json)
        assert "recommendations" in result
        # Should suggest simplifying queries
        assert any("成功率较低" in rec for rec in result["recommendations"])

    @pytest.mark.asyncio
    async def test_generate_recommendations_with_similar_queries(self, context_retriever, mock_context_service, sample_session_id, sample_user_id):
        """Test recommendation generation with similar successful queries."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.user_id = sample_user_id
        mock_session.session_id = sample_session_id
        mock_session.is_active = True
        mock_session.last_active_at = int(time.time())
        mock_session.context_data = {}

        # Mock successful similar queries - use dict instead of MagicMock for JSON serialization
        mock_query1 = MagicMock()
        mock_query1.query_text = "Find Person with age > 25"
        mock_query1.query_cypher = "MATCH (p:Person) WHERE p.age > 25 RETURN p"
        mock_query1.success = True
        mock_query1.latency_ms = 150
        mock_query1.created_at = int(time.time())

        mock_query2 = MagicMock()
        mock_query2.query_text = "Find Person with name John"
        mock_query2.query_cypher = "MATCH (p:Person) WHERE p.name = 'John' RETURN p"
        mock_query2.success = True
        mock_query2.latency_ms = 120
        mock_query2.created_at = int(time.time())

        mock_context_service.get_session.return_value = mock_session
        mock_context_service.get_user_preferences.return_value = {}
        mock_context_service.get_relevant_history.return_value = [mock_query1, mock_query2]
        mock_context_service.get_session_statistics.return_value = {"success_rate": 0.8}

        # Execute
        result_json = await context_retriever.retrieve_context(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            context_type="all",
            max_items=5
        )

        # Verify
        result = json.loads(result_json)
        assert "recommendations" in result
        # Should mention similar successful queries
        assert any("相似的成功查询" in rec for rec in result["recommendations"])


class TestPreferenceLearner:
    """Test PreferenceLearner tool."""

    @pytest.fixture
    def preference_learner(self, mock_context_service):
        """Create PreferenceLearner instance with mocked service."""
        learner = PreferenceLearner()
        learner._context_service = mock_context_service
        return learner

    @pytest.mark.asyncio
    async def test_learn_preferences_with_history(self, preference_learner, mock_context_service, sample_session_id):
        """Test learning preferences from query history."""
        # Setup mock history with complexity and pattern data
        mock_queries = []
        for i in range(10):
            query = MagicMock()
            query.success = True
            query.complexity_analysis = {"complexity_level": "simple"}
            query.path_patterns = {"patterns": [{"pattern_type": "DIRECT"}]}
            query.query_intention = {"object_vertex_types": ["Person", "Company"]}
            query.result_count = 50 + i * 10
            query.latency_ms = 100 + i * 20
            mock_queries.append(query)

        mock_context_service.get_session_history.return_value = mock_queries
        mock_context_service.update_user_preferences.return_value = None

        # Execute
        result_json = await preference_learner.learn_preferences(
            session_id=sample_session_id,
            learning_mode="auto"
        )

        # Verify
        result = json.loads(result_json)
        assert "preferences" in result
        assert "confidence" in result
        assert "learning_summary" in result
        assert "preference_updates" in result

        # Check learned preferences
        preferences = result["preferences"]
        assert "preferred_complexity" in preferences
        assert preferences["preferred_complexity"] == "simple"

        # Check learning summary
        summary = result["learning_summary"]
        assert summary["queries_analyzed"] == 10
        assert summary["preferences_learned"] > 0

    @pytest.mark.asyncio
    async def test_learn_preferences_without_history(self, preference_learner, mock_context_service, sample_session_id):
        """Test learning preferences with no query history."""
        # Setup mock with empty history
        mock_context_service.get_session_history.return_value = []

        # Execute
        result_json = await preference_learner.learn_preferences(
            session_id=sample_session_id,
            learning_mode="auto"
        )

        # Verify
        result = json.loads(result_json)
        assert "preferences" in result
        assert len(result["preferences"]) == 0
        assert "recommendations" in result
        assert any("更多查询历史" in rec for rec in result["recommendations"])

    @pytest.mark.asyncio
    async def test_learn_complexity_preference(self, preference_learner, mock_context_service, sample_session_id):
        """Test learning complexity preference."""
        # Setup mock history with varying complexity
        mock_queries = []
        for i in range(5):
            query = MagicMock()
            query.success = True
            query.complexity_analysis = {"complexity_level": "simple"}
            query.path_patterns = None
            query.query_intention = None
            query.result_count = None
            query.latency_ms = None
            mock_queries.append(query)

        # Add 3 moderate complexity queries
        for i in range(3):
            query = MagicMock()
            query.success = True
            query.complexity_analysis = {"complexity_level": "moderate"}
            query.path_patterns = None
            query.query_intention = None
            query.result_count = None
            query.latency_ms = None
            mock_queries.append(query)

        mock_context_service.get_session_history.return_value = mock_queries
        mock_context_service.update_user_preferences.return_value = None

        # Execute
        result_json = await preference_learner.learn_preferences(
            session_id=sample_session_id,
            learning_mode="auto"
        )

        # Verify - should prefer "simple" (5 vs 3)
        result = json.loads(result_json)
        preferences = result["preferences"]
        assert "preferred_complexity" in preferences
        assert preferences["preferred_complexity"] == "simple"

    @pytest.mark.asyncio
    async def test_learn_pattern_preference(self, preference_learner, mock_context_service, sample_session_id):
        """Test learning query pattern preference."""
        # Setup mock history with different patterns
        mock_queries = []
        patterns_list = ["DIRECT", "DIRECT", "DIRECT", "MULTI_HOP", "AGGREGATION"]

        for pattern_type in patterns_list:
            query = MagicMock()
            query.success = True
            query.complexity_analysis = None
            query.path_patterns = {"patterns": [{"pattern_type": pattern_type}]}
            query.query_intention = None
            query.result_count = None
            query.latency_ms = None
            mock_queries.append(query)

        mock_context_service.get_session_history.return_value = mock_queries
        mock_context_service.update_user_preferences.return_value = None

        # Execute
        result_json = await preference_learner.learn_preferences(
            session_id=sample_session_id,
            learning_mode="auto"
        )

        # Verify - DIRECT should be most common
        result = json.loads(result_json)
        preferences = result["preferences"]
        assert "preferred_patterns" in preferences
        assert "DIRECT" in preferences["preferred_patterns"]

    @pytest.mark.asyncio
    async def test_learn_performance_preference(self, preference_learner, mock_context_service, sample_session_id):
        """Test learning performance preference."""
        # Setup mock history with latencies
        mock_queries = []
        latencies = [50, 100, 150, 200, 250, 300, 350, 400]

        for latency in latencies:
            query = MagicMock()
            query.success = True
            query.complexity_analysis = None
            query.path_patterns = None
            query.query_intention = None
            query.result_count = None
            query.latency_ms = latency
            mock_queries.append(query)

        mock_context_service.get_session_history.return_value = mock_queries
        mock_context_service.update_user_preferences.return_value = None

        # Execute
        result_json = await preference_learner.learn_preferences(
            session_id=sample_session_id,
            learning_mode="auto"
        )

        # Verify - should learn acceptable latency (75th percentile)
        result = json.loads(result_json)
        preferences = result["preferences"]
        assert "acceptable_latency_ms" in preferences
        # 75th percentile of [50, 100, 150, 200, 250, 300, 350, 400] is at index 6 (int(8 * 0.75)) = 350
        assert preferences["acceptable_latency_ms"] == 350

    @pytest.mark.asyncio
    async def test_learn_preferences_error_handling(self, preference_learner, mock_context_service, sample_session_id):
        """Test error handling in preference learning."""
        # Setup mock to raise exception
        mock_context_service.get_session_history.side_effect = Exception("Service error")

        # Execute
        result_json = await preference_learner.learn_preferences(
            session_id=sample_session_id,
            learning_mode="auto"
        )

        # Verify error handling
        result = json.loads(result_json)
        assert "error" in result
        assert "Service error" in result["error"]
        assert result["preferences"] == {}


class TestQuerySuggester:
    """Test QuerySuggester tool."""

    @pytest.fixture
    def query_suggester(self, mock_context_service):
        """Create QuerySuggester instance with mocked service."""
        suggester = QuerySuggester()
        suggester._context_service = mock_context_service
        return suggester

    @pytest.mark.asyncio
    async def test_suggest_all_types(self, query_suggester, mock_context_service, sample_session_id):
        """Test suggesting all types of query improvements."""
        # Setup mocks
        mock_context_service.get_user_preferences.return_value = {
            "acceptable_latency_ms": 200
        }
        mock_context_service.get_relevant_history.return_value = []

        # Execute
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            suggestion_type="all"
        )

        # Verify
        result = json.loads(result_json)
        assert "suggestions" in result
        assert "improvements" in result["suggestions"]
        assert "alternatives" in result["suggestions"]
        assert "completions" in result["suggestions"]
        assert "corrections" in result["suggestions"]
        assert "confidence" in result
        assert "rationale" in result

    @pytest.mark.asyncio
    async def test_suggest_improvements_with_limit(self, query_suggester, mock_context_service, sample_session_id):
        """Test suggesting improvements based on latency preference."""
        # Setup mocks with latency preference
        mock_context_service.get_user_preferences.return_value = {
            "acceptable_latency_ms": 200
        }
        mock_context_service.get_relevant_history.return_value = []

        # Execute
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            suggestion_type="improvements"
        )

        # Verify
        result = json.loads(result_json)
        improvements = result["suggestions"]["improvements"]
        assert len(improvements) > 0
        # Should suggest adding LIMIT based on latency preference
        assert any("LIMIT" in improvement for improvement in improvements)

    @pytest.mark.asyncio
    async def test_suggest_alternatives_from_history(self, query_suggester, mock_context_service, sample_session_id):
        """Test suggesting alternatives based on similar queries."""
        # Setup mock history with successful queries
        mock_query1 = MagicMock()
        mock_query1.success = True
        mock_query1.query_cypher = "MATCH (p:Person) WHERE p.age > 25 RETURN p"
        mock_query1.latency_ms = 150

        mock_query2 = MagicMock()
        mock_query2.success = True
        mock_query2.query_cypher = "MATCH (p:Person) RETURN p LIMIT 10"
        mock_query2.latency_ms = 80

        mock_context_service.get_user_preferences.return_value = {}
        mock_context_service.get_relevant_history.return_value = [mock_query1, mock_query2]

        # Execute
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            suggestion_type="alternatives"
        )

        # Verify
        result = json.loads(result_json)
        alternatives = result["suggestions"]["alternatives"]
        assert len(alternatives) >= 2
        # Should include the successful queries as alternatives
        assert any("Person" in alt for alt in alternatives)

    @pytest.mark.asyncio
    async def test_suggest_completions_with_preferences(self, query_suggester, mock_context_service, sample_session_id):
        """Test suggesting query completions based on preferences."""
        # Setup mocks with vertex type preferences
        mock_context_service.get_user_preferences.return_value = {
            "preferred_vertex_types": ["Person", "Company", "Product"]
        }
        mock_context_service.get_relevant_history.return_value = []

        # Execute with short query
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find",  # Short query should trigger completions
            suggestion_type="completions"
        )

        # Verify
        result = json.loads(result_json)
        completions = result["suggestions"]["completions"]
        assert len(completions) > 0
        # Should suggest completions with preferred vertex types
        assert any("Person" in completion or "Company" in completion for completion in completions)

    @pytest.mark.asyncio
    async def test_suggest_corrections_syntax_error(self, query_suggester, mock_context_service, sample_session_id):
        """Test suggesting corrections for syntax errors."""
        # Setup mocks
        mock_context_service.get_user_preferences.return_value = {}
        mock_context_service.get_relevant_history.return_value = []

        # Execute with unbalanced parentheses
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find Person (with age",  # Unbalanced parentheses
            suggestion_type="corrections"
        )

        # Verify
        result = json.loads(result_json)
        corrections = result["suggestions"]["corrections"]
        assert len(corrections) > 0
        # Should detect parentheses mismatch
        assert any("括号" in correction for correction in corrections)

    @pytest.mark.asyncio
    async def test_suggest_corrections_from_failures(self, query_suggester, mock_context_service, sample_session_id):
        """Test suggesting corrections based on historical failures."""
        # Setup mock history with failed query
        mock_failed_query = MagicMock()
        mock_failed_query.success = False
        mock_failed_query.error_message = "Syntax error: unexpected token"

        mock_context_service.get_user_preferences.return_value = {}
        mock_context_service.get_relevant_history.return_value = [mock_failed_query]

        # Execute
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            suggestion_type="corrections"
        )

        # Verify
        result = json.loads(result_json)
        corrections = result["suggestions"]["corrections"]
        # Should mention avoiding similar errors
        assert any("避免类似错误" in correction for correction in corrections)

    @pytest.mark.asyncio
    async def test_suggest_error_handling(self, query_suggester, mock_context_service, sample_session_id):
        """Test error handling in query suggestion."""
        # Setup mock to raise exception
        mock_context_service.get_user_preferences.side_effect = Exception("Service error")

        # Execute
        result_json = await query_suggester.suggest_queries(
            session_id=sample_session_id,
            current_query="Find Person nodes",
            suggestion_type="all"
        )

        # Verify error handling
        result = json.loads(result_json)
        assert "error" in result
        assert "Service error" in result["error"]
        assert "suggestions" in result
