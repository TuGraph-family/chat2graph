"""
Unit tests for QueryFeedbackDao

Tests all CRUD operations, feedback aggregation, and business logic for QueryFeedbackDao.

Author: kaichuan - Phase 2 Week 1
Date: 2025-11-25
"""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.dal.database import Do
from app.core.dal.do.query_feedback_do import QueryFeedbackDo
from app.core.dal.dao.query_feedback_dao import QueryFeedbackDao


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """Create an in-memory SQLite database for testing."""
    from app.core.dal.do.query_feedback_do import QueryFeedbackDo
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
def feedback_dao(db_session):
    """Create QueryFeedbackDao instance with test database session."""
    return QueryFeedbackDao(db_session)


@pytest.fixture
def sample_feedback_data():
    """Generate sample feedback data for testing."""
    return {
        "query_history_id": f"query_{uuid4()}",
        "user_id": f"user_{uuid4()}",
        "feedback_type": "thumbs_up",
        "feedback_value": 1,
        "comment": "Great query result!"
    }


class TestQueryFeedbackDaoCreate:
    """Test create operations."""

    def test_create_thumbs_up_feedback(self, feedback_dao, sample_feedback_data):
        """Test creating thumbs up feedback."""
        feedback = feedback_dao.create(**sample_feedback_data)

        assert feedback is not None
        assert feedback.id is not None
        assert feedback.feedback_type == "thumbs_up"
        assert feedback.feedback_value == 1
        assert feedback.created_at is not None

    def test_create_thumbs_down_feedback(self, feedback_dao):
        """Test creating thumbs down feedback."""
        feedback = feedback_dao.create(
            query_history_id=f"query_{uuid4()}",
            user_id=f"user_{uuid4()}",
            feedback_type="thumbs_down",
            feedback_value=-1,
            comment="Query result was incorrect"
        )

        assert feedback.feedback_type == "thumbs_down"
        assert feedback.feedback_value == -1

    def test_create_correction_feedback(self, feedback_dao):
        """Test creating correction feedback."""
        feedback = feedback_dao.create(
            query_history_id=f"query_{uuid4()}",
            user_id=f"user_{uuid4()}",
            feedback_type="correction",
            feedback_value=0,
            correction_data={
                "corrected_query": "Find Person nodes with name 'Alice'",
                "corrected_result": "Expected result data",
                "issue": "Wrong field used in query"
            },
            comment="The query should use 'name' instead of 'username'"
        )

        assert feedback.feedback_type == "correction"
        assert feedback.correction_data is not None
        assert "corrected_query" in feedback.correction_data

    def test_create_suggestion_feedback(self, feedback_dao):
        """Test creating suggestion feedback."""
        feedback = feedback_dao.create(
            query_history_id=f"query_{uuid4()}",
            user_id=f"user_{uuid4()}",
            feedback_type="suggestion",
            feedback_value=0,
            comment="Consider adding an index on the 'age' property for better performance"
        )

        assert feedback.feedback_type == "suggestion"
        assert feedback.feedback_value == 0
        assert "index" in feedback.comment.lower()

    def test_create_minimal_feedback(self, feedback_dao):
        """Test creating feedback with minimal required fields."""
        feedback = feedback_dao.create(
            query_history_id=f"query_{uuid4()}",
            user_id=f"user_{uuid4()}",
            feedback_type="thumbs_up"
        )

        assert feedback is not None
        assert feedback.feedback_value is None
        assert feedback.comment is None

    def test_create_multiple_feedback_same_query(self, feedback_dao):
        """Test creating multiple feedback entries for same query."""
        query_id = f"query_{uuid4()}"

        feedback1 = feedback_dao.create(
            query_history_id=query_id,
            user_id=f"user1_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )

        feedback2 = feedback_dao.create(
            query_history_id=query_id,
            user_id=f"user2_{uuid4()}",
            feedback_type="thumbs_down",
            feedback_value=-1
        )

        assert feedback1.query_history_id == feedback2.query_history_id
        assert feedback1.id != feedback2.id


class TestQueryFeedbackDaoRead:
    """Test read operations."""

    def test_get_by_id(self, feedback_dao, sample_feedback_data):
        """Test retrieving feedback by ID."""
        created = feedback_dao.create(**sample_feedback_data)
        retrieved = feedback_dao.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.feedback_type == created.feedback_type

    def test_get_by_query_history(self, feedback_dao):
        """Test retrieving all feedback for a specific query."""
        query_id = f"query_{uuid4()}"

        # Create multiple feedback entries for same query
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u1_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u2_{uuid4()}",
            feedback_type="thumbs_down",
            feedback_value=-1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u3_{uuid4()}",
            feedback_type="suggestion",
            comment="Add index"
        )

        # Create feedback for different query
        feedback_dao.create(
            query_history_id=f"other_query_{uuid4()}",
            user_id=f"u4_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )

        results = feedback_dao.get_by_query_history(query_id)

        assert len(results) == 3
        assert all(f.query_history_id == query_id for f in results)

    def test_get_by_user(self, feedback_dao):
        """Test retrieving all feedback from a specific user."""
        user_id = f"user_{uuid4()}"

        feedback_dao.create(
            query_history_id=f"q1_{uuid4()}",
            user_id=user_id,
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=f"q2_{uuid4()}",
            user_id=user_id,
            feedback_type="correction",
            correction_data={"issue": "test"}
        )

        # Create feedback from different user
        feedback_dao.create(
            query_history_id=f"q3_{uuid4()}",
            user_id=f"other_user_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )

        results = feedback_dao.get_by_user(user_id)

        assert len(results) == 2
        assert all(f.user_id == user_id for f in results)

    def test_get_by_user_with_type_filter(self, feedback_dao):
        """Test retrieving user feedback filtered by type."""
        user_id = f"user_{uuid4()}"

        feedback_dao.create(
            query_history_id=f"q1_{uuid4()}",
            user_id=user_id,
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=f"q2_{uuid4()}",
            user_id=user_id,
            feedback_type="thumbs_down",
            feedback_value=-1
        )
        feedback_dao.create(
            query_history_id=f"q3_{uuid4()}",
            user_id=user_id,
            feedback_type="thumbs_up",
            feedback_value=1
        )

        thumbs_up_results = feedback_dao.get_by_user(user_id, feedback_type="thumbs_up")
        thumbs_down_results = feedback_dao.get_by_user(user_id, feedback_type="thumbs_down")

        assert len(thumbs_up_results) == 2
        assert len(thumbs_down_results) == 1
        assert all(f.feedback_type == "thumbs_up" for f in thumbs_up_results)


class TestQueryFeedbackDaoAggregation:
    """Test feedback aggregation operations."""

    def test_aggregate_feedback_for_query(self, feedback_dao):
        """Test aggregating feedback for a specific query."""
        query_id = f"query_{uuid4()}"

        # Create diverse feedback
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u1_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u2_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u3_{uuid4()}",
            feedback_type="thumbs_down",
            feedback_value=-1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u4_{uuid4()}",
            feedback_type="suggestion",
            feedback_value=0
        )

        stats = feedback_dao.aggregate_feedback(query_history_id=query_id)

        assert stats["total_feedback"] == 4
        assert stats["feedback_type_distribution"]["thumbs_up"] == 2
        assert stats["feedback_type_distribution"]["thumbs_down"] == 1
        assert stats["feedback_type_distribution"]["suggestion"] == 1
        assert stats["total_value"] == 1  # 1 + 1 - 1 + 0 = 1
        assert abs(stats["average_value"] - 0.25) < 0.01  # 1/4 = 0.25

    def test_aggregate_all_feedback(self, feedback_dao):
        """Test aggregating all feedback across all queries."""
        # Create feedback for multiple queries
        for i in range(3):
            query_id = f"query_{i}_{uuid4()}"
            feedback_dao.create(
                query_history_id=query_id,
                user_id=f"u{i}_{uuid4()}",
                feedback_type="thumbs_up",
                feedback_value=1
            )

        for i in range(2):
            query_id = f"query2_{i}_{uuid4()}"
            feedback_dao.create(
                query_history_id=query_id,
                user_id=f"u{i}_{uuid4()}",
                feedback_type="thumbs_down",
                feedback_value=-1
            )

        stats = feedback_dao.aggregate_feedback()

        assert stats["total_feedback"] == 5
        assert stats["feedback_type_distribution"]["thumbs_up"] == 3
        assert stats["feedback_type_distribution"]["thumbs_down"] == 2
        assert stats["total_value"] == 1  # 3 - 2 = 1
        assert abs(stats["average_value"] - 0.2) < 0.01  # 1/5 = 0.2

    def test_aggregate_feedback_empty(self, feedback_dao):
        """Test aggregating feedback with no data."""
        stats = feedback_dao.aggregate_feedback(query_history_id="nonexistent_query")

        assert stats["total_feedback"] == 0
        assert stats["feedback_type_distribution"] == {}
        assert stats["total_value"] == 0
        assert stats["average_value"] == 0.0

    def test_aggregate_feedback_no_values(self, feedback_dao):
        """Test aggregating feedback without feedback values."""
        query_id = f"query_{uuid4()}"

        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u1_{uuid4()}",
            feedback_type="suggestion",
            comment="Add feature X"
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u2_{uuid4()}",
            feedback_type="correction",
            correction_data={"issue": "test"}
        )

        stats = feedback_dao.aggregate_feedback(query_history_id=query_id)

        assert stats["total_feedback"] == 2
        assert stats["total_value"] == 0
        assert stats["average_value"] == 0.0

    def test_aggregate_mixed_feedback(self, feedback_dao):
        """Test aggregating feedback with mixed value types."""
        query_id = f"query_{uuid4()}"

        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u1_{uuid4()}",
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u2_{uuid4()}",
            feedback_type="suggestion",
            feedback_value=None
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u3_{uuid4()}",
            feedback_type="thumbs_down",
            feedback_value=-1
        )

        stats = feedback_dao.aggregate_feedback(query_history_id=query_id)

        assert stats["total_feedback"] == 3
        # Only count entries with non-null feedback_value
        assert stats["total_value"] == 0  # 1 - 1 = 0
        assert stats["average_value"] == 0.0


