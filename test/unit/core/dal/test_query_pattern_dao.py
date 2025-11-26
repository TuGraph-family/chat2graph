"""
Unit tests for QueryPatternDao

Tests all CRUD operations, pattern matching, statistics updates for QueryPatternDao.

Author: kaichuan - Phase 2 Week 1
Date: 2025-11-25
"""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.dal.database import Do
from app.core.dal.do.query_pattern_do import QueryPatternDo
from app.core.dal.dao.query_pattern_dao import QueryPatternDao


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """Create an in-memory SQLite database for testing."""
    from app.core.dal.do.query_pattern_do import QueryPatternDo
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
def pattern_dao(db_session):
    """Create QueryPatternDao instance with test database session."""
    return QueryPatternDao(db_session)


@pytest.fixture
def sample_pattern_data():
    """Generate sample pattern data for testing."""
    return {
        "pattern_type": "DIRECT",
        "pattern_template": "Find {entity_type} with {property} {operator} {value}",
        "pattern_signature": f"direct_vertex_query_{uuid4()}",
        "cypher_template": "MATCH (n:{entity_type}) WHERE n.{property} {operator} {value} RETURN n",
        "example_queries": [
            "Find Person with age > 25",
            "Find Company with revenue > 1000000"
        ],
        "frequency": 10,
        "success_rate": 0.95,
        "avg_latency_ms": 150.5,
        "avg_token_usage": 1200
    }


class TestQueryPatternDaoCreate:
    """Test create operations."""

    def test_create_pattern_success(self, pattern_dao, sample_pattern_data):
        """Test successful pattern creation."""
        pattern = pattern_dao.create(**sample_pattern_data)

        assert pattern is not None
        assert pattern.id is not None
        assert pattern.pattern_type == "DIRECT"
        assert pattern.frequency == 10
        assert pattern.success_rate == 0.95
        assert pattern.created_at is not None

    def test_create_minimal_pattern(self, pattern_dao):
        """Test creating pattern with minimal required fields."""
        pattern = pattern_dao.create(
            pattern_type="MULTI_HOP",
            pattern_template="Find path from {start} to {end}",
            pattern_signature=f"multi_hop_{uuid4()}"
        )

        assert pattern is not None
        assert pattern.frequency == 0
        assert pattern.success_rate == 0.0
        assert pattern.cypher_template is None

    def test_create_different_pattern_types(self, pattern_dao):
        """Test creating patterns of different types."""
        pattern_types = ["DIRECT", "MULTI_HOP", "AGGREGATION", "TEMPORAL", "SPATIAL", "PATTERN_MATCH"]

        for ptype in pattern_types:
            pattern = pattern_dao.create(
                pattern_type=ptype,
                pattern_template=f"Template for {ptype}",
                pattern_signature=f"{ptype.lower()}_{uuid4()}"
            )
            assert pattern.pattern_type == ptype

    def test_create_with_metadata(self, pattern_dao, sample_pattern_data):
        """Test creating pattern with metadata."""
        sample_pattern_data["pattern_metadata"] = {
            "created_by": "system",
            "complexity_score": 0.6,
            "recommended_index": ["name", "age"]
        }

        pattern = pattern_dao.create(**sample_pattern_data)

        assert pattern.pattern_metadata is not None
        assert pattern.pattern_metadata["complexity_score"] == 0.6

    def test_create_duplicate_signature_fails(self, pattern_dao, sample_pattern_data):
        """Test that duplicate pattern signature raises error."""
        pattern_dao.create(**sample_pattern_data)

        # Try to create another pattern with same signature
        with pytest.raises(Exception):  # SQLite will raise IntegrityError
            pattern_dao.create(**sample_pattern_data)


