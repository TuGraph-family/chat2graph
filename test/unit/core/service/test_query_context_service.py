"""
Unit tests for QueryContextService

Tests all service methods, session management, context operations, and history tracking.

Author: kaichuan - Phase 2 Week 1
Date: 2025-11-25
"""

from uuid import uuid4
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all DO classes BEFORE importing Do to ensure they are registered with Do.metadata
from app.core.dal.do.query_session_do import QuerySessionDo
from app.core.dal.do.query_history_do import QueryHistoryDo
from app.core.dal.do.query_feedback_do import QueryFeedbackDo
from app.core.dal.do.query_pattern_do import QueryPatternDo
from app.core.dal.database import Do
from app.core.service.query_context_service import QueryContextService


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """Create an isolated test database for testing."""
    from app.core.dal import database
    from app.core.dal.dao.dao import Dao
    from app.core.common.singleton import Singleton
    import os
    import tempfile

    # Clear Singleton caches FIRST, before any patching
    if hasattr(Dao, '_instances'):
        Dao._instances.clear()
    if hasattr(Singleton, '_instances'):
        Singleton._instances.clear()

    # Use unique filename with timestamp to avoid conflicts
    temp_db_path = tempfile.mktemp(
        suffix=f"_{uuid4().hex}.sqlite",
        prefix="test_db_"
    )
    test_engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)

    # Create all tables
    # Index names have been fixed to use table-specific prefixes (e.g., idx_query_session_session_id)
    # This ensures globally unique index names as required by SQLite
    Do.metadata.create_all(test_engine)

    TestSessionMaker = sessionmaker(bind=test_engine)

    # Monkey-patch DbSession in ALL locations BEFORE creating service
    monkeypatch.setattr("app.core.dal.database.DbSession", TestSessionMaker)
    monkeypatch.setattr("app.core.dal.dao.dao.DbSession", TestSessionMaker)
    monkeypatch.setattr("app.core.service.query_context_service.DbSession", TestSessionMaker)
    monkeypatch.setattr(database, "engine", test_engine)

    test_session = TestSessionMaker()
    yield test_session
    test_session.close()

    # Clean up
    Do.metadata.drop_all(test_engine)
    test_engine.dispose()

    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture
def context_service(db_session):
    """Create QueryContextService instance with test database."""
    # Clear singleton cache again to ensure fresh service with test database
    from app.core.common.singleton import Singleton
    if hasattr(Singleton, '_instances'):
        Singleton._instances.clear()

    return QueryContextService()


@pytest.fixture
def sample_user_id():
    """Generate sample user ID for testing."""
    return f"user_{uuid4()}"


