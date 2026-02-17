"""
Base module for output components in Climate Disclosure Agent (CDA).

This module defines the abstract base classes for output renderers,
which define the interface for formatting and presenting extracted data.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..base import BaseComponent


class OutputRenderer(BaseComponent, ABC):
    """
    Abstract base class for output renderers in Climate Disclosure Agent.
    
    Output renderers are responsible for formatting and presenting
    extracted data in various formats such as JSON, CSV, HTML, etc.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the output renderer with optional configuration.
        
        Args:
            config: Optional configuration dictionary for the renderer
        """
        super().__init__(config)
    
    @abstractmethod
    def can_render(self, data: Any, format_type: str) -> bool:
        """
        Determine if this renderer can handle the given data and format.
        
        Args:
            data: The data to be rendered
            format_type: The desired output format
            
        Returns:
            True if this renderer can handle the data and format, False otherwise
        """
        pass
    
    @abstractmethod
    def render(self, data: Dict[str, Any], format_type: str) -> str:
        """
        Render the data in the specified format.
        
        Args:
            data: The data to render
            format_type: The format to render the data in (e.g., 'json', 'csv', 'html')
            
        Returns:
            A string representation of the rendered data
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get a list of supported output formats.
        
        Returns:
            A list of strings representing supported formats
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate the data before rendering.
        
        Args:
            data: The data to validate
            
        Returns:
            True if the data is valid for rendering, False otherwise
        """
        # Basic validation - check that data is a non-empty dictionary
        return isinstance(data, dict) and len(data) > 0
    
    def prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the data for rendering by performing any necessary transformations.
        
        Args:
            data: The raw data to prepare
            
        Returns:
            The prepared data ready for rendering
        """
        # Default implementation - return data as is
        return data