class TestQueryFeedbackDaoUpdate:
    """Test update operations."""

    def test_update_feedback(self, feedback_dao, sample_feedback_data):
        """Test updating feedback record."""
        feedback = feedback_dao.create(**sample_feedback_data)

        updated = feedback_dao.update(
            id=feedback.id,
            comment="Updated comment with more details"
        )

        assert updated.comment == "Updated comment with more details"
        assert updated.feedback_type == sample_feedback_data["feedback_type"]

    def test_update_add_correction_data(self, feedback_dao):
        """Test adding correction data to existing feedback."""
        feedback = feedback_dao.create(
            query_history_id=f"q_{uuid4()}",
            user_id=f"u_{uuid4()}",
            feedback_type="correction"
        )

        updated = feedback_dao.update(
            id=feedback.id,
            correction_data={
                "corrected_query": "Updated query",
                "reason": "Better approach"
            }
        )

        assert updated.correction_data is not None
        assert updated.correction_data["reason"] == "Better approach"


class TestQueryFeedbackDaoDelete:
    """Test delete operations."""

    def test_delete_feedback(self, feedback_dao, sample_feedback_data, db_session):
        """Test deleting feedback record."""
        feedback = feedback_dao.create(**sample_feedback_data)
        feedback_id = feedback.id

        feedback_dao.delete(feedback_id)
        db_session.expire_all()

        assert feedback_dao.get_by_id(feedback_id) is None


