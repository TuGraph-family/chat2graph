"""
Enhanced Memory Service for Chat2Graph integration with MemFuse.

This module provides a singleton service for integrating Chat2Graph with the external
MemFuse memory system, enabling persistent storage and retrieval of reasoning logs
and operator execution experiences.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from app.core.common.singleton import Singleton
from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.model.task import Task


class MemoryType(Enum):
    """Types of memory entries that can be stored and retrieved."""
    REASONING_LOG = "reasoning_log"
    OPERATOR_LOG = "operator_log"
    WORKFLOW_EXPERIENCE = "workflow_experience"


@dataclass
class MemoryEntry:
    """Data structure for memory entries."""
    session_id: str
    job_id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any]
    operator_id: Optional[str] = None
    workflow_id: Optional[str] = None


@dataclass
class RetrievalQuery:
    """Data structure for memory retrieval queries."""
    query: str
    session_id: str
    memory_type: Optional[MemoryType] = None
    top_k: int = 10
    operator_id: Optional[str] = None


@dataclass
class RetrievalResult:
    """Data structure for memory retrieval results."""
    content: str
    score: float
    metadata: Dict[str, Any]
    memory_type: MemoryType


class MemoryServiceConfig:
    """Configuration for MemoryService."""
    
    def __init__(self):
        self.memfuse_base_url = "http://localhost:8001"
        self.enabled = True
        self.timeout = 30.0
        self.retry_count = 3
        self.async_write = True
        self.retrieval_enabled = True
        self.max_content_length = 10000  # Maximum content length for memory entries
        self.cache_ttl = 300  # Cache TTL in seconds


class MemoryServiceInterface(ABC):
    """Interface definition for MemoryService."""
    
    @abstractmethod
    async def write_reasoning_log(self, session_id: str, job_id: str, 
                                operator_id: str, reasoning_messages: List[ModelMessage]) -> bool:
        """Write reasoning log to memory."""
        pass
    
    @abstractmethod
    async def write_operator_log(self, session_id: str, job_id: str, 
                               operator_id: str, operator_result: WorkflowMessage) -> bool:
        """Write operator execution log to memory."""
        pass
    
    @abstractmethod
    async def retrieve_relevant_memories(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Retrieve relevant memories from storage."""
        pass
    
    @abstractmethod
    async def write_workflow_experience(self, session_id: str, job_id: str,
                                      workflow_id: str, experience_data: Dict[str, Any]) -> bool:
        """Write workflow execution experience to memory."""
        pass


