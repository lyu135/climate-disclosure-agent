"""Climate risk coverage validator based on TCFD taxonomy."""

from typing import Dict, List, Set
from pydantic import BaseModel

from ..extraction.schema import DisclosureExtract
from ..validation.base import BaseValidator, ValidationResult, ValidationFinding, Severity


class RiskCoverageValidator(BaseValidator):
    """
    Assess the breadth and depth of climate risk disclosure.

    Based on the TCFD framework, climate risks are divided into two major categories:
    physical risks and transition risks, checking coverage of each sub-category.
    """

    name = "risk_coverage"

    RISK_TAXONOMY = {
        "physical": {
            "acute": ["extreme_weather", "flooding", "wildfire", "drought"],
            "chronic": ["sea_level_rise", "temperature_change", "precipitation_change"],
        },
        "transition": {
            "policy_legal": ["carbon_pricing", "regulation", "litigation"],
            "technology": ["substitution", "disruption", "efficiency"],
            "market": ["demand_shift", "commodity_price", "stranded_assets"],
            "reputation": ["stigmatization", "stakeholder_concern"],
        }
    }

    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []

        # Count risk type coverage
        covered_types = set()
        for risk in extract.risks:
            covered_types.add(risk.risk_type)
            covered_types.add(risk.category)

        # Check major category coverage
        has_physical = any(r.risk_type == "physical" for r in extract.risks)
        has_transition = any(r.risk_type == "transition" for r in extract.risks)

        if not has_physical:
            findings.append(self._finding(
                code="RISK-001",
                severity=Severity.CRITICAL,
                message="No physical climate risks disclosed"
            ))

        if not has_transition:
            findings.append(self._finding(
                code="RISK-002",
                severity=Severity.CRITICAL,
                message="No transition climate risks disclosed"
            ))

        # Check depth (quantification)
        quantified_risks = [r for r in extract.risks if r.financial_impact_value is not None]
        quantification_rate = len(quantified_risks) / max(len(extract.risks), 1)

        if quantification_rate < 0.3:
            findings.append(self._finding(
                code="RISK-003",
                severity=Severity.WARNING,
                message=f"Only {quantification_rate:.0%} of risks have quantified financial impact"
            ))

        # Scoring
        breadth = (int(has_physical) + int(has_transition)) / 2
        depth = quantification_rate
        score = breadth * 0.5 + depth * 0.5

        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={
                "risk_types_covered": list(covered_types),
                "physical_covered": has_physical,
                "transition_covered": has_transition,
                "quantification_rate": quantification_rate
            }
        )

    def _analyze_risk_taxonomy_coverage(self, extract: DisclosureExtract) -> Dict[str, Dict[str, bool]]:
        """Analyze coverage of risk taxonomy categories."""
        coverage = {}
        
        for category, subcategories in self.RISK_TAXONOMY.items():
            coverage[category] = {}
            for subcategory, keywords in subcategories.items():
                # Check if this subcategory is mentioned in the risks
                category_covered = any(
                    any(keyword in risk.description.lower() for keyword in keywords)
                    for risk in extract.risks
                    if risk.risk_type == category
                )
                coverage[category][subcategory] = category_covered
                
        return coverage

    def _get_missing_risk_categories(self, extract: DisclosureExtract) -> List[str]:
        """Identify missing risk categories."""
        coverage = self._analyze_risk_taxonomy_coverage(extract)
        missing = []
        
        for category, subcategories in coverage.items():
            for subcategory, covered in subcategories.items():
                if not covered:
                    missing.append(f"{category}.{subcategory}")
                    
        return missing