import time
import requests
import asyncio
from telegram import Bot
import re
import http.server
import socketserver
from http import HTTPStatus
import threading

# Telegram bot token and channel ID
BOT_TOKEN = '7024971848:AAHvOTDCMoCn2L9BTrXMB8FzyouAAnwpb2F'
CHANNEL_ID = '@headline_today'
bot = Bot(token=BOT_TOKEN)

# NewsData.io API Key
NEWS_API_KEY = 'pub_685073eff04f970dd66d5f239e10bb1e8dd5d'
NEWS_API_URL = 'https://newsdata.io/api/1/news'

# Store previously sent news links
posted_news_links = set()

# Function to fetch news from NewsData.io
def fetch_news():
    try:
        params = {
            'apikey': NEWS_API_KEY,
            'country': 'us',
            'language': 'en'
        }
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'results' in data:
            return [(article['title'], article.get('description', 'No summary available.'), article['link']) for article in data['results']]
        
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    
    return []

# Function to generate hashtags
def generate_hashtags(title):
    common_words = {"is", "am", "are", "does", "the", "and", "but", "or", "not", "was", "were", "has", "have", "had", 
                    "do", "does", "did", "with", "for", "from", "this", "that", "which", "on", "in", "at", "by", "to", 
                    "a", "an", "of", "it", "be", "as", "so", "if", "than", "then", "about", "after", "before", "who", 
                    "whom", "whose", "where", "when", "why", "how", "could", "carry", "require"}  

    words = re.findall(r'\b\w+\b', title.lower())  
    hashtags = ['#' + word for word in words if len(word) > 3 and word not in common_words][:5]
    return ' '.join(hashtags)

# Escape markdown function
def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'  
    return re.sub(f"([{re.escape(escape_chars)}])", r'\\\1', text)

# Async function to post news to Telegram (One Article Per 20 Minutes)
async def run_scheduler():
    while True:
        articles = fetch_news()
        for title, summary, link in articles:
            if link in posted_news_links:
                continue  # Skip duplicate news
            
            posted_news_links.add(link)
            hashtags = generate_hashtags(title)
            message = f"📰 *{escape_markdown(title)}*\n\n{summary}\n\n🔗 [Read more]({link})\n\n{hashtags}\n\nJoin us- [Headline Today](https://linktr.ee/headlinetoday)"
            
            await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown', disable_web_page_preview=True)
            print(f"Posted: {title}")
            await asyncio.sleep(1200)  # Wait 20 minutes before posting the next news article

# Function to run the bot asynchronously
def start_bot():
    asyncio.run(run_scheduler())

# Simple HTTP server for Render
PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

# Start the HTTP server in a separate thread
def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Server started at port", PORT)
        httpd.serve_forever()

if __name__ == '__main__':
    print("Starting bot and server...")

    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    # Start the HTTP server
    start_server()
