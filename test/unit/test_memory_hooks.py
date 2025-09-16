"""
Unit tests for Memory Hook functionality.

This module contains tests for the hook mechanism that integrates Memory
functionality into Reasoner and Operator execution flows.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.memory.enhanced.hook import (
    HookManager,
    HookResult,
    MemoryOperatorHook,
    MemoryReasonerHook,
)
from app.core.memory.enhanced.memory_service import (
    MemoryService,
    MemoryServiceConfig,
    MemoryType,
    RetrievalResult,
)
from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator_config import OperatorConfig
from app.core.common.type import MessageSourceType, WorkflowStatus


@pytest.fixture
def mock_memory_service():
    """Create mock memory service."""
    config = MemoryServiceConfig()
    config.enabled = True
    service = MagicMock(spec=MemoryService)
    service._config = config
    service.is_enabled = True
    return service


@pytest.fixture
def mock_task():
    """Create mock task for testing."""
    job = Job(
        id="test-job",
        session_id="test-session",
        goal="Test goal",
        context="Test context"
    )
    
    operator_config = OperatorConfig(
        id="test-operator",
        instruction="Test instruction",
        actions=[]
    )
    
    return Task(
        job=job,
        operator_config=operator_config,
        workflow_messages=[],
        tools=[],
        actions=[],
        knowledge=None,
        insights=None,
        lesson="Test lesson",
        file_descriptors=[]
    )


@pytest.fixture
def mock_reasoner():
    """Create mock reasoner."""
    return MagicMock(spec=Reasoner)


class TestMemoryReasonerHook:
    """Test cases for MemoryReasonerHook."""
    
    @pytest.mark.asyncio
    async def test_pre_reasoning_hook_with_memories(self, mock_memory_service, 
                                                  mock_task, mock_reasoner):
        """Test pre-reasoning hook when memories are found."""
        hook = MemoryReasonerHook(mock_memory_service)
        
        # Mock memory retrieval
        mock_memories = [
            RetrievalResult(
                content="Previous reasoning content",
                score=0.9,
                metadata={"type": "reasoning_log"},
                memory_type=MemoryType.REASONING_LOG
            )
        ]
        mock_memory_service.retrieve_relevant_memories.return_value = mock_memories
        
        result = await hook.pre_reasoning(mock_task, mock_reasoner)
        
        assert result is not None
        assert result.success == True
        assert "retrieved_memories" in result.data
        assert len(result.data["retrieved_memories"]) == 1
    
    @pytest.mark.asyncio
    async def test_pre_reasoning_hook_no_memories(self, mock_memory_service, 
                                                mock_task, mock_reasoner):
        """Test pre-reasoning hook when no memories are found."""
        hook = MemoryReasonerHook(mock_memory_service)
        
        # Mock empty memory retrieval
        mock_memory_service.retrieve_relevant_memories.return_value = []
        
        result = await hook.pre_reasoning(mock_task, mock_reasoner)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_post_reasoning_hook_success(self, mock_memory_service, 
                                             mock_task, mock_reasoner):
        """Test post-reasoning hook successful execution."""
        hook = MemoryReasonerHook(mock_memory_service)
        
        # Mock successful write
        mock_memory_service.write_reasoning_log.return_value = True
        
        messages = [
            ModelMessage(
                source_type=MessageSourceType.MODEL,
                payload={"content": "Test message"}
            )
        ]
        
        result = await hook.post_reasoning(
            mock_task, mock_reasoner, "reasoning result", messages
        )
        
        assert result is not None
        assert result.success == True
    
    @pytest.mark.asyncio
    async def test_pre_reasoning_hook_error_handling(self, mock_memory_service, 
                                                   mock_task, mock_reasoner):
        """Test pre-reasoning hook error handling."""
        hook = MemoryReasonerHook(mock_memory_service)
        
        # Mock memory service error
        mock_memory_service.retrieve_relevant_memories.side_effect = Exception(
            "Connection failed"
        )
        
        result = await hook.pre_reasoning(mock_task, mock_reasoner)
        
        assert result is not None
        assert result.success == False
        assert "Connection failed" in result.error


class TestMemoryOperatorHook:
    """Test cases for MemoryOperatorHook."""
    
    @pytest.mark.asyncio
    async def test_pre_execution_hook_with_memories(self, mock_memory_service):
        """Test pre-execution hook when memories are found."""
        hook = MemoryOperatorHook(mock_memory_service)
        
        job = Job(
            id="test-job",
            session_id="test-session", 
            goal="Test goal",
            context="Test context"
        )
        
        # Mock memory retrieval
        mock_memories = [
            RetrievalResult(
                content="Previous operator execution",
                score=0.85,
                metadata={"type": "operator_log"},
                memory_type=MemoryType.OPERATOR_LOG
            )
        ]
        mock_memory_service.retrieve_relevant_memories.return_value = mock_memories
        
        result = await hook.pre_execution(
            job, MagicMock(), [], None, "test-operator"
        )
        
        assert result is not None
        assert result.success == True
        assert "retrieved_memories" in result.data
    
    @pytest.mark.asyncio
    async def test_post_execution_hook_success(self, mock_memory_service, 
                                             mock_workflow_message):
        """Test post-execution hook successful execution."""
        hook = MemoryOperatorHook(mock_memory_service)
        
        job = Job(
            id="test-job",
            session_id="test-session",
            goal="Test goal", 
            context="Test context"
        )
        
        # Mock successful write
        mock_memory_service.write_operator_log.return_value = True
        
        result = await hook.post_execution(
            job, MagicMock(), [], None, mock_workflow_message, "test-operator"
        )
        
        assert result is not None
        assert result.success == True


class TestHookManager:
    """Test cases for HookManager."""
    
    def test_hook_registration(self):
        """Test hook registration functionality."""
        manager = HookManager()
        
        mock_reasoner_hook = MagicMock()
        mock_operator_hook = MagicMock()
        
        manager.register_reasoner_hook(mock_reasoner_hook)
        manager.register_operator_hook(mock_operator_hook)
        
        assert len(manager._reasoner_hooks) == 1
        assert len(manager._operator_hooks) == 1
    
    @pytest.mark.asyncio
    async def test_execute_hooks_with_results(self, mock_memory_service, 
                                            mock_task, mock_reasoner):
        """Test hook execution with results."""
        manager = HookManager()
        hook = MemoryReasonerHook(mock_memory_service)
        manager.register_reasoner_hook(hook)
        
        # Mock memory retrieval
        mock_memory_service.retrieve_relevant_memories.return_value = []
        
        results = await manager.execute_pre_reasoning_hooks(mock_task, mock_reasoner)
        
        # Should have no results since no memories were retrieved
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_hook_error_isolation(self, mock_memory_service, 
                                      mock_task, mock_reasoner):
        """Test that hook errors don't break execution."""
        manager = HookManager()
        
        # Create hook that raises exception
        failing_hook = MemoryReasonerHook(mock_memory_service)
        mock_memory_service.retrieve_relevant_memories.side_effect = Exception(
            "Test error"
        )
        
        manager.register_reasoner_hook(failing_hook)
        
        results = await manager.execute_pre_reasoning_hooks(mock_task, mock_reasoner)
        
        # Should have one failed result
        assert len(results) == 1
        assert results[0].success == False
        assert "Test error" in results[0].error
