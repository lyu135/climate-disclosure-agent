"""
Configuration module for Climate Disclosure Agent (CDA).

This module defines the global configuration settings for the CDA system,
including LLM settings, API keys, and other environmental configurations.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Config:
    """
    Global configuration class for Climate Disclosure Agent.
    
    Contains all configuration parameters needed for the CDA system,
    including LLM settings, API keys, and processing options.
    """
    
    # LLM Configuration
    llm_model: str = "gpt-4"
    """The language model to use for extraction and processing."""
    
    llm_api_key: Optional[str] = None
    """API key for the language model service."""
    
    llm_base_url: Optional[str] = None
    """Base URL for the language model API."""
    
    llm_temperature: float = 0.1
    """Temperature setting for language model responses."""
    
    llm_max_tokens: int = 4096
    """Maximum tokens to generate in language model responses."""
    
    # Processing Configuration
    max_concurrent_requests: int = 5
    """Maximum number of concurrent API requests."""
    
    timeout_seconds: int = 60
    """Timeout for API requests in seconds."""
    
    # Environmental variables
    environment: str = "production"
    """Current environment (development, staging, production)."""
    
    # Cache settings
    cache_enabled: bool = True
    """Whether caching is enabled for processed documents."""
    
    cache_ttl_minutes: int = 1440  # 24 hours
    """Time-to-live for cached entries in minutes."""
    
    def __post_init__(self):
        """Load configuration from environment variables if not set."""
        if self.llm_api_key is None:
            self.llm_api_key = os.getenv('LLM_API_KEY')
        
        if self.llm_base_url is None:
            self.llm_base_url = os.getenv('LLM_BASE_URL')
        
        if self.environment is None:
            self.environment = os.getenv('ENVIRONMENT', 'production')

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create a Config instance from a dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})

    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        return cls(
            llm_model=os.getenv('LLM_MODEL', 'gpt-4'),
            llm_api_key=os.getenv('LLM_API_KEY'),
            llm_base_url=os.getenv('LLM_BASE_URL'),
            llm_temperature=float(os.getenv('LLM_TEMPERATURE', '0.1')),
            llm_max_tokens=int(os.getenv('LLM_MAX_TOKENS', '4096')),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '5')),
            timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', '60')),
            environment=os.getenv('ENVIRONMENT', 'production'),
            cache_enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            cache_ttl_minutes=int(os.getenv('CACHE_TTL_MINUTES', '1440'))
        )