class TestQueryPatternDaoRead:
    """Test read operations."""

    def test_get_by_id(self, pattern_dao, sample_pattern_data):
        """Test retrieving pattern by ID."""
        created = pattern_dao.create(**sample_pattern_data)
        retrieved = pattern_dao.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.pattern_signature == created.pattern_signature

    def test_get_by_signature(self, pattern_dao, sample_pattern_data):
        """Test retrieving pattern by signature."""
        created = pattern_dao.create(**sample_pattern_data)
        retrieved = pattern_dao.get_by_signature(created.pattern_signature)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.pattern_type == "DIRECT"

    def test_get_by_signature_not_found(self, pattern_dao):
        """Test retrieving non-existent signature returns None."""
        result = pattern_dao.get_by_signature("nonexistent_signature")
        assert result is None

    def test_get_by_type(self, pattern_dao):
        """Test retrieving patterns by type."""
        # Create multiple patterns of same type
        for i in range(3):
            pattern_dao.create(
                pattern_type="MULTI_HOP",
                pattern_template=f"Multi-hop template {i}",
                pattern_signature=f"multi_hop_{i}_{uuid4()}",
                frequency=10 - i  # Decreasing frequency
            )

        # Create pattern of different type
        pattern_dao.create(
            pattern_type="AGGREGATION",
            pattern_template="Aggregation template",
            pattern_signature=f"agg_{uuid4()}",
            frequency=5
        )

        results = pattern_dao.get_by_type("MULTI_HOP")

        assert len(results) == 3
        assert all(p.pattern_type == "MULTI_HOP" for p in results)
        # Should be ordered by frequency DESC
        assert results[0].frequency >= results[1].frequency >= results[2].frequency

    def test_get_by_type_with_limit(self, pattern_dao):
        """Test retrieving patterns by type with limit."""
        for i in range(5):
            pattern_dao.create(
                pattern_type="DIRECT",
                pattern_template=f"Template {i}",
                pattern_signature=f"direct_{i}_{uuid4()}",
                frequency=i
            )

        results = pattern_dao.get_by_type("DIRECT", limit=3)
        assert len(results) == 3

    def test_get_top_patterns(self, pattern_dao):
        """Test retrieving top patterns by frequency."""
        frequencies = [100, 50, 75, 25, 90, 10, 60]

        for i, freq in enumerate(frequencies):
            pattern_dao.create(
                pattern_type=f"TYPE_{i}",
                pattern_template=f"Template {i}",
                pattern_signature=f"pattern_{i}_{uuid4()}",
                frequency=freq
            )

        top_3 = pattern_dao.get_top_patterns(limit=3)

        assert len(top_3) == 3
        assert top_3[0].frequency == 100
        assert top_3[1].frequency == 90
        assert top_3[2].frequency == 75

    def test_get_top_patterns_with_min_frequency(self, pattern_dao):
        """Test retrieving top patterns with minimum frequency threshold."""
        frequencies = [100, 50, 5, 75, 2, 90]

        for i, freq in enumerate(frequencies):
            pattern_dao.create(
                pattern_type=f"TYPE_{i}",
                pattern_template=f"Template {i}",
                pattern_signature=f"pattern_{i}_{uuid4()}",
                frequency=freq
            )

        # Get patterns with frequency >= 50
        results = pattern_dao.get_top_patterns(limit=10, min_frequency=50)

        assert len(results) == 4  # 100, 90, 75, 50
        assert all(p.frequency >= 50 for p in results)


class TestQueryPatternDaoFrequency:
    """Test frequency management operations."""

    def test_increment_frequency(self, pattern_dao, sample_pattern_data):
        """Test incrementing pattern frequency."""
        pattern = pattern_dao.create(**sample_pattern_data)
        original_frequency = pattern.frequency

        updated = pattern_dao.increment_frequency(pattern.pattern_signature)

        assert updated.frequency == original_frequency + 1

    def test_increment_frequency_multiple_times(self, pattern_dao, sample_pattern_data):
        """Test incrementing frequency multiple times."""
        pattern = pattern_dao.create(**sample_pattern_data)
        original_frequency = pattern.frequency

        for i in range(5):
            updated = pattern_dao.increment_frequency(pattern.pattern_signature)

        assert updated.frequency == original_frequency + 5

    def test_increment_frequency_nonexistent_pattern(self, pattern_dao):
        """Test incrementing frequency for non-existent pattern raises error."""
        with pytest.raises(ValueError, match="Pattern .* not found"):
            pattern_dao.increment_frequency("nonexistent_signature")


