"""
Base module for extraction components in Climate Disclosure Agent (CDA).

This module defines the abstract base classes for data extractors,
which define the interface for extracting structured information
from ingested documents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..base import BaseComponent


class Extractor(BaseComponent, ABC):
    """
    Abstract base class for extractors in Climate Disclosure Agent.
    
    Extractors are responsible for extracting structured information
    from ingested documents according to predefined schemas or
    configurable rules.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extractor with optional configuration.
        
        Args:
            config: Optional configuration dictionary for the extractor
        """
        super().__init__(config)
    
    @abstractmethod
    def can_extract(self, data: Any) -> bool:
        """
        Determine if this extractor can process the given data.
        
        Args:
            data: The input data to check
            
        Returns:
            True if this extractor can process the data, False otherwise
        """
        pass
    
    @abstractmethod
    def extract(self, data: Any) -> Dict[str, Any]:
        """
        Extract structured information from the input data.
        
        Args:
            data: The input data to extract information from
            
        Returns:
            A dictionary containing the extracted structured information
        """
        pass
    
    @abstractmethod
    def get_extraction_schema(self) -> Dict[str, Any]:
        """
        Get the schema that defines what information this extractor extracts.
        
        Returns:
            A dictionary representing the extraction schema
        """
        pass
    
    def validate_extraction(self, extracted_data: Dict[str, Any]) -> bool:
        """
        Validate the extracted data against the expected schema.
        
        Args:
            extracted_data: The data extracted by this extractor
            
        Returns:
            True if the extracted data is valid, False otherwise
        """
        schema = self.get_extraction_schema()
        # Basic validation - check that all required fields are present
        for key in schema.get('required', []):
            if key not in extracted_data:
                return False
        return True