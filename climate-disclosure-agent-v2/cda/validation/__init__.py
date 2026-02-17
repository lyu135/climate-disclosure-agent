"""Validation module for Climate Disclosure Agent."""

from .base import BaseValidator, ValidationResult, Finding, Severity
from .consistency import ConsistencyValidator
from .quantification import QuantificationValidator
from .completeness import CompletenessValidator
from .risk_coverage import RiskCoverageValidator

# Import the news consistency validator if it exists
try:
    from .news_consistency import NewsConsistencyValidator
except ImportError:
    NewsConsistencyValidator = None

__all__ = [
    "BaseValidator",
    "ValidationResult",
    "Finding",
    "Severity",
    "ConsistencyValidator",
    "QuantificationValidator",
    "CompletenessValidator",
    "RiskCoverageValidator",
    "NewsConsistencyValidator"
]