import requests
import base64
import logging
import random
import urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)


class TriviaAPI:
    """Handler for Open Trivia DB API"""
    
    BASE_URL = "https://opentdb.com/api.php"
    TIMEOUT = 10
    
    DIFFICULTY_MAP = {
        'easy': 'easy',
        'medium': 'medium', 
        'hard': 'hard',
        'any': None
    }
    
    CATEGORY_MAP = {
        'general': 9,
        'books': 10,
        'film': 11,
        'music': 12,
        'science': 17,
        'computers': 18,
        'math': 19,
        'sports': 21,
        'geography': 22,
        'history': 23,
        'politics': 24,
        'art': 25,
        'celebrities': 26,
        'animals': 27,
        'vehicles': 28,
        'comics': 29,
        'gadgets': 30,
        'japanese': 31,
        'cartoon': 32
    }

    def get_questions(self, amount=10, difficulty='hard', category=None, qtype='multiple'):
        """Fetch trivia questions from Open Trivia DB"""
        params = {
            'amount': min(amount, 50),
            'encode': 'base64',
            'type': qtype
        }
        
        if difficulty and difficulty != 'any':
            params['difficulty'] = difficulty
            
        if category and category in self.CATEGORY_MAP:
            params['category'] = self.CATEGORY_MAP[category]
        
        try:
            logger.info(f"Fetching {amount} trivia questions, difficulty={difficulty}")
            response = requests.get(self.BASE_URL, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get('response_code') == 0:
                questions = self._decode_questions(data['results'])
                logger.info(f"Got {len(questions)} questions")
                return questions
            elif data.get('response_code') == 1:
                logger.warning("Not enough questions available")
                return []
            else:
                logger.error(f"Trivia API error code: {data.get('response_code')}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trivia: {e}")
            return []

    def _decode_b64(self, text):
        """Safely decode base64 encoded text"""
        try:
            return base64.b64decode(text).decode('utf-8')
        except Exception:
            return text

    def _decode_questions(self, raw_questions):
        """Decode all base64 fields in questions"""
        decoded = []
        for q in raw_questions:
            try:
                correct = self._decode_b64(q['correct_answer'])
                incorrect = [self._decode_b64(a) for a in q['incorrect_answers']]
                
                # Shuffle options
                all_options = incorrect + [correct]
                random.shuffle(all_options)
                
                decoded.append({
                    'question': self._decode_b64(q['question']),
                    'correct_answer': correct,
                    'incorrect_answers': incorrect,
                    'options': all_options,
                    'category': self._decode_b64(q['category']),
                    'difficulty': q['difficulty'],
                    'type': q['type']
                })
            except Exception as e:
                logger.error(f"Error decoding question: {e}")
                continue
        return decoded


class WikipediaAPI:
    """Handler for Wikipedia REST API - COMPLETELY FIXED"""
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    TIMEOUT = 15
    
    # Proper headers to avoid 403 Forbidden
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }

    def get_summary(self, topic):
        """Get page summary for a topic"""
        if not topic or len(topic.strip()) < 2:
            return None
            
        # Clean and format topic for URL
        topic_clean = topic.strip().replace(' ', '_')
        encoded_topic = urllib.parse.quote(topic_clean)
        
        # Try direct summary API first
        url = f"{self.BASE_URL}/page/summary/{encoded_topic}"
        
        try:
            logger.info(f"Fetching Wikipedia summary for: {topic}")
            response = requests.get(url, timeout=self.TIMEOUT, headers=self.HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_summary(data)
            elif response.status_code == 404:
                logger.info(f"Direct page not found, searching for: {topic}")
                return self._search_and_get(topic)
            else:
                logger.warning(f"Wikipedia API returned {response.status_code}")
                return self._search_and_get(topic)
                
        except requests.exceptions.Timeout:
            logger.error(f"Wikipedia API timeout for: {topic}")
            return self._search_and_get(topic)
        except requests.exceptions.RequestException as e:
            logger.error(f"Wikipedia API error: {e}")
            return self._search_and_get(topic)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._search_and_get(topic)

    def _search_and_get(self, query):
        """Search Wikipedia and get the top result"""
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'format': 'json',
            'srlimit': 3,
            'origin': '*',
            'srprop': 'snippet'
        }
        
        try:
            logger.info(f"Searching Wikipedia for: {query}")
            response = requests.get(search_url, params=params, timeout=self.TIMEOUT, headers=self.HEADERS)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('query', {}).get('search', [])
            if results:
                # Try each result until we find a valid page
                for result in results:
                    title = result.get('title')
                    if title:
                        logger.info(f"Found article: {title}")
                        # Recursively get summary
                        summary = self.get_summary(title)
                        if summary:
                            return summary
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f"Search timeout for: {query}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            return None

    def _format_summary(self, data):
        """Format Wikipedia summary response"""
        if not data:
            return None
            
        # Handle disambiguation pages
        if data.get('type') == 'disambiguation':
            extract = data.get('extract', 'This is a disambiguation page. Please be more specific.')
            if 'may refer to' in extract:
                extract = extract[:500] + '...'
            
            return {
                'title': data.get('title', 'Unknown'),
                'extract': extract,
                'description': data.get('description', 'Multiple meanings available'),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', '#'),
                'thumbnail': None,
                'type': 'disambiguation'
            }
        
        # Regular article
        extract = data.get('extract', '')
        if not extract:
            extract = data.get('extract_html', 'No description available.')
        
        # Limit extract length for better display
        if len(extract) > 1500:
            extract = extract[:1500] + '...'
        
        return {
            'title': data.get('title', 'Unknown'),
            'extract': extract,
            'description': data.get('description', ''),
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', '#'),
            'thumbnail': data.get('thumbnail', {}).get('source') if data.get('thumbnail') else None,
            'type': 'article',
            'lastRevision': data.get('timestamp', '')
        }