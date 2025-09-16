"""
Integration tests for Memory functionality.

This module contains integration tests that verify the complete Memory
enhancement functionality works correctly with real Chat2Graph components.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.memory.enhanced.integration import (
    EnhancedOperator,
    EnhancedReasoner,
    MemoryIntegrationManager,
)
from app.core.memory.enhanced.memory_service import MemoryService, MemoryServiceConfig
from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.common.type import MessageSourceType, WorkflowStatus


@pytest.fixture
def integration_config():
    """Create test configuration for integration."""
    config = MemoryServiceConfig()
    config.memfuse_base_url = "http://localhost:8001"
    config.enabled = True
    config.timeout = 5.0
    config.async_write = False  # Use sync for testing
    config.retrieval_enabled = True
    return config


@pytest.fixture
def mock_base_reasoner():
    """Create mock base reasoner."""
    reasoner = MagicMock(spec=Reasoner)
    reasoner.infer = AsyncMock(return_value="Test reasoning result")
    reasoner._memories = {}
    
    # Mock memory methods
    mock_memory = MagicMock()
    mock_memory.get_messages.return_value = [
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload={"content": "Test message"}
        )
    ]
    reasoner.get_memory.return_value = mock_memory
    
    return reasoner


@pytest.fixture
def mock_base_operator():
    """Create mock base operator."""
    config = OperatorConfig(
        id="test-operator",
        instruction="Test instruction",
        actions=[]
    )
    
    operator = MagicMock(spec=Operator)
    operator._config = config
    operator.get_id.return_value = "test-operator"
    operator.execute = AsyncMock(return_value=WorkflowMessage(
        payload={"scratchpad": "Test result"},
        job_id="test-job"
    ))
    
    return operator


@pytest.fixture
def test_job():
    """Create test job."""
    return Job(
        id="test-job",
        session_id="test-session",
        goal="Test integration goal",
        context="Test integration context"
    )


@pytest.fixture
def test_task(test_job):
    """Create test task."""
    operator_config = OperatorConfig(
        id="test-operator",
        instruction="Test instruction",
        actions=[]
    )
    
    return Task(
        job=test_job,
        operator_config=operator_config,
        workflow_messages=[],
        tools=[],
        actions=[],
        knowledge=None,
        insights=None,
        lesson=None,
        file_descriptors=[]
    )


class TestEnhancedReasoner:
    """Test cases for EnhancedReasoner."""
    
    @pytest.mark.asyncio
    async def test_enhanced_reasoner_with_memory_disabled(self, mock_base_reasoner, 
                                                        test_task):
        """Test EnhancedReasoner when memory is disabled."""
        config = MemoryServiceConfig()
        config.enabled = False
        
        memory_service = MemoryService(config)
        enhanced_reasoner = EnhancedReasoner(mock_base_reasoner, memory_service)
        
        result = await enhanced_reasoner.infer(test_task)
        
        assert result == "Test reasoning result"
        mock_base_reasoner.infer.assert_called_once()
        
        await memory_service.close()
    
    @pytest.mark.asyncio
    async def test_enhanced_reasoner_with_memory_retrieval(self, integration_config,
                                                         mock_base_reasoner, test_task):
        """Test EnhancedReasoner with memory retrieval."""
        memory_service = MemoryService(integration_config)
        enhanced_reasoner = EnhancedReasoner(mock_base_reasoner, memory_service)
        
        # Mock memory retrieval
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "results": [
                    {
                        "content": "Previous reasoning memory",
                        "score": 0.9,
                        "metadata": {"type": "reasoning_log"}
                    }
                ]
            }
        }
        
        with patch.object(memory_service._client, 'post', return_value=mock_response):
            result = await enhanced_reasoner.infer(test_task)
        
        assert result == "Test reasoning result"
        
        # Verify that the base reasoner was called with enhanced task
        mock_base_reasoner.infer.assert_called_once()
        enhanced_task = mock_base_reasoner.infer.call_args[1]['task']
        assert "RELEVANT HISTORICAL MEMORIES" in enhanced_task.job.context
        
        await memory_service.close()


class TestEnhancedOperator:
    """Test cases for EnhancedOperator."""
    
    @pytest.mark.asyncio
    async def test_enhanced_operator_execution(self, integration_config,
                                             mock_base_operator, test_job):
        """Test EnhancedOperator execution with memory integration."""
        memory_service = MemoryService(integration_config)
        enhanced_operator = EnhancedOperator(mock_base_operator, memory_service)
        
        # Mock memory operations
        mock_retrieve_response = MagicMock()
        mock_retrieve_response.status_code = 200
        mock_retrieve_response.json.return_value = {"data": {"results": []}}
        
        mock_write_response = MagicMock()
        mock_write_response.status_code = 200
        
        with patch.object(memory_service._client, 'post') as mock_post:
            mock_post.side_effect = [mock_retrieve_response, mock_write_response]
            
            result = await enhanced_operator.execute(
                reasoner=MagicMock(),
                job=test_job
            )
        
        assert result is not None
        mock_base_operator.execute.assert_called_once()
        
        await memory_service.close()
    
    @pytest.mark.asyncio
    async def test_enhanced_operator_with_memory_context(self, integration_config,
                                                       mock_base_operator, test_job):
        """Test EnhancedOperator with memory context enhancement."""
        memory_service = MemoryService(integration_config)
        enhanced_operator = EnhancedOperator(mock_base_operator, memory_service)
        
        # Mock memory retrieval with results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "results": [
                    {
                        "content": "Previous operator experience",
                        "score": 0.85,
                        "metadata": {"type": "operator_log"}
                    }
                ]
            }
        }
        
        with patch.object(memory_service._client, 'post', return_value=mock_response):
            await enhanced_operator.execute(
                reasoner=MagicMock(),
                job=test_job
            )
        
        # Verify that the base operator was called with enhanced job
        mock_base_operator.execute.assert_called_once()
        call_args = mock_base_operator.execute.call_args
        enhanced_job = call_args[1]['job']
        assert "RELEVANT OPERATOR EXPERIENCES" in enhanced_job.context
        
        await memory_service.close()


class TestMemoryIntegrationManager:
    """Test cases for MemoryIntegrationManager."""
    
    @pytest.mark.asyncio
    async def test_integration_manager_initialization(self, integration_config):
        """Test MemoryIntegrationManager initialization."""
        manager = MemoryIntegrationManager(integration_config)
        
        await manager.initialize()
        
        assert manager._initialized == True
        assert manager._memory_service is not None
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_reasoner_wrapping(self, integration_config, mock_base_reasoner):
        """Test reasoner wrapping functionality."""
        manager = MemoryIntegrationManager(integration_config)
        await manager.initialize()
        
        wrapped_reasoner = manager.wrap_reasoner(mock_base_reasoner)
        
        assert isinstance(wrapped_reasoner, EnhancedReasoner)
        assert wrapped_reasoner._base_reasoner == mock_base_reasoner
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_operator_wrapping(self, integration_config, mock_base_operator):
        """Test operator wrapping functionality."""
        manager = MemoryIntegrationManager(integration_config)
        await manager.initialize()
        
        wrapped_operator = manager.wrap_operator(mock_base_operator)
        
        assert isinstance(wrapped_operator, EnhancedOperator)
        assert wrapped_operator._base_operator == mock_base_operator
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_manager_with_disabled_memory(self, mock_base_reasoner, 
                                              mock_base_operator):
        """Test manager behavior when memory is disabled."""
        config = MemoryServiceConfig()
        config.enabled = False
        
        manager = MemoryIntegrationManager(config)
        await manager.initialize()
        
        # Should return original instances when disabled
        wrapped_reasoner = manager.wrap_reasoner(mock_base_reasoner)
        wrapped_operator = manager.wrap_operator(mock_base_operator)
        
        assert wrapped_reasoner == mock_base_reasoner
        assert wrapped_operator == mock_base_operator
        
        await manager.cleanup()


class TestMemoryIntegrationEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_memory_flow(self, integration_config, mock_base_reasoner,
                                      mock_base_operator, test_job, test_task):
        """Test complete memory integration flow."""
        # Initialize integration manager
        manager = MemoryIntegrationManager(integration_config)
        await manager.initialize()
        
        # Wrap components
        enhanced_reasoner = manager.wrap_reasoner(mock_base_reasoner)
        enhanced_operator = manager.wrap_operator(mock_base_operator)
        
        # Mock MemFuse responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"results": []}}
        
        with patch.object(manager._memory_service._client, 'post', 
                         return_value=mock_response):
            # Test reasoner execution
            reasoning_result = await enhanced_reasoner.infer(test_task)
            assert reasoning_result == "Test reasoning result"
            
            # Test operator execution
            operator_result = await enhanced_operator.execute(
                reasoner=enhanced_reasoner,
                job=test_job
            )
            assert operator_result is not None
        
        await manager.cleanup()
