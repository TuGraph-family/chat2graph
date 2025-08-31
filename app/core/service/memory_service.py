"""
Memory Service for Chat2Graph integration with MemFuse.

This service provides integration with the external MemFuse memory system,
enabling persistent storage and retrieval of reasoning logs and operator
execution experiences.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.common.singleton import Singleton
from app.core.memory.enhanced import (
    MemoryService as EnhancedMemoryService,
    MemoryServiceConfig,
    MemoryType,
    RetrievalQuery,
    RetrievalResult,
)
from app.core.model.message import ModelMessage, WorkflowMessage


class MemoryService(EnhancedMemoryService, metaclass=Singleton):
    """
    Memory Service singleton for Chat2Graph.
    
    This service extends the enhanced memory service and integrates it into
    the Chat2Graph service layer following the existing singleton pattern.
    """
    
    def __init__(self, config: Optional[MemoryServiceConfig] = None):
        if config is None:
            config = self._create_config_from_env()
        
        super().__init__(config)
        self._logger = logging.getLogger(__name__)
        
        # Initialize Memory integration hooks if enabled
        if self.is_enabled:
            self._initialize_hooks()
    
    def _create_config_from_env(self) -> MemoryServiceConfig:
        """Create configuration from environment variables."""
        config = MemoryServiceConfig()
        
        # Load configuration from environment variables
        config.memfuse_base_url = os.getenv(
            "MEMFUSE_BASE_URL", "http://localhost:8001"
        )
        config.enabled = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
        config.timeout = float(os.getenv("MEMFUSE_TIMEOUT", "30.0"))
        config.retry_count = int(os.getenv("MEMFUSE_RETRY_COUNT", "3"))
        config.async_write = os.getenv(
            "MEMORY_ASYNC_WRITE", "true"
        ).lower() == "true"
        config.retrieval_enabled = os.getenv(
            "MEMORY_RETRIEVAL_ENABLED", "true"
        ).lower() == "true"
        config.max_content_length = int(
            os.getenv("MEMORY_MAX_CONTENT_LENGTH", "10000")
        )
        config.cache_ttl = int(os.getenv("MEMORY_CACHE_TTL", "300"))
        
        return config
    
    def _initialize_hooks(self):
        """Initialize Memory integration hooks."""
        try:
            from app.core.memory.enhanced.hook import (
                HookManager,
                MemoryOperatorHook,
                MemoryReasonerHook,
                hook_manager,
            )
            
            # Register Memory hooks
            memory_reasoner_hook = MemoryReasonerHook(self)
            memory_operator_hook = MemoryOperatorHook(self)
            
            hook_manager.register_reasoner_hook(memory_reasoner_hook)
            hook_manager.register_operator_hook(memory_operator_hook)
            
            self._logger.info("Memory integration hooks initialized")
            
        except ImportError as e:
            self._logger.warning(f"Failed to initialize Memory hooks: {e}")
    
    async def health_check(self) -> bool:
        """Check if MemFuse service is healthy and accessible."""
        if not self.is_enabled:
            return True
            
        try:
            # Try to connect to MemFuse service
            response = await self._client.get(
                f"{self._config.memfuse_base_url}/health",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            self._logger.warning(f"MemFuse health check failed: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to MemFuse service and return status information."""
        status = {
            "enabled": self.is_enabled,
            "memfuse_url": self._config.memfuse_base_url,
            "healthy": False,
            "error": None
        }
        
        if not self.is_enabled:
            status["error"] = "Memory service is disabled"
            return status
        
        try:
            # Test basic connectivity
            response = await self._client.get(
                f"{self._config.memfuse_base_url}/health",
                timeout=5.0
            )
            
            if response.status_code == 200:
                status["healthy"] = True
            else:
                status["error"] = f"HTTP {response.status_code}"
                
        except Exception as e:
            status["error"] = str(e)
        
        return status