class MemoryService(MemoryServiceInterface, metaclass=Singleton):
    """
    Enhanced Memory Service for Chat2Graph.
    
    This service provides integration with the external MemFuse memory system,
    enabling persistent storage and intelligent retrieval of reasoning logs
    and operator execution experiences.
    
    Key responsibilities:
    1. API interaction with MemFuse service
    2. Data format conversion and validation
    3. Error handling and retry mechanisms
    4. Configuration management
    """
    
    def __init__(self, config: Optional[MemoryServiceConfig] = None):
        self._config = config or MemoryServiceConfig()
        self._client = httpx.AsyncClient(timeout=self._config.timeout)
        self._logger = logging.getLogger(__name__)
        self._retrieval_cache: Dict[str, tuple] = {}  # Cache for retrieval results
        
    @property
    def is_enabled(self) -> bool:
        """Check if memory service is enabled."""
        return self._config.enabled
    
    async def write_reasoning_log(self, session_id: str, job_id: str, 
                                operator_id: str, reasoning_messages: List[ModelMessage]) -> bool:
        """
        Write reasoning log to MemFuse memory system.
        
        Args:
            session_id: Session identifier
            job_id: Job identifier
            operator_id: Operator identifier
            reasoning_messages: List of reasoning messages from the inference process
            
        Returns:
            bool: True if write was successful, False otherwise
        """
        if not self._config.enabled:
            return True
            
        try:
            log_content = self._format_reasoning_log(reasoning_messages, job_id, operator_id)
            
            if len(log_content) > self._config.max_content_length:
                log_content = log_content[:self._config.max_content_length] + "... [TRUNCATED]"
            
            response = await self._client.post(
                f"{self._config.memfuse_base_url}/sessions/{session_id}/messages",
                json={
                    "content": log_content,
                    "metadata": {
                        "type": "reasoning_log",
                        "job_id": job_id,
                        "operator_id": operator_id,
                        "message_count": len(reasoning_messages),
                        "timestamp": time.time()
                    }
                }
            )
            
            success = response.status_code == 200
            if success:
                self._logger.debug(f"Successfully wrote reasoning log for operator {operator_id}")
            else:
                self._logger.warning(f"Failed to write reasoning log: HTTP {response.status_code}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to write reasoning log: {e}")
            return False
    
    async def write_operator_log(self, session_id: str, job_id: str, 
                               operator_id: str, operator_result: WorkflowMessage) -> bool:
        """
        Write operator execution log to MemFuse memory system.
        
        Args:
            session_id: Session identifier
            job_id: Job identifier
            operator_id: Operator identifier
            operator_result: Result of operator execution
            
        Returns:
            bool: True if write was successful, False otherwise
        """
        if not self._config.enabled:
            return True
            
        try:
            log_content = self._format_operator_log(operator_result, job_id, operator_id)
            
            if len(log_content) > self._config.max_content_length:
                log_content = log_content[:self._config.max_content_length] + "... [TRUNCATED]"
            
            # Use tag=m3 for operator logs to leverage MemFuse's workflow memory
            response = await self._client.post(
                f"{self._config.memfuse_base_url}/sessions/{session_id}/messages?tag=m3",
                json={
                    "content": log_content,
                    "metadata": {
                        "type": "operator_log",
                        "job_id": job_id,
                        "operator_id": operator_id,
                        "status": operator_result.status.value if operator_result.status else "unknown",
                        "timestamp": time.time()
                    }
                }
            )
            
            success = response.status_code == 200
            if success:
                self._logger.debug(f"Successfully wrote operator log for {operator_id}")
            else:
                self._logger.warning(f"Failed to write operator log: HTTP {response.status_code}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to write operator log: {e}")
            return False
    
    async def retrieve_relevant_memories(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """
        Retrieve relevant memories from MemFuse memory system.
        
        Args:
            query: Retrieval query parameters
            
        Returns:
            List of retrieval results
        """
        if not self._config.enabled or not self._config.retrieval_enabled:
            return []
        
        # Check cache first
        cache_key = self._generate_cache_key(query)
        if cache_key in self._retrieval_cache:
            cached_result, timestamp = self._retrieval_cache[cache_key]
            if time.time() - timestamp < self._config.cache_ttl:
                return cached_result
            
        try:
            url = f"{self._config.memfuse_base_url}/api/v1/users/{query.session_id}/query"
            params = {}
            
            # Set tag parameter based on memory type
            if query.memory_type in [MemoryType.OPERATOR_LOG, MemoryType.WORKFLOW_EXPERIENCE]:
                params["tag"] = "m3"
            
            request_data = {
                "query": query.query,
                "top_k": query.top_k,
                "session_id": query.session_id
            }
            
            response = await self._client.post(url, json=request_data, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = self._parse_retrieval_results(data.get("data", {}).get("results", []))
                
                # Cache the results
                self._retrieval_cache[cache_key] = (results, time.time())
                
                self._logger.debug(f"Retrieved {len(results)} memories for query: {query.query[:50]}...")
                return results
            else:
                self._logger.warning(f"Retrieval failed with status {response.status_code}")
                return []
                
        except Exception as e:
            self._logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def write_workflow_experience(self, session_id: str, job_id: str,
                                      workflow_id: str, experience_data: Dict[str, Any]) -> bool:
        """
        Write workflow execution experience to memory.
        
        Args:
            session_id: Session identifier
            job_id: Job identifier
            workflow_id: Workflow identifier
            experience_data: Experience data to store
            
        Returns:
            bool: True if write was successful, False otherwise
        """
        if not self._config.enabled:
            return True
            
        try:
            experience_content = self._format_workflow_experience(experience_data, job_id, workflow_id)
            
            response = await self._client.post(
                f"{self._config.memfuse_base_url}/sessions/{session_id}/messages?tag=m3",
                json={
                    "content": experience_content,
                    "metadata": {
                        "type": "workflow_experience",
                        "job_id": job_id,
                        "workflow_id": workflow_id,
                        "timestamp": time.time(),
                        **experience_data
                    }
                }
            )
            
            success = response.status_code == 200
            if success:
                self._logger.debug(f"Successfully wrote workflow experience for {workflow_id}")
            else:
                self._logger.warning(f"Failed to write workflow experience: HTTP {response.status_code}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to write workflow experience: {e}")
            return False
    
    def _format_reasoning_log(self, messages: List[ModelMessage], job_id: str, operator_id: str) -> str:
        """Format reasoning messages into a structured log."""
        log_parts = [
            "=== REASONING LOG ===",
            f"Job ID: {job_id}",
            f"Operator ID: {operator_id}",
            f"Message Count: {len(messages)}",
            f"Timestamp: {time.time()}",
            "=== MESSAGES ==="
        ]
        
        for i, msg in enumerate(messages):
            log_parts.append(f"[{i+1}] {msg.source_type.value}: {msg.get_payload()}")
        
        log_parts.append("=== END REASONING LOG ===")
        return "\n".join(log_parts)
    
    def _format_operator_log(self, result: WorkflowMessage, job_id: str, operator_id: str) -> str:
        """Format operator execution result into a structured log."""
        return f"""=== OPERATOR EXECUTION LOG ===
Job ID: {job_id}
Operator ID: {operator_id}
Timestamp: {time.time()}
Status: {result.status.value if result.status else 'unknown'}
Result: {result.scratchpad}
Evaluation: {result.evaluation or 'N/A'}
Lesson: {result.lesson or 'N/A'}
=== END OPERATOR LOG ==="""
    
    def _format_workflow_experience(self, experience_data: Dict[str, Any], 
                                  job_id: str, workflow_id: str) -> str:
        """Format workflow experience data into a structured log."""
        return f"""=== WORKFLOW EXPERIENCE ===
Job ID: {job_id}
Workflow ID: {workflow_id}
Timestamp: {time.time()}
Experience Data: {json.dumps(experience_data, indent=2)}
=== END WORKFLOW EXPERIENCE ==="""
    
    def _parse_retrieval_results(self, raw_results: List[Dict[str, Any]]) -> List[RetrievalResult]:
        """Parse raw retrieval results from MemFuse API."""
        results = []
        for item in raw_results:
            try:
                metadata = item.get("metadata", {})
                mem_type_str = metadata.get("type", "reasoning_log")
                
                # Map memory type string to enum
                memory_type = MemoryType.REASONING_LOG
                for mem_type in MemoryType:
                    if mem_type.value == mem_type_str:
                        memory_type = mem_type
                        break
                
                results.append(RetrievalResult(
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    metadata=metadata,
                    memory_type=memory_type
                ))
            except Exception as e:
                self._logger.warning(f"Failed to parse retrieval result: {e}")
                continue
        
        return results
    
    def _generate_cache_key(self, query: RetrievalQuery) -> str:
        """Generate cache key for retrieval query."""
        key_parts = [
            query.query,
            query.session_id,
            str(query.memory_type.value if query.memory_type else "all"),
            str(query.top_k),
            query.operator_id or "none"
        ]
        return "|".join(key_parts)
    
    async def health_check(self) -> bool:
        """Check if MemFuse service is healthy."""
        try:
            response = await self._client.get(f"{self._config.memfuse_base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self._client.aclose()
        self._retrieval_cache.clear()
