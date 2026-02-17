"""
Consistency validator for the Climate Disclosure Agent framework.

Checks internal consistency of climate disclosure reports.
"""
from typing import List
from cda.validation.base import BaseValidator, ValidationResult, ValidationFinding, Severity
from cda.extraction.schema import DisclosureExtract, EmissionScope


def _scope3_material(extract: DisclosureExtract) -> bool:
    """Check if Scope 3 emissions appear material (>40% of total)."""
    total_emissions = 0
    scope3_emissions = 0
    
    for emission in extract.emissions:
        if emission.value:
            total_emissions += emission.value
            if emission.scope == EmissionScope.SCOPE_3:
                scope3_emissions = emission.value
    
    return scope3_emissions > 0 and total_emissions > 0 and (scope3_emissions / total_emissions) > 0.4


def _mentions_climate_investment(extract: DisclosureExtract) -> bool:
    """Check if the extract mentions climate-related investments."""
    refs_text = " ".join(extract.source_references.values()).lower()
    investment_keywords = ["investment", "investing", "capital expenditure", "capex", "funding"]
    return any(keyword in refs_text for keyword in investment_keywords)


def _has_specific_projects(extract: DisclosureExtract) -> bool:
    """Check if there are specific project details mentioned."""
    refs_text = " ".join(extract.source_references.values()).lower()
    project_keywords = ["project", "initiative", "technology", "program", "solution"]
    return any(keyword in refs_text for keyword in project_keywords)


def _check_timeline_monotonicity(targets) -> bool:
    """Check if target timelines are logically consistent."""
    # Simple check: if there are multiple targets, ensure they're not contradictory
    if len(targets) < 2:
        return True
    
    # For now, just ensure we have reasonable years
    for target in targets:
        if target.target_year and target.base_year:
            if target.target_year <= target.base_year:
                return False  # Target year should be after base year
    return True


class ConsistencyValidator(BaseValidator):
    """
    Checks internal consistency of the report.

    Core logic:
    - Alignment between commitments and actions (said Net Zero, have pathway?)
    - Alignment between data and narrative (mentioned Scope 3 is big, have management measures?)
    - Timeline logic (2030 interim target < 2050 long-term target)
    """

    name = "consistency"
    description = "Checks internal consistency of climate disclosures"

    # Consistency check rules
    RULES = [
        {
            "code": "CONSIST-001",
            "name": "net_zero_pathway",
            "condition": lambda e: any("net zero" in t.description.lower() for t in e.targets),
            "check": lambda e: any(t.interim_targets for t in e.targets if "net zero" in t.description.lower()),
            "message": "Net Zero target declared but no interim milestones found",
            "severity": Severity.CRITICAL
        },
        {
            "code": "CONSIST-002",
            "name": "scope3_materiality",
            "condition": lambda e: _scope3_material(e),
            "check": lambda e: any(
                r.category in ["supply_chain", "value_chain", "upstream", "downstream"] for r in e.risks
            ),
            "message": "Scope 3 appears material (>40% of total) but no supply chain risk disclosed",
            "severity": Severity.WARNING
        },
        {
            "code": "CONSIST-003",
            "name": "target_timeline_logic",
            "condition": lambda e: len(e.targets) > 1,
            "check": _check_timeline_monotonicity,
            "message": "Target timeline inconsistency: target year should be after base year",
            "severity": Severity.WARNING
        },
        {
            "code": "CONSIST-004",
            "name": "investment_specificity",
            "condition": lambda e: _mentions_climate_investment(e),
            "check": lambda e: _has_specific_projects(e),
            "message": "Climate investment amount mentioned without specific project breakdown",
            "severity": Severity.INFO
        },
        {
            "code": "CONSIST-005",
            "name": "governance_action_gap",
            "condition": lambda e: e.governance.board_oversight is True,
            "check": lambda e: e.governance.executive_incentive_linked is not None,
            "message": "Board oversight claimed but executive incentive linkage not specified",
            "severity": Severity.WARNING
        },
    ]

    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        """
        Perform consistency validation.
        
        Args:
            extract: Structured disclosure extract to validate
            
        Returns:
            ValidationResult with consistency score and findings
        """
        findings = []
        passed = 0
        applicable = 0

        for rule in self.RULES:
            if rule["condition"](extract):
                applicable += 1
                if rule["check"](extract):
                    passed += 1
                else:
                    findings.append(self._finding(
                        code=rule["code"],
                        severity=rule["severity"],
                        message=rule["message"]
                    ))

        score = passed / applicable if applicable > 0 else 1.0

        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={"rules_applicable": applicable, "rules_passed": passed}
        )