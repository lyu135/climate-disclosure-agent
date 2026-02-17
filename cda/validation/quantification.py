"""
Quantification validator for the Climate Disclosure Agent framework.

Assesses the "data density" of climate disclosures - whether sufficient
quantitative metrics support the narrative.
"""
from typing import List
from cda.validation.base import BaseValidator, ValidationResult, ValidationFinding, Severity
from cda.extraction.schema import DisclosureExtract, EmissionScope


class QuantificationValidator(BaseValidator):
    """
    Assess "data density" of disclosure - whether sufficient quantitative 
    metrics support the narrative.

    Scoring dimensions:
    1. Emission data completeness (absolute/relative/intensity/baseline/methodology/audit)
    2. Target quantification (percentage/timeline/milestones)
    3. Risk quantification (financial impact/probability/timeline)
    """

    name = "quantification"
    description = "Assesses the quantitative metrics in climate disclosures"

    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        """
        Perform quantification validation.
        
        Args:
            extract: Structured disclosure extract to validate
            
        Returns:
            ValidationResult with quantification score and findings
        """
        findings = []
        sub_scores = {}

        # --- Emission data completeness ---
        emission_checks = {
            "has_scope1_absolute": any(
                e.scope == EmissionScope.SCOPE_1 and e.value is not None
                for e in extract.emissions
            ),
            "has_scope2_absolute": any(
                e.scope == EmissionScope.SCOPE_2 and e.value is not None
                for e in extract.emissions
            ),
            "has_scope3_absolute": any(
                e.scope == EmissionScope.SCOPE_3 and e.value is not None
                for e in extract.emissions
            ),
            "has_baseline_year": any(
                e.baseline_year is not None for e in extract.emissions
            ),
            "has_intensity_metric": any(
                e.intensity_value is not None for e in extract.emissions
            ),
            "has_methodology": any(
                e.methodology is not None for e in extract.emissions
            ),
            "has_third_party_assurance": any(
                e.assurance_level is not None for e in extract.emissions
            ),
        }
        sub_scores["emissions"] = sum(emission_checks.values()) / len(emission_checks)

        # --- Target quantification ---
        target_checks = {
            "has_reduction_percentage": any(
                t.reduction_pct is not None for t in extract.targets
            ),
            "has_target_year": any(
                t.target_year is not None for t in extract.targets
            ),
            "has_base_year": any(
                t.base_year is not None for t in extract.targets
            ),
            "has_interim_milestones": any(
                len(t.interim_targets) > 0 for t in extract.targets
            ),
            "has_scope_coverage": any(
                len(t.scopes_covered) > 0 for t in extract.targets
            ),
        }
        sub_scores["targets"] = sum(target_checks.values()) / max(len(target_checks), 1)

        # --- Risk quantification ---
        risk_checks = {
            "has_financial_impact": any(
                r.financial_impact_value is not None for r in extract.risks
            ),
            "has_time_horizon": any(
                r.time_horizon is not None for r in extract.risks
            ),
            "has_likelihood": any(
                r.likelihood is not None for r in extract.risks
            ),
            "has_mitigation": any(
                r.mitigation_strategy is not None for r in extract.risks
            ),
        }
        sub_scores["risks"] = sum(risk_checks.values()) / max(len(risk_checks), 1)

        # Generate findings for missing elements
        for check_name, passed in {**emission_checks, **target_checks, **risk_checks}.items():
            if not passed:
                findings.append(self._finding(
                    code=f"QUANT-{check_name.upper()}",
                    severity=Severity.WARNING,
                    message=f"Missing quantification: {check_name.replace('_', ' ')}",
                    field=check_name
                ))

        # Weighted total score
        weights = {"emissions": 0.4, "targets": 0.35, "risks": 0.25}
        overall = sum(sub_scores[k] * weights[k] for k in weights)

        return ValidationResult(
            validator_name=self.name,
            score=overall,
            findings=findings,
            metadata={"sub_scores": sub_scores}
        )