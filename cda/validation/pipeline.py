"""
Validation Pipeline - Orchestrates multiple validators and adapters.

This module manages the execution sequence of validators and adapters,
aggregates results, and handles conflicts.
"""
from typing import List, Optional
from cda.validation.base import BaseValidator, ValidationResult
from cda.adapters.base import BaseAdapter, DataNotAvailableError
from cda.extraction.schema import DisclosureExtract
from cda.validation.consistency import ConsistencyValidator
from cda.validation.quantification import QuantificationValidator
from cda.validation.completeness import CompletenessValidator
from cda.validation.risk_coverage import RiskCoverageValidator
from cda.validation.news_consistency import NewsConsistencyValidator


class ValidationPipeline:
    """
    Validation pipeline - orchestrates execution of multiple validators and adapters.

    The Pipeline supports:
    - Sequential execution of all internal validators
    - Optional execution of external data cross-validation
    - Result aggregation and conflict resolution
    """

    def __init__(self, validators: List[BaseValidator], adapters: List[BaseAdapter] = None):
        """
        Initialize the validation pipeline.

        Args:
            validators: List of validators to run
            adapters: List of adapters for cross-validation (optional)
        """
        self.validators = validators
        self.adapters = adapters or []

    @classmethod
    def default_pipeline(cls, news_api_key: Optional[str] = None, adapters: List[BaseAdapter] = None):
        """
        Create a default pipeline with all validators including news consistency.

        Args:
            news_api_key: API key for news service (optional)
            adapters: List of adapters for cross-validation (optional)

        Returns:
            ValidationPipeline with default validators
        """
        validators = [
            ConsistencyValidator(),
            QuantificationValidator(),
            CompletenessValidator(),
            RiskCoverageValidator(),
            NewsConsistencyValidator(news_api_key=news_api_key)  # New addition
        ]
        return cls(validators=validators, adapters=adapters)

    def run(
        self,
        extract: DisclosureExtract,
        cross_validate: bool = True
    ) -> List[ValidationResult]:
        """
        Run the validation pipeline.
        
        Args:
            extract: Structured disclosure extract to validate
            cross_validate: Whether to run external cross-validation
            
        Returns:
            List of validation results
        """
        results = []

        # Phase 1: Internal validation
        for validator in self.validators:
            try:
                result = validator.validate(extract)
                results.append(result)
            except Exception as e:
                # Log error but continue with other validators
                import logging
                logging.error(f"Validator {validator.name} failed: {e}")
                
                # Add error as a finding
                error_result = ValidationResult(
                    validator_name=validator.name,
                    score=0.0,
                    findings=[{
                        "validator": validator.name,
                        "code": "VALIDATOR-ERROR",
                        "severity": "critical",
                        "message": f"Validator {validator.name} failed: {str(e)}"
                    }]
                )
                results.append(error_result)

        # Phase 2: External cross-validation (optional)
        if cross_validate and self.adapters:
            for adapter in self.adapters:
                try:
                    xv_result = adapter.cross_validate(extract)
                    results.append(xv_result)
                except DataNotAvailableError:
                    # Graceful degradation: no data available, skip without affecting other validations
                    results.append(ValidationResult(
                        validator_name=f"adapter:{adapter.name}",
                        score=None,
                        findings=[{
                            "validator": adapter.name,
                            "code": "ADAPTER-NO-DATA",
                            "severity": "info",
                            "message": f"External data not available from {adapter.name}, skipped."
                        }]
                    ))
                except Exception as e:
                    # Handle unexpected adapter errors gracefully
                    import logging
                    logging.error(f"Adapter {adapter.name} failed: {e}")
                    
                    results.append(ValidationResult(
                        validator_name=f"adapter:{adapter.name}",
                        score=None,
                        findings=[{
                            "validator": adapter.name,
                            "code": "ADAPTER-ERROR",
                            "severity": "warning",
                            "message": f"Adapter {adapter.name} failed: {str(e)}"
                        }]
                    ))

        return results