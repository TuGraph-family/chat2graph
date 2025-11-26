"""
Unit tests for QueryHistoryDao

Tests all CRUD operations, query methods, and business logic for QueryHistoryDao.

Author: kaichuan - Phase 2 Week 1
Date: 2025-11-25
"""

import time
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.dal.database import Do
from app.core.dal.do.query_history_do import QueryHistoryDo
from app.core.dal.dao.query_history_dao import QueryHistoryDao


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """Create an in-memory SQLite database for testing."""
    from app.core.dal.do.query_history_do import QueryHistoryDo
    from app.core.dal import database
    from app.core.dal.dao.dao import Dao
    import os
    import tempfile

    temp_db_path = tempfile.mktemp(suffix=".sqlite", prefix="test_db_")
    test_engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)

    Do.metadata.create_all(test_engine)
    TestSessionMaker = sessionmaker(bind=test_engine)

    monkeypatch.setattr("app.core.dal.database.DbSession", TestSessionMaker)
    monkeypatch.setattr("app.core.dal.dao.dao.DbSession", TestSessionMaker)
    monkeypatch.setattr(database, "engine", test_engine)

    if hasattr(Dao, '_instances'):
        Dao._instances.clear()

    test_session = TestSessionMaker()
    yield test_session
    test_session.close()

    Do.metadata.drop_all(test_engine)
    test_engine.dispose()

    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture
def history_dao(db_session):
    """Create QueryHistoryDao instance with test database session."""
    return QueryHistoryDao(db_session)


@pytest.fixture
def sample_history_data():
    """Generate sample query history data for testing."""
    return {
        "session_id": f"session_{uuid4()}",
        "user_id": f"user_{uuid4()}",
        "query_text": "Find all Person nodes with age > 25",
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
        "success": True,
        "result_count": 42,
        "latency_ms": 150
    }


class TestQueryHistoryDaoCreate:
    """Test create operations."""

    def test_create_history_success(self, history_dao, sample_history_data):
        """Test successful history creation."""
        history = history_dao.create(**sample_history_data)

        assert history is not None
        assert history.id is not None
        assert history.session_id == sample_history_data["session_id"]
        assert history.user_id == sample_history_data["user_id"]
        assert history.query_text == sample_history_data["query_text"]
        assert history.success is True
        assert history.created_at is not None

    def test_create_with_minimal_data(self, history_dao):
        """Test creating history with minimal required fields."""
        history = history_dao.create(
            session_id="test_session",
            user_id="test_user",
            query_text="Test query",
            success=False
        )

        assert history is not None
        assert history.query_cypher is None
        assert history.error_message is None
        assert history.success is False

    def test_create_failed_query(self, history_dao):
        """Test creating history for a failed query."""
        history = history_dao.create(
            session_id="session_fail",
            user_id="user_fail",
            query_text="Invalid query",
            query_cypher="MATCH (x) RETURN invalid",
            success=False,
            error_message="Syntax error: unknown variable 'invalid'"
        )

        assert history.success is False
        assert history.error_message is not None
        assert "Syntax error" in history.error_message

    def test_create_with_full_analysis(self, history_dao, sample_history_data):
        """Test creating history with complete analysis results."""
        sample_history_data.update({
            "path_patterns": {
                "pattern_type": "VERTEX_QUERY",
                "depth": 0
            },
            "validation_result": {
                "schema_validation": "PASS",
                "semantic_validation": "PASS"
            },
            "token_usage": {
                "total_tokens": 1250,
                "prompt_tokens": 1000,
                "completion_tokens": 250
            },
            "agents_executed": ["query_intention_analyzer", "query_designer"]
        })

        history = history_dao.create(**sample_history_data)

        assert history.path_patterns is not None
        assert history.validation_result is not None
        assert history.token_usage["total_tokens"] == 1250
        assert len(history.agents_executed) == 2


