from flask import Flask, request, jsonify
from flask_cors import CORS
from news_api import NewsAPI
from nlp_processor import NLPProcessor
from trivia_api import TriviaAPI, WikipediaAPI
from config import Config
import logging
import traceback
import requests as req

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CORS(app, origins=[
    'http://localhost:3000',
    'http://172.23.2.8:3000',
    'http://127.0.0.1:3000'
], supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])

# Initialize all components
news_api = NewsAPI()
nlp_processor = NLPProcessor()
trivia_api = TriviaAPI()
wiki_api = WikipediaAPI()


# ─── Health ───────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'AI News Chatbot API is running',
        'version': '2.0.0',
        'features': ['news', 'trivia', 'wikipedia']
    })


# ─── News endpoints ───────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return _cors_preflight()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400

        query_info = nlp_processor.extract_query_info(user_message)

        if query_info.get('keywords') and len(query_info['keywords']) < 2:
            query_info['keywords'] = None

        news_articles = fetch_news(query_info)
        response_text = generate_response(news_articles, query_info)
        suggestions = generate_suggestions(query_info)

        return jsonify({
            'success': True,
            'response': response_text,
            'articles': news_articles,
            'query_info': query_info,
            'suggestions': suggestions,
            'total_articles': len(news_articles)
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/categories', methods=['GET', 'OPTIONS'])
def get_categories():
    if request.method == 'OPTIONS':
        return _cors_preflight()
    try:
        categories = [
            {
                'id': cid,
                'name': info['name'],
                'description': info['description'],
                'keywords': info['keywords'][:5]
            }
            for cid, info in Config.CATEGORIES.items()
        ]
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        logger.error(f"Categories error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch categories'}), 500


@app.route('/api/countries', methods=['GET', 'OPTIONS'])
def get_countries():
    if request.method == 'OPTIONS':
        return _cors_preflight()
    try:
        countries = [
            {'code': code, 'name': info['name'], 'keywords': info['keywords']}
            for code, info in Config.COUNTRIES.items()
        ]
        return jsonify({'success': True, 'countries': countries})
    except Exception as e:
        logger.error(f"Countries error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch countries'}), 500


@app.route('/api/search', methods=['GET', 'OPTIONS'])
def search():
    if request.method == 'OPTIONS':
        return _cors_preflight()
    try:
        query = request.args.get('q', '')
        category = request.args.get('category', None)

        if not query or len(query) < 2:
            return jsonify({'success': False, 'error': 'Query must be at least 2 characters'}), 400

        articles = news_api.search_news(query, category)
        return jsonify({'success': True, 'articles': articles, 'query': query, 'total': len(articles)})

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ─── Trivia endpoints ─────────────────────────────────────────────────────────

@app.route('/api/trivia/questions', methods=['GET', 'OPTIONS'])
def get_trivia_questions():
    """Fetch trivia/MCQ questions from Open Trivia DB"""
    if request.method == 'OPTIONS':
        return _cors_preflight()

    try:
        amount = int(request.args.get('amount', 10))
        difficulty = request.args.get('difficulty', 'hard')
        category = request.args.get('category', None)
        qtype = request.args.get('type', 'multiple')

        amount = max(1, min(amount, 50))

        questions = trivia_api.get_questions(
            amount=amount,
            difficulty=difficulty,
            category=category,
            qtype=qtype
        )

        if not questions:
            return jsonify({
                'success': False,
                'error': 'No questions available for these filters. Try different settings.'
            }), 404

        return jsonify({
            'success': True,
            'questions': questions,
            'total': len(questions),
            'difficulty': difficulty,
            'category': category
        })

    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount parameter'}), 400
    except Exception as e:
        logger.error(f"Trivia error: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'Failed to fetch questions'}), 500


@app.route('/api/trivia/categories', methods=['GET'])
def get_trivia_categories():
    """Return available trivia categories"""
    categories = [
        {'id': k, 'name': k.title(), 'code': v}
        for k, v in TriviaAPI.CATEGORY_MAP.items()
    ]
    return jsonify({'success': True, 'categories': categories})


# ─── Wikipedia endpoints ──────────────────────────────────────────────────────

@app.route('/api/wiki/summary', methods=['GET', 'OPTIONS'])
def get_wiki_summary():
    """Get Wikipedia summary for a topic"""
    if request.method == 'OPTIONS':
        return _cors_preflight()

    try:
        topic = request.args.get('topic', '').strip()
        if not topic:
            return jsonify({'success': False, 'error': 'Topic parameter is required'}), 400

        if len(topic) < 2:
            return jsonify({'success': False, 'error': 'Topic must be at least 2 characters'}), 400

        # First try to get summary
        summary = wiki_api.get_summary(topic)

        if not summary:
            # If no summary found, try search and get results
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': topic,
                'format': 'json',
                'srlimit': 5,
                'origin': '*'
            }
            
            try:
                search_response = req.get(search_url, params=params, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                search_data = search_response.json()
                results = search_data.get('query', {}).get('search', [])
                
                if results:
                    return jsonify({
                        'success': False,
                        'requires_selection': True,
                        'results': [{'title': r['title'], 'pageid': r['pageid']} for r in results[:5]],
                        'error': f'Multiple results found for "{topic}". Please select one.'
                    })
            except:
                pass
                
            return jsonify({
                'success': False,
                'error': f'No Wikipedia article found for "{topic}"'
            }), 404

        return jsonify({
            'success': True,
            'summary': summary,
            'topic': topic
        })

    except Exception as e:
        logger.error(f"Wikipedia error: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'Failed to fetch Wikipedia summary'}), 500


@app.route('/api/wiki/search', methods=['GET', 'OPTIONS'])
def wiki_search():
    """Search Wikipedia for articles"""
    if request.method == 'OPTIONS':
        return _cors_preflight()

    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'success': False, 'error': 'Query must be at least 2 characters'}), 400

        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'format': 'json',
            'srlimit': 5,
            'srprop': 'snippet|titlesnippet',
            'origin': '*'
        }
        
        response = req.get('https://en.wikipedia.org/w/api.php', params=params, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get('query', {}).get('search', []):
            # Clean the snippet from HTML tags
            snippet = item.get('snippet', '')
            import re
            snippet = re.sub(r'<[^>]+>', '', snippet)
            
            results.append({
                'title': item['title'],
                'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet,
                'pageid': item['pageid']
            })

        return jsonify({'success': True, 'results': results, 'query': query})

    except Exception as e:
        logger.error(f"Wiki search error: {e}")
        return jsonify({'success': False, 'error': 'Search failed'}), 500


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _cors_preflight():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response


def fetch_news(query_info):
    try:
        category = query_info.get('category', 'general')
        country = query_info.get('country')
        keywords = query_info.get('keywords')

        if keywords and len(keywords) > 2:
            articles = news_api.search_news(keywords, category)
            if articles:
                return articles

        if country and category and category != 'general':
            articles = news_api.get_top_headlines(category=category, country=country)
            if articles:
                return articles

        if category and category != 'general':
            articles = news_api.get_category_news(category)
            if articles:
                return articles

        if country:
            articles = news_api.get_country_news(country)
            if articles:
                return articles

        return news_api.get_top_headlines()
    except Exception as e:
        logger.error(f"fetch_news error: {e}")
        return []


def generate_response(articles, query_info):
    try:
        if not articles:
            return "No news articles found. Try a different query!"

        category = query_info.get('category', 'general')
        country_code = query_info.get('country')
        keywords = query_info.get('keywords')
        category_name = Config.CATEGORIES.get(category, {}).get('name', 'General')
        country_name = Config.COUNTRIES.get(country_code, {}).get('name') if country_code else None

        if keywords and len(keywords) > 2:
            count = len(articles)
            return f"Found {count} article{'s' if count != 1 else ''} about '{keywords}':"
        elif country_name and category_name != 'General':
            return f"Latest {category_name} headlines from {country_name}:"
        elif category_name != 'General':
            return f"Latest {category_name} news:"
        elif country_name:
            return f"Top headlines from {country_name}:"
        else:
            return "Latest headlines from around the world:"
    except Exception as e:
        logger.error(f"generate_response error: {e}")
        return "Here are the latest headlines:"


def generate_suggestions(query_info):
    return [
        "Technology news",
        "Sports headlines",
        "Business news",
        "Science discoveries",
        "Health news"
    ]


if __name__ == '__main__':
    port = Config.PORT
    logger.info(f"Starting AI News Chatbot API v2 on port {port}")
    logger.info("Features: News, Trivia (MCQs), Wikipedia")
    app.run(host='0.0.0.0', port=port, debug=True)