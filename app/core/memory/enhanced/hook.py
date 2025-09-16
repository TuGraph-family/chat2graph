"""
Hook mechanism for integrating Memory functionality into Chat2Graph.

This module provides a non-intrusive hook system that allows Memory functionality
to be integrated into existing Reasoner and Operator execution flows without
modifying the core logic.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner

from .memory_service import MemoryService, MemoryType, RetrievalQuery


class HookResult:
    """Result of hook execution."""
    
    def __init__(self, success: bool, data: Optional[Any] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error


class ReasonerHook(ABC):
    """Abstract base class for Reasoner hooks."""
    
    @abstractmethod
    async def pre_reasoning(self, task: Task, reasoner: Reasoner) -> Optional[HookResult]:
        """Hook executed before reasoning process."""
        pass
    
    @abstractmethod
    async def post_reasoning(self, task: Task, reasoner: Reasoner, 
                           reasoning_result: str, messages: List[ModelMessage]) -> Optional[HookResult]:
        """Hook executed after reasoning process."""
        pass


class OperatorHook(ABC):
    """Abstract base class for Operator hooks."""
    
    @abstractmethod
    async def pre_execution(self, job: Job, reasoner: Reasoner, 
                          workflow_messages: List[WorkflowMessage], 
                          lesson: Optional[str], operator_id: str) -> Optional[HookResult]:
        """Hook executed before operator execution."""
        pass
    
    @abstractmethod
    async def post_execution(self, job: Job, reasoner: Reasoner,
                           workflow_messages: List[WorkflowMessage],
                           lesson: Optional[str], operator_result: WorkflowMessage,
                           operator_id: str) -> Optional[HookResult]:
        """Hook executed after operator execution."""
        pass


class MemoryReasonerHook(ReasonerHook):
    """Memory integration hook for Reasoner."""
    
    def __init__(self, memory_service: MemoryService):
        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)
    
    async def pre_reasoning(self, task: Task, reasoner: Reasoner) -> Optional[HookResult]:
        """Retrieve relevant reasoning memories before inference."""
        try:
            if not task.operator_config:
                return None
                
            # Construct retrieval query
            query_text = self._build_reasoning_query(task)
            
            query = RetrievalQuery(
                query=query_text,
                session_id=task.job.session_id,
                memory_type=MemoryType.REASONING_LOG,
                top_k=5,
                operator_id=task.operator_config.id
            )
            
            # Retrieve relevant memories
            memories = await self._memory_service.retrieve_relevant_memories(query)
            
            if memories:
                self._logger.info(f"Retrieved {len(memories)} relevant reasoning memories for operator {task.operator_config.id}")
                return HookResult(success=True, data={"retrieved_memories": memories})
            
            return None
            
        except Exception as e:
            self._logger.error(f"Pre-reasoning hook failed: {e}")
            return HookResult(success=False, error=str(e))
    
    async def post_reasoning(self, task: Task, reasoner: Reasoner, 
                           reasoning_result: str, messages: List[ModelMessage]) -> Optional[HookResult]:
        """Write reasoning log to memory after inference."""
        try:
            if not task.operator_config or not messages:
                return None
                
            # Asynchronously write reasoning log
            if self._memory_service._config.async_write:
                asyncio.create_task(self._memory_service.write_reasoning_log(
                    session_id=task.job.session_id,
                    job_id=task.job.id,
                    operator_id=task.operator_config.id,
                    reasoning_messages=messages
                ))
                return HookResult(success=True)
            else:
                success = await self._memory_service.write_reasoning_log(
                    session_id=task.job.session_id,
                    job_id=task.job.id,
                    operator_id=task.operator_config.id,
                    reasoning_messages=messages
                )
                return HookResult(success=success)
                
        except Exception as e:
            self._logger.error(f"Post-reasoning hook failed: {e}")
            return HookResult(success=False, error=str(e))
    
    def _build_reasoning_query(self, task: Task) -> str:
        """Build query text for reasoning memory retrieval."""
        query_parts = [
            f"Job Goal: {task.job.goal}",
            f"Operator: {task.operator_config.id}",
            f"Context: {task.job.context[:500]}..."  # Limit context length
        ]
        
        if task.lesson:
            query_parts.append(f"Lesson: {task.lesson}")
            
        return "\n".join(query_parts)


class MemoryOperatorHook(OperatorHook):
    """Memory integration hook for Operator."""
    
    def __init__(self, memory_service: MemoryService):
        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)
    
    async def pre_execution(self, job: Job, reasoner: Reasoner, 
                          workflow_messages: List[WorkflowMessage], 
                          lesson: Optional[str], operator_id: str) -> Optional[HookResult]:
        """Retrieve relevant operator execution memories before execution."""
        try:
            # Construct retrieval query
            query_text = self._build_operator_query(job, operator_id, lesson)
            
            query = RetrievalQuery(
                query=query_text,
                session_id=job.session_id,
                memory_type=MemoryType.OPERATOR_LOG,
                top_k=5,
                operator_id=operator_id
            )
            
            # Retrieve relevant memories
            memories = await self._memory_service.retrieve_relevant_memories(query)
            
            if memories:
                self._logger.info(f"Retrieved {len(memories)} relevant operator memories for {operator_id}")
                return HookResult(success=True, data={"retrieved_memories": memories})
            
            return None
            
        except Exception as e:
            self._logger.error(f"Pre-execution hook failed: {e}")
            return HookResult(success=False, error=str(e))
    
    async def post_execution(self, job: Job, reasoner: Reasoner,
                           workflow_messages: List[WorkflowMessage],
                           lesson: Optional[str], operator_result: WorkflowMessage,
                           operator_id: str) -> Optional[HookResult]:
        """Write operator execution log to memory after execution."""
        try:
            # Asynchronously write operator log
            if self._memory_service._config.async_write:
                asyncio.create_task(self._memory_service.write_operator_log(
                    session_id=job.session_id,
                    job_id=job.id,
                    operator_id=operator_id,
                    operator_result=operator_result
                ))
                return HookResult(success=True)
            else:
                success = await self._memory_service.write_operator_log(
                    session_id=job.session_id,
                    job_id=job.id,
                    operator_id=operator_id,
                    operator_result=operator_result
                )
                return HookResult(success=success)
                
        except Exception as e:
            self._logger.error(f"Post-execution hook failed: {e}")
            return HookResult(success=False, error=str(e))
    
    def _build_operator_query(self, job: Job, operator_id: str, lesson: Optional[str]) -> str:
        """Build query text for operator memory retrieval."""
        query_parts = [
            f"Job Goal: {job.goal}",
            f"Operator: {operator_id}",
            f"Context: {job.context[:500]}..."  # Limit context length
        ]
        
        if lesson:
            query_parts.append(f"Lesson: {lesson}")
            
        return "\n".join(query_parts)


class HookManager:
    """Manager for coordinating hook execution."""
    
    def __init__(self):
        self._reasoner_hooks: List[ReasonerHook] = []
        self._operator_hooks: List[OperatorHook] = []
        self._logger = logging.getLogger(__name__)
    
    def register_reasoner_hook(self, hook: ReasonerHook):
        """Register a reasoner hook."""
        self._reasoner_hooks.append(hook)
        self._logger.debug(f"Registered reasoner hook: {hook.__class__.__name__}")
    
    def register_operator_hook(self, hook: OperatorHook):
        """Register an operator hook."""
        self._operator_hooks.append(hook)
        self._logger.debug(f"Registered operator hook: {hook.__class__.__name__}")
    
    async def execute_pre_reasoning_hooks(self, task: Task, reasoner: Reasoner) -> List[HookResult]:
        """Execute all pre-reasoning hooks."""
        results = []
        for hook in self._reasoner_hooks:
            try:
                result = await hook.pre_reasoning(task, reasoner)
                if result:
                    results.append(result)
            except Exception as e:
                self._logger.error(f"Reasoner pre-hook failed: {e}")
                results.append(HookResult(success=False, error=str(e)))
        return results
    
    async def execute_post_reasoning_hooks(self, task: Task, reasoner: Reasoner,
                                         reasoning_result: str, messages: List[ModelMessage]) -> List[HookResult]:
        """Execute all post-reasoning hooks."""
        results = []
        for hook in self._reasoner_hooks:
            try:
                result = await hook.post_reasoning(task, reasoner, reasoning_result, messages)
                if result:
                    results.append(result)
            except Exception as e:
                self._logger.error(f"Reasoner post-hook failed: {e}")
                results.append(HookResult(success=False, error=str(e)))
        return results
    
    async def execute_pre_operator_hooks(self, job: Job, reasoner: Reasoner,
                                       workflow_messages: List[WorkflowMessage],
                                       lesson: Optional[str], operator_id: str) -> List[HookResult]:
        """Execute all pre-operator hooks."""
        results = []
        for hook in self._operator_hooks:
            try:
                result = await hook.pre_execution(job, reasoner, workflow_messages, lesson, operator_id)
                if result:
                    results.append(result)
            except Exception as e:
                self._logger.error(f"Operator pre-hook failed: {e}")
                results.append(HookResult(success=False, error=str(e)))
        return results
    
    async def execute_post_operator_hooks(self, job: Job, reasoner: Reasoner,
                                        workflow_messages: List[WorkflowMessage],
                                        lesson: Optional[str], operator_result: WorkflowMessage,
                                        operator_id: str) -> List[HookResult]:
        """Execute all post-operator hooks."""
        results = []
        for hook in self._operator_hooks:
            try:
                result = await hook.post_execution(job, reasoner, workflow_messages, 
                                                 lesson, operator_result, operator_id)
                if result:
                    results.append(result)
            except Exception as e:
                self._logger.error(f"Operator post-hook failed: {e}")
                results.append(HookResult(success=False, error=str(e)))
        return results


# Global hook manager instance
hook_manager = HookManager()
