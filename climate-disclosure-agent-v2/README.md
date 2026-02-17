# Climate Disclosure Validation Agent

**A modular, extensible agent framework for automated climate disclosure analysis with pluggable validation modules and external data adapters.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![ESG](https://img.shields.io/badge/ESG-Climate--Disclosure-green)](https://github.com/openclaw/climate-disclosure-agent)

## Overview

The Climate Disclosure Validation Agent (CDA) is a lightweight framework designed to assess the quality and completeness of corporate climate disclosures. Rather than being a monolithic product, CDA provides a programmable methodology for evaluating how well organizations report on their climate-related risks, opportunities, and strategies according to international standards like TCFD, SASB, and GRI.

## Key Features

- **Modular Architecture**: Pluggable validation modules for consistency, quantification, completeness, and risk coverage
- **Standard Compliance**: Built on TCFD, SASB, and GRI frameworks for credible assessment
- **Extensible Design**: Easy-to-implement custom validators and data adapters
- **External Data Integration**: Cross-validate claims against SBTi, CDP, and other databases
- **Comprehensive Scoring**: Multi-dimensional scoring with detailed findings and recommendations
- **Rich Visualizations**: Interactive charts and reports for analysis interpretation
- **Zero-Config Setup**: Works out-of-the-box with sensible defaults

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Core Concepts](#core-concepts)
- [Extension Guide](#extension-guide)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.9 or higher
- An API key for your preferred LLM provider (OpenAI, Anthropic, etc.)

### Install from Source

```bash
git clone https://github.com/openclaw/climate-disclosure-agent.git
cd climate-disclosure-agent
pip install -e .
```

### Install via pip (when released)

```bash
pip install climate-disclosure-agent
```

### Development Setup

```bash
git clone https://github.com/openclaw/climate-disclosure-agent.git
cd climate-disclosure-agent
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage (5 Lines of Code)

```python
from cda import ClimateDisclosureAgent

agent = ClimateDisclosureAgent()
result = agent.analyze("cargill_esg_2024.pdf", company_name="Cargill")

print(f"Score: {result.overall_score}/100 ({result.grade})")
print(f"Issues: {len([f for vr in result.validation_results for f in vr.findings])}")
```

### Advanced Usage with External Data

```python
from cda import ClimateDisclosureAgent
from cda.adapters import SBTiAdapter, CDPAdapter

agent = ClimateDisclosureAgent(
    adapters=[
        SBTiAdapter("sbti_companies.csv"),
        CDPAdapter("cdp_scores.csv"),
    ]
)

result = agent.analyze(
    "cargill_esg_2024.pdf",
    company_name="Cargill",
    sector="food_agriculture",
    validate_external=True
)

# View detailed findings
for vr in result.validation_results:
    print(f"[{vr.validator_name}] Score: {vr.score}")
    for f in vr.findings:
        print(f"  - [{f.severity}] {f.message}")
```

### Batch Analysis and Comparison

```python
from cda import ClimateDisclosureAgent
from cda.output import DisclosureVisualizer

agent = ClimateDisclosureAgent()
viz = DisclosureVisualizer()

# Compare multiple companies
companies = {
    "Cargill": "reports/cargill_2024.pdf",
    "ADM": "reports/adm_2024.pdf",
    "Bunge": "reports/bunge_2024.pdf",
}

results = [
    agent.analyze(path, company_name=name, sector="food_agriculture")
    for name, path in companies.items()
]

# Generate comparison visualizations
fig = viz.comparison_radar(results)
fig.show()

heatmap_fig = viz.completeness_heatmap(results)
heatmap_fig.show()
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    ClimateDisclosureAgent                 │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │   Ingestion  │───▶│  Extraction  │───▶│  Validation │  │
│  │    Layer     │    │    Engine    │    │   Pipeline  │  │
│  └─────────────┘    └──────────────┘    └──────┬──────┘  │
│        ▲                   ▲                   │         │
│        │                   │                   ▼         │
│  ┌─────┴─────┐    ┌───────┴──────┐    ┌──────────────┐  │
│  │  Input     │    │   LLM        │    │   Scoring    │  │
│  │  Adapters  │    │   Provider   │    │   Engine     │  │
│  │  (PDF/JSON │    │   Interface  │    │              │  │
│  │   /Text)   │    │  (OpenAI/    │    │  ┌────────┐  │  │
│  └───────────┘    │   Claude/    │    │  │Consist.│  │  │
│                    │   Local)     │    │  │Quantif.│  │  │
│                    └──────────────┘    │  │Complet.│  │  │
│                                       │  │Risk    │  │  │
│  ┌────────────────────────────────┐   │  └────────┘  │  │
│  │     External Data Adapters     │───┤              │  │
│  │  (SBTi / CDP / TRACE / Custom) │   └──────────────┘  │
│  └────────────────────────────────┘          │           │
│                                              ▼           │
│                                     ┌──────────────┐     │
│                                     │    Output     │     │
│                                     │  (JSON/DF/   │     │
│                                     │   Viz/Report) │     │
│                                     └──────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### Component Layers

1. **Ingestion Layer**: Handles various input formats (PDF, JSON, plain text)
2. **Extraction Engine**: Uses LLMs to extract structured data from unstructured documents
3. **Validation Pipeline**: Runs multiple validators to assess disclosure quality
4. **Scoring Engine**: Aggregates validation results into a comprehensive score
5. **Output Layer**: Renders results in various formats (JSON, DataFrame, visualization, report)

## Core Concepts

### Data Model (DisclosureExtract)

The central data structure that flows through the system:

```python
class DisclosureExtract(BaseModel):
    company_name: str
    report_year: int
    report_type: str = "sustainability"
    framework: List[str] = []  # ["TCFD", "GRI", "SASB"]
    sector: Optional[str] = None
    
    # Emissions data
    emissions: List[EmissionData] = []
    
    # Targets commitments
    targets: List[TargetData] = []
    
    # Risk disclosures
    risks: List[RiskItem] = []
    
    # Governance structure
    governance: GovernanceData = GovernanceData()
    
    # Source references for audit trail
    source_references: dict[str, str] = Field(...)
```

### Validation Framework

The system uses five core validators to assess disclosure quality:

1. **Consistency Validator**: Checks internal consistency between narrative and data
2. **Quantification Validator**: Evaluates the degree of quantitative disclosure
3. **Completeness Validator**: Assesses coverage against TCFD/SASB/GRI frameworks
4. **Risk Coverage Validator**: Verifies climate risk identification and disclosure
5. **News Consistency Validator**: Cross-validates disclosures with real-world news to detect greenwashing

### News Consistency Validation (Greenwashing Detection)

CDA includes a powerful news consistency validator that cross-references climate disclosures with real-world events to detect potential greenwashing:

**How it works:**
1. Searches environmental/climate news during the report period (Brave/Google/Bing APIs)
2. Extracts environmental events using LLM (fines, lawsuits, violations, accidents, regulations)
3. Cross-validates against disclosure claims to identify contradictions
4. Calculates credibility score (0-100) based on omissions and misrepresentations

**Event Types Detected:**
- Fines and penalties
- Lawsuits and legal actions
- Environmental accidents
- Regulatory violations
- Government investigations
- NGO reports and criticisms

**Contradiction Types:**
- **Omission**: Significant events not mentioned in the report
- **Misrepresentation**: Claims contradicted by news evidence
- **Timing Mismatch**: Event dates don't align with disclosure timeline
- **Magnitude Mismatch**: Severity downplayed compared to news reports

**Example Usage:**
```python
from cda.validation.news_consistency import NewsConsistencyValidator

# Initialize with news API key
validator = NewsConsistencyValidator(
    news_api_key="your_brave_api_key",
    news_provider="brave"  # or "google", "bing"
)

# Validate disclosure
result = validator.validate(disclosure_data)

print(f"Credibility Score: {result.score * 100:.1f}/100")
print(f"News Articles Found: {result.metadata['news_articles_found']}")
print(f"Events Extracted: {result.metadata['events_extracted']}")
print(f"Contradictions: {result.metadata['contradictions_found']}")

# Review findings
for finding in result.findings:
    print(f"\n[{finding.severity}] {finding.code}")
    print(f"  Message: {finding.message}")
    print(f"  Recommendation: {finding.recommendation}")
    print(f"  Source: {finding.metadata['source_url']}")
```

**Configuration:**
```python
# Set API keys via environment variables
export BRAVE_API_KEY="your_key"
export GOOGLE_NEWS_API_KEY="your_key"
export BING_NEWS_API_KEY="your_key"

# Or pass directly
validator = NewsConsistencyValidator(news_api_key="your_key")
```

**Integration with Main Agent:**
```python
from cda import ClimateDisclosureAgent

agent = ClimateDisclosureAgent(
    enable_news_validation=True,
    news_api_key="your_brave_api_key"
)

result = agent.analyze("company_report.pdf", company_name="Acme Corp")

# News validation results included automatically
news_result = next(
    vr for vr in result.validation_results 
    if vr.validator_name == "news_consistency"
)
print(f"Credibility: {news_result.score * 100:.1f}/100")

### External Data Adapters

Adapters allow cross-validation against external databases:
- SBTi (Science-Based Targets initiative)
- CDP (Carbon Disclosure Project)
- Climate TRACE
- News sources (for credibility validation)
- Custom data sources

## Extension Guide

### Creating a Custom Validator

```python
from cda.validation import BaseValidator, ValidationResult, Severity

class GreenwashingDetector(BaseValidator):
    """Detects potential greenwashing signals"""

    name = "greenwashing_detector"
    description = "Identifies discrepancies between claims and data"

    VAGUE_TERMS = [
        "carbon neutral", "eco-friendly", "sustainable",
        "net positive", "climate leader"
    ]

    def validate(self, extract):
        findings = []

        # Count vague terms vs quantified data
        vague_count = sum(
            1 for ref in extract.source_references.values()
            if any(term in ref.lower() for term in self.VAGUE_TERMS)
        )

        quantified_count = len([
            e for e in extract.emissions if e.value is not None
        ])

        if vague_count > quantified_count * 2:
            findings.append(self._finding(
                code="GREENWASH-001",
                severity=Severity.WARNING,
                message=f"High ratio of vague claims ({vague_count}) "
                        f"vs quantified data ({quantified_count})"
            ))

        score = 1.0 - min(vague_count / max(quantified_count * 3, 1), 1.0)

        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings
        )

# Register with the agent
agent = ClimateDisclosureAgent()
agent.validators.append(GreenwashingDetector())
```

### Creating a Custom Data Adapter

```python
from cda.adapters import BaseAdapter, ValidationResult, ValidationFinding, Severity
import pandas as pd

class CustomAdapter(BaseAdapter):
    """Custom data source adapter"""

    name = "custom_data"
    data_source_url = "https://your-data-source.com"

    def __init__(self, data_source):
        self._data = pd.read_csv(data_source) if isinstance(data_source, str) else data_source

    def cross_validate(self, extract):
        # Find company in external data
        match = self._data[self._data["company_name"].str.contains(
            extract.company_name, case=False, na=False
        )]

        findings = []
        if match.empty:
            findings.append(ValidationFinding(
                validator=self.name,
                code="CUSTOM-001",
                severity=Severity.INFO,
                message=f"Company not found in {self.name} dataset"
            ))
        else:
            # Validate specific claims against external data
            for idx, record in match.iterrows():
                # Add validation logic here
                pass

        return ValidationResult(
            validator_name=f"adapter:{self.name}",
            score=1.0 if not match.empty else 0.8,  # Example scoring
            findings=findings
        )

    def get_benchmark(self, sector: str) -> dict:
        return {"source": self.name, "data_available": not self._data.empty}

    def _has_data(self) -> bool:
        return self._data is not None and not self._data.empty
```

### Custom Output Format

```python
from cda.output import OutputRenderer

class CustomReport(OutputRenderer):
    """Custom report renderer"""

    def render(self, result):
        # Generate custom report format
        report = f"# Climate Disclosure Report: {result.company_name}\n\n"
        report += f"**Overall Score**: {result.overall_score}/100 ({result.grade})\n\n"
        
        for vr in result.validation_results:
            report += f"## {vr.validator_name}: {vr.score}\n"
            for finding in vr.findings:
                report += f"- **[{finding.severity}]** {finding.message}\n"
        
        return report
```

## Contributing

We welcome contributions to the Climate Disclosure Validation Agent! Here's how you can help:

### Reporting Issues

- Use the issue tracker to report bugs or suggest features
- Provide detailed reproduction steps for bugs
- Clearly describe your feature request with use cases

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Setting Up Development Environment

```bash
git clone https://github.com/openclaw/climate-disclosure-agent.git
cd climate-disclosure-agent
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all public interfaces
- Write docstrings for all classes and functions
- Maintain high test coverage (≥80%)
- Keep pull requests focused on a single feature or bug fix

### Areas Needing Contribution

- Additional industry-specific validation rules
- More external data adapters
- Enhanced visualization options
- Improved natural language processing
- Additional output formats
- Documentation improvements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Pydantic](https://pydantic.dev/) for robust data validation
- Uses [LangChain](https://python.langchain.com/) for LLM integration
- Powered by [Plotly](https://plotly.com/python/) for interactive visualizations
- Inspired by TCFD, SASB, and GRI sustainability reporting frameworks