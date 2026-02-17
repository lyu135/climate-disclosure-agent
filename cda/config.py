"""
Configuration module for Climate Disclosure Agent (CDA).

This module defines the global configuration settings for the CDA system,
including LLM settings, API keys, and other environmental configurations.
"""

import os
from typing import Optional, Dict, Any, List
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

    # News Validator Configuration
    news_validator_enabled: bool = True
    """Whether the news consistency validator is enabled."""

    news_api_provider: str = "brave"  # "google" | "bing" | "brave"
    """Provider for news API (brave, google, bing)."""

    news_api_key: Optional[str] = None
    """API key for news service."""

    news_max_articles: int = 50
    """Maximum number of articles to fetch."""

    news_llm_provider: str = "openai"
    """LLM provider for news processing."""

    news_llm_model: str = "gpt-3.5-turbo"
    """LLM model for news processing."""

    news_default_keywords: List[str] = None
    """Default keywords for news search."""

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

        if self.news_api_key is None:
            self.news_api_key = os.getenv('NEWS_API_KEY')
            
        if self.environment is None:
            self.environment = os.getenv('ENVIRONMENT', 'production')

        # Set default keywords if not provided
        if self.news_default_keywords is None:
            self.news_default_keywords = [
                "environment", "climate", "pollution", "emission",
                "fine", "penalty", "lawsuit", "violation",
                "regulation", "investigation"
            ]

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
            news_validator_enabled=os.getenv('NEWS_VALIDATOR_ENABLED', 'true').lower() == 'true',
            news_api_provider=os.getenv('NEWS_API_PROVIDER', 'brave'),
            news_api_key=os.getenv('NEWS_API_KEY'),
            news_max_articles=int(os.getenv('NEWS_MAX_ARTICLES', '50')),
            news_llm_provider=os.getenv('NEWS_LLM_PROVIDER', 'openai'),
            news_llm_model=os.getenv('NEWS_LLM_MODEL', 'gpt-3.5-turbo'),
            news_default_keywords=(
                os.getenv('NEWS_DEFAULT_KEYWORDS', 
                         "environment,climate,pollution,emission,fine,penalty,lawsuit,violation,regulation,investigation")
                .split(',')
            ),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '5')),
            timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', '60')),
            environment=os.getenv('ENVIRONMENT', 'production'),
            cache_enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            cache_ttl_minutes=int(os.getenv('CACHE_TTL_MINUTES', '1440'))
        )