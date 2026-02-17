"""News data source implementations for the News Consistency Validator."""

import os
import requests
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus

from .news_models import NewsArticle


DEFAULT_KEYWORDS = [
    "environment", "climate", "pollution", "emission",
    "fine", "penalty", "lawsuit", "violation",
    "regulation", "EPA", "investigation",
    "carbon", "greenhouse gas", "sustainability"
]


class NewsDataSource(ABC):
    """Abstract base class for news data sources."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize data source."""
        self.api_key = api_key

    @abstractmethod
    def search_news(
        self,
        company_name: str,
        start_date: str,
        end_date: str,
        keywords: List[str] = None,
        max_results: int = 50
    ) -> List[NewsArticle]:
        """
        Search for news articles.

        Args:
            company_name: Name of the company
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            keywords: Additional keywords (default: environmental terms)
            max_results: Maximum number of results

        Returns:
            List of news articles
        """
        pass


class BraveNewsAPI(NewsDataSource):
    """Brave Search API implementation."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Brave Search API."""
        super().__init__(api_key)
        self.base_url = "https://api.search.brave.com/res/v1/news/search"
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY environment variable not set")

    def search_news(
        self,
        company_name: str,
        start_date: str,
        end_date: str,
        keywords: List[str] = None,
        max_results: int = 50
    ) -> List[NewsArticle]:
        """
        Search for news using Brave Search API.
        """
        if keywords is None:
            keywords = DEFAULT_KEYWORDS
            
        # Construct query: "{company_name}" AND ({keyword1} OR {keyword2} OR ...)
        keyword_str = " OR ".join(keywords)
        query = f'"{company_name}" AND ({keyword_str})'
        
        headers = {
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": max_results,
            "freshness": f"pd365",  # Past year, we'll filter further
            "country": "us",
            "search_lang": "en"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            raw_articles = data.get('news', [])
            
            # Filter articles by date range
            filtered_articles = []
            for item in raw_articles:
                pub_date_str = item.get('published', '')
                if pub_date_str:
                    try:
                        # Parse publication date
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        pub_date = pub_date.replace(tzinfo=None)  # Remove timezone for comparison
                        
                        # Parse our date range
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        
                        # Check if article is within date range
                        if start_dt <= pub_date <= end_dt:
                            article = NewsArticle(
                                title=item.get('title', ''),
                                url=item.get('url', ''),
                                source=item.get('source', 'Unknown'),
                                published_date=pub_date.strftime('%Y-%m-%d'),
                                snippet=item.get('description', ''),
                                relevance_score=item.get('relevance_score', 0.0)
                            )
                            filtered_articles.append(article)
                    except ValueError:
                        # Skip articles with invalid dates
                        continue
            
            # Remove duplicates based on URL and title
            unique_articles = []
            seen_urls = set()
            seen_titles = set()
            
            for article in filtered_articles:
                if article.url not in seen_urls and article.title not in seen_titles:
                    unique_articles.append(article)
                    seen_urls.add(article.url)
                    seen_titles.add(article.title)
                    
                if len(unique_articles) >= max_results:
                    break
            
            return unique_articles
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying Brave Search API: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error in BraveNewsAPI: {str(e)}")
            return []


class GoogleNewsAPI(NewsDataSource):
    """Google News API implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Google News API."""
        super().__init__(api_key)
        self.base_url = "https://newsapi.org/v2/everything"
        self.api_key = api_key or os.getenv("GOOGLE_NEWS_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_NEWS_API_KEY environment variable not set")

    def search_news(
        self,
        company_name: str,
        start_date: str,
        end_date: str,
        keywords: List[str] = None,
        max_results: int = 50
    ) -> List[NewsArticle]:
        """
        Search for news using Google News API.
        """
        if keywords is None:
            keywords = DEFAULT_KEYWORDS
            
        # Construct query: "{company_name}" AND ({keyword1} OR {keyword2} OR ...)
        keyword_str = " OR ".join(keywords)
        query = f'"{company_name}" AND ({keyword_str}) AND ("environment" OR "climate" OR "emission" OR "pollution" OR "fine" OR "lawsuit" OR "violation")'
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params = {
            "q": query,
            "from": start_date,
            "to": end_date,
            "sortBy": "relevancy",
            "pageSize": min(max_results, 100),  # Max page size is 100
            "page": 1,
            "language": "en"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            raw_articles = data.get('articles', [])
            
            articles = []
            for item in raw_articles:
                source_name = item.get('source', {}).get('name', 'Unknown')
                
                # Parse publication date
                pub_date_str = item.get('publishedAt', '')
                pub_date = ''
                if pub_date_str:
                    try:
                        pub_date_obj = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        pub_date = pub_date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        pub_date = ''
                
                article = NewsArticle(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    source=source_name,
                    published_date=pub_date,
                    snippet=item.get('description', '') or item.get('content', '')[:200],
                    relevance_score=0.0  # Google News API doesn't provide relevance score
                )
                articles.append(article)
                
                if len(articles) >= max_results:
                    break
            
            # Remove duplicates based on URL and title
            unique_articles = []
            seen_urls = set()
            seen_titles = set()
            
            for article in articles:
                if article.url not in seen_urls and article.title not in seen_titles:
                    unique_articles.append(article)
                    seen_urls.add(article.url)
                    seen_titles.add(article.title)
                    
                if len(unique_articles) >= max_results:
                    break
            
            return unique_articles
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying Google News API: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error in GoogleNewsAPI: {str(e)}")
            return []


class BingNewsAPI(NewsDataSource):
    """Bing News API implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Bing News API."""
        super().__init__(api_key)
        self.base_url = "https://api.bing.microsoft.com/v7.0/news/search"
        self.api_key = api_key or os.getenv("BING_NEWS_API_KEY")
        
        if not self.api_key:
            raise ValueError("BING_NEWS_API_KEY environment variable not set")

    def search_news(
        self,
        company_name: str,
        start_date: str,
        end_date: str,
        keywords: List[str] = None,
        max_results: int = 50
    ) -> List[NewsArticle]:
        """
        Search for news using Bing News API.
        """
        if keywords is None:
            keywords = DEFAULT_KEYWORDS
            
        # Construct query: "{company_name}" AND ({keyword1} OR {keyword2} OR ...)
        keyword_str = " OR ".join(keywords)
        query = f'"{company_name}" AND ({keyword_str})'
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": min(max_results, 100),  # Max count is 100
            "offset": 0,
            "mkt": "en-US",
            "since": int(datetime.strptime(start_date, "%Y-%m-%d").timestamp()),
            "sortBy": "Date"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            raw_articles = data.get('value', [])
            
            articles = []
            for item in raw_articles:
                # Parse publication date
                pub_date_str = item.get('datePublished', '')
                pub_date = ''
                if pub_date_str:
                    try:
                        pub_date_obj = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        pub_date = pub_date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        pub_date = ''
                
                # Check if article is within our date range
                if pub_date:
                    article_date = datetime.strptime(pub_date, "%Y-%m-%d")
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    
                    if start_dt <= article_date <= end_dt:
                        article = NewsArticle(
                            title=item.get('name', ''),
                            url=item.get('url', ''),
                            source=item.get('provider', [{}])[0].get('name', 'Unknown') if item.get('provider') else 'Unknown',
                            published_date=pub_date,
                            snippet=item.get('description', ''),
                            relevance_score=0.0  # Bing News API doesn't provide relevance score
                        )
                        articles.append(article)
                
                if len(articles) >= max_results:
                    break
            
            # Remove duplicates based on URL and title
            unique_articles = []
            seen_urls = set()
            seen_titles = set()
            
            for article in articles:
                if article.url not in seen_urls and article.title not in seen_titles:
                    unique_articles.append(article)
                    seen_urls.add(article.url)
                    seen_titles.add(article.title)
                    
                if len(unique_articles) >= max_results:
                    break
            
            return unique_articles
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying Bing News API: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error in BingNewsAPI: {str(e)}")
            return []


class NewsDataSourceManager:
    """Manager for multiple news data sources with fallback capability."""
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize manager with API keys for different providers.
        
        Args:
            api_keys: Dictionary mapping provider names to API keys
        """
        self.api_keys = api_keys
        self.sources = {}
        
        # Initialize sources if API keys are provided
        if 'brave' in api_keys:
            self.sources['brave'] = BraveNewsAPI(api_keys['brave'])
        if 'google' in api_keys:
            self.sources['google'] = GoogleNewsAPI(api_keys['google'])
        if 'bing' in api_keys:
            self.sources['bing'] = BingNewsAPI(api_keys['bing'])
    
    def search_news(
        self,
        company_name: str,
        start_date: str,
        end_date: str,
        keywords: List[str] = None,
        max_results: int = 50,
        preferred_source: str = 'brave'
    ) -> List[NewsArticle]:
        """
        Search news using preferred source with fallback to others.
        
        Args:
            company_name: Name of the company
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            keywords: Additional keywords
            max_results: Maximum number of results
            preferred_source: Preferred news source ('brave', 'google', 'bing')
        
        Returns:
            List of news articles
        """
        # Try preferred source first
        if preferred_source in self.sources:
            try:
                articles = self.sources[preferred_source].search_news(
                    company_name, start_date, end_date, keywords, max_results
                )
                if articles:
                    return articles
            except Exception as e:
                print(f"Preferred source {preferred_source} failed: {str(e)}")
        
        # Try other sources as fallback
        for source_name, source in self.sources.items():
            if source_name != preferred_source:
                try:
                    articles = source.search_news(
                        company_name, start_date, end_date, keywords, max_results
                    )
                    if articles:
                        return articles
                except Exception as e:
                    print(f"Fallback source {source_name} failed: {str(e)}")
        
        # If all sources fail, return empty list
        print("All news sources failed, returning empty list")
        return []