class TestQueryContextServiceSessionManagement:
    """Test session creation and management."""

    def test_create_session_with_auto_id(self, context_service, sample_user_id):
        """Test creating session with auto-generated session_id."""
        session = context_service.create_session(user_id=sample_user_id)

        assert session is not None
        assert session.user_id == sample_user_id
        assert session.session_id is not None
        assert session.session_id.startswith("session_")
        assert session.is_active is True
        assert session.context_data == {}
        assert session.created_at is not None

    def test_create_session_with_custom_id(self, context_service, sample_user_id):
        """Test creating session with custom session_id."""
        custom_session_id = f"custom_session_{uuid4()}"
        session = context_service.create_session(
            user_id=sample_user_id,
            session_id=custom_session_id
        )

        assert session.session_id == custom_session_id
        assert session.user_id == sample_user_id

    def test_create_session_with_initial_context(self, context_service, sample_user_id):
        """Test creating session with initial context data."""
        initial_context = {
            "user_preferences": {"language": "en", "theme": "dark"},
            "metadata": {"source": "web"}
        }

        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context=initial_context
        )

        assert session.context_data == initial_context
        assert session.context_data["user_preferences"]["language"] == "en"

    def test_get_session_success(self, context_service, sample_user_id):
        """Test retrieving existing session."""
        created = context_service.create_session(user_id=sample_user_id)
        retrieved = context_service.get_session(created.session_id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.session_id == created.session_id

    def test_get_session_not_found(self, context_service):
        """Test retrieving non-existent session returns None."""
        result = context_service.get_session("nonexistent_session_id")
        assert result is None

    def test_get_or_create_session_existing(self, context_service, sample_user_id):
        """Test get_or_create returns existing session."""
        session_id = f"session_{uuid4()}"
        created = context_service.create_session(
            user_id=sample_user_id,
            session_id=session_id
        )

        retrieved = context_service.get_or_create_session(
            user_id=sample_user_id,
            session_id=session_id
        )

        assert retrieved.id == created.id
        assert retrieved.session_id == session_id

    def test_get_or_create_session_creates_new(self, context_service, sample_user_id):
        """Test get_or_create creates new session when not found."""
        new_session = context_service.get_or_create_session(
            user_id=sample_user_id,
            session_id=None
        )

        assert new_session is not None
        assert new_session.user_id == sample_user_id
        assert new_session.session_id is not None

    def test_deactivate_session(self, context_service, sample_user_id):
        """Test deactivating a session."""
        session = context_service.create_session(user_id=sample_user_id)
        assert session.is_active is True

        deactivated = context_service.deactivate_session(session.session_id)

        assert deactivated.is_active is False
        assert deactivated.id == session.id

    def test_get_active_sessions(self, context_service, sample_user_id):
        """Test retrieving all active sessions for a user."""
        # Create 3 active sessions
        session1 = context_service.create_session(user_id=sample_user_id)
        session2 = context_service.create_session(user_id=sample_user_id)
        session3 = context_service.create_session(user_id=sample_user_id)

        # Deactivate one
        context_service.deactivate_session(session2.session_id)

        # Create session for different user
        other_user = f"user_{uuid4()}"
        context_service.create_session(user_id=other_user)

        active_sessions = context_service.get_active_sessions(sample_user_id)

        assert len(active_sessions) == 2
        session_ids = [s.session_id for s in active_sessions]
        assert session1.session_id in session_ids
        assert session3.session_id in session_ids
        assert session2.session_id not in session_ids


class TestQueryContextServiceContextManagement:
    """Test context data management operations."""

    def test_update_context_success(self, context_service, sample_user_id):
        """Test updating session context."""
        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context={"key1": "value1"}
        )

        updated = context_service.update_context(
            session_id=session.session_id,
            context_updates={"key2": "value2", "key3": "value3"}
        )

        assert updated.context_data["key1"] == "value1"  # Original preserved
        assert updated.context_data["key2"] == "value2"  # New added
        assert updated.context_data["key3"] == "value3"  # New added

    def test_update_context_overwrites_existing(self, context_service, sample_user_id):
        """Test that update_context overwrites existing keys."""
        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context={"key1": "old_value"}
        )

        updated = context_service.update_context(
            session_id=session.session_id,
            context_updates={"key1": "new_value"}
        )

        assert updated.context_data["key1"] == "new_value"

    def test_update_context_nonexistent_session(self, context_service):
        """Test updating context for non-existent session raises error."""
        with pytest.raises(ValueError, match="Session .* not found"):
            context_service.update_context(
                session_id="nonexistent_session",
                context_updates={"key": "value"}
            )

    def test_get_user_preferences_success(self, context_service, sample_user_id):
        """Test retrieving user preferences from context."""
        preferences = {
            "language": "en",
            "theme": "dark",
            "notifications": True
        }

        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context={"user_preferences": preferences}
        )

        retrieved_prefs = context_service.get_user_preferences(session.session_id)

        assert retrieved_prefs == preferences
        assert retrieved_prefs["language"] == "en"

    def test_get_user_preferences_empty(self, context_service, sample_user_id):
        """Test getting preferences when none exist."""
        session = context_service.create_session(user_id=sample_user_id)
        preferences = context_service.get_user_preferences(session.session_id)

        assert preferences == {}

    def test_get_user_preferences_nonexistent_session(self, context_service):
        """Test getting preferences for non-existent session returns empty dict."""
        preferences = context_service.get_user_preferences("nonexistent_session")
        assert preferences == {}

    def test_update_user_preferences(self, context_service, sample_user_id):
        """Test updating user preferences."""
        session = context_service.create_session(user_id=sample_user_id)

        new_preferences = {
            "language": "zh",
            "theme": "light"
        }

        updated = context_service.update_user_preferences(
            session_id=session.session_id,
            preferences=new_preferences
        )

        assert updated.context_data["user_preferences"] == new_preferences

        # Verify retrieval
        retrieved = context_service.get_user_preferences(session.session_id)
        assert retrieved == new_preferences


