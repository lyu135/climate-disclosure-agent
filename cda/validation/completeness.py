"""Disclosure completeness validator based on TCFD/SASB frameworks."""

from typing import Dict, List, Optional
from pydantic import BaseModel

from ..extraction.schema import DisclosureExtract
from ..validation.base import BaseValidator, ValidationResult, ValidationFinding, Severity


class CompletenessValidator(BaseValidator):
    """
    Based on TCFD/SASB/GRI framework checks disclosure coverage.

    Core idea: According to the industry to which the enterprise belongs, 
    check whether all disclosure dimensions required by the standard are covered.
    """

    name = "completeness"

    # TCFD four pillars checklist
    TCFD_CHECKLIST = {
        "governance": {
            "board_oversight": "Board-level oversight of climate risks",
            "management_role": "Management's role in climate assessment",
        },
        "strategy": {
            "climate_risks_identified": "Climate-related risks identified",
            "climate_opportunities": "Climate-related opportunities described",
            "scenario_analysis": "Scenario analysis conducted",
            "strategy_resilience": "Strategy resilience assessment",
        },
        "risk_management": {
            "risk_identification_process": "Process for identifying climate risks",
            "risk_management_process": "Process for managing climate risks",
            "integration_with_erm": "Integration with overall risk management",
        },
        "metrics_targets": {
            "ghg_emissions": "GHG emissions disclosed (Scope 1, 2, 3)",
            "climate_targets": "Climate-related targets set",
            "progress_tracking": "Progress against targets tracked",
        }
    }

    # SASB industry-specific metrics (example: food/agriculture)
    SASB_SECTOR_METRICS = {
        "food_agriculture": [
            "ghg_emissions", "energy_management", "water_management",
            "land_use", "biodiversity_impact", "supply_chain_environmental",
            "food_safety", "packaging_waste"
        ],
        "oil_gas": [
            "ghg_emissions", "air_quality", "water_management",
            "biodiversity", "reserves_valuation", "community_impact"
        ],
        "financials": [
            "financed_emissions", "climate_risk_exposure",
            "sustainable_finance_products", "engagement_policy"
        ],
        # More industries can be extended...
    }

    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []

        # TCFD completeness check
        tcfd_results = self._check_tcfd(extract)

        # SASB industry check (if sector is provided)
        sasb_results = {}
        if extract.sector:
            sasb_results = self._check_sasb(extract)

        # Summary
        total_items = sum(len(v) for v in self.TCFD_CHECKLIST.values())
        covered_items = sum(1 for v in tcfd_results.values() if v)

        score = covered_items / total_items

        for item, covered in tcfd_results.items():
            if not covered:
                findings.append(self._finding(
                    code=f"COMPL-TCFD-{item.upper()}",
                    severity=Severity.WARNING,
                    message=f"TCFD recommended disclosure missing: {item}",
                    field=item
                ))

        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={
                "tcfd_coverage": tcfd_results,
                "sasb_coverage": sasb_results,
                "tcfd_score": score,
            }
        )

    def _check_tcfd(self, extract: DisclosureExtract) -> Dict[str, bool]:
        """Check TCFD coverage item by item"""
        results = {}

        # Governance
        results["board_oversight"] = extract.governance.board_oversight is not None
        results["management_role"] = extract.governance.reporting_frequency is not None

        # Strategy
        results["climate_risks_identified"] = len(extract.risks) > 0
        results["climate_opportunities"] = any(
            "opportunity" in r.description.lower() for r in extract.risks
        )
        results["scenario_analysis"] = "scenario" in str(extract.source_references).lower()

        # Risk Management
        results["risk_identification_process"] = any(
            r.category is not None for r in extract.risks
        )
        results["risk_management_process"] = any(
            r.mitigation_strategy is not None for r in extract.risks
        )

        # Metrics & Targets
        results["ghg_emissions"] = len(extract.emissions) > 0
        results["climate_targets"] = len(extract.targets) > 0
        results["progress_tracking"] = any(
            e.baseline_year is not None for e in extract.emissions
        )

        return results

    def _check_sasb(self, extract: DisclosureExtract) -> Dict[str, bool]:
        """Check SASB sector-specific metrics coverage"""
        if not extract.sector or extract.sector.lower() not in self.SASB_SECTOR_METRICS:
            return {}

        sector_metrics = self.SASB_SECTOR_METRICS[extract.sector.lower()]
        results = {}

        # For each metric, check if it's covered in the disclosure
        for metric in sector_metrics:
            # This is a simplified check - in practice, this could be more sophisticated
            # to look for specific mentions of each metric in the disclosure
            results[metric] = self._metric_mentioned(extract, metric)

        return results

    def _metric_mentioned(self, extract: DisclosureExtract, metric: str) -> bool:
        """Check if a specific metric is mentioned in the disclosure."""
        # Look for the metric in various parts of the disclosure
        text_to_search = " ".join([
            str(extract.source_references),
            " ".join([r.description for r in extract.risks]),
            " ".join([t.description for t in extract.targets]),
            " ".join([str(e.value) for e in extract.emissions if e.value is not None])
        ]).lower()

        # Map metric keywords to common terms that might appear in reports
        keyword_map = {
            "ghg_emissions": ["ghg", "greenhouse gas", "emission", "co2", "carbon"],
            "energy_management": ["energy", "consumption", "efficiency", "renewable"],
            "water_management": ["water", "consumption", "scarcity", "quality", "usage"],
            "land_use": ["land", "use", "agriculture", "deforestation"],
            "biodiversity_impact": ["biodiversity", "habitat", "species", "ecosystem"],
            "supply_chain_environmental": ["supply chain", "supplier", "vendor", "procurement"],
            "food_safety": ["food safety", "contamination", "quality"],
            "packaging_waste": ["packaging", "waste", "recycling", "material"],
            "air_quality": ["air", "quality", "pollution", "particulates"],
            "biodiversity": ["biodiversity", "habitat", "species", "ecosystem"],
            "reserves_valuation": ["reserves", "valuation", "assets", "impairment"],
            "community_impact": ["community", "social", "stakeholder", "local"],
            "financed_emissions": ["financed", "financing", "portfolio", "lending"],
            "climate_risk_exposure": ["climate", "risk", "exposure", "vulnerability"],
            "sustainable_finance_products": ["sustainable", "finance", "green bond", "product"],
            "engagement_policy": ["engagement", "policy", "shareholder", "proxy"]
        }

        keywords = keyword_map.get(metric, [metric])
        return any(keyword in text_to_search for keyword in keywords)