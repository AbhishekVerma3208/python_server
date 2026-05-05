import re
import nltk
import logging
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    logger.warning(f"Error downloading NLTK data: {e}")

class NLPProcessor:
    """Advanced NLP processor for understanding user queries"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Load categories and countries from config
        self.categories = Config.CATEGORIES
        self.countries = Config.COUNTRIES
        
        # Pre-compile patterns for better performance
        self._compile_patterns()
        
        logger.info("NLP Processor initialized successfully")

    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        # Category patterns
        self.category_patterns = {}
        for category_id, category_info in self.categories.items():
            pattern = '|'.join(re.escape(keyword) for keyword in category_info['keywords'])
            self.category_patterns[category_id] = re.compile(f'\\b({pattern})\\b', re.IGNORECASE)
        
        # Country patterns
        self.country_patterns = {}
        for country_code, country_info in self.countries.items():
            pattern = '|'.join(re.escape(keyword) for keyword in country_info['keywords'])
            self.country_patterns[country_code] = re.compile(f'\\b({pattern})\\b', re.IGNORECASE)

    def extract_query_info(self, user_input):
        """
        Extract comprehensive information from user input
        """
        try:
            # Basic preprocessing
            user_input = user_input.strip()
            if not user_input:
                return self._get_default_query_info()
            
            # Tokenization and lemmatization
            tokens = self._preprocess_text(user_input)
            
            # Extract entities
            query_info = {
                'category': self._identify_category(user_input, tokens),
                'country': self._identify_country(user_input),
                'keywords': self._extract_keywords(user_input, tokens),
                'original_query': user_input,
                'sentiment': self._analyze_sentiment(tokens),
                'query_type': self._identify_query_type(user_input)
            }
            
            # Extract specific entities (people, organizations, etc.)
            query_info['entities'] = self._extract_entities(tokens)
            
            logger.info(f"Query processed: {query_info}")
            return query_info
            
        except Exception as e:
            logger.error(f"Error in NLP processing: {e}")
            return self._get_default_query_info()

    def _preprocess_text(self, text):
        """Preprocess text: tokenize, lemmatize, remove stopwords"""
        try:
            # Tokenize
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and non-alphabetic tokens
            tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
            
            # Lemmatize
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
            return tokens
        except Exception as e:
            logger.error(f"Error in text preprocessing: {e}")
            return []

    def _identify_category(self, text, tokens):
        """Identify news category with confidence score"""
        text_lower = text.lower()
        
        # Check each category's patterns
        best_category = 'general'
        best_score = 0
        
        for category_id, pattern in self.category_patterns.items():
            matches = pattern.findall(text_lower)
            score = len(matches) * 2  # Higher weight for direct matches
            
            # Check in tokens as well
            token_matches = sum(1 for token in tokens if token in self.categories[category_id]['keywords'])
            score += token_matches
            
            if score > best_score:
                best_score = score
                best_category = category_id
        
        return best_category

    def _identify_country(self, text):
        """Identify country from text"""
        text_lower = text.lower()
        
        for country_code, pattern in self.country_patterns.items():
            if pattern.search(text_lower):
                return country_code
        
        return None

    def _extract_keywords(self, text, tokens):
        """Extract meaningful keywords for search"""
        # Remove common query phrases
        common_phrases = ['show', 'get', 'give', 'tell', 'me', 'about', 'for', 'the', 
                         'news', 'headlines', 'latest', 'today', 'what', 'is', 'are']
        
        # Filter out common phrases and category/country keywords
        keywords = []
        for token in tokens:
            if token not in common_phrases:
                # Check if it's not a category keyword
                is_category_keyword = False
                for category_info in self.categories.values():
                    if token in category_info['keywords']:
                        is_category_keyword = True
                        break
                
                # Check if it's not a country keyword
                is_country_keyword = False
                for country_info in self.countries.values():
                    if token in country_info['keywords']:
                        is_country_keyword = True
                        break
                
                if not is_category_keyword and not is_country_keyword and len(token) > 1:
                    keywords.append(token)
        
        # Only return keywords if they're meaningful (more than 1 character)
        if keywords and len(' '.join(keywords)) > 2:
            return ' '.join(keywords)
        return None

    def _extract_phrases(self, text):
        """Extract meaningful phrases from text"""
        phrases = []
        words = text.split()
        
        for i in range(len(words) - 1):
            # Bigrams
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram.split()) == 2 and all(len(w) > 2 for w in bigram.split()):
                phrases.append(bigram)
            
            # Trigrams
            if i < len(words) - 2:
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if len(trigram.split()) == 3 and all(len(w) > 2 for w in trigram.split()):
                    phrases.append(trigram)
        
        return phrases

    def _extract_entities(self, tokens):
        """Extract named entities (simplified version)"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': []
        }
        
        # Simple heuristic-based entity extraction
        for token in tokens:
            if token.istitle() and len(token) > 2:
                # Check against known locations
                is_location = False
                for country_info in self.countries.values():
                    if token.lower() in country_info['keywords']:
                        entities['locations'].append(token)
                        is_location = True
                        break
                
                if not is_location:
                    entities['organizations'].append(token)
        
        return entities

    def _analyze_sentiment(self, tokens):
        """Basic sentiment analysis"""
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'love'}
        negative_words = {'bad', 'worst', 'terrible', 'awful', 'hate', 'poor', 'ugly'}
        
        pos_count = sum(1 for token in tokens if token in positive_words)
        neg_count = sum(1 for token in tokens if token in negative_words)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'

    def _identify_query_type(self, text):
        """Identify the type of query"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['latest', 'recent', 'new', 'today', 'breaking']):
            return 'latest'
        elif any(word in text_lower for word in ['top', 'headlines', 'popular']):
            return 'top'
        elif any(word in text_lower for word in ['search', 'find', 'looking for']):
            return 'search'
        else:
            return 'general'

    def _get_default_query_info(self):
        """Return default query info when processing fails"""
        return {
            'category': 'general',
            'country': None,
            'keywords': None,
            'original_query': '',
            'sentiment': 'neutral',
            'query_type': 'general',
            'entities': {'persons': [], 'organizations': [], 'locations': []}
        }