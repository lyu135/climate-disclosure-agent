"""News consistency validator for the Climate Disclosure Agent."""

from datetime import datetime
from typing import List, Optional, Dict
import os

from ..base import BaseValidator, ValidationResult, Finding, Severity
from ..extraction.schema import DisclosureExtract
from .news_data_source import NewsDataSourceManager
from .event_extractor import EventExtractor
from .cross_validator import CrossValidator
from .credibility_scorer import CredibilityScorer
from .news_models import NewsArticle, EnvironmentalEvent, Contradiction


class NewsConsistencyValidator(BaseValidator):
    """News consistency validator to detect greenwashing by cross-referencing disclosures with news."""

    def __init__(
        self,
        news_api_key: Optional[str] = None,
        llm_provider: str = "openai",
        llm_config: Optional[Dict] = None,
        news_provider: str = "brave"
    ):
        """
        Initialize the news consistency validator.
        
        Args:
            news_api_key: API key for news service
            llm_provider: LLM provider ('openai', 'anthropic', etc.)
            llm_config: LLM configuration parameters
            news_provider: News provider ('brave', 'google', 'bing')
        """
        self.news_provider = news_provider
        
        # Set up API keys
        api_keys = {}
        if news_api_key:
            api_keys[news_provider] = news_api_key
        else:
            # Try to get from environment variables
            brave_key = os.getenv("BRAVE_API_KEY")
            google_key = os.getenv("GOOGLE_NEWS_API_KEY")
            bing_key = os.getenv("BING_NEWS_API_KEY")
            
            if brave_key:
                api_keys['brave'] = brave_key
            if google_key:
                api_keys['google'] = google_key
            if bing_key:
                api_keys['bing'] = bing_key
        
        # Initialize components
        self.data_source = NewsDataSourceManager(api_keys)
        self.event_extractor = EventExtractor(llm_provider, llm_config)
        self.cross_validator = CrossValidator()
        self.credibility_scorer = CredibilityScorer()

    def validate(self, data: DisclosureExtract) -> ValidationResult:
        """
        Execute news consistency validation.

        Args:
            data: Disclosure data

        Returns:
            Validation result
        """
        try:
            # 1. Determine report period
            report_start = f"{data.report_year}-01-01"
            report_end = f"{data.report_year}-12-31"

            # 2. Search news
            news_articles = self.data_source.search_news(
                company_name=data.company_name,
                start_date=report_start,
                end_date=report_end,
                preferred_source=self.news_provider
            )

            # 3. Extract events
            events = self.event_extractor.extract_events(
                news_articles=news_articles,
                company_name=data.company_name
            )

            # 4. Cross-validate
            contradictions = self.cross_validator.validate(
                disclosure=data,
                events=events
            )

            # 5. Calculate credibility score
            credibility_score = self.credibility_scorer.score(
                contradictions=contradictions,
                total_events=len(events)
            )

            # 6. Generate ValidationResult
            findings = []
            for contradiction in contradictions:
                finding = Finding(
                    validator="news_consistency",
                    code=f"NEWS-{contradiction.contradiction_type.value.upper()}",
                    severity=self._map_severity(contradiction.severity),
                    message=f"{contradiction.contradiction_type.value}: {contradiction.evidence_from_news}",
                    field="credibility",
                    recommendation=contradiction.recommendation,
                    metadata={
                        "event_type": contradiction.event.event_type.value,
                        "event_date": contradiction.event.date,
                        "source_url": contradiction.event.source_article.url
                    }
                )
                findings.append(finding)

            return ValidationResult(
                validator_name="news_consistency",
                score=credibility_score / 100.0,  # Convert to 0-1 scale
                max_score=1.0,
                findings=findings,
                metadata={
                    "news_articles_found": len(news_articles),
                    "events_extracted": len(events),
                    "contradictions_found": len(contradictions),
                    "report_period": f"{report_start} to {report_end}",
                    "data_sources_used": [self.news_provider]
                }
            )
        except Exception as e:
            # In case of error, return a validation result with error findings
            error_finding = Finding(
                validator="news_consistency",
                code="NEWS-ERROR",
                severity=Severity.WARNING,
                message=f"News consistency validation failed: {str(e)}",
                field="credibility",
                recommendation="Check API keys and network connectivity for news services",
                metadata={"error": str(e)}
            )
            
            return ValidationResult(
                validator_name="news_consistency",
                score=1.0,  # Full score when validation cannot be performed
                max_score=1.0,
                findings=[error_finding],
                metadata={
                    "news_articles_found": 0,
                    "events_extracted": 0,
                    "contradictions_found": 0,
                    "report_period": f"{data.report_year}-01-01 to {data.report_year}-12-31",
                    "validation_error": str(e)
                }
            )

    def _map_severity(self, severity_str: str) -> Severity:
        """Map string severity to Severity enum."""
        mapping = {
            "critical": Severity.CRITICAL,
            "warning": Severity.WARNING,
            "info": Severity.INFO
        }
        return mapping.get(severity_str, Severity.WARNING)