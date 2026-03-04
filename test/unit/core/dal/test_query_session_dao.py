"""
Unit tests for QuerySessionDao

Tests all CRUD operations, edge cases, and business logic for QuerySessionDao.

Author: kaichuan - Phase 2 Week 1
Date: 2025-11-25
"""

import time
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.dal.database import Do
from app.core.dal.do.query_session_do import QuerySessionDo
from app.core.dal.dao.query_session_dao import QuerySessionDao


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """Create an in-memory SQLite database for testing."""
    # Import all DO classes to ensure they are registered
    from app.core.dal.do.query_session_do import QuerySessionDo
    from app.core.dal import database
    from app.core.dal.dao.dao import Dao
    import os
    import tempfile

    # Use a unique temporary database file for each test
    temp_db_path = tempfile.mktemp(suffix=".sqlite", prefix="test_db_")

    # Create test engine
    test_engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)

    # Create all tables using Do base metadata (which includes all models)
    Do.metadata.create_all(test_engine)

    TestSessionMaker = sessionmaker(bind=test_engine)

    # Monkey-patch DbSession in all the places it's imported
    monkeypatch.setattr("app.core.dal.database.DbSession", TestSessionMaker)
    monkeypatch.setattr("app.core.dal.dao.dao.DbSession", TestSessionMaker)

    # Also patch the engine
    monkeypatch.setattr(database, "engine", test_engine)

    # Clear Singleton instances to avoid stale DAOs
    if hasattr(Dao, '_instances'):
        Dao._instances.clear()

    test_session = TestSessionMaker()
    yield test_session
    test_session.close()

    # Cleanup
    Do.metadata.drop_all(test_engine)
    test_engine.dispose()

    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture
def session_dao(db_session):
    """Create QuerySessionDao instance with test database session."""
    return QuerySessionDao(db_session)


@pytest.fixture
def sample_session_data():
    """Generate sample session data for testing."""
    return {
        "user_id": f"user_{uuid4()}",
        "session_id": f"session_{uuid4()}",
        "context_data": {
            "user_preferences": {
                "preferred_complexity": "SIMPLE",
                "preferred_patterns": ["VERTEX_QUERY"],
            },
            "session_state": "active",
            "recent_queries": []
        }
    }


class TestQuerySessionDaoCreate:
    """Test create operations."""

    def test_create_session_success(self, session_dao, sample_session_data):
        """Test successful session creation."""
        session = session_dao.create(**sample_session_data)

        assert session is not None
        assert session.id is not None
        assert session.user_id == sample_session_data["user_id"]
        assert session.session_id == sample_session_data["session_id"]
        assert session.context_data == sample_session_data["context_data"]
        assert session.is_active is True
        assert session.created_at is not None

    def test_create_session_with_minimal_data(self, session_dao):
        """Test session creation with minimal required fields."""
        session = session_dao.create(
            user_id="test_user",
            session_id="test_session"
        )

        assert session is not None
        assert session.user_id == "test_user"
        assert session.session_id == "test_session"
        assert session.context_data is None
        assert session.is_active is True

    def test_create_session_with_inactive_flag(self, session_dao, sample_session_data):
        """Test creating an inactive session."""
        sample_session_data["is_active"] = False
        session = session_dao.create(**sample_session_data)

        assert session.is_active is False

    def test_create_session_duplicate_session_id_fails(self, session_dao, sample_session_data):
        """Test that duplicate session_id raises error."""
        session_dao.create(**sample_session_data)

        # Try to create another session with same session_id
        with pytest.raises(Exception):  # SQLite will raise IntegrityError
            session_dao.create(**sample_session_data)

    def test_create_session_auto_generates_id(self, session_dao, sample_session_data):
        """Test that ID is auto-generated as UUID."""
        session = session_dao.create(**sample_session_data)

        # Check that ID is a valid UUID string
        assert len(session.id) == 36  # UUID format: 8-4-4-4-12
        assert session.id.count('-') == 4


