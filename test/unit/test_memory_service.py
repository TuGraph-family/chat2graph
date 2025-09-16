"""
Unit tests for Memory Service functionality.

This module contains comprehensive tests for the enhanced Memory service,
including MemFuse integration, hook mechanisms, and error handling.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from app.core.memory.enhanced import (
    MemoryService,
    MemoryServiceConfig,
    MemoryType,
    RetrievalQuery,
    RetrievalResult,
)
from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.common.type import MessageSourceType, WorkflowStatus


@pytest.fixture
def memory_config():
    """Create test memory configuration."""
    config = MemoryServiceConfig()
    config.memfuse_base_url = "http://localhost:8001"
    config.enabled = True
    config.timeout = 5.0
    config.retry_count = 1
    config.async_write = False  # Use sync for testing
    config.retrieval_enabled = True
    config.max_content_length = 1000
    config.cache_ttl = 60
    return config


@pytest.fixture
def mock_job():
    """Create a mock job for testing."""
    return Job(
        id="test-job-123",
        session_id="test-session-456",
        goal="Test goal for memory functionality",
        context="Test context for memory operations"
    )


@pytest.fixture
def mock_reasoning_messages():
    """Create mock reasoning messages."""
    return [
        ModelMessage(
            source_type=MessageSourceType.USER,
            payload={"content": "User input message"}
        ),
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload={"content": "Model response message"}
        )
    ]


@pytest.fixture
def mock_workflow_message():
    """Create mock workflow message."""
    return WorkflowMessage(
        payload={
            "scratchpad": "Test operator execution result",
            "status": WorkflowStatus.SUCCESS,
            "evaluation": "Operation completed successfully",
            "lesson": "Test lesson learned"
        },
        job_id="test-job-123"
    )


class TestMemoryService:
    """Test cases for MemoryService."""
    
    @pytest.mark.asyncio
    async def test_memory_service_initialization(self, memory_config):
        """Test MemoryService initialization."""
        service = MemoryService(memory_config)
        
        assert service.is_enabled == True
        assert service._config.memfuse_base_url == "http://localhost:8001"
        assert service._config.enabled == True
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_write_reasoning_log_success(self, memory_config, mock_job, 
                                             mock_reasoning_messages):
        """Test successful reasoning log write."""
        service = MemoryService(memory_config)
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(service._client, 'post', return_value=mock_response):
            result = await service.write_reasoning_log(
                session_id=mock_job.session_id,
                job_id=mock_job.id,
                operator_id="test-operator",
                reasoning_messages=mock_reasoning_messages
            )
        
        assert result == True
        await service.close()
    
    @pytest.mark.asyncio
    async def test_write_operator_log_success(self, memory_config, mock_job, 
                                            mock_workflow_message):
        """Test successful operator log write."""
        service = MemoryService(memory_config)
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(service._client, 'post', return_value=mock_response):
            result = await service.write_operator_log(
                session_id=mock_job.session_id,
                job_id=mock_job.id,
                operator_id="test-operator",
                operator_result=mock_workflow_message
            )
        
        assert result == True
        await service.close()
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_memories_success(self, memory_config):
        """Test successful memory retrieval."""
        service = MemoryService(memory_config)
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "results": [
                    {
                        "content": "Test memory content",
                        "score": 0.95,
                        "metadata": {
                            "type": "reasoning_log",
                            "job_id": "test-job",
                            "operator_id": "test-operator"
                        }
                    }
                ]
            }
        }
        
        with patch.object(service._client, 'post', return_value=mock_response):
            query = RetrievalQuery(
                query="test query",
                session_id="test-session",
                memory_type=MemoryType.REASONING_LOG,
                top_k=5
            )
            
            results = await service.retrieve_relevant_memories(query)
        
        assert len(results) == 1
        assert results[0].content == "Test memory content"
        assert results[0].score == 0.95
        assert results[0].memory_type == MemoryType.REASONING_LOG
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_memory_service_disabled(self, memory_config):
        """Test MemoryService behavior when disabled."""
        memory_config.enabled = False
        service = MemoryService(memory_config)
        
        # All operations should return success/empty when disabled
        result = await service.write_reasoning_log(
            "session", "job", "operator", []
        )
        assert result == True
        
        memories = await service.retrieve_relevant_memories(
            RetrievalQuery("query", "session")
        )
        assert memories == []
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, memory_config, mock_job):
        """Test HTTP error handling."""
        service = MemoryService(memory_config)
        
        # Mock HTTP error
        with patch.object(service._client, 'post', 
                         side_effect=httpx.RequestError("Connection failed")):
            result = await service.write_reasoning_log(
                session_id=mock_job.session_id,
                job_id=mock_job.id,
                operator_id="test-operator",
                reasoning_messages=[]
            )
        
        assert result == False
        await service.close()
    
    @pytest.mark.asyncio
    async def test_content_length_truncation(self, memory_config, mock_job):
        """Test content length truncation."""
        memory_config.max_content_length = 100
        service = MemoryService(memory_config)
        
        # Create long reasoning messages
        long_messages = [
            ModelMessage(
                source_type=MessageSourceType.MODEL,
                payload={"content": "x" * 200}  # Longer than max_content_length
            )
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(service._client, 'post', return_value=mock_response) as mock_post:
            await service.write_reasoning_log(
                session_id=mock_job.session_id,
                job_id=mock_job.id,
                operator_id="test-operator",
                reasoning_messages=long_messages
            )
            
            # Verify content was truncated
            call_args = mock_post.call_args
            content = call_args[1]['json']['content']
            assert len(content) <= memory_config.max_content_length + 20  # Allow for truncation marker
            assert "TRUNCATED" in content
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_retrieval_caching(self, memory_config):
        """Test retrieval result caching."""
        service = MemoryService(memory_config)
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"results": []}
        }
        
        query = RetrievalQuery(
            query="test query",
            session_id="test-session",
            memory_type=MemoryType.REASONING_LOG
        )
        
        with patch.object(service._client, 'post', return_value=mock_response) as mock_post:
            # First call
            await service.retrieve_relevant_memories(query)
            # Second call (should use cache)
            await service.retrieve_relevant_memories(query)
            
            # Should only make one HTTP request due to caching
            assert mock_post.call_count == 1
        
        await service.close()


class TestMemoryServiceIntegration:
    """Integration tests for Memory Service."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_memory_flow(self, memory_config, mock_job, 
                                        mock_reasoning_messages, mock_workflow_message):
        """Test complete memory flow: write and retrieve."""
        service = MemoryService(memory_config)
        
        # Mock successful write
        mock_write_response = MagicMock()
        mock_write_response.status_code = 200
        
        # Mock successful retrieval
        mock_retrieve_response = MagicMock()
        mock_retrieve_response.status_code = 200
        mock_retrieve_response.json.return_value = {
            "data": {
                "results": [
                    {
                        "content": "Retrieved memory content",
                        "score": 0.9,
                        "metadata": {"type": "reasoning_log"}
                    }
                ]
            }
        }
        
        with patch.object(service._client, 'post') as mock_post:
            mock_post.side_effect = [mock_write_response, mock_retrieve_response]
            
            # Write reasoning log
            write_result = await service.write_reasoning_log(
                session_id=mock_job.session_id,
                job_id=mock_job.id,
                operator_id="test-operator",
                reasoning_messages=mock_reasoning_messages
            )
            
            # Retrieve memories
            query = RetrievalQuery(
                query="test query",
                session_id=mock_job.session_id,
                memory_type=MemoryType.REASONING_LOG
            )
            memories = await service.retrieve_relevant_memories(query)
            
            assert write_result == True
            assert len(memories) == 1
            assert memories[0].content == "Retrieved memory content"
        
        await service.close()
