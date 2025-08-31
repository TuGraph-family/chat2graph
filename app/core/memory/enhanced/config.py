"""
Configuration management for enhanced Memory functionality.

This module provides configuration classes and utilities for managing
Memory service settings, including MemFuse integration parameters,
performance tuning, and feature toggles.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryConfig:
    """Configuration for Memory functionality."""
    
    # MemFuse service configuration
    memfuse_base_url: str = "http://localhost:8001"
    memfuse_timeout: float = 30.0
    memfuse_retry_count: int = 3
    
    # Feature toggles
    enabled: bool = True
    retrieval_enabled: bool = True
    async_write: bool = True
    
    # Performance settings
    max_content_length: int = 10000
    cache_ttl: int = 300  # Cache TTL in seconds
    retrieval_top_k: int = 5
    max_memories_in_context: int = 3
    
    # Logging settings
    log_level: str = "INFO"
    log_memory_operations: bool = True
    
    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """Create configuration from environment variables."""
        return cls(
            memfuse_base_url=os.getenv("MEMFUSE_BASE_URL", "http://localhost:8001"),
            memfuse_timeout=float(os.getenv("MEMFUSE_TIMEOUT", "30.0")),
            memfuse_retry_count=int(os.getenv("MEMFUSE_RETRY_COUNT", "3")),
            
            enabled=os.getenv("MEMORY_ENABLED", "true").lower() == "true",
            retrieval_enabled=os.getenv(
                "MEMORY_RETRIEVAL_ENABLED", "true"
            ).lower() == "true",
            async_write=os.getenv(
                "MEMORY_ASYNC_WRITE", "true"
            ).lower() == "true",
            
            max_content_length=int(
                os.getenv("MEMORY_MAX_CONTENT_LENGTH", "10000")
            ),
            cache_ttl=int(os.getenv("MEMORY_CACHE_TTL", "300")),
            retrieval_top_k=int(os.getenv("MEMORY_RETRIEVAL_TOP_K", "5")),
            max_memories_in_context=int(
                os.getenv("MEMORY_MAX_MEMORIES_IN_CONTEXT", "3")
            ),
            
            log_level=os.getenv("MEMORY_LOG_LEVEL", "INFO"),
            log_memory_operations=os.getenv(
                "MEMORY_LOG_OPERATIONS", "true"
            ).lower() == "true",
        )
    
    def to_memory_service_config(self):
        """Convert to MemoryServiceConfig for the enhanced memory service."""
        from .memory_service import MemoryServiceConfig
        
        config = MemoryServiceConfig()
        config.memfuse_base_url = self.memfuse_base_url
        config.enabled = self.enabled
        config.timeout = self.memfuse_timeout
        config.retry_count = self.memfuse_retry_count
        config.async_write = self.async_write
        config.retrieval_enabled = self.retrieval_enabled
        config.max_content_length = self.max_content_length
        config.cache_ttl = self.cache_ttl
        
        return config
