# Extending the Climate Disclosure Agent

The Climate Disclosure Agent (CDA) is designed to be highly extensible through custom validators and adapters. This guide explains how to create and integrate your own validation logic and external data sources.

## Creating Custom Validators

### Understanding the BaseValidator

All validators extend the `BaseValidator` abstract class. A validator must implement the `validate()` method which takes a `DisclosureExtract` and returns a `ValidationResult`.

```python
from cda.validation.base import BaseValidator, ValidationResult, ValidationFinding, Severity
from cda.extraction.schema import DisclosureExtract

class MyCustomValidator(BaseValidator):
    name = "my_custom_validator"  # Unique identifier for the validator
    
    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []
        score = 1.0  # Default perfect score
        
        # Your validation logic here
        # Example: Check if company has any climate targets
        if not extract.targets:
            findings.append(self._finding(
                code="MYVAL-001",
                severity=Severity.CRITICAL,
                message="No climate targets disclosed",
                field="targets"
            ))
            score = 0.0
        
        # Calculate score based on validation results
        # Return ValidationResult with score and findings
        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={"custom_metadata": "value"}
        )
    
    def _finding(self, code, severity, message, **kwargs) -> ValidationFinding:
        """Helper method to create ValidationFinding objects"""
        return ValidationFinding(
            validator=self.name,
            code=code,
            severity=severity,
            message=message,
            **kwargs
        )
```

### Validator Development Best Practices

1. **Define Clear Validation Rules**: Each validator should focus on a specific aspect of disclosure quality.

2. **Use Appropriate Severity Levels**:
   - `CRITICAL`: Fundamental issues that significantly impact assessment
   - `WARNING`: Important issues that affect quality but aren't fundamental
   - `INFO`: Observations that provide context but don't affect scores

3. **Provide Meaningful Messages**: Error messages should clearly explain the issue and suggest improvements.

4. **Include Field References**: When possible, link findings to specific fields in the disclosure data.

5. **Add Metadata**: Include additional information in the metadata field for debugging and analysis.

### Example: Greenwashing Detector Validator

Here's a more complex example that detects potential greenwashing signals:

```python
from cda.validation.base import BaseValidator, ValidationResult, ValidationFinding, Severity
from cda.extraction.schema import DisclosureExtract

class GreenwashingDetector(BaseValidator):
    """Detects potential greenwashing signals in climate disclosures"""
    
    name = "greenwashing_detector"
    description = "Identifies disproportionate use of vague marketing terms vs. quantified data"
    
    VAGUE_TERMS = [
        "carbon neutral", "green", "eco-friendly", "sustainable",
        "net positive", "climate leader", "environmentally responsible",
        "eco-conscious", "clean energy", "green technology"
    ]

    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []
        
        # Count mentions of vague terms
        vague_count = 0
        for ref in extract.source_references.values():
            for term in self.VAGUE_TERMS:
                if term.lower() in ref.lower():
                    vague_count += 1
                    break  # Don't double count for multiple terms in same reference
        
        # Count quantified data elements
        quantified_count = len([
            e for e in extract.emissions 
            if e.value is not None or e.intensity_value is not None
        ])
        quantified_count += len([t for t in extract.targets if t.reduction_pct is not None])
        quantified_count += len([
            r for r in extract.risks 
            if r.financial_impact_value is not None
        ])
        
        # Generate findings based on ratio
        if vague_count > 0 and quantified_count == 0:
            findings.append(self._finding(
                code="GREENWASH-001",
                severity=Severity.CRITICAL,
                message=f"Vague marketing terms found ({vague_count}) but no quantified data present",
                recommendation="Support marketing claims with concrete metrics and targets"
            ))
        elif vague_count > quantified_count * 2:
            findings.append(self._finding(
                code="GREENWASH-002",
                severity=Severity.WARNING,
                message=f"High ratio of vague claims ({vague_count}) vs quantified data ({quantified_count})",
                recommendation="Balance marketing language with measurable data"
            ))
        
        # Calculate score inversely proportional to greenwashing indicators
        score = max(0.0, 1.0 - min(vague_count / max(quantified_count * 3, 1), 1.0))
        
        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={
                "vague_terms_count": vague_count,
                "quantified_data_count": quantified_count,
                "vague_to_quant_ratio": vague_count / max(quantified_count, 1)
            }
        )

    def _finding(self, code, severity, message, **kwargs) -> ValidationFinding:
        return ValidationFinding(
            validator=self.name,
            code=code,
            severity=severity,
            message=message,
            **kwargs
        )
```

