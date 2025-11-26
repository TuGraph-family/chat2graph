"""
Integration Test Configuration and Fixtures

提供集成测试的通用配置和固定装置。

Author: kaichuan
Date: 2025-11-25
"""

from typing import List, Dict
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "operator: mark test as operator integration test"
    )
    config.addinivalue_line(
        "markers", "workflow: mark test as workflow integration test"
    )


# ==================== Mock Reasoner Fixtures ====================

@pytest.fixture
def mock_reasoner():
    """Create a mock reasoner for operator testing."""
    reasoner = AsyncMock()
    reasoner.infer = AsyncMock()
    reasoner.infer.return_value = {
        "result": "mocked_result",
        "success": True
    }
    return reasoner


# ==================== Job Fixtures ====================

@pytest.fixture
def sample_job():
    """Create a sample SubJob for testing."""
    from app.core.model.job import SubJob

    return SubJob(
        id=f"test_job_{uuid4()}",
        session_id=f"test_session_{uuid4()}",
        goal="Test goal for integration testing",
        context="Test context with sample data",
        original_job_id=f"original_job_{uuid4()}"
    )


# ==================== Query Fixtures ====================

@pytest.fixture
def sample_queries():
    """Create sample natural language queries for testing."""
    return {
        "simple": [
            "Find all Person nodes",
            "Get all companies",
            "Show me people named John"
        ],
        "complex": [
            "Find friends of friends who work at tech companies",
            "Get people who work at the same company as John"
        ],
        "aggregation": [
            "Count how many people work at each company",
            "Find the average age of employees at Company X"
        ]
    }


@pytest.fixture
def expected_cypher_queries():
    """Create expected Cypher query outputs for validation."""
    return {
        "Find all Person nodes": "MATCH (p:Person) RETURN p",
        "Get all companies": "MATCH (c:Company) RETURN c"
    }