class TestQueryHistoryDaoRead:
    """Test read operations."""

    def test_get_by_id(self, history_dao, sample_history_data):
        """Test retrieving history by ID."""
        created = history_dao.create(**sample_history_data)
        retrieved = history_dao.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.query_text == created.query_text

    def test_get_by_id_not_found(self, history_dao):
        """Test retrieving non-existent history returns None."""
        result = history_dao.get_by_id("non_existent_id")
        assert result is None

    def test_get_by_session(self, history_dao):
        """Test retrieving all queries from a session."""
        session_id = f"session_{uuid4()}"
        user_id = f"user_{uuid4()}"

        # Create multiple queries for same session
        history_dao.create(
            session_id=session_id,
            user_id=user_id,
            query_text="Query 1",
            success=True,
            latency_ms=100
        )
        time.sleep(0.01)  # Ensure different timestamps
        history_dao.create(
            session_id=session_id,
            user_id=user_id,
            query_text="Query 2",
            success=True,
            latency_ms=200
        )
        time.sleep(0.01)
        history_dao.create(
            session_id=session_id,
            user_id=user_id,
            query_text="Query 3",
            success=False
        )

        # Create query for different session
        history_dao.create(
            session_id=f"other_session_{uuid4()}",
            user_id=user_id,
            query_text="Other query",
            success=True
        )

        results = history_dao.get_by_session(session_id)

        assert len(results) == 3
        # Should be ordered by created_at DESC (most recent first)
        assert results[0].query_text == "Query 3"
        assert results[2].query_text == "Query 1"

    def test_get_by_session_with_limit(self, history_dao):
        """Test retrieving session queries with limit."""
        session_id = f"session_{uuid4()}"

        for i in range(5):
            history_dao.create(
                session_id=session_id,
                user_id=f"user_{uuid4()}",
                query_text=f"Query {i}",
                success=True
            )
            time.sleep(0.01)

        results = history_dao.get_by_session(session_id, limit=3)
        assert len(results) == 3

    def test_get_successful_queries(self, history_dao):
        """Test retrieving only successful queries for a user."""
        user_id = f"user_{uuid4()}"

        history_dao.create(
            session_id=f"s1_{uuid4()}",
            user_id=user_id,
            query_text="Success 1",
            success=True,
            latency_ms=100
        )
        time.sleep(0.01)
        history_dao.create(
            session_id=f"s2_{uuid4()}",
            user_id=user_id,
            query_text="Failed query",
            success=False,
            error_message="Error"
        )
        time.sleep(0.01)
        history_dao.create(
            session_id=f"s3_{uuid4()}",
            user_id=user_id,
            query_text="Success 2",
            success=True,
            latency_ms=200
        )

        # Create query for different user
        history_dao.create(
            session_id=f"s4_{uuid4()}",
            user_id=f"other_user_{uuid4()}",
            query_text="Other success",
            success=True
        )

        results = history_dao.get_successful_queries(user_id)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert all(r.user_id == user_id for r in results)

    def test_get_successful_queries_with_limit(self, history_dao):
        """Test limiting successful queries results."""
        user_id = f"user_{uuid4()}"

        for i in range(10):
            history_dao.create(
                session_id=f"s{i}_{uuid4()}",
                user_id=user_id,
                query_text=f"Query {i}",
                success=True
            )
            time.sleep(0.01)

        results = history_dao.get_successful_queries(user_id, limit=5)
        assert len(results) == 5

    def test_find_similar_queries(self, history_dao):
        """Test finding similar queries by text matching."""
        history_dao.create(
            session_id=f"s1_{uuid4()}",
            user_id=f"u1_{uuid4()}",
            query_text="Find Person nodes with name John",
            success=True
        )
        history_dao.create(
            session_id=f"s2_{uuid4()}",
            user_id=f"u2_{uuid4()}",
            query_text="Find all Person vertices named Alice",
            success=True
        )
        history_dao.create(
            session_id=f"s3_{uuid4()}",
            user_id=f"u3_{uuid4()}",
            query_text="Get Company nodes",
            success=True
        )
        history_dao.create(
            session_id=f"s4_{uuid4()}",
            user_id=f"u4_{uuid4()}",
            query_text="Find Person with age greater than 25",
            success=True
        )

        # Search for queries containing "Person"
        results = history_dao.find_similar_queries("Find Person")

        # Should find 3 queries containing both "Find" and "Person"
        assert len(results) == 3
        assert all("Person" in r.query_text for r in results)

    def test_find_similar_queries_empty(self, history_dao):
        """Test finding similar queries with no matches."""
        history_dao.create(
            session_id=f"s1_{uuid4()}",
            user_id=f"u1_{uuid4()}",
            query_text="Find Person nodes",
            success=True
        )

        results = history_dao.find_similar_queries("Company Employee relationship")
        assert len(results) == 0

    def test_find_similar_queries_only_successful(self, history_dao):
        """Test that similar query search only returns successful queries."""
        history_dao.create(
            session_id=f"s1_{uuid4()}",
            user_id=f"u1_{uuid4()}",
            query_text="Find Person nodes",
            success=True
        )
        history_dao.create(
            session_id=f"s2_{uuid4()}",
            user_id=f"u2_{uuid4()}",
            query_text="Find Person with error",
            success=False
        )

        results = history_dao.find_similar_queries("Find Person")
        assert len(results) == 1
        assert results[0].success is True


