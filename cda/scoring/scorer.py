"""
Scoring module for the Climate Disclosure Agent framework.

Contains the Scorer class that aggregates validation results into
a comprehensive score.
"""
from typing import List
from cda.validation.base import ValidationResult, AggregatedResult
from cda.extraction.schema import DisclosureExtract


class Scorer:
    """
    Aggregates multi-dimensional validation results into a composite score.

    Scoring system:
    - Total score 0-100, mapped to A/B/C/D/F grades
    - Configurable weights per dimension
    - External cross-validation as "bonus/penalty" rather than base score
    """

    DEFAULT_WEIGHTS = {
        "consistency": 0.25,
        "quantification": 0.30,
        "completeness": 0.25,
        "risk_coverage": 0.20,
    }

    GRADE_MAP = [
        (90, "A"),
        (80, "B"),
        (70, "C"),
        (60, "D"),
        (0,  "F"),
    ]

    def __init__(self, weights: dict = None):
        """
        Initialize the scorer.
        
        Args:
            weights: Custom weights for scoring dimensions
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def aggregate(
        self,
        extract: DisclosureExtract,
        results: List[ValidationResult]
    ) -> AggregatedResult:
        """
        Aggregate validation results into a comprehensive score.
        
        Args:
            extract: The disclosure extract being scored
            results: List of validation results
            
        Returns:
            AggregatedResult with overall score and grade
        """
        dimension_scores = {}

        # Internal validator scores
        for result in results:
            if result.score is not None and not result.validator_name.startswith("adapter:"):
                dimension_scores[result.validator_name] = result.score

        # Weighted total score
        overall = sum(
            dimension_scores.get(dim, 0) * weight
            for dim, weight in self.weights.items()
        ) * 100  # Convert to percentage

        # External cross-validation adjustment
        adapter_results = [r for r in results if r.validator_name.startswith("adapter:")]
        cross_validation_penalty = sum(
            len([f for f in r.findings if getattr(f, 'severity', None) == 'critical']) * 5
            for r in adapter_results
        )
        overall = max(overall - cross_validation_penalty, 0)

        # Grade mapping
        grade = "F"
        for threshold, g in self.GRADE_MAP:
            if overall >= threshold:
                grade = g
                break

        return AggregatedResult(
            company_name=extract.company_name,
            overall_score=round(overall, 1),
            grade=grade,
            dimension_scores={k: round(v * 100, 1) for k, v in dimension_scores.items()},
            validation_results=results,
            cross_validation={
                "adapters_used": [r.validator_name for r in adapter_results],
                "penalty_applied": cross_validation_penalty
            },
            summary=self._generate_summary(extract, overall, grade, dimension_scores)
        )

    def _generate_summary(self, extract, score, grade, dims) -> str:
        """
        Generate a summary of the results.
        
        Args:
            extract: The disclosure extract
            score: Overall score
            grade: Letter grade
            dims: Dimension scores
            
        Returns:
            Summary string
        """
        weakest = min(dims, key=dims.get) if dims else "N/A"
        return (
            f"{extract.company_name} ({extract.report_year}) scores {score:.0f}/100 "
            f"(Grade {grade}). Weakest dimension: {weakest}."
        )