import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # API Keys
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '193fd54545fe404ca61e82eb02bff275')
    
    # API Endpoints
    NEWS_API_BASE_URL = 'https://newsapi.org/v2'
    
    # Server Configuration
    PORT = int(os.getenv('PORT', 5000))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://172.23.2.8:3000,http://127.0.0.1:3000').split(',')
    
    # News Categories with keywords for better matching
    CATEGORIES = {
        'general': {
            'name': 'General',
            'keywords': ['news', 'latest', 'headlines', 'breaking', 'today', 'update', 'current'],
            'description': 'Top headlines from various sources'
        },
        'business': {
            'name': 'Business',
            'keywords': ['business', 'economy', 'finance', 'stock', 'market', 'company', 'startup', 
                        'corporate', 'industry', 'trade', 'investment', 'banking', 'entrepreneur', 
                        'wall street', 'stocks', 'shares', 'economy', 'financial'],
            'description': 'Business news, stock market updates, and economic trends'
        },
        'technology': {
            'name': 'Technology',
            'keywords': ['technology', 'tech', 'software', 'hardware', 'ai', 'artificial intelligence', 
                        'computer', 'internet', 'digital', 'gadget', 'smartphone', 'app', 'coding', 
                        'programming', 'cybersecurity', 'robotics', 'innovation', 'startup'],
            'description': 'Latest tech news, AI developments, and gadget reviews'
        },
        'sports': {
            'name': 'Sports',
            'keywords': ['sports', 'sport', 'game', 'match', 'football', 'soccer', 'cricket', 
                        'basketball', 'tennis', 'olympics', 'tournament', 'player', 'team', 'score',
                        'nfl', 'nba', 'premier league', 'champions league', 'world cup'],
            'description': 'Sports news, match scores, and athlete updates'
        },
        'entertainment': {
            'name': 'Entertainment',
            'keywords': ['entertainment', 'movie', 'film', 'celebrity', 'hollywood', 'bollywood', 
                        'music', 'tv', 'television', 'series', 'actor', 'actress', 'drama', 'netflix',
                        'streaming', 'oscar', 'grammy', 'award', 'concert'],
            'description': 'Entertainment news, celebrity gossip, and movie reviews'
        },
        'health': {
            'name': 'Health',
            'keywords': ['health', 'medical', 'fitness', 'wellness', 'disease', 'covid', 'vaccine', 
                        'hospital', 'doctor', 'medicine', 'treatment', 'nutrition', 'workout', 'diet',
                        'mental health', 'healthcare', 'pharma', 'clinical'],
            'description': 'Health news, medical breakthroughs, and wellness tips'
        },
        'science': {
            'name': 'Science',
            'keywords': ['science', 'scientific', 'research', 'space', 'nasa', 'discovery', 'physics', 
                        'chemistry', 'biology', 'experiment', 'study', 'laboratory', 'scientist',
                        'climate', 'environment', 'evolution', 'genetics'],
            'description': 'Scientific discoveries, space exploration, and research updates'
        }
    }
    
    # Country codes with full names and keywords
    COUNTRIES = {
        'us': {
            'name': 'United States',
            'keywords': ['usa', 'united states', 'america', 'american', 'us']
        },
        'gb': {
            'name': 'United Kingdom',
            'keywords': ['uk', 'britain', 'british', 'england', 'london', 'united kingdom']
        },
        'in': {
            'name': 'India',
            'keywords': ['india', 'indian', 'delhi', 'mumbai', 'bangalore', 'bharat']
        },
        'ca': {
            'name': 'Canada',
            'keywords': ['canada', 'canadian', 'toronto', 'vancouver', 'montreal']
        },
        'au': {
            'name': 'Australia',
            'keywords': ['australia', 'australian', 'sydney', 'melbourne', 'perth']
        },
        'de': {
            'name': 'Germany',
            'keywords': ['germany', 'german', 'berlin', 'munich', 'deutschland']
        },
        'fr': {
            'name': 'France',
            'keywords': ['france', 'french', 'paris', 'lyon', 'marseille']
        },
        'jp': {
            'name': 'Japan',
            'keywords': ['japan', 'japanese', 'tokyo', 'osaka', 'kyoto']
        },
        'cn': {
            'name': 'China',
            'keywords': ['china', 'chinese', 'beijing', 'shanghai', 'hong kong']
        },
        'ru': {
            'name': 'Russia',
            'keywords': ['russia', 'russian', 'moscow', 'st petersburg']
        },
        'br': {
            'name': 'Brazil',
            'keywords': ['brazil', 'brazilian', 'rio', 'sao paulo', 'brasil']
        },
        'za': {
            'name': 'South Africa',
            'keywords': ['south africa', 'african', 'johannesburg', 'cape town']
        }
    }
    
    # API Request Configuration
    MAX_ARTICLES = 10
    REQUEST_TIMEOUT = 10
    
    # Response Messages
    ERROR_MESSAGES = {
        'api_error': 'Unable to fetch news at the moment. Please try again later.',
        'no_results': 'No news articles found for your query. Try different keywords or categories.',
        'invalid_query': 'Please provide a valid query to search for news.',
        'server_error': 'Internal server error. Please try again.'
    }