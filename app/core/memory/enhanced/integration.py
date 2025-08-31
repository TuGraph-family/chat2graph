"""
Integration layer for enhanced Memory functionality.

This module provides wrapper classes and integration managers that enable
Memory functionality to be seamlessly integrated into existing Chat2Graph
components without breaking compatibility.
"""

import logging
from typing import Any, List, Optional

from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator

from .hook import HookManager, MemoryOperatorHook, MemoryReasonerHook, hook_manager
from .memory_service import MemoryService, MemoryServiceConfig


class EnhancedReasoner(Reasoner):
    """
    Enhanced Reasoner wrapper that integrates Memory functionality.
    
    This wrapper adds Memory capabilities to existing Reasoner implementations
    without modifying their core logic, using the decorator pattern to maintain
    full interface compatibility.
    """
    
    def __init__(self, base_reasoner: Reasoner, memory_service: Optional[MemoryService] = None):
        super().__init__()
        self._base_reasoner = base_reasoner
        self._memory_service = memory_service or MemoryService.instance
        self._logger = logging.getLogger(__name__)
        
        # Copy memories from base reasoner
        self._memories = base_reasoner._memories
    
    async def infer(self, task: Task) -> str:
        """Enhanced inference method with Memory integration."""
        
        # Execute pre-reasoning hooks
        pre_hook_results = await hook_manager.execute_pre_reasoning_hooks(task, self)
        
        # Enhance task context with retrieved memories
        retrieved_memories = []
        for result in pre_hook_results:
            if result.success and result.data and "retrieved_memories" in result.data:
                retrieved_memories.extend(result.data["retrieved_memories"])
        
        # Create enhanced task if memories were retrieved
        if retrieved_memories:
            enhanced_task = self._enhance_task_with_memories(task, retrieved_memories)
        else:
            enhanced_task = task
        
        # Execute original reasoning logic
        reasoning_result = await self._base_reasoner.infer(enhanced_task)
        
        # Get reasoning messages for post-hook
        try:
            reasoner_memory = self._base_reasoner.get_memory(task)
            messages = reasoner_memory.get_messages()
        except Exception as e:
            self._logger.warning(f"Failed to get reasoning messages: {e}")
            messages = []
        
        # Execute post-reasoning hooks
        await hook_manager.execute_post_reasoning_hooks(
            task, self, reasoning_result, messages
        )
        
        return reasoning_result
    
    def _enhance_task_with_memories(self, task: Task, memories: List[Any]) -> Task:
        """Enhance task context with retrieved memories."""
        if not memories:
            return task
        
        # Build memory context
        memory_context = "\n=== RELEVANT HISTORICAL MEMORIES ===\n"
        for i, memory in enumerate(memories[:3]):  # Limit to top 3 memories
            memory_context += f"[Memory {i+1}] Score: {memory.score:.2f}\n"
            memory_context += f"Content: {memory.content[:500]}...\n\n"  # Limit content length
        memory_context += "=== END MEMORIES ===\n"
        
        # Create enhanced job with memory context
        enhanced_job = Job(
            id=task.job.id,
            session_id=task.job.session_id,
            goal=task.job.goal,
            context=task.job.context + "\n" + memory_context,
            status=task.job.status,
            timestamp=task.job.timestamp
        )
        
        # Create enhanced task
        enhanced_task = Task(
            job=enhanced_job,
            operator_config=task.operator_config,
            workflow_messages=task.workflow_messages,
            tools=task.tools,
            actions=task.actions,
            knowledge=task.knowledge,
            insights=task.insights,
            lesson=task.lesson,
            file_descriptors=task.file_descriptors
        )
        
        return enhanced_task
    
    # Delegate other methods to base reasoner
    async def update_knowledge(self, data: Any) -> None:
        return await self._base_reasoner.update_knowledge(data)
    
    async def evaluate(self, data: Any) -> Any:
        return await self._base_reasoner.evaluate(data)
    
    async def conclude(self, reasoner_memory) -> str:
        return await self._base_reasoner.conclude(reasoner_memory)
    
    def init_memory(self, task: Task):
        return self._base_reasoner.init_memory(task)
    
    def get_memory(self, task: Task):
        return self._base_reasoner.get_memory(task)


