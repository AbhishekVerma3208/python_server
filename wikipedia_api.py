import requests
import logging
import urllib.parse

logger = logging.getLogger(__name__)

class WikipediaAPI:
    """Wikipedia API Handler with proper headers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'AI-News-Chatbot/1.0 (https://github.com/your-repo; your-email@example.com)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        self.timeout = 15

    def get_summary(self, topic):
        """Get Wikipedia summary for a topic"""
        try:
            # Clean the topic
            topic_clean = topic.strip().replace(' ', '_')
            encoded_topic = urllib.parse.quote(topic_clean)
            
            # Try direct API
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
            logger.info(f"Fetching: {url}")
            
            response = requests.get(url, timeout=self.timeout, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_response(data)
            else:
                # Fallback to search
                return self._search(topic)
                
        except Exception as e:
            logger.error(f"Wikipedia error: {e}")
            return self._search(topic)

    def _search(self, query):
        """Search Wikipedia for articles"""
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': 1,
                'origin': '*'
            }
            
            response = requests.get(url, params=params, timeout=self.timeout, headers=self.headers)
            data = response.json()
            
            results = data.get('query', {}).get('search', [])
            if results:
                title = results[0]['title']
                return self.get_summary(title)
            return None
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None

    def _format_response(self, data):
        """Format the API response"""
        return {
            'title': data.get('title', ''),
            'extract': data.get('extract', 'No information available.'),
            'description': data.get('description', ''),
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
            'thumbnail': data.get('thumbnail', {}).get('source') if data.get('thumbnail') else None
        }