class TestQuerySessionDaoRead:
    """Test read operations."""

    def test_get_by_id_success(self, session_dao, sample_session_data):
        """Test retrieving session by ID."""
        created = session_dao.create(**sample_session_data)
        retrieved = session_dao.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.session_id == created.session_id

    def test_get_by_id_not_found(self, session_dao):
        """Test retrieving non-existent session returns None."""
        result = session_dao.get_by_id("non_existent_id")
        assert result is None

    def test_get_by_session_id_success(self, session_dao, sample_session_data):
        """Test retrieving session by session_id."""
        created = session_dao.create(**sample_session_data)
        retrieved = session_dao.get_by_session_id(created.session_id)

        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.id == created.id

    def test_get_by_session_id_not_found(self, session_dao):
        """Test retrieving non-existent session_id returns None."""
        result = session_dao.get_by_session_id("non_existent_session")
        assert result is None

    def test_get_active_sessions_by_user(self, session_dao):
        """Test retrieving all active sessions for a user."""
        user_id = f"user_{uuid4()}"

        # Create multiple sessions for the same user
        session1 = session_dao.create(
            user_id=user_id,
            session_id=f"session_1_{uuid4()}",
            is_active=True,
            last_active_at=int(time.time()) - 100
        )
        session2 = session_dao.create(
            user_id=user_id,
            session_id=f"session_2_{uuid4()}",
            is_active=True,
            last_active_at=int(time.time())
        )
        session3 = session_dao.create(
            user_id=user_id,
            session_id=f"session_3_{uuid4()}",
            is_active=False  # Inactive session
        )

        # Create session for different user
        session_dao.create(
            user_id=f"other_user_{uuid4()}",
            session_id=f"other_session_{uuid4()}",
            is_active=True
        )

        # Get active sessions
        active_sessions = session_dao.get_active_sessions_by_user(user_id)

        assert len(active_sessions) == 2
        assert active_sessions[0].session_id == session2.session_id  # Most recent first
        assert active_sessions[1].session_id == session1.session_id
        assert all(s.is_active for s in active_sessions)

    def test_get_active_sessions_by_user_empty(self, session_dao):
        """Test retrieving active sessions for user with no active sessions."""
        result = session_dao.get_active_sessions_by_user("non_existent_user")
        assert result == []

    def test_filter_by_user_id(self, session_dao):
        """Test filtering sessions by user_id."""
        user_id = f"user_{uuid4()}"

        session_dao.create(user_id=user_id, session_id=f"s1_{uuid4()}")
        session_dao.create(user_id=user_id, session_id=f"s2_{uuid4()}")
        session_dao.create(user_id=f"other_{uuid4()}", session_id=f"s3_{uuid4()}")

        results = session_dao.filter_by(user_id=user_id)
        assert len(results) == 2

    def test_get_all_sessions(self, session_dao, sample_session_data):
        """Test retrieving all sessions."""
        session_dao.create(**sample_session_data)

        other_data = sample_session_data.copy()
        other_data["session_id"] = f"other_{uuid4()}"
        session_dao.create(**other_data)

        all_sessions = session_dao.get_all()
        assert len(all_sessions) >= 2

    def test_count_sessions(self, session_dao, sample_session_data):
        """Test counting sessions."""
        initial_count = session_dao.count()

        session_dao.create(**sample_session_data)

        other_data = sample_session_data.copy()
        other_data["session_id"] = f"other_{uuid4()}"
        session_dao.create(**other_data)

        assert session_dao.count() == initial_count + 2


class TestQuerySessionDaoUpdate:
    """Test update operations."""

    def test_update_session_context(self, session_dao, sample_session_data):
        """Test updating session context data."""
        session = session_dao.create(**sample_session_data)

        new_context = {
            "user_preferences": {
                "preferred_complexity": "COMPLEX",
                "preferred_patterns": ["MULTI_HOP"],
            },
            "session_state": "updated"
        }

        current_time = int(time.time())
        updated = session_dao.update_context(
            session_id=session.session_id,
            context_data=new_context
        )

        assert updated.context_data == new_context
        assert updated.last_active_at >= current_time

    def test_update_context_nonexistent_session(self, session_dao):
        """Test updating context for non-existent session raises error."""
        with pytest.raises(ValueError, match="Session .* not found"):
            session_dao.update_context(
                session_id="non_existent",
                context_data={"test": "data"}
            )

    def test_update_session_fields(self, session_dao, sample_session_data):
        """Test updating various session fields."""
        session = session_dao.create(**sample_session_data)

        updated = session_dao.update(
            id=session.id,
            is_active=False,
            last_active_at=12345678
        )

        assert updated.is_active is False
        assert updated.last_active_at == 12345678

    def test_update_nonexistent_session(self, session_dao):
        """Test updating non-existent session raises error."""
        with pytest.raises(ValueError, match="not found"):
            session_dao.update(id="non_existent_id", is_active=False)

    def test_deactivate_session_success(self, session_dao, sample_session_data):
        """Test deactivating an active session."""
        session = session_dao.create(**sample_session_data)
        assert session.is_active is True

        deactivated = session_dao.deactivate_session(session.session_id)

        assert deactivated.is_active is False
        assert deactivated.id == session.id

    def test_deactivate_nonexistent_session(self, session_dao):
        """Test deactivating non-existent session raises error."""
        with pytest.raises(ValueError, match="Session .* not found"):
            session_dao.deactivate_session("non_existent_session")

    def test_deactivate_already_inactive_session(self, session_dao, sample_session_data):
        """Test deactivating already inactive session."""
        sample_session_data["is_active"] = False
        session = session_dao.create(**sample_session_data)

        deactivated = session_dao.deactivate_session(session.session_id)

        assert deactivated.is_active is False


