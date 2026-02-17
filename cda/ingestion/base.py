"""
Base module for ingestion components in Climate Disclosure Agent (CDA).

This module defines the abstract base classes for input handling,
which define the interface for ingesting various document formats.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path


class InputHandler(ABC):
    """
    Abstract base class for input handlers in Climate Disclosure Agent.
    
    Input handlers are responsible for ingesting and preprocessing
    various document formats before they are processed by the extraction
    components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the input handler with optional configuration.
        
        Args:
            config: Optional configuration dictionary for the handler
        """
        self.config = config or {}
    
    @abstractmethod
    def can_handle(self, source: Any) -> bool:
        """
        Determine if this handler can process the given source.
        
        Args:
            source: The input source to check (could be a file path, URL, etc.)
            
        Returns:
            True if this handler can process the source, False otherwise
        """
        pass
    
    @abstractmethod
    def ingest(self, source: Any) -> List[Dict[str, Any]]:
        """
        Ingest the source and return a list of structured data.
        
        Args:
            source: The input source to ingest
            
        Returns:
            A list of dictionaries containing the ingested data
        """
        pass
    
    def preprocess(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess the ingested data before extraction.
        
        This method can be overridden by subclasses to implement
        custom preprocessing logic.
        
        Args:
            data: The raw ingested data
            
        Returns:
            The preprocessed data
        """
        return data
    
    def validate_source(self, source: Any) -> bool:
        """
        Validate the source before ingestion.
        
        Args:
            source: The input source to validate
            
        Returns:
            True if the source is valid, False otherwise
        """
        if isinstance(source, (str, Path)):
            return Path(source).exists()
        return True  # For other types, assume valid unless proven otherwise