class TestQueryPatternDaoStatistics:
    """Test statistics update operations."""

    def test_update_statistics_success(self, pattern_dao):
        """Test updating statistics after successful execution."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Test template",
            pattern_signature=f"test_{uuid4()}",
            frequency=10,
            success_rate=0.8,
            avg_latency_ms=100.0,
            avg_token_usage=1000
        )

        # Simulate successful execution
        updated = pattern_dao.update_statistics(
            pattern_signature=pattern.pattern_signature,
            success=True,
            latency_ms=120,
            token_usage=1100
        )

        # Success rate: (0.8 * 9 + 1) / 10 = 8.2/10 = 0.82
        assert abs(updated.success_rate - 0.82) < 0.01

        # Avg latency: (100 * 9 + 120) / 10 = 1020/10 = 102
        assert abs(updated.avg_latency_ms - 102.0) < 1.0

        # Avg token: (1000 * 9 + 1100) / 10 = 10100/10 = 1010
        assert updated.avg_token_usage == 1010

    def test_update_statistics_failure(self, pattern_dao):
        """Test updating statistics after failed execution."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Test template",
            pattern_signature=f"test_{uuid4()}",
            frequency=10,
            success_rate=0.9
        )

        updated = pattern_dao.update_statistics(
            pattern_signature=pattern.pattern_signature,
            success=False
        )

        # Success rate: (0.9 * 9 + 0) / 10 = 8.1/10 = 0.81
        assert abs(updated.success_rate - 0.81) < 0.01

    def test_update_statistics_initial_latency(self, pattern_dao):
        """Test updating statistics when pattern has no initial latency."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Test template",
            pattern_signature=f"test_{uuid4()}",
            frequency=1,
            success_rate=0.0
            # No avg_latency_ms
        )

        updated = pattern_dao.update_statistics(
            pattern_signature=pattern.pattern_signature,
            success=True,
            latency_ms=150
        )

        # First latency measurement
        assert updated.avg_latency_ms == 150.0

    def test_update_statistics_without_optional_params(self, pattern_dao):
        """Test updating statistics without latency and token usage."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Test template",
            pattern_signature=f"test_{uuid4()}",
            frequency=5,
            success_rate=0.6,
            avg_latency_ms=100.0
        )

        updated = pattern_dao.update_statistics(
            pattern_signature=pattern.pattern_signature,
            success=True
        )

        # Success rate should be updated
        assert updated.success_rate > 0.6
        # Latency should remain unchanged
        assert updated.avg_latency_ms == 100.0

    def test_update_statistics_nonexistent_pattern(self, pattern_dao):
        """Test updating statistics for non-existent pattern raises error."""
        with pytest.raises(ValueError, match="Pattern .* not found"):
            pattern_dao.update_statistics(
                pattern_signature="nonexistent",
                success=True
            )


class TestQueryPatternDaoUpdate:
    """Test update operations."""

    def test_update_pattern_template(self, pattern_dao, sample_pattern_data):
        """Test updating pattern template."""
        pattern = pattern_dao.create(**sample_pattern_data)

        updated = pattern_dao.update(
            id=pattern.id,
            pattern_template="Updated template with new format",
            cypher_template="MATCH (n) RETURN n"
        )

        assert updated.pattern_template == "Updated template with new format"
        assert updated.cypher_template == "MATCH (n) RETURN n"

    def test_update_metadata(self, pattern_dao, sample_pattern_data):
        """Test updating pattern metadata."""
        pattern = pattern_dao.create(**sample_pattern_data)

        new_metadata = {
            "version": "2.0",
            "optimized": True,
            "tags": ["common", "optimized"]
        }

        updated = pattern_dao.update(
            id=pattern.id,
            pattern_metadata=new_metadata
        )

        assert updated.pattern_metadata["version"] == "2.0"
        assert updated.pattern_metadata["optimized"] is True


class TestQueryPatternDaoDelete:
    """Test delete operations."""

    def test_delete_pattern(self, pattern_dao, sample_pattern_data, db_session):
        """Test deleting pattern."""
        pattern = pattern_dao.create(**sample_pattern_data)
        pattern_id = pattern.id

        pattern_dao.delete(pattern_id)
        db_session.expire_all()

        assert pattern_dao.get_by_id(pattern_id) is None


