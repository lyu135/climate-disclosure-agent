"""
Data models for the Climate Disclosure Agent framework.

Contains Pydantic models that define the structure of extracted data
and validation results.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class EmissionScope(str, Enum):
    """Emission scope types."""
    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"


class EmissionData(BaseModel):
    """Single emission data item."""
    scope: EmissionScope
    value: Optional[float] = None              # tCO2e
    unit: str = "tCO2e"
    year: Optional[int] = None
    baseline_year: Optional[int] = None
    intensity_value: Optional[float] = None    # Intensity metric
    intensity_unit: Optional[str] = None       # e.g., "tCO2e/revenue_million"
    methodology: Optional[str] = None          # Calculation method
    assurance_level: Optional[str] = None      # Third-party audit level


class TargetData(BaseModel):
    """Emission reduction target data."""
    description: str
    target_year: Optional[int] = None
    base_year: Optional[int] = None
    reduction_pct: Optional[float] = None      # Reduction percentage
    scopes_covered: List[EmissionScope] = []
    is_science_based: Optional[bool] = None
    sbti_status: Optional[str] = None          # committed/approved/none
    interim_targets: List[dict] = []           # Interim milestones


class RiskItem(BaseModel):
    """Climate risk disclosure item."""
    risk_type: str                             # physical/transition
    category: str                              # e.g., "acute_physical", "policy_legal"
    description: str
    time_horizon: Optional[str] = None         # short/medium/long
    financial_impact: Optional[str] = None     # Quantified impact description
    financial_impact_value: Optional[float] = None
    mitigation_strategy: Optional[str] = None
    likelihood: Optional[str] = None


class GovernanceData(BaseModel):
    """Governance structure data."""
    board_oversight: Optional[bool] = None
    board_climate_committee: Optional[bool] = None
    executive_incentive_linked: Optional[bool] = None
    reporting_frequency: Optional[str] = None


class DisclosureExtract(BaseModel):
    """
    Structured extraction result — the core data model for the framework.
    All Validators and Adapters use this structure as input.
    """
    company_name: str
    report_year: int
    report_type: str = "sustainability"        # sustainability/annual/cdp
    framework: List[str] = []                  # ["TCFD", "GRI", "SASB"]
    sector: Optional[str] = None

    # Emission data
    emissions: List[EmissionData] = []

    # Target commitments
    targets: List[TargetData] = []

    # Risk disclosures
    risks: List[RiskItem] = []

    # Governance structure
    governance: GovernanceData = GovernanceData()

    # Original text snippet indices (for provenance)
    source_references: dict[str, str] = Field(
        default_factory=dict,
        description="Field to original text mapping, for audit provenance"
    )

    # Metadata
    extraction_confidence: float = 0.0
    extraction_method: str = "llm"