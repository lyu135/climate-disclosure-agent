"""Data models for the News Consistency Validator."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class EventType(str, Enum):
    """Event type enumeration."""
    FINE = "fine"
    LAWSUIT = "lawsuit"
    ACCIDENT = "accident"
    REGULATION = "regulation"
    VIOLATION = "violation"
    INVESTIGATION = "investigation"
    NGO_REPORT = "ngo_report"
    OTHER = "other"


class ContradictionType(str, Enum):
    """Contradiction type enumeration."""
    OMISSION = "omission"
    MISREPRESENTATION = "misrepresentation"
    TIMING_MISMATCH = "timing_mismatch"
    MAGNITUDE_MISMATCH = "magnitude_mismatch"


class NewsArticle(BaseModel):
    """News article data model."""
    title: str                           # Title
    url: str                             # Link
    source: str                          # Source (Reuters/Bloomberg/etc)
    published_date: str                  # Publication date (YYYY-MM-DD)
    snippet: str                         # Summary
    full_text: Optional[str] = None      # Full text (optional)
    relevance_score: float = 0.0         # Relevance score (0.0-1.0)


class EnvironmentalEvent(BaseModel):
    """Environmental event data model."""
    event_type: EventType                # Event type
    description: str                     # Event description
    date: str                            # Event date (YYYY-MM-DD)
    severity: str                        # Severity (critical/high/medium/low)
    financial_impact: Optional[float] = None  # Financial impact ($)
    source_article: NewsArticle          # Source article
    keywords: List[str] = []             # Keywords
    confidence: float = 0.0              # Extraction confidence (0.0-1.0)


class Contradiction(BaseModel):
    """Contradiction data model."""
    contradiction_type: ContradictionType
    severity: str                        # critical/warning/info
    claim_in_report: Optional[str] = None    # Claim in report
    evidence_from_news: str              # Evidence from news
    event: EnvironmentalEvent            # Related event
    impact_on_credibility: float         # Impact on credibility (-50 to 0)
    recommendation: str                  # Improvement recommendation


class NewsValidationResult(BaseModel):
    """News validation result."""
    company_name: str
    report_period_start: str             # Report period start (YYYY-MM-DD)
    report_period_end: str               # Report period end (YYYY-MM-DD)

    # Collected data
    news_articles_found: int             # Number of news articles found
    events_extracted: List[EnvironmentalEvent]  # Extracted events

    # Validation results
    contradictions: List[Contradiction]  # Found contradictions
    credibility_score: float             # Credibility score (0-100)

    # Statistics
    critical_issues: int                 # Number of critical issues
    warnings: int                        # Number of warnings
    info_items: int                      # Number of info items

    # Metadata
    validation_date: str                 # Validation date
    data_sources: List[str]              # Data sources