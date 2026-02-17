"""Example usage of the News Consistency Validator."""

from cda.validation.news_consistency import NewsConsistencyValidator
from cda.base import DisclosureExtract
from cda.validation.pipeline import ValidationPipeline
from cda.scoring.scorer import Scorer


def example_news_validation():
    """Example of using the news consistency validator."""
    
    # Create a sample disclosure extract
    disclosure = DisclosureExtract(
        company_name="Apple Inc.",
        report_year=2023,
        risks="We face risks related to environmental regulations and climate change.",
        goals="Achieve carbon neutrality across our supply chain by 2030.",
        emissions_data="Scope 1 emissions: 150,000 tCO2e in 2023, reduced by 20% from 2022.",
        initiatives="Renewable energy transition, recycling programs, sustainable materials."
    )
    
    # Initialize the news consistency validator
    # Note: You'll need to provide an actual API key for real usage
    validator = NewsConsistencyValidator(
        news_api_key=None,  # Will try to use environment variable
        llm_provider="openai",
        llm_config={"model": "gpt-3.5-turbo"}
    )
    
    print("Running news consistency validation...")
    
    try:
        # Validate the disclosure
        result = validator.validate(disclosure)
        
        print(f"\nValidation Result:")
        print(f"  Validator: {result.validator_name}")
        print(f"  Dimension: {result.dimension}")
        print(f"  Score: {result.score}/100")
        print(f"  Findings: {len(result.findings)} issues found")
        
        for finding in result.findings:
            print(f"    - {finding.severity.value}: {finding.message}")
            print(f"      Recommendation: {finding.recommendation}")
        
        print(f"\nMetadata: {result.metadata}")
        
    except Exception as e:
        print(f"Error during validation: {str(e)}")


def example_full_pipeline():
    """Example of using the news validator in the full pipeline."""
    
    # Create a sample disclosure extract
    disclosure = DisclosureExtract(
        company_name="Microsoft Corporation",
        report_year=2023,
        risks="We face risks related to environmental regulations and climate change.",
        goals="Achieve carbon negativity by 2030 and remove all historical emissions by 2050.",
        emissions_data="Scope 1+2 emissions: 1.66M tCO2e in 2023, reduced by 37% from 2019.",
        initiatives="Carbon fee program, renewable energy purchases, carbon removal investments."
    )
    
    # Create the default pipeline with news validator
    pipeline = ValidationPipeline.default_pipeline(news_api_key=None)
    
    print("\nRunning full validation pipeline with news consistency...")
    
    try:
        # Run the pipeline
        results = pipeline.run(disclosure)
        
        print(f"\nPipeline completed with {len(results)} validation results:")
        
        for result in results:
            print(f"  - {result.validator_name}: {result.score}")
            
            if result.findings:
                print(f"    Findings: {len(result.findings)}")
                for finding in result.findings:
                    print(f"      * {finding.severity.value}: {finding.message}")
        
        # Score the results
        scorer = Scorer()
        aggregated = scorer.aggregate(disclosure, results)
        
        print(f"\nAggregated Score: {aggregated.overall_score}/100 (Grade: {aggregated.grade})")
        print(f"Dimension Scores: {aggregated.dimension_scores}")
        
    except Exception as e:
        print(f"Error during pipeline execution: {str(e)}")


def example_scenarios():
    """Demonstrate different validation scenarios."""
    
    print("\n" + "="*60)
    print("EXAMPLE SCENARIOS FOR NEWS CONSISTENCY VALIDATION")
    print("="*60)
    
    print("\nScenario 1: Company with no negative environmental news")
    print("-" * 50)
    good_disclosure = DisclosureExtract(
        company_name="GreenTech Solutions",
        report_year=2023,
        risks="Standard environmental compliance risks.",
        goals="Continue sustainability leadership.",
        emissions_data="Net-zero emissions achieved in 2023.",
        initiatives="Solar installations, waste reduction programs."
    )
    
    print(f"Company: {good_disclosure.company_name}")
    print(f"Goals: {good_disclosure.goals}")
    print("Expected: High credibility score (no contradictions)")
    
    print("\nScenario 2: Company with negative news not disclosed")
    print("-" * 50)
    problematic_disclosure = DisclosureExtract(
        company_name="Polluting Industries",
        report_year=2023,
        risks="We have minimal environmental risks.",
        goals="Environmental stewardship remains a priority.",
        emissions_data="Emissions have remained stable.",
        initiatives="Various environmental programs."
    )
    
    print(f"Company: {problematic_disclosure.company_name}")
    print(f"Risks: {problematic_disclosure.risks}")
    print("Expected: Low credibility score due to omissions")
    
    print("\nScenario 3: Company with conflicting claims")
    print("-" * 50)
    conflicting_disclosure = DisclosureExtract(
        company_name="CleanEnergy Corp",
        report_year=2023,
        risks="No significant environmental risks anticipated.",
        goals="Achieve carbon neutrality by 2025.",
        emissions_data="Zero emissions reported for all operations.",
        initiatives="Committed to 100% clean energy."
    )
    
    print(f"Company: {conflicting_disclosure.company_name}")
    print(f"Goals: {conflicting_disclosure.goals}")
    print("Expected: Medium credibility score if claims are contradicted by news")


if __name__ == "__main__":
    example_news_validation()
    example_full_pipeline()
    example_scenarios()