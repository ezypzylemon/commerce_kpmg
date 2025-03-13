# Database Configuration
DB_PATH = "fashion_trends.db"

# Crawling Schedule
CRAWL_TIME = "13:00"

# URLs
URLS = {
    'vogue': "https://www.vogue.co.kr/fashion/fashion-trend/",
    'wkorea': "https://www.wkorea.com/fashion/",
    'jentestore': "https://jentestore.com/promotion?category=trend",
    'wwdkorea': "https://www.wwdkorea.com/news/articleList.html?sc_section_code=S1N3&view_type=sm",
    'marieclaire': "https://www.marieclairekorea.com/category/fashion/fashion_trend/"
}

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Logging Configuration
LOG_CONFIG = {
    'filename': 'fashion_trend_crawler.log',
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s'
}

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fashion_trends'
}

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyD5g-ytYa_3q1cNbN21EyZUgxXx8gTrbGk"  # Google AI Studio에서 발급받은 키