class TestQueryPatternDoModel:
    """Test QueryPatternDo model methods."""

    def test_to_dict(self, pattern_dao, sample_pattern_data):
        """Test converting pattern to dictionary."""
        pattern = pattern_dao.create(**sample_pattern_data)
        pattern_dict = pattern.to_dict()

        assert pattern_dict["id"] == pattern.id
        assert pattern_dict["pattern_type"] == "DIRECT"
        assert pattern_dict["frequency"] == 10
        assert pattern_dict["success_rate"] == 0.95
        assert "created_at" in pattern_dict

    def test_repr(self, pattern_dao, sample_pattern_data):
        """Test string representation."""
        pattern = pattern_dao.create(**sample_pattern_data)
        repr_str = repr(pattern)

        assert "QueryPatternDo" in repr_str
        assert pattern.id in repr_str
        assert "DIRECT" in repr_str
        assert "frequency=10" in repr_str
        assert "0.95" in repr_str


class TestQueryPatternDaoEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_with_zero_frequency(self, pattern_dao):
        """Test creating pattern with zero frequency."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=f"sig_{uuid4()}",
            frequency=0
        )

        assert pattern.frequency == 0

    def test_create_with_perfect_success_rate(self, pattern_dao):
        """Test pattern with 100% success rate."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=f"sig_{uuid4()}",
            frequency=100,
            success_rate=1.0
        )

        assert pattern.success_rate == 1.0

    def test_create_with_zero_success_rate(self, pattern_dao):
        """Test pattern with 0% success rate."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=f"sig_{uuid4()}",
            frequency=10,
            success_rate=0.0
        )

        assert pattern.success_rate == 0.0

    def test_very_long_template(self, pattern_dao):
        """Test pattern with very long template."""
        long_template = "MATCH " + "(n)-[r]->(m) " * 100 + "RETURN n"

        pattern = pattern_dao.create(
            pattern_type="COMPLEX",
            pattern_template=long_template,
            pattern_signature=f"complex_{uuid4()}"
        )

        assert len(pattern.pattern_template) > 1000

    def test_complex_example_queries(self, pattern_dao):
        """Test pattern with many example queries."""
        example_queries = [f"Example query {i}" for i in range(50)]

        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=f"sig_{uuid4()}",
            example_queries=example_queries
        )

        assert len(pattern.example_queries) == 50

    def test_pattern_with_special_characters_in_signature(self, pattern_dao):
        """Test pattern with special characters in signature."""
        special_sig = f"pattern-with_special.chars_{uuid4()}"

        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=special_sig
        )

        assert pattern.pattern_signature == special_sig

    def test_update_statistics_precision(self, pattern_dao):
        """Test statistics calculations maintain precision."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=f"sig_{uuid4()}",
            frequency=3,
            success_rate=0.666666,
            avg_latency_ms=100.333
        )

        updated = pattern_dao.update_statistics(
            pattern_signature=pattern.pattern_signature,
            success=True,
            latency_ms=150
        )

        # Check that calculations maintain reasonable precision
        assert updated.success_rate > 0.7
        assert updated.avg_latency_ms > 100

    def test_concurrent_frequency_increments(self, pattern_dao):
        """Test multiple concurrent frequency increments."""
        pattern = pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="Template",
            pattern_signature=f"sig_{uuid4()}",
            frequency=0
        )

        # Simulate 10 concurrent increments
        for _ in range(10):
            pattern_dao.increment_frequency(pattern.pattern_signature)

        final = pattern_dao.get_by_signature(pattern.pattern_signature)
        assert final.frequency == 10

    def test_filter_by_multiple_criteria(self, pattern_dao):
        """Test filtering patterns by multiple conditions."""
        pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="T1",
            pattern_signature=f"s1_{uuid4()}",
            frequency=100
        )
        pattern_dao.create(
            pattern_type="DIRECT",
            pattern_template="T2",
            pattern_signature=f"s2_{uuid4()}",
            frequency=50
        )
        pattern_dao.create(
            pattern_type="MULTI_HOP",
            pattern_template="T3",
            pattern_signature=f"s3_{uuid4()}",
            frequency=75
        )

        results = pattern_dao.filter_by(pattern_type="DIRECT")
        assert len(results) == 2
        assert all(p.pattern_type == "DIRECT" for p in results)
