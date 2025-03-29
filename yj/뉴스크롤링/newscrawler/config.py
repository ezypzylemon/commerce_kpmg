# config.py
import os
from datetime import datetime, timedelta

# 환경변수에서 민감한 정보 로드 (환경변수가 없으면 기본값 사용)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '9999')
DB_NAME = os.environ.get('DB_NAME', 'news_db')

# MySQL 설정
MYSQL_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'use_unicode': True,
    'pool_size': 5,  # 연결 풀 크기
    'pool_reset_session': True
}

# 테이블 이름
NEWS_TABLE = "knews_articles"

# 검색 키워드 설정
KEYWORDS = ["패션", "의류", "패션 트렌드", "의류 산업", "스타일", "브랜드", "디자인", "유행", "트렌드"]

# 검색 기간 설정
SEARCH_DAYS = 30
SEARCH_START_DATE = (datetime.now() - timedelta(days=SEARCH_DAYS)).strftime('%Y-%m-%d')
SEARCH_END_DATE = datetime.now().strftime('%Y-%m-%d')

# 크롤링 설정
MAX_PAGES = 20  # 크롤링할 최대 페이지 수
PAGE_DELAY = 1.0  # 페이지 간 딜레이(초)
ARTICLE_DELAY = 0.5  # 기사 간 딜레이(초)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# 재시도 설정
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 2  # 재시도 기본 딜레이(초)

# 로깅 설정
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'crawler.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # 루트 로거
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

# 크롤링 타겟 URL (섹션별)
TARGET_URLS = {
    "한국섬유신문": {
        "패션": "https://www.ktnews.com/news/articleList.html?sc_section_code=S1N1&sc_sub_section_code=S2N13&view_type=sm",
        "섬유": "https://www.ktnews.com/news/articleList.html?sc_section_code=S1N2&view_type=sm",
        "원단": "https://www.ktnews.com/news/articleList.html?sc_section_code=S1N3&view_type=sm"
    }
}

# config.py에 추가
# 토큰화 설정
# config.py에 다음 추가
TOKENISED_DB = "hyungtaeso"
TOKENISED_TABLE = "tokenised"