"""
Base classes for the Climate Disclosure Agent framework.

Contains abstract base classes for various components of the system.
"""
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    """Severity levels for validation findings."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ValidationFinding(BaseModel):
    """Single validation finding."""
    validator: str                # Source validator name
    code: str                     # Issue code, e.g., "CONSIST-001"
    severity: Severity
    message: str                  # Human-readable description
    field: Optional[str] = None   # Affected field
    evidence: Optional[str] = None  # Original text evidence
    recommendation: Optional[str] = None


class ValidationResult(BaseModel):
    """Output from a single validator."""
    validator_name: str
    score: float                  # 0.0 - 1.0
    max_score: float = 1.0
    findings: list[ValidationFinding] = []
    metadata: dict = {}


class AggregatedResult(BaseModel):
    """Pipeline aggregated result."""
    company_name: str
    overall_score: float
    grade: str                    # A/B/C/D/F
    dimension_scores: dict[str, float]  # Dimension scores
    validation_results: list[ValidationResult]
    cross_validation: Optional[dict] = None  # External cross-validation result
    summary: str                  # LLM-generated summary


class BaseValidator(ABC):
    """
    Validator abstract base class.

    Extension approach:
    1. Inherit BaseValidator
    2. Implement validate() method
    3. Register to Agent or Pipeline
    """

    name: str = "base"
    version: str = "1.0"
    description: str = ""

    @abstractmethod
    def validate(self, extract):
        """
        Perform validation and return results.

        Args:
            extract: Structured extraction result
        Returns:
            ValidationResult: Contains score and findings
        """
        pass

    def _finding(self, code, severity, message, **kwargs):
        """Factory method to simplify Finding creation."""
        return ValidationFinding(
            validator=self.name,
            code=code,
            severity=severity,
            message=message,
            **kwargs
        )