# News Validation Feature Documentation

## Overview

The News Consistency Validator is a powerful feature of the Climate Disclosure Agent (CDA) that cross-validates corporate climate disclosures with real-world news events. This feature helps detect potential greenwashing by identifying discrepancies between what companies claim in their reports and what is reported in the media.

## Purpose

The primary goal of news validation is to:
- Detect omissions of material environmental events in corporate reports
- Identify misrepresentations or misleading claims about environmental performance
- Assess the credibility of climate-related disclosures
- Provide transparency into corporate environmental accountability

## How It Works

### 1. News Collection
The system searches for news articles during the reporting period using multiple sources:
- **Brave Search API** (default)
- **Google News API**
- **Bing News API**

Search queries combine the company name with environmental keywords such as:
- environment, climate, pollution, emission
- fine, penalty, lawsuit, violation
- regulation, EPA, investigation
- carbon, greenhouse gas, sustainability

### 2. Event Extraction
Using LLM-based processing, the system extracts environmental events from news articles, categorizing them as:
- **Fine**: Financial penalties for environmental violations
- **Lawsuit**: Legal proceedings related to environmental issues
- **Accident**: Environmental incidents or accidents
- **Regulation**: New regulatory requirements
- **Violation**: Breaches of environmental standards
- **Investigation**: Ongoing environmental investigations
- **NGO Report**: Environmental assessments by NGOs

### 3. Cross-Validation
The system compares extracted news events with the company's disclosure to identify:
- **Omissions**: Events reported in news but not in the disclosure
- **Misrepresentations**: Claims in the report that contradict news events
- **Timing Mismatches**: Events that occurred during the report period but weren't disclosed
- **Magnitude Mismatches**: Discrepancies in the scale of environmental impacts

### 4. Credibility Scoring
A credibility score (0-100) is calculated based on:
- Number and severity of contradictions found
- Type of contradictions (omission vs. misrepresentation)
- Financial impact of unreported events

## Configuration

### API Keys
To use the news validation feature, you need an API key from one of the supported news services:

#### Brave Search API (Recommended)
- Free tier: 2000 queries/month
- Register at: https://brave.com/search/api/
- Environment variable: `BRAVE_API_KEY`

#### Google News API
- Free tier: 100 queries/day
- Register at: https://newsapi.org/
- Environment variable: `GOOGLE_NEWS_API_KEY`

#### Bing News API
- Free tier: 1000 queries/month
- Register at: https://www.microsoft.com/en-us/bing/apis/bing-news-search-api
- Environment variable: `BING_NEWS_API_KEY`

### Configuration Options
The news validator can be configured through environment variables:

- `NEWS_VALIDATOR_ENABLED`: Enable/disable the validator (default: true)
- `NEWS_API_PROVIDER`: News provider to use (brave, google, bing) (default: brave)
- `NEWS_API_KEY`: API key for news service
- `NEWS_MAX_ARTICLES`: Maximum articles to fetch (default: 50)
- `NEWS_LLM_PROVIDER`: LLM provider for processing (default: openai)
- `NEWS_LLM_MODEL`: LLM model for processing (default: gpt-3.5-turbo)
- `NEWS_DEFAULT_KEYWORDS`: Comma-separated list of search keywords

## Usage

### Basic Usage
```python
from cda.validation.news_consistency import NewsConsistencyValidator
from cda.base import DisclosureExtract

# Create a disclosure extract
disclosure = DisclosureExtract(
    company_name="Apple Inc.",
    report_year=2023,
    risks="We face risks related to environmental regulations.",
    goals="Achieve carbon neutrality by 2030.",
    emissions_data="Scope 1 emissions: 150,000 tCO2e",
    initiatives="Renewable energy transition."
)

# Initialize the validator
validator = NewsConsistencyValidator(news_api_key="your_api_key")

# Run validation
result = validator.validate(disclosure)

print(f"Credibility Score: {result.score}/100")
for finding in result.findings:
    print(f"- {finding.severity}: {finding.message}")
    print(f"  Recommendation: {finding.recommendation}")
```

### Integration with Pipeline
```python
from cda.validation.pipeline import ValidationPipeline

# Use the default pipeline which includes news validation
pipeline = ValidationPipeline.default_pipeline(news_api_key="your_api_key")
results = pipeline.run(disclosure)

# Or create a custom pipeline
from cda.validation.news_consistency import NewsConsistencyValidator

custom_pipeline = ValidationPipeline(
    validators=[
        # ... other validators ...
        NewsConsistencyValidator(news_api_key="your_api_key")
    ]
)
```

## Scoring System

The credibility score is calculated as follows:

- **Base Score**: 100 points
- **Deductions**:
  - Critical contradictions: -30 points each
  - Warning-level contradictions: -15 points each
  - Information-level contradictions: -5 points each
- **Minimum Score**: 0 points
- **No Events Found**: 100 points (assuming no negative news)

### Rating Scale
- **90-100**: Excellent (no contradictions or only minor issues)
- **70-89**: Good (few minor warnings)
- **50-69**: Fair (multiple warnings or few critical issues)
- **30-49**: Poor (multiple critical issues)
- **0-29**: Very Poor (extensive contradictions, suspected greenwashing)

## Contradiction Types

### Omission
An environmental event occurred but was not disclosed in the report.
- Example: Company fined $5M for pollution violations, but not mentioned in report
- Severity: Critical or Warning depending on financial impact

### Misrepresentation
Claims in the report contradict actual events reported in news.
- Example: Company claims "zero emissions" but news reports exceed emission limits
- Severity: Critical or Warning depending on the nature of the misrepresentation

### Timing Mismatch
Events occurred during the reporting period but weren't disclosed in a timely manner.
- Severity: Warning or Info depending on significance

### Magnitude Mismatch
Discrepancy between reported and actual scale of environmental impacts.
- Example: News reports $50M fine but report mentions only $5M financial impact
- Severity: Warning or Info depending on the scale of discrepancy

## Error Handling

The news validator is designed to handle errors gracefully:

- If API keys are invalid or rate limits are exceeded, the validator returns a score of 0 with appropriate findings
- Network errors result in graceful degradation with informative error messages
- If no news sources are available, the validator returns neutral results
- LLM processing failures are caught and logged without stopping the entire pipeline

## Privacy and Data Usage

- News articles are temporarily processed for event extraction
- No personal data is collected or stored
- API requests comply with the respective service's privacy policies
- Processed results are kept only as long as necessary for scoring

## Limitations

- News coverage may not be comprehensive for all companies
- Some environmental events may not be reported in mainstream media
- Language limitations may affect non-English news sources
- Time delays between events and news reporting
- Potential bias in news coverage

## Best Practices

1. **Use Multiple Sources**: Configure multiple news API keys for redundancy
2. **Regular Updates**: Run news validation periodically to catch newly reported events
3. **Context Consideration**: Interpret results in the context of company size and industry
4. **Verification**: Manually verify critical findings before making business decisions
5. **Combine with Other Data**: Use news validation alongside other data sources for comprehensive assessment

## Troubleshooting

### Common Issues
- **Low News Volume**: Verify company name spelling and try alternative names
- **API Errors**: Check API keys and rate limits
- **Poor LLM Results**: Consider upgrading to a more capable LLM model
- **False Positives**: Adjust keywords or increase confidence thresholds

### Debugging
Enable logging to see detailed information about the validation process:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

For further assistance, consult the community forums or submit an issue on GitHub.