### Registering Custom Validators

To use your custom validator, register it with the agent:

```python
from cda import ClimateDisclosureAgent

# Initialize the agent
agent = ClimateDisclosureAgent()

# Add your custom validator
custom_validator = MyCustomValidator()
agent.pipeline.validators.append(custom_validator)

# Or initialize with custom validators
agent = ClimateDisclosureAgent(
    validators=["consistency", "quantification", "completeness", "risk_coverage"]
)

# Manually add your validator to the pipeline
agent.pipeline.validators.append(MyCustomValidator())
```

## Creating Custom Adapters

### Understanding the BaseAdapter

Adapters connect the CDA to external data sources. All adapters extend the `BaseAdapter` abstract class and must implement methods for cross-validation and benchmarking.

```python
from cda.adapters.base import BaseAdapter, DataNotAvailableError, ValidationResult
from cda.extraction.schema import DisclosureExtract

class MyCustomAdapter(BaseAdapter):
    """Example custom adapter implementation"""
    
    name = "my_custom_adapter"
    data_source_url = "https://example.com/data-source"
    requires_auth = True
    
    def __init__(self, data_source=None, api_key=None):
        """
        Initialize the adapter with data source
        
        Args:
            data_source: Path to data file, DataFrame, or API endpoint
            api_key: Authentication token if required
        """
        self.api_key = api_key
        self._data = self._load_data(data_source)
    
    def cross_validate(self, extract: DisclosureExtract) -> ValidationResult:
        """Perform cross-validation against external data"""
        if self._data is None:
            raise DataNotAvailableError(
                f"No data provided for {self.name}. Source: {self.data_source_url}"
            )
        
        findings = []
        
        # Perform cross-validation logic
        # Example: Look up company in external dataset
        company_match = self._find_company(extract.company_name)
        
        if not company_match:
            findings.append(self._finding(
                code="DATA-001",
                severity=Severity.INFO,
                message=f"Company '{extract.company_name}' not found in external data source"
            ))
        else:
            # Compare disclosure with external data
            discrepancies = self._compare_disclosure_with_external(extract, company_match)
            findings.extend(discrepancies)
        
        # Calculate score based on validation results
        critical_issues = len([f for f in findings if f.severity == Severity.CRITICAL])
        score = max(0.0, 1.0 - (critical_issues * 0.3))  # Deduct 0.3 for each critical issue
        
        return ValidationResult(
            validator_name=f"adapter:{self.name}",
            score=score,
            findings=findings,
            metadata={"match_found": bool(company_match)}
        )
    
    def get_benchmark(self, sector: str) -> dict:
        """Get industry benchmark data"""
        if self._data is None:
            return {}
        
        sector_data = self._filter_by_sector(sector)
        return {
            "total_companies": len(sector_data),
            "metric_average": self._calculate_average(sector_data),
            "compliance_rate": self._calculate_compliance_rate(sector_data)
        }
    
    def _has_data(self) -> bool:
        """Check if adapter has loaded data"""
        return self._data is not None
    
    def _load_data(self, source):
        """Load data from various sources"""
        if source is None:
            return None
        
        import pandas as pd
        
        if isinstance(source, pd.DataFrame):
            return source
        elif isinstance(source, str):
            if source.endswith('.csv'):
                return pd.read_csv(source)
            elif source.endswith(('.xlsx', '.xls')):
                return pd.read_excel(source)
        else:
            # Handle API data loading
            return self._load_from_api(source)
    
    def _find_company(self, company_name: str):
        """Find company record in external data"""
        if self._data is None:
            return None
            
        # Simple exact match first
        matches = self._data[
            self._data['company_name'].str.contains(company_name, case=False, na=False)
        ]
        
        if len(matches) > 0:
            return matches.iloc[0]
        
        # Try fuzzy matching if no exact match
        return self._fuzzy_match(company_name)
    
    def _fuzzy_match(self, company_name: str):
        """Perform fuzzy matching for company names"""
        from difflib import get_close_matches
        
        if self._data is None:
            return None
            
        company_list = self._data['company_name'].tolist()
        matches = get_close_matches(company_name, company_list, n=1, cutoff=0.7)
        
        if matches:
            return self._data[self._data['company_name'] == matches[0]].iloc[0]
        return None
    
    def _compare_disclosure_with_external(self, extract: DisclosureExtract, external_record):
        """Compare disclosure data with external record"""
        findings = []
        
        # Example: Compare emissions data
        for emission in extract.emissions:
            if emission.value:
                external_value = external_record.get('reported_emissions')
                if external_value and abs(emission.value - external_value) > (external_value * 0.1):
                    findings.append(self._finding(
                        code="DATA-002",
                        severity=Severity.WARNING,
                        message=f"Emissions discrepancy: disclosed {emission.value}, external {external_value}",
                        field="emissions.value"
                    ))
        
        return findings
    
    def _filter_by_sector(self, sector: str):
        """Filter data by sector"""
        if self._data is None or 'sector' not in self._data.columns:
            return self._data
        return self._data[self._data['sector'].str.contains(sector, case=False, na=False)]
    
    def _calculate_average(self, sector_data):
        """Calculate average metric for sector"""
        if sector_data.empty or 'metric' not in sector_data.columns:
            return 0
        return sector_data['metric'].mean()
    
    def _calculate_compliance_rate(self, sector_data):
        """Calculate compliance rate for sector"""
        if sector_data.empty or 'compliant' not in sector_data.columns:
            return 0
        return (sector_data['compliant'].sum() / len(sector_data)) if len(sector_data) > 0 else 0
    
    def _load_from_api(self, endpoint: str):
        """Load data from API endpoint"""
        import requests
        
        headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        import pandas as pd
        return pd.DataFrame(response.json())
    
    def _finding(self, code, severity, message, **kwargs):
        """Create a validation finding"""
        from cda.validation.base import ValidationFinding
        return ValidationFinding(
            validator=self.name,
            code=code,
            severity=severity,
            message=message,
            **kwargs
        )
```

