"""
Memory Enhancement Demo for Chat2Graph.

This script demonstrates the enhanced memory functionality by showing
how reasoning logs and operator experiences are stored and retrieved
from the MemFuse memory service.
"""

import asyncio
import logging
import os
from typing import List

from app.core.memory.enhanced import MemoryConfig, MemoryService
from app.core.memory.enhanced.integration import MemoryIntegrationManager
from app.core.model.job import Job
from app.core.model.message import ModelMessage, WorkflowMessage
from app.core.model.task import Task
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.common.type import MessageSourceType, WorkflowStatus


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_memory_service():
    """Demonstrate basic MemoryService functionality."""
    print("=== MemoryService Demo ===")
    
    # Create memory service with test configuration
    config = MemoryConfig.from_env()
    memory_service = MemoryService(config.to_memory_service_config())
    
    # Test connection to MemFuse
    connection_status = await memory_service.test_connection()
    print(f"MemFuse Connection Status: {connection_status}")
    
    if not connection_status["healthy"]:
        print(f"Warning: MemFuse service not available - {connection_status['error']}")
        print("Please ensure MemFuse is running on http://localhost:8001")
        return
    
    # Create test data
    job = Job(
        id="demo-job-001",
        session_id="demo-session-001", 
        goal="Demonstrate memory functionality",
        context="This is a demo of the enhanced memory system"
    )
    
    # Demo reasoning log write
    reasoning_messages = [
        ModelMessage(
            source_type=MessageSourceType.USER,
            payload={"content": "User: How does memory enhancement work?"}
        ),
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload={"content": "Assistant: Memory enhancement stores reasoning logs..."}
        )
    ]
    
    print("\n1. Writing reasoning log to memory...")
    write_success = await memory_service.write_reasoning_log(
        session_id=job.session_id,
        job_id=job.id,
        operator_id="demo-operator",
        reasoning_messages=reasoning_messages
    )
    print(f"Reasoning log write success: {write_success}")
    
    # Demo operator log write
    operator_result = WorkflowMessage(
        payload={
            "scratchpad": "Demo operator executed successfully",
            "status": WorkflowStatus.SUCCESS,
            "evaluation": "Operation completed without errors",
            "lesson": "Memory integration works as expected"
        },
        job_id=job.id
    )
    
    print("\n2. Writing operator log to memory...")
    operator_write_success = await memory_service.write_operator_log(
        session_id=job.session_id,
        job_id=job.id,
        operator_id="demo-operator",
        operator_result=operator_result
    )
    print(f"Operator log write success: {operator_write_success}")
    
    # Demo memory retrieval
    from app.core.memory.enhanced import RetrievalQuery, MemoryType
    
    print("\n3. Retrieving relevant memories...")
    query = RetrievalQuery(
        query="memory enhancement demonstration",
        session_id=job.session_id,
        memory_type=MemoryType.REASONING_LOG,
        top_k=3
    )
    
    memories = await memory_service.retrieve_relevant_memories(query)
    print(f"Retrieved {len(memories)} memories")
    
    for i, memory in enumerate(memories):
        print(f"  Memory {i+1}: Score={memory.score:.2f}, Type={memory.memory_type.value}")
        print(f"    Content: {memory.content[:100]}...")
    
    await memory_service.close()
    print("\nMemoryService demo completed!")


async def demo_configuration():
    """Demonstrate configuration management."""
    print("\n=== Configuration Demo ===")
    
    # Load configuration from environment
    config = MemoryConfig.from_env()
    
    print("Current Memory Configuration:")
    print(f"  Enabled: {config.enabled}")
    print(f"  MemFuse URL: {config.memfuse_base_url}")
    print(f"  Retrieval Enabled: {config.retrieval_enabled}")
    print(f"  Async Write: {config.async_write}")
    print(f"  Cache TTL: {config.cache_ttl} seconds")
    print(f"  Max Content Length: {config.max_content_length} bytes")
    print(f"  Retrieval Top K: {config.retrieval_top_k}")


async def main():
    """Run all memory enhancement demos."""
    print("🧠 Chat2Graph Memory Enhancement Demo")
    print("=" * 50)
    
    # Check if MemFuse URL is configured
    memfuse_url = os.getenv("MEMFUSE_BASE_URL", "http://localhost:8001")
    print(f"MemFuse Service URL: {memfuse_url}")
    
    try:
        # Demo 1: Basic MemoryService functionality
        await demo_memory_service()
        
        # Demo 2: Configuration management
        await demo_configuration()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\nDemo failed: {e}")
        print("Please ensure:")
        print("1. MemFuse service is running on http://localhost:8001")
        print("2. Environment variables are properly configured")
        print("3. All dependencies are installed")
    
    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
