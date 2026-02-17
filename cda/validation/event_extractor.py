"""Event extractor for the News Consistency Validator."""

import json
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from .news_models import NewsArticle, EnvironmentalEvent, EventType


class EventExtractor:
    """Extract environmental events from news articles using LLM."""

    def __init__(self, llm_provider: str = "openai", llm_config: Optional[Dict] = None):
        """
        Initialize LLM for event extraction.
        
        Args:
            llm_provider: LLM provider ('openai', 'anthropic', etc.)
            llm_config: LLM configuration parameters
        """
        self.llm_provider = llm_provider
        self.llm_config = llm_config or {}
        
        # Default LLM configuration
        default_config = {
            "model": "gpt-3.5-turbo",  # Can be overridden
            "temperature": 0.1,        # Low temperature for consistent extraction
            "max_tokens": 1000
        }
        
        # Merge with user config
        self.llm_config = {**default_config, **self.llm_config}
        
        # Initialize LLM based on provider
        if llm_provider.lower() == "openai":
            self.llm = ChatOpenAI(**self.llm_config)
        else:
            # For now, default to OpenAI - can extend later
            self.llm = ChatOpenAI(**self.llm_config)

    def extract_events(
        self,
        news_articles: List[NewsArticle],
        company_name: str
    ) -> List[EnvironmentalEvent]:
        """
        Extract environmental events from a list of news articles.

        Args:
            news_articles: List of news articles
            company_name: Name of the company

        Returns:
            List of environmental events
        """
        if not news_articles:
            return []
        
        # Process articles in batches to avoid token limits
        batch_size = 10
        all_events = []
        
        for i in range(0, len(news_articles), batch_size):
            batch = news_articles[i:i + batch_size]
            batch_events = self._extract_events_from_batch(batch, company_name)
            all_events.extend(batch_events)
        
        return all_events

    def _extract_events_from_batch(
        self,
        articles: List[NewsArticle],
        company_name: str
    ) -> List[EnvironmentalEvent]:
        """Extract events from a batch of articles."""
        events = []
        
        for article in articles:
            event = self._extract_single_event(article, company_name)
            if event and event.confidence >= 0.5:  # Filter low-confidence extractions
                events.append(event)
        
        return events

    def _extract_single_event(
        self,
        article: NewsArticle,
        company_name: str
    ) -> Optional[EnvironmentalEvent]:
        """Extract an event from a single article."""
        # Build the prompt
        prompt = self._build_extraction_prompt(company_name, article)
        
        try:
            # Call the LLM
            response = self.llm.invoke([HumanMessage(content=prompt)])
            response_text = response.content.strip()
            
            # Parse the response
            event_data = self._parse_llm_response(response_text)
            
            if event_data is None:
                return None
                
            # Create EnvironmentalEvent object
            event = EnvironmentalEvent(
                event_type=EventType(event_data["event_type"]),
                description=event_data["description"],
                date=event_data["date"],
                severity=event_data["severity"],
                financial_impact=event_data.get("financial_impact"),
                source_article=article,
                keywords=event_data.get("keywords", []),
                confidence=event_data.get("confidence", 0.5)
            )
            
            return event
            
        except Exception as e:
            print(f"Error extracting event from article '{article.title}': {str(e)}")
            return None

    def _build_extraction_prompt(self, company_name: str, article: NewsArticle) -> str:
        """Build the prompt for LLM event extraction."""
        prompt_template = """
You are an environmental compliance analyst. Extract structured information about environmental/climate events from the following news article.

Company: {company_name}
Article Title: {title}
Article Date: {date}
Article Content: {snippet}

Extract the following information (return JSON only):
{{
  "event_type": "fine|lawsuit|accident|regulation|violation|investigation|ngo_report|other",
  "description": "Brief description of the event",
  "date": "YYYY-MM-DD (event date, not article date)",
  "severity": "critical|high|medium|low",
  "financial_impact": 1000000.0 (in USD, null if not mentioned),
  "keywords": ["keyword1", "keyword2"],
  "confidence": 0.9 (0.0-1.0, your confidence in this extraction)
}}

If the article is not about an environmental/climate event related to {company_name}, return null.
"""
        
        # Format the prompt
        formatted_prompt = prompt_template.format(
            company_name=company_name,
            title=article.title,
            date=article.published_date,
            snippet=article.snippet
        )
        
        return formatted_prompt

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response to extract event data."""
        # Clean the response
        response = response.strip()
        
        # Handle case where LLM returns "null" for non-environmental articles
        if response.lower().strip() == "null" or not response:
            return None
        
        # Try to find JSON in the response (in case LLM adds extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # If no JSON found, return None
            return None
        
        try:
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["event_type", "description", "date", "severity", "confidence"]
            for field in required_fields:
                if field not in data:
                    return None
            
            # Validate and normalize date format
            date_str = data["date"]
            if date_str:
                try:
                    # Try to parse the date
                    parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    data["date"] = parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    # If parsing fails, try other formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            data["date"] = parsed_date.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
            
            # Validate event type
            try:
                EventType(data["event_type"])
            except ValueError:
                # If event type is invalid, default to "other"
                data["event_type"] = "other"
            
            # Validate severity
            valid_severities = ["critical", "high", "medium", "low"]
            if data["severity"] not in valid_severities:
                data["severity"] = "medium"  # Default severity
            
            # Validate confidence
            confidence = float(data.get("confidence", 0.5))
            data["confidence"] = max(0.0, min(1.0, confidence))  # Clamp to 0-1 range
            
            # Extract financial impact if present
            financial_impact = data.get("financial_impact")
            if financial_impact is not None:
                try:
                    data["financial_impact"] = float(financial_impact)
                except (ValueError, TypeError):
                    data["financial_impact"] = None
            
            # Ensure keywords is a list
            if "keywords" not in data or not isinstance(data["keywords"], list):
                data["keywords"] = []
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            print(f"Response: {response}")
            return None
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            return None

    def _extract_financial_impact(self, text: str) -> Optional[float]:
        """Extract financial impact from text using regex patterns."""
        # Look for patterns like "$500M", "500 million dollars", etc.
        patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|bn|billion)?',  # $500M, $1.5B
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*mil(lion)?',  # 500 mil, 1.5 million
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*b(il(lion)?)?',  # 500 b, 1.5 billion
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match[0] if isinstance(match, tuple) else match
                try:
                    # Remove commas and convert to float
                    amount = float(amount_str.replace(',', ''))
                    
                    # Apply multipliers based on context
                    if 'million' in text.lower():
                        amount *= 1_000_000
                    elif 'billion' in text.lower() or 'bn' in text.lower():
                        amount *= 1_000_000_000
                    
                    amounts.append(amount)
                except ValueError:
                    continue
        
        # Return the highest amount found, or None if none found
        return max(amounts) if amounts else None