### Adapter Development Best Practices

1. **Handle Missing Data Gracefully**: Always check if data is available and raise `DataNotAvailableError` when appropriate rather than crashing.

2. **Provide Clear Data Source Information**: Include URLs and instructions for users to obtain the required data.

3. **Implement Fuzzy Matching**: Company names often vary between sources, so implement fuzzy matching capabilities.

4. **Include Status Checks**: Implement the `_has_data()` method to allow runtime checks of adapter readiness.

5. **Offer Benchmarking Capabilities**: Provide sector or peer comparison functionality where relevant.

### Using Custom Adapters

To use your custom adapter:

```python
from cda import ClimateDisclosureAgent

# Initialize your custom adapter
my_adapter = MyCustomAdapter(
    data_source="path/to/my_data.csv",
    api_key="your-api-key"  # if required
)

# Initialize the agent with your adapter
agent = ClimateDisclosureAgent(
    adapters=[my_adapter]
)

# Run analysis with external validation enabled
result = agent.analyze(
    "report.pdf",
    company_name="My Company",
    validate_external=True  # Enable cross-validation
)
```

## Advanced Extension Topics

### Custom Scoring Logic

You can also customize the scoring logic by extending the `Scorer` class:

```python
from cda.scoring.scorer import Scorer

class CustomScorer(Scorer):
    def __init__(self, weights=None, custom_rules=None):
        super().__init__(weights)
        self.custom_rules = custom_rules or {}
    
    def aggregate(self, extract, results):
        # Call parent aggregation
        base_result = super().aggregate(extract, results)
        
        # Apply custom rules
        for rule_name, rule_func in self.custom_rules.items():
            base_result = rule_func(base_result, extract, results)
        
        return base_result
```

### Combining Multiple Extensions

You can combine custom validators and adapters for comprehensive analysis:

```python
from cda import ClimateDisclosureAgent
from cda.adapters import SBTiAdapter

# Create custom extensions
greenwash_validator = GreenwashingDetector()
custom_adapter = MyCustomAdapter("data.csv")

# Initialize agent with both custom and standard extensions
agent = ClimateDisclosureAgent(
    validators=["consistency", "quantification", "completeness", "risk_coverage"],
    adapters=[SBTiAdapter("sbti_data.csv"), custom_adapter]
)

# Add custom validator to pipeline
agent.pipeline.validators.append(greenwash_validator)

# Run comprehensive analysis
result = agent.analyze("report.pdf", company_name="Example Corp")
```

By following these patterns, you can extend the CDA framework to meet specific validation requirements or integrate with proprietary data sources.