"""
Base classes for adapters in the Climate Disclosure Agent framework.
"""
from abc import ABC, abstractmethod
from typing import Optional


class DataNotAvailableError(Exception):
    """Raised when data is not available."""
    pass


class BaseAdapter(ABC):
    """
    External data source adapter base class.

    Design principles:
    - Data source provided by user (CSV/API key/DataFrame)
    - Adapter handles "connection logic", not "data retrieval"
    - Graceful degradation: skip if no data instead of failing
    """

    name: str = "base"
    data_source_url: str = ""       # Data acquisition URL hint
    requires_auth: bool = False

    @abstractmethod
    def cross_validate(self, extract):
        """
        Cross-validate extraction results with external data.

        Returns:
            ValidationResult: Cross-validation findings
        Raises:
            DataNotAvailableError: When user hasn't provided data
        """
        pass

    @abstractmethod
    def get_benchmark(self, sector: str) -> dict:
        """Get industry benchmark data."""
        pass

    def status(self) -> dict:
        """Check adapter status."""
        return {
            "name": self.name,
            "data_loaded": self._has_data(),
            "source_url": self.data_source_url,
        }

    @abstractmethod
    def _has_data(self) -> bool:
        pass