class EnhancedOperator(Operator):
    """
    Enhanced Operator wrapper that integrates Memory functionality.
    
    This wrapper adds Memory capabilities to existing Operator implementations
    without modifying their core logic, using the decorator pattern to maintain
    full interface compatibility.
    """
    
    def __init__(self, base_operator: Operator, memory_service: Optional[MemoryService] = None):
        super().__init__(base_operator._config)
        self._base_operator = base_operator
        self._memory_service = memory_service or MemoryService.instance
        self._logger = logging.getLogger(__name__)
    
    async def execute(self, reasoner: Reasoner, job: Job,
                     workflow_messages: Optional[List[WorkflowMessage]] = None,
                     previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
                     lesson: Optional[str] = None) -> WorkflowMessage:
        """Enhanced execution method with Memory integration."""
        
        operator_id = self.get_id()
        workflow_msgs = workflow_messages or []
        
        # Execute pre-execution hooks
        pre_hook_results = await hook_manager.execute_pre_operator_hooks(
            job, reasoner, workflow_msgs, lesson, operator_id
        )
        
        # Check for early return from hooks
        for result in pre_hook_results:
            if result.success and result.data and "early_return" in result.data:
                return result.data["early_return"]
        
        # Enhance job context with retrieved memories
        retrieved_memories = []
        for result in pre_hook_results:
            if result.success and result.data and "retrieved_memories" in result.data:
                retrieved_memories.extend(result.data["retrieved_memories"])
        
        # Create enhanced job if memories were retrieved
        if retrieved_memories:
            enhanced_job = self._enhance_job_with_memories(job, retrieved_memories)
        else:
            enhanced_job = job
        
        # Execute original operator logic
        operator_result = await self._base_operator.execute(
            reasoner=reasoner,
            job=enhanced_job,
            workflow_messages=workflow_messages,
            previous_expert_outputs=previous_expert_outputs,
            lesson=lesson
        )
        
        # Execute post-execution hooks
        await hook_manager.execute_post_operator_hooks(
            job, reasoner, workflow_msgs, lesson, operator_result, operator_id
        )
        
        return operator_result
    
    def _enhance_job_with_memories(self, job: Job, memories: List[Any]) -> Job:
        """Enhance job context with retrieved memories."""
        if not memories:
            return job
        
        # Build memory context
        memory_context = "\n=== RELEVANT OPERATOR EXPERIENCES ===\n"
        for i, memory in enumerate(memories[:3]):  # Limit to top 3 memories
            memory_context += f"[Experience {i+1}] Score: {memory.score:.2f}\n"
            memory_context += f"Content: {memory.content[:500]}...\n\n"  # Limit content length
        memory_context += "=== END EXPERIENCES ===\n"
        
        # Create enhanced job with memory context
        enhanced_job = Job(
            id=job.id,
            session_id=job.session_id,
            goal=job.goal,
            context=job.context + "\n" + memory_context,
            status=job.status,
            timestamp=job.timestamp
        )
        
        return enhanced_job
    
    # Delegate other methods to base operator
    def get_knowledge(self, job: Job):
        return self._base_operator.get_knowledge(job)
    
    def get_env_insights(self):
        return self._base_operator.get_env_insights()
    
    def get_id(self) -> str:
        return self._base_operator.get_id()


class MemoryIntegrationManager:
    """
    Manager for Memory integration lifecycle.
    
    This class handles the initialization and configuration of Memory functionality,
    providing a centralized way to enable/disable and configure Memory features.
    """
    
    def __init__(self, config: Optional[MemoryServiceConfig] = None):
        self._config = config or MemoryServiceConfig()
        self._memory_service: Optional[MemoryService] = None
        self._initialized = False
        self._logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize Memory integration."""
        if self._initialized:
            return
        
        try:
            # Initialize MemoryService
            self._memory_service = MemoryService(self._config)
            
            # Register hooks if memory service is available
            if self._memory_service and self._memory_service.is_enabled:
                memory_reasoner_hook = MemoryReasonerHook(self._memory_service)
                memory_operator_hook = MemoryOperatorHook(self._memory_service)
                
                hook_manager.register_reasoner_hook(memory_reasoner_hook)
                hook_manager.register_operator_hook(memory_operator_hook)
            
            self._initialized = True
            self._logger.info("Memory integration initialized successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize memory integration: {e}")
            raise
    
    def wrap_reasoner(self, reasoner: Reasoner) -> Reasoner:
        """Wrap Reasoner with Memory functionality if enabled."""
        if not self._initialized or not self._memory_service or not self._memory_service.is_enabled:
            return reasoner
        
        return EnhancedReasoner(reasoner, self._memory_service)
    
    def wrap_operator(self, operator: Operator) -> Operator:
        """Wrap Operator with Memory functionality if enabled."""
        if not self._initialized or not self._memory_service or not self._memory_service.is_enabled:
            return operator
        
        return EnhancedOperator(operator, self._memory_service)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._memory_service:
            await self._memory_service.close()


# Global integration manager instance
memory_integration_manager = MemoryIntegrationManager()
