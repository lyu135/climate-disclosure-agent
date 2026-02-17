"""
LLM Extractor - Performs structured extraction from text using LLMs.

This module uses language models to extract structured climate disclosure
information from unstructured text.
"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging
from cda.extraction.schema import DisclosureExtract


logger = logging.getLogger(__name__)


class LLMExtractor:
    """
    LLM-based extractor for structured climate data.
    
    Uses language models to extract structured information from
    unstructured text based on the DisclosureExtract schema.
    """
    
    def __init__(self, provider: str = "openai", config: Optional[Dict] = None):
        """
        Initialize the LLM extractor.
        
        Args:
            provider: LLM provider ("openai", "claude", "local")
            config: Provider-specific configuration
        """
        self.provider = provider
        self.config = config or {}
        self._client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on provider."""
        if self.provider == "openai":
            try:
                import openai
                api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                
                # Set API key
                openai.api_key = api_key
                
                # Return a simple config dict for later use
                return {
                    "client": openai,
                    "model": self.config.get("model", "qwen-plus"),
                    "temperature": self.config.get("temperature", 0.0)
                }
            except ImportError:
                raise ImportError("openai package not installed. Install with 'pip install openai'")
        
        elif self.provider == "claude":
            try:
                import anthropic
                api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                
                client = anthropic.Anthropic(api_key=api_key)
                return {
                    "client": client,
                    "model": self.config.get("model", "claude-3-sonnet-20240229"),
                    "temperature": self.config.get("temperature", 0.0)
                }
            except ImportError:
                raise ImportError("anthropic package not installed. Install with 'pip install anthropic'")
        
        elif self.provider == "local":
            # Placeholder for local model support
            raise NotImplementedError("Local model support not yet implemented")
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def extract(self, text: str, company_name: Optional[str] = None, sector: Optional[str] = None) -> DisclosureExtract:
        """
        Extract structured climate disclosure data from text.
        
        Args:
            text: Input text to extract from
            company_name: Company name (if known)
            sector: Industry sector (if known)
            
        Returns:
            DisclosureExtract containing structured data
        """
        try:
            # Prepare the prompt
            prompt = self._prepare_extraction_prompt(text, company_name, sector)
            
            # Call the appropriate LLM provider
            if self.provider == "openai":
                result = self._call_openai(prompt)
            elif self.provider == "claude":
                result = self._call_claude(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse the result into the DisclosureExtract model
            return self._parse_result(result, company_name, sector)
        
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Return a minimal DisclosureExtract in case of failure
            return DisclosureExtract(
                company_name=company_name or "Unknown",
                report_year=2024,  # Default to current year
                extraction_confidence=0.0,
                extraction_method=f"llm_{self.provider}"
            )
    
    def _prepare_extraction_prompt(self, text: str, company_name: Optional[str], sector: Optional[str]) -> str:
        """
        Prepare the extraction prompt for the LLM.
        
        Args:
            text: Input text to extract from
            company_name: Company name (if known)
            sector: Industry sector (if known)
            
        Returns:
            Formatted prompt string
        """
        # Truncate text if too long to avoid token limits
        max_length = self.config.get("max_text_length", 10000)
        if len(text) > max_length:
            logger.warning(f"Input text truncated from {len(text)} to {max_length} characters")
            text = text[:max_length]
        
        prompt = f"""
You are an expert climate disclosure analyst. Extract structured information from the following text according to the schema defined below.

Please return only the JSON object with the extracted data, nothing else.

SCHEMA:
- company_name: string - The company name
- report_year: integer - The year of the report
- report_type: string - Type of report ("sustainability", "annual", "cdp")
- framework: array of strings - Frameworks used (e.g., ["TCFD", "GRI", "SASB"])
- sector: string - Industry sector (optional)
- emissions: array of objects with properties:
  - scope: string - "scope_1", "scope_2", or "scope_3"
  - value: number - Emission value in tCO2e (optional)
  - unit: string - Unit of measurement, default "tCO2e"
  - year: integer - Reporting year (optional)
  - baseline_year: integer - Baseline year for comparisons (optional)
  - intensity_value: number - Intensity metric value (optional)
  - intensity_unit: string - Unit for intensity metric (optional)
  - methodology: string - Calculation methodology (optional)
  - assurance_level: string - Third-party audit level (optional)
- targets: array of objects with properties:
  - description: string - Description of the target
  - target_year: integer - Year the target is aimed for (optional)
  - base_year: integer - Base year for the target (optional)
  - reduction_pct: number - Percentage reduction (optional)
  - scopes_covered: array of strings - Scopes covered by the target
  - is_science_based: boolean - Whether it's a science-based target (optional)
  - sbti_status: string - SBTi status ("committed", "approved", "none") (optional)
  - interim_targets: array of objects - Milestone targets (optional)
- risks: array of objects with properties:
  - risk_type: string - "physical" or "transition"
  - category: string - Risk category (e.g., "acute_physical", "policy_legal")
  - description: string - Detailed risk description
  - time_horizon: string - Time horizon ("short", "medium", "long") (optional)
  - financial_impact: string - Financial impact description (optional)
  - financial_impact_value: number - Quantified financial impact (optional)
  - mitigation_strategy: string - Mitigation strategy (optional)
  - likelihood: string - Likelihood assessment (optional)
- governance: object with properties:
  - board_oversight: boolean - Whether board has oversight (optional)
  - board_climate_committee: boolean - Whether board has climate committee (optional)
  - executive_incentive_linked: boolean - Whether executive incentives linked to climate (optional)
  - reporting_frequency: string - Frequency of climate reporting (optional)
- source_references: object - Mapping of fields to original text snippets (optional)
- extraction_confidence: number - Confidence score 0.0-1.0
- extraction_method: string - Method used for extraction

INPUT TEXT:
{text}

EXTRACTED DATA (return only valid JSON):
"""
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API to perform extraction."""
        try:
            client = self._client["client"]
            model = self._client["model"]
            temperature = self._client["temperature"]
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API to perform extraction."""
        try:
            client = self._client["client"]
            model = self._client["model"]
            temperature = self._client["temperature"]
            
            # Claude doesn't have a native JSON mode, so we need to be more explicit
            prompt_with_json_instruction = f"""
Human: {prompt}

Please respond with only the JSON object containing the extracted data, with no additional text or explanations.

<response>
Assistant:
"""
            
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt_with_json_instruction}
                ]
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
    
    def _parse_result(self, result: str, company_name: Optional[str], sector: Optional[str]) -> DisclosureExtract:
        """
        Parse the LLM result into a DisclosureExtract object.
        
        Args:
            result: Raw LLM output
            company_name: Company name (if known)
            sector: Industry sector (if known)
            
        Returns:
            Parsed DisclosureExtract object
        """
        import json
        
        try:
            # Clean up the response to extract JSON if wrapped in markdown
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]  # Remove ```json
            if result.endswith("```"):
                result = result[:-3]  # Remove ```
            
            # Parse the JSON
            data = json.loads(result)
            
            # Ensure required fields have defaults
            if company_name:
                data['company_name'] = company_name
            if sector and 'sector' not in data:
                data['sector'] = sector
            
            # Create and return the DisclosureExtract object
            return DisclosureExtract(**data)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM result as JSON: {e}")
            logger.debug(f"Raw LLM output: {result}")
            
            # Return a minimal DisclosureExtract in case of parsing failure
            return DisclosureExtract(
                company_name=company_name or "Unknown",
                report_year=2024,  # Default to current year
                extraction_confidence=0.0,
                extraction_method=f"llm_{self.provider}"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM result: {e}")
            # Return a minimal DisclosureExtract in case of any other error
            return DisclosureExtract(
                company_name=company_name or "Unknown",
                report_year=2024,  # Default to current year
                extraction_confidence=0.0,
                extraction_method=f"llm_{self.provider}"
            )