class TestQuerySessionDaoDelete:
    """Test delete operations."""

    def test_delete_session_success(self, session_dao, sample_session_data, db_session):
        """Test deleting a session."""
        session = session_dao.create(**sample_session_data)
        session_id = session.id

        session_dao.delete(session_id)

        # Need to expire the session cache to see the deletion
        db_session.expire_all()

        # Verify session is deleted
        assert session_dao.get_by_id(session_id) is None

    def test_delete_nonexistent_session(self, session_dao):
        """Test deleting non-existent session (should not raise error)."""
        # SQLAlchemy delete on non-existent ID does not raise error
        session_dao.delete("non_existent_id")


class TestQuerySessionDoModel:
    """Test QuerySessionDo model methods."""

    def test_to_dict(self, session_dao, sample_session_data):
        """Test converting session to dictionary."""
        session = session_dao.create(**sample_session_data)
        session_dict = session.to_dict()

        assert session_dict["id"] == session.id
        assert session_dict["user_id"] == sample_session_data["user_id"]
        assert session_dict["session_id"] == sample_session_data["session_id"]
        assert session_dict["context_data"] == sample_session_data["context_data"]
        assert session_dict["is_active"] is True
        assert "created_at" in session_dict
        assert "updated_at" in session_dict
        assert "last_active_at" in session_dict

    def test_repr(self, session_dao, sample_session_data):
        """Test string representation of session."""
        session = session_dao.create(**sample_session_data)
        repr_str = repr(session)

        assert "QuerySessionDo" in repr_str
        assert session.id in repr_str
        assert session.session_id in repr_str
        assert session.user_id in repr_str


class TestQuerySessionDaoEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_with_empty_context_data(self, session_dao):
        """Test creating session with empty context data."""
        session = session_dao.create(
            user_id="test_user",
            session_id="test_session",
            context_data={}
        )

        assert session.context_data == {}

    def test_create_with_complex_nested_context(self, session_dao):
        """Test creating session with deeply nested context data."""
        complex_context = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": ["item1", "item2"],
                        "count": 42
                    }
                }
            },
            "preferences": {
                "p1": True,
                "p2": [1, 2, 3]
            }
        }

        session = session_dao.create(
            user_id="test_user",
            session_id="test_session",
            context_data=complex_context
        )

        assert session.context_data == complex_context

    def test_update_preserves_other_fields(self, session_dao, sample_session_data):
        """Test that updating one field doesn't affect others."""
        session = session_dao.create(**sample_session_data)
        original_context = session.context_data

        updated = session_dao.update(id=session.id, is_active=False)

        assert updated.is_active is False
        assert updated.context_data == original_context
        assert updated.user_id == sample_session_data["user_id"]

    def test_concurrent_updates_same_session(self, session_dao, sample_session_data):
        """Test handling concurrent updates to same session."""
        session = session_dao.create(**sample_session_data)

        # Simulate concurrent updates
        updated1 = session_dao.update(id=session.id, last_active_at=111111)
        updated2 = session_dao.update(id=session.id, last_active_at=222222)

        # Last update should win
        final = session_dao.get_by_id(session.id)
        assert final.last_active_at == 222222

    def test_large_context_data(self, session_dao):
        """Test handling large context data."""
        large_context = {
            f"key_{i}": f"value_{i}" * 100
            for i in range(100)
        }

        session = session_dao.create(
            user_id="test_user",
            session_id="test_session",
            context_data=large_context
        )

        retrieved = session_dao.get_by_id(session.id)
        assert len(retrieved.context_data) == 100

    def test_special_characters_in_ids(self, session_dao):
        """Test handling special characters in user_id and session_id."""
        session = session_dao.create(
            user_id="user@example.com",
            session_id="session-with-dashes_and_underscores.123"
        )

        assert session.user_id == "user@example.com"
        assert session.session_id == "session-with-dashes_and_underscores.123"

    def test_null_last_active_at(self, session_dao, sample_session_data):
        """Test session with null last_active_at."""
        session = session_dao.create(**sample_session_data)

        # last_active_at should be None initially
        assert session.last_active_at is None

    def test_timestamp_consistency(self, session_dao, sample_session_data):
        """Test that timestamps are consistent and increasing."""
        session = session_dao.create(**sample_session_data)

        # created_at should be set
        assert session.created_at is not None
        assert session.created_at > 0

        # Update and check last_active_at
        time.sleep(0.1)  # Small delay to ensure different timestamp
        updated = session_dao.update_context(
            session_id=session.session_id,
            context_data={"updated": True}
        )

        assert updated.last_active_at >= session.created_at