class TestQueryContextServiceHistoryManagement:
    """Test query history management operations."""

    def test_save_query_minimal(self, context_service, sample_user_id):
        """Test saving query with minimal required fields."""
        session = context_service.create_session(user_id=sample_user_id)

        query = context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text="Find Person nodes",
            success=True
        )

        assert query is not None
        assert query.session_id == session.session_id
        assert query.user_id == sample_user_id
        assert query.query_text == "Find Person nodes"
        assert query.success is True
        assert query.created_at is not None

    def test_save_query_complete(self, context_service, sample_user_id):
        """Test saving query with all fields."""
        session = context_service.create_session(user_id=sample_user_id)

        query_data = {
            "session_id": session.session_id,
            "user_id": sample_user_id,
            "query_text": "Find Person with age > 25",
            "query_cypher": "MATCH (p:Person) WHERE p.age > 25 RETURN p",
            "query_intention": {
                "action": "find",
                "object_vertex_types": ["Person"],
                "conditions": [{"field": "age", "operator": ">", "value": 25}]
            },
            "complexity_analysis": {
                "complexity_level": "SIMPLE",
                "complexity_score": 0.3
            },
            "path_patterns": {
                "pattern_type": "VERTEX_QUERY",
                "depth": 0
            },
            "validation_result": {
                "schema_validation": "PASS",
                "semantic_validation": "PASS"
            },
            "result_data": {"records": [{"name": "Alice", "age": 30}]},
            "result_count": 1,
            "success": True,
            "latency_ms": 150,
            "token_usage": {"total_tokens": 1250},
            "agents_executed": ["query_intention_analyzer", "query_designer"]
        }

        query = context_service.save_query(**query_data)

        assert query.query_cypher is not None
        assert query.query_intention is not None
        assert query.complexity_analysis["complexity_level"] == "SIMPLE"
        assert query.result_count == 1
        assert query.latency_ms == 150
        assert len(query.agents_executed) == 2

    def test_save_query_failed(self, context_service, sample_user_id):
        """Test saving failed query with error message."""
        session = context_service.create_session(user_id=sample_user_id)

        query = context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text="Invalid query",
            success=False,
            error_message="Syntax error: unknown property"
        )

        assert query.success is False
        assert query.error_message is not None
        assert "Syntax error" in query.error_message

    def test_get_session_history(self, context_service, sample_user_id):
        """Test retrieving session query history."""
        session = context_service.create_session(user_id=sample_user_id)

        # Create multiple queries
        for i in range(5):
            context_service.save_query(
                session_id=session.session_id,
                user_id=sample_user_id,
                query_text=f"Query {i}",
                success=True
            )
            time.sleep(0.01)  # Ensure different timestamps

        history = context_service.get_session_history(session.session_id, limit=3)

        assert len(history) == 3
        # Should be ordered by most recent first
        assert "Query" in history[0].query_text

    def test_get_session_history_empty(self, context_service, sample_user_id):
        """Test getting history for session with no queries."""
        session = context_service.create_session(user_id=sample_user_id)
        history = context_service.get_session_history(session.session_id)

        assert history == []

    def test_get_relevant_history(self, context_service, sample_user_id):
        """Test finding similar queries."""
        session = context_service.create_session(user_id=sample_user_id)

        # Create queries with similar text
        context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text="Find Person nodes with name John",
            success=True
        )
        context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text="Find all Person vertices named Alice",
            success=True
        )
        context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text="Get Company nodes",
            success=True
        )

        # Search for similar queries
        # Note: find_similar_queries uses AND logic - all search terms must match
        # Searching for "Find Person" will match both queries containing these words
        similar = context_service.get_relevant_history(
            query_text="Find Person",
            limit=5
        )

        # Should find queries containing both "Find" and "Person"
        assert len(similar) == 2
        assert all("Find" in q.query_text and "Person" in q.query_text for q in similar)

    def test_get_session_statistics_with_data(self, context_service, sample_user_id):
        """Test getting session statistics with query data."""
        session = context_service.create_session(user_id=sample_user_id)

        # Create 7 successful and 3 failed queries
        for i in range(7):
            context_service.save_query(
                session_id=session.session_id,
                user_id=sample_user_id,
                query_text=f"Success {i}",
                success=True,
                latency_ms=100 + i * 10
            )

        for i in range(3):
            context_service.save_query(
                session_id=session.session_id,
                user_id=sample_user_id,
                query_text=f"Failed {i}",
                success=False
            )

        stats = context_service.get_session_statistics(session.session_id)

        assert stats["total_queries"] == 10
        assert stats["successful_queries"] == 7
        assert abs(stats["success_rate"] - 0.7) < 0.01
        assert stats["average_latency_ms"] is not None
        assert 100 <= stats["average_latency_ms"] <= 200

    def test_get_session_statistics_empty(self, context_service, sample_user_id):
        """Test getting statistics for session with no queries."""
        session = context_service.create_session(user_id=sample_user_id)
        stats = context_service.get_session_statistics(session.session_id)

        assert stats["total_queries"] == 0
        assert stats["successful_queries"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["average_latency_ms"] is None

    def test_get_session_statistics_no_latency(self, context_service, sample_user_id):
        """Test statistics when queries have no latency data."""
        session = context_service.create_session(user_id=sample_user_id)

        for i in range(3):
            context_service.save_query(
                session_id=session.session_id,
                user_id=sample_user_id,
                query_text=f"Query {i}",
                success=True
                # No latency_ms
            )

        stats = context_service.get_session_statistics(session.session_id)

        assert stats["total_queries"] == 3
        assert stats["successful_queries"] == 3
        assert stats["average_latency_ms"] is None


class TestQueryContextServiceIntegration:
    """Test integrated workflows combining multiple operations."""

    def test_complete_session_workflow(self, context_service, sample_user_id):
        """Test complete workflow: create session, update context, save queries, get stats."""
        # 1. Create session
        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context={"source": "web"}
        )

        # 2. Update user preferences
        context_service.update_user_preferences(
            session_id=session.session_id,
            preferences={"language": "en", "theme": "dark"}
        )

        # 3. Save some queries
        for i in range(5):
            context_service.save_query(
                session_id=session.session_id,
                user_id=sample_user_id,
                query_text=f"Query {i}",
                success=True,
                latency_ms=100
            )

        # 4. Get statistics
        stats = context_service.get_session_statistics(session.session_id)
        assert stats["total_queries"] == 5
        assert stats["success_rate"] == 1.0

        # 5. Get history
        history = context_service.get_session_history(session.session_id)
        assert len(history) == 5

        # 6. Get preferences
        prefs = context_service.get_user_preferences(session.session_id)
        assert prefs["language"] == "en"

        # 7. Deactivate session
        deactivated = context_service.deactivate_session(session.session_id)
        assert deactivated.is_active is False

    def test_multiple_sessions_same_user(self, context_service, sample_user_id):
        """Test managing multiple sessions for same user."""
        # Create 3 sessions
        session1 = context_service.create_session(user_id=sample_user_id)
        session2 = context_service.create_session(user_id=sample_user_id)
        session3 = context_service.create_session(user_id=sample_user_id)

        # Save queries in different sessions
        context_service.save_query(
            session_id=session1.session_id,
            user_id=sample_user_id,
            query_text="Session 1 Query",
            success=True
        )
        context_service.save_query(
            session_id=session2.session_id,
            user_id=sample_user_id,
            query_text="Session 2 Query",
            success=True
        )

        # Verify session isolation
        history1 = context_service.get_session_history(session1.session_id)
        history2 = context_service.get_session_history(session2.session_id)
        history3 = context_service.get_session_history(session3.session_id)

        assert len(history1) == 1
        assert len(history2) == 1
        assert len(history3) == 0

        # Verify all sessions are active
        active_sessions = context_service.get_active_sessions(sample_user_id)
        assert len(active_sessions) == 3

    def test_context_persistence_across_operations(self, context_service, sample_user_id):
        """Test that context persists across multiple operations."""
        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context={"key1": "value1"}
        )

        # Update context multiple times
        context_service.update_context(
            session_id=session.session_id,
            context_updates={"key2": "value2"}
        )
        context_service.update_context(
            session_id=session.session_id,
            context_updates={"key3": "value3"}
        )

        # Retrieve and verify all context preserved
        retrieved = context_service.get_session(session.session_id)
        assert retrieved.context_data["key1"] == "value1"
        assert retrieved.context_data["key2"] == "value2"
        assert retrieved.context_data["key3"] == "value3"


class TestQueryContextServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_session_with_empty_context(self, context_service, sample_user_id):
        """Test session with empty context data."""
        session = context_service.create_session(
            user_id=sample_user_id,
            initial_context={}
        )

        assert session.context_data == {}

    def test_update_context_with_nested_data(self, context_service, sample_user_id):
        """Test updating context with deeply nested structures."""
        session = context_service.create_session(user_id=sample_user_id)

        complex_context = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [1, 2, 3, 4, 5]
                    }
                }
            }
        }

        updated = context_service.update_context(
            session_id=session.session_id,
            context_updates=complex_context
        )

        assert updated.context_data["level1"]["level2"]["level3"]["data"] == [1, 2, 3, 4, 5]

    def test_save_query_with_large_result_data(self, context_service, sample_user_id):
        """Test saving query with large result dataset."""
        session = context_service.create_session(user_id=sample_user_id)

        large_result = {
            f"record_{i}": {"id": i, "data": f"value_{i}"}
            for i in range(100)
        }

        query = context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text="Large result query",
            result_data=large_result,
            result_count=100,
            success=True
        )

        assert query.result_data is not None
        assert query.result_count == 100

    def test_get_session_history_with_limit(self, context_service, sample_user_id):
        """Test history retrieval respects limit parameter."""
        session = context_service.create_session(user_id=sample_user_id)

        # Create 20 queries
        for i in range(20):
            context_service.save_query(
                session_id=session.session_id,
                user_id=sample_user_id,
                query_text=f"Query {i}",
                success=True
            )
            time.sleep(0.01)

        # Test different limits
        history_5 = context_service.get_session_history(session.session_id, limit=5)
        history_10 = context_service.get_session_history(session.session_id, limit=10)

        assert len(history_5) == 5
        assert len(history_10) == 10

    def test_concurrent_session_updates(self, context_service, sample_user_id):
        """Test multiple rapid updates to same session."""
        session = context_service.create_session(user_id=sample_user_id)

        # Rapid sequential updates
        for i in range(10):
            context_service.update_context(
                session_id=session.session_id,
                context_updates={f"key_{i}": f"value_{i}"}
            )

        retrieved = context_service.get_session(session.session_id)

        # All updates should be preserved
        for i in range(10):
            assert retrieved.context_data[f"key_{i}"] == f"value_{i}"

    def test_query_with_special_characters(self, context_service, sample_user_id):
        """Test saving query with special characters."""
        session = context_service.create_session(user_id=sample_user_id)

        special_query = "Find nodes where name CONTAINS \"John's\"; DROP TABLE;"

        query = context_service.save_query(
            session_id=session.session_id,
            user_id=sample_user_id,
            query_text=special_query,
            success=True
        )

        assert query.query_text == special_query