class TestQueryHistoryDaoStatistics:
    """Test statistics operations."""

    def test_get_statistics_all(self, history_dao):
        """Test getting overall statistics."""
        user_id = f"user_{uuid4()}"

        # Create successful queries
        for i in range(7):
            history_dao.create(
                session_id=f"s{i}_{uuid4()}",
                user_id=user_id,
                query_text=f"Query {i}",
                success=True,
                latency_ms=100 + i * 10
            )

        # Create failed queries
        for i in range(3):
            history_dao.create(
                session_id=f"sf{i}_{uuid4()}",
                user_id=user_id,
                query_text=f"Failed {i}",
                success=False
            )

        stats = history_dao.get_statistics()

        assert stats["total_queries"] >= 10
        assert stats["successful_queries"] >= 7
        assert stats["success_rate"] >= 0.7
        assert stats["average_latency_ms"] is not None
        assert 100 <= stats["average_latency_ms"] <= 200

    def test_get_statistics_by_user(self, history_dao):
        """Test getting statistics for specific user."""
        user1_id = f"user1_{uuid4()}"
        user2_id = f"user2_{uuid4()}"

        # User 1: 5 successful, 2 failed
        for i in range(5):
            history_dao.create(
                session_id=f"s{i}_{uuid4()}",
                user_id=user1_id,
                query_text=f"Query {i}",
                success=True,
                latency_ms=150
            )
        for i in range(2):
            history_dao.create(
                session_id=f"sf{i}_{uuid4()}",
                user_id=user1_id,
                query_text=f"Failed {i}",
                success=False
            )

        # User 2: 3 successful
        for i in range(3):
            history_dao.create(
                session_id=f"s2{i}_{uuid4()}",
                user_id=user2_id,
                query_text=f"Query {i}",
                success=True,
                latency_ms=200
            )

        stats1 = history_dao.get_statistics(user_id=user1_id)
        stats2 = history_dao.get_statistics(user_id=user2_id)

        assert stats1["total_queries"] == 7
        assert stats1["successful_queries"] == 5
        assert abs(stats1["success_rate"] - 5/7) < 0.01

        assert stats2["total_queries"] == 3
        assert stats2["successful_queries"] == 3
        assert stats2["success_rate"] == 1.0
        assert abs(stats2["average_latency_ms"] - 200) < 1

    def test_get_statistics_with_time_range(self, history_dao):
        """Test getting statistics within time range."""
        user_id = f"user_{uuid4()}"
        base_time = int(time.time())

        # Create queries at different times
        for i in range(5):
            history_dao.create(
                session_id=f"s{i}_{uuid4()}",
                user_id=user_id,
                query_text=f"Query {i}",
                success=True,
                latency_ms=100
            )

        # Get current stats
        stats = history_dao.get_statistics(
            user_id=user_id,
            start_time=base_time,
            end_time=base_time + 10
        )

        assert stats["total_queries"] == 5
        assert stats["successful_queries"] == 5

    def test_get_statistics_empty(self, history_dao):
        """Test statistics with no data."""
        stats = history_dao.get_statistics(user_id="nonexistent_user")

        assert stats["total_queries"] == 0
        assert stats["successful_queries"] == 0
        assert stats["success_rate"] == 0
        assert stats["average_latency_ms"] is None

    def test_get_statistics_no_latency(self, history_dao):
        """Test statistics when queries have no latency data."""
        user_id = f"user_{uuid4()}"

        for i in range(3):
            history_dao.create(
                session_id=f"s{i}_{uuid4()}",
                user_id=user_id,
                query_text=f"Query {i}",
                success=True
                # No latency_ms
            )

        stats = history_dao.get_statistics(user_id=user_id)

        assert stats["total_queries"] == 3
        assert stats["successful_queries"] == 3
        assert stats["average_latency_ms"] is None


class TestQueryHistoryDaoUpdate:
    """Test update operations."""

    def test_update_history(self, history_dao, sample_history_data):
        """Test updating history record."""
        history = history_dao.create(**sample_history_data)

        updated = history_dao.update(
            id=history.id,
            result_count=100,
            latency_ms=250
        )

        assert updated.result_count == 100
        assert updated.latency_ms == 250
        assert updated.query_text == sample_history_data["query_text"]

    def test_update_add_analysis(self, history_dao):
        """Test adding analysis results to existing history."""
        history = history_dao.create(
            session_id=f"s_{uuid4()}",
            user_id=f"u_{uuid4()}",
            query_text="Test query",
            success=True
        )

        assert history.complexity_analysis is None

        updated = history_dao.update(
            id=history.id,
            complexity_analysis={
                "complexity_level": "MODERATE",
                "complexity_score": 0.6
            }
        )

        assert updated.complexity_analysis is not None
        assert updated.complexity_analysis["complexity_level"] == "MODERATE"


