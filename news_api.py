import requests
import logging
from datetime import datetime
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAPI:
    """Comprehensive News API handler with multiple endpoints"""
    
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = Config.NEWS_API_BASE_URL
        self.timeout = Config.REQUEST_TIMEOUT
        self.max_articles = Config.MAX_ARTICLES
        
        # Cache for rate limiting
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        logger.info("News API initialized")

    def get_top_headlines(self, category='general', country='us', query=None, page=1):
        """
        Fetch top headlines with multiple parameters
        """
        endpoint = f"{self.base_url}/top-headlines"
        
        # Build cache key
        cache_key = f"top_{category}_{country}_{query}_{page}"
        
        # Check cache
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_time < self.cache_duration:
                logger.info(f"Returning cached results for {cache_key}")
                return cache_data
        
        params = {
            'apiKey': self.api_key,
            'pageSize': self.max_articles,
            'page': page
        }
        
        # Add parameters based on what's provided
        if category and category != 'general':
            params['category'] = category
        
        if country:
            params['country'] = country
        
        if query:
            params['q'] = query
        
        try:
            logger.info(f"Fetching top headlines with params: {params}")
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = self._format_articles(data['articles'])
                # Cache the results
                self.cache[cache_key] = (datetime.now().timestamp(), articles)
                return articles
            else:
                logger.error(f"API returned error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            return []

    def search_news(self, query, category=None, from_date=None, to_date=None, sort_by='relevancy'):
        """
        Search for news with advanced filters (BEST FEATURE)
        """
        endpoint = f"{self.base_url}/everything"
        
        # Build cache key
        cache_key = f"search_{query}_{category}_{from_date}_{to_date}_{sort_by}"
        
        # Check cache
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_time < self.cache_duration:
                logger.info(f"Returning cached search results for {cache_key}")
                return cache_data
        
        params = {
            'apiKey': self.api_key,
            'q': query,
            'pageSize': self.max_articles,
            'sortBy': sort_by,
            'language': 'en'
        }
        
        # Add date filters
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        # Enhance query with category if provided
        if category and category != 'general':
            params['q'] = f"{query} AND ({category})"
        
        try:
            logger.info(f"Searching news with params: {params}")
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = self._format_articles(data['articles'])
                # Cache the results
                self.cache[cache_key] = (datetime.now().timestamp(), articles)
                return articles
            else:
                logger.error(f"Search API returned error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching news: {e}")
            return []

    def get_category_news(self, category):
        """
        Get news for a specific category
        """
        if category in Config.CATEGORIES:
            return self.get_top_headlines(category=category)
        return []

    def get_country_news(self, country):
        """
        Get news for a specific country
        """
        if country in Config.COUNTRIES:
            return self.get_top_headlines(country=country)
        return []

    def get_trending_topics(self):
        """
        Get trending topics (simulated - would need a real trending API)
        """
        # This would ideally come from a trending topics API
        trending = [
            {'topic': 'Technology', 'count': 1500},
            {'topic': 'Sports', 'count': 1200},
            {'topic': 'Business', 'count': 1000},
            {'topic': 'Entertainment', 'count': 900},
            {'topic': 'Science', 'count': 800}
        ]
        return trending

    def get_news_by_source(self, source, category=None):
        """
        Get news from specific sources
        """
        endpoint = f"{self.base_url}/everything"
        
        params = {
            'apiKey': self.api_key,
            'sources': source,
            'pageSize': self.max_articles,
            'sortBy': 'publishedAt'
        }
        
        if category:
            params['q'] = category
        
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                return self._format_articles(data['articles'])
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news by source: {e}")
            return []

    def _format_articles(self, articles):
        """
        Format and enrich articles for display with proper null checks
        """
        formatted_articles = []
        
        for idx, article in enumerate(articles):
            try:
                # Skip invalid articles
                if not article or not article.get('title') or article.get('title') == '[Removed]':
                    continue
                
                # Safely get description with null check
                description = article.get('description')
                if description is None:
                    description = ''
                
                # Calculate reading time with null check
                reading_time = self._calculate_reading_time(description)
                
                # Format date
                published_at = article.get('publishedAt', '')
                formatted_date = self._format_date(published_at)
                
                # Generate a simple ID
                url = article.get('url', '')
                article_id = f"article_{idx}_{hash(url)}" if url else f"article_{idx}"
                
                # Safely get image with fallback
                image_url = article.get('urlToImage')
                if not image_url:
                    image_url = 'https://via.placeholder.com/400x200?text=No+Image'
                
                # Safely get author
                author = article.get('author')
                if not author:
                    author = 'Unknown Author'
                
                formatted_article = {
                    'id': article_id,
                    'title': article.get('title', 'No title available'),
                    'description': description if description else 'Click to read more about this news article.',
                    'content': article.get('content', ''),
                    'url': url if url else '#',
                    'source': {
                        'id': article.get('source', {}).get('id', ''),
                        'name': article.get('source', {}).get('name', 'Unknown Source')
                    },
                    'publishedAt': published_at,
                    'formattedDate': formatted_date,
                    'image': image_url,
                    'author': author,
                    'readingTime': reading_time
                }
                
                formatted_articles.append(formatted_article)
                
            except Exception as e:
                logger.error(f"Error formatting article {idx}: {e}")
                continue
        
        return formatted_articles

    def _calculate_reading_time(self, text):
        """Calculate estimated reading time with null check"""
        try:
            if text is None or text == '':
                return 1
            
            words_per_minute = 200
            word_count = len(text.split())
            if word_count == 0:
                return 1
            minutes = word_count / words_per_minute
            return max(1, round(minutes))
        except Exception as e:
            logger.error(f"Error calculating reading time: {e}")
            return 1

    def _format_date(self, date_string):
        """Format date for display with error handling"""
        try:
            if not date_string:
                return ''
            
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            now = datetime.now(date_obj.tzinfo)
            
            # Calculate time difference
            diff = now - date_obj
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes} minutes ago"
                elif diff.seconds < 7200:
                    return "1 hour ago"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours} hours ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return date_obj.strftime("%b %d, %Y")
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return date_string

    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Cache cleared")