class TestQueryFeedbackDoModel:
    """Test QueryFeedbackDo model methods."""

    def test_to_dict(self, feedback_dao, sample_feedback_data):
        """Test converting feedback to dictionary."""
        feedback = feedback_dao.create(**sample_feedback_data)
        feedback_dict = feedback.to_dict()

        assert feedback_dict["id"] == feedback.id
        assert feedback_dict["feedback_type"] == "thumbs_up"
        assert feedback_dict["feedback_value"] == 1
        assert "created_at" in feedback_dict

    def test_repr(self, feedback_dao, sample_feedback_data):
        """Test string representation."""
        feedback = feedback_dao.create(**sample_feedback_data)
        repr_str = repr(feedback)

        assert "QueryFeedbackDo" in repr_str
        assert feedback.id in repr_str
        assert "thumbs_up" in repr_str
        assert "value=1" in repr_str


class TestQueryFeedbackDaoEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_with_long_comment(self, feedback_dao):
        """Test creating feedback with very long comment."""
        long_comment = "This is a detailed comment. " * 100

        feedback = feedback_dao.create(
            query_history_id=f"q_{uuid4()}",
            user_id=f"u_{uuid4()}",
            feedback_type="suggestion",
            comment=long_comment
        )

        assert len(feedback.comment) > 1000
        assert feedback.comment == long_comment

    def test_create_with_complex_correction_data(self, feedback_dao):
        """Test creating feedback with complex nested correction data."""
        complex_data = {
            "original_query": "Find Person",
            "corrected_query": "Find Person with age > 25",
            "changes": [
                {"type": "add_condition", "field": "age", "operator": ">", "value": 25},
                {"type": "add_filter", "reason": "Better performance"}
            ],
            "metadata": {
                "editor": "user123",
                "timestamp": 1234567890
            }
        }

        feedback = feedback_dao.create(
            query_history_id=f"q_{uuid4()}",
            user_id=f"u_{uuid4()}",
            feedback_type="correction",
            correction_data=complex_data
        )

        assert feedback.correction_data is not None
        assert len(feedback.correction_data["changes"]) == 2

    def test_feedback_special_characters(self, feedback_dao):
        """Test feedback with special characters."""
        special_comment = "Query contains 'quotes', \"double quotes\", and <tags>"

        feedback = feedback_dao.create(
            query_history_id=f"q_{uuid4()}",
            user_id=f"u_{uuid4()}",
            feedback_type="suggestion",
            comment=special_comment
        )

        assert feedback.comment == special_comment

    def test_multiple_feedback_types_same_query(self, feedback_dao):
        """Test creating different feedback types for same query."""
        query_id = f"query_{uuid4()}"
        user_id = f"user_{uuid4()}"

        feedback_dao.create(
            query_history_id=query_id,
            user_id=user_id,
            feedback_type="thumbs_up",
            feedback_value=1
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=user_id,
            feedback_type="suggestion",
            comment="Also, consider adding..."
        )

        results = feedback_dao.get_by_query_history(query_id)
        assert len(results) == 2

        types = [f.feedback_type for f in results]
        assert "thumbs_up" in types
        assert "suggestion" in types

    def test_extreme_feedback_values(self, feedback_dao):
        """Test feedback with extreme values."""
        query_id = f"query_{uuid4()}"

        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u1_{uuid4()}",
            feedback_type="custom",
            feedback_value=100
        )
        feedback_dao.create(
            query_history_id=query_id,
            user_id=f"u2_{uuid4()}",
            feedback_type="custom",
            feedback_value=-100
        )

        stats = feedback_dao.aggregate_feedback(query_history_id=query_id)
        assert stats["total_value"] == 0  # 100 - 100 = 0
        assert stats["average_value"] == 0.0