class TestQueryHistoryDaoDelete:
    """Test delete operations."""

    def test_delete_history(self, history_dao, sample_history_data, db_session):
        """Test deleting history record."""
        history = history_dao.create(**sample_history_data)
        history_id = history.id

        history_dao.delete(history_id)
        db_session.expire_all()

        assert history_dao.get_by_id(history_id) is None


class TestQueryHistoryDoModel:
    """Test QueryHistoryDo model methods."""

    def test_to_dict(self, history_dao, sample_history_data):
        """Test converting history to dictionary."""
        history = history_dao.create(**sample_history_data)
        history_dict = history.to_dict()

        assert history_dict["id"] == history.id
        assert history_dict["query_text"] == sample_history_data["query_text"]
        assert history_dict["success"] is True
        assert history_dict["latency_ms"] == 150
        assert "created_at" in history_dict

    def test_repr(self, history_dao, sample_history_data):
        """Test string representation."""
        history = history_dao.create(**sample_history_data)
        repr_str = repr(history)

        assert "QueryHistoryDo" in repr_str
        assert history.id in repr_str
        assert "SUCCESS" in repr_str
        assert "150ms" in repr_str

    def test_repr_failed_query(self, history_dao):
        """Test string representation for failed query."""
        history = history_dao.create(
            session_id=f"s_{uuid4()}",
            user_id=f"u_{uuid4()}",
            query_text="Failed query",
            success=False
        )
        repr_str = repr(history)

        assert "FAILED" in repr_str


class TestQueryHistoryDaoEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_with_large_result_data(self, history_dao):
        """Test creating history with large result data."""
        large_result = {
            f"record_{i}": {"id": i, "data": f"value_{i}"}
            for i in range(100)
        }

        history = history_dao.create(
            session_id=f"s_{uuid4()}",
            user_id=f"u_{uuid4()}",
            query_text="Large result query",
            success=True,
            result_data=large_result,
            result_count=100
        )

        assert history.result_data is not None
        assert len(history.result_data) == 100

    def test_query_text_with_special_characters(self, history_dao):
        """Test query text with special characters."""
        special_query = "Find nodes where name CONTAINS \"John's\"; DROP TABLE;"

        history = history_dao.create(
            session_id=f"s_{uuid4()}",
            user_id=f"u_{uuid4()}",
            query_text=special_query,
            success=True
        )

        assert history.query_text == special_query

    def test_concurrent_creates(self, history_dao):
        """Test creating multiple histories in quick succession."""
        session_id = f"session_{uuid4()}"

        histories = []
        for i in range(10):
            history = history_dao.create(
                session_id=session_id,
                user_id=f"user_{uuid4()}",
                query_text=f"Query {i}",
                success=True
            )
            histories.append(history)

        # All should have unique IDs
        ids = [h.id for h in histories]
        assert len(ids) == len(set(ids))

    def test_filter_by_multiple_criteria(self, history_dao):
        """Test filtering with multiple conditions."""
        user_id = f"user_{uuid4()}"

        history_dao.create(
            session_id=f"s1_{uuid4()}",
            user_id=user_id,
            query_text="Success",
            success=True
        )
        history_dao.create(
            session_id=f"s2_{uuid4()}",
            user_id=user_id,
            query_text="Failed",
            success=False
        )

        results = history_dao.filter_by(user_id=user_id, success=True)
        assert len(results) == 1
        assert results[0].success is True

    def test_zero_latency(self, history_dao):
        """Test handling zero latency."""
        history = history_dao.create(
            session_id=f"s_{uuid4()}",
            user_id=f"u_{uuid4()}",
            query_text="Instant query",
            success=True,
            latency_ms=0
        )

        assert history.latency_ms == 0

    def test_very_long_query_text(self, history_dao):
        """Test handling very long query text."""
        long_query = "Find Person " + "AND Property " * 500

        history = history_dao.create(
            session_id=f"s_{uuid4()}",
            user_id=f"u_{uuid4()}",
            query_text=long_query,
            success=True
        )

        assert len(history.query_text) > 5000
