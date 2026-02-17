"""
Climate Disclosure Agent - Main entry point class.

This module contains the ClimateDisclosureAgent class which orchestrates
the entire analysis workflow: ingestion, extraction, validation, and scoring.
"""
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

from cda.extraction.llm_extractor import LLMExtractor
from cda.validation.pipeline import ValidationPipeline
from cda.validation.base import ValidationResult, AggregatedResult
from cda.scoring.scorer import Scorer
from cda.adapters.base import BaseAdapter
from cda.ingestion.pdf_handler import PDFHandler
from cda.extraction.schema import DisclosureExtract


class ClimateDisclosureAgent:
    """
    Main entry class that orchestrates the entire analysis workflow.

    Features:
    - Zero-config operation (all dependencies have default implementations)
    - Customizable components via constructor injection
    - Chainable method calls
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_config: Optional[Dict] = None,
        validators: Optional[List[str]] = None,
        adapters: Optional[List[BaseAdapter]] = None,
        scoring_weights: Optional[Dict] = None,
        language: str = "en"
    ):
        """
        Initialize the Climate Disclosure Agent.

        Args:
            llm_provider: LLM provider to use ("openai", "claude", "local")
            llm_config: Configuration for the LLM provider
            validators: List of validator names to use (None = all)
            adapters: List of data adapters for external validation
            scoring_weights: Custom weights for scoring dimensions
            language: Output language
        """
        self.extractor = self._init_extractor(llm_provider, llm_config)
        self.validators = self._init_validators(validators)
        self.adapters = adapters or []
        self.scorer = Scorer(weights=scoring_weights)
        self.pipeline = ValidationPipeline(
            validators=self.validators,
            adapters=self.adapters
        )
        self.language = language

    def analyze(
        self,
        source: Union[str, Dict],
        company_name: Optional[str] = None,
        sector: Optional[str] = None,
        validate_external: bool = True,
        output_format: str = "json"
    ) -> AggregatedResult:
        """
        Core analysis method.

        Workflow:
        1. Ingestion: Parse input → Raw text
        2. Extraction: LLM extraction → DisclosureExtract
        3. Validation: Pipeline validation → ValidationResult[]
        4. Cross-validation: External data validation (optional)
        5. Scoring: Aggregate scores → AggregatedResult

        Args:
            source: PDF path, JSON path, or dict
            company_name: Company name (optional if can be extracted)
            sector: Industry sector (optional)
            validate_external: Whether to run external validation
            output_format: Output format ("json", "dataframe", "report")

        Returns:
            AggregatedResult containing analysis results
        """
        try:
            # Step 1: Input ingestion
            raw_text = self._ingest(source)

            # Step 2: Structured extraction
            extract = self.extractor.extract(
                raw_text,
                company_name=company_name,
                sector=sector
            )

            # Step 3 & 4: Validation Pipeline
            validation_results = self.pipeline.run(
                extract,
                cross_validate=validate_external
            )

            # Step 5: Aggregate scoring
            result = self.scorer.aggregate(extract, validation_results)

            return self._format_output(result, output_format)
        
        except Exception as e:
            raise RuntimeError(f"Analysis failed: {str(e)}") from e

    def compare(
        self,
        sources: List[Union[str, Dict]],
        company_names: Optional[List[str]] = None,
        **kwargs
    ):
        """Batch analyze and compare multiple companies."""
        from cda.output.dataframe_output import ComparisonResult
        
        results = [
            self.analyze(src, name, **kwargs)
            for src, name in zip(sources, company_names or [None]*len(sources))
        ]
        return ComparisonResult(results=results)

    def _ingest(self, source: Union[str, Dict]) -> str:
        """Ingest input source and return raw text."""
        if isinstance(source, str):
            path = Path(source)
            if path.suffix.lower() == '.pdf':
                handler = PDFHandler()
                return handler.parse_pdf(source)
            elif path.suffix.lower() in ['.json', '.txt']:
                with open(source, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        elif isinstance(source, dict):
            # Assume it's already parsed data
            return str(source)
        else:
            raise TypeError(f"Source must be string path or dict, got {type(source)}")

    def _format_output(self, result: AggregatedResult, output_format: str):
        """Format the result according to the requested format."""
        if output_format == "json":
            return result.model_dump()
        elif output_format == "dataframe":
            from cda.output.dataframe_output import DataFrameOutput
            return DataFrameOutput().render(result)
        elif output_format == "report":
            from cda.output.report import ReportRenderer
            return ReportRenderer().render(result)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _init_extractor(self, llm_provider: str, llm_config: Optional[Dict]):
        """Initialize the LLM extractor."""
        return LLMExtractor(provider=llm_provider, config=llm_config)

    def _init_validators(self, names: Optional[List[str]]):
        """Initialize validators by name, None means all."""
        from cda.validation.consistency import ConsistencyValidator
        from cda.validation.quantification import QuantificationValidator
        from cda.validation.completeness import CompletenessValidator
        from cda.validation.risk_coverage import RiskCoverageValidator
        
        registry = {
            "consistency": ConsistencyValidator(),
            "quantification": QuantificationValidator(),
            "completeness": CompletenessValidator(),
            "risk_coverage": RiskCoverageValidator(),
        }
        
        if names is None:
            return list(registry.values())
        return [registry[n] for n in names if n in registry]