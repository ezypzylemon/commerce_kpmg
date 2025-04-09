import os
from dotenv import load_dotenv

# .env 파일 로드 (없으면 환경 변수 사용)
load_dotenv()

# MySQL 데이터베이스 설정 - 매거진
MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'dydrkfl0320'),
    'database': os.getenv('DB_NAME', 'fashion_trends'),
    'port': int(os.getenv('DB_PORT', '3306'))
}

# MySQL 데이터베이스 설정 - 뉴스
NEWS_DB_CONFIG = {
    'host': os.getenv('NEWS_DB_HOST', 'localhost'),
    'user': os.getenv('NEWS_DB_USER', 'root'),
    'password': os.getenv('NEWS_DB_PASSWORD', 'dydrkfl0320'),
    'database': os.getenv('NEWS_DB_NAME', 'dump_migration'),
    'port': int(os.getenv('NEWS_DB_PORT', '3306'))
}

# 기존 DB 설정 (이전 코드와의 호환성을 위해 유지)
DB_CONFIG = MYSQL_CONFIG

# 앱 설정
APP_CONFIG = {
    'debug': os.getenv('APP_DEBUG', 'False').lower() == 'true',
    'secret_key': os.getenv('SECRET_KEY', 'your_secret_key_here'),
    'static_folder': os.getenv('STATIC_FOLDER', 'static'),
    'template_folder': os.getenv('TEMPLATE_FOLDER', 'templates')
}

# 기본 설정값
DEFAULT_PERIOD = os.getenv('DEFAULT_PERIOD', '7일')
DEFAULT_MAGAZINE = os.getenv('DEFAULT_MAGAZINE', 'W')
DEFAULT_KEYWORD = os.getenv('DEFAULT_KEYWORD', 'Y2K')
MAGAZINE_CHOICES = os.getenv('MAGAZINE_CHOICES', 'Vogue,W,Harper\'s').split(',')

# 캐싱 설정
# CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '3600'))  # 기본 1시간 캐싱

# 기간별 일수 매핑
PERIOD_DAYS = {
    '7일': 7,
    '2주': 14,
    '1개월': 30,
    '3개월': 90,
    '6개월': 180,
    '1년': 365
}

# 카테고리별 키워드 정의
CATEGORY_KEYWORDS = {
    '의류': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
    '신발': ['구두', '샌들', '부츠', '스니커즈', '로퍼', '플립플롭', '슬리퍼', '펌프스'],
    '액세서리': ['목걸이', '귀걸이', '반지', '브레이슬릿', '시계', '선글라스', '스카프', '벨트', '가방'],
    '가방': ['백팩', '토트백', '크로스백', '클러치', '숄더백', '에코백'],
    '기타': ['화장품', '향수', '주얼리', '선글라스', '시계']
}

# 불용어 목록
STOPWORDS = set([
    '것', '수', '등', '더', '위해', '또한', '있는', '하는', '에서', '으로',
    '그리고', '이번', '한편', '있다', '했다', '대한', '가장', '이런',
    '한다', '한다면', '바', '때', '다양한', '통해', '기자', '최근',
    '우리', '많은', '중', '때문', '대한', '모든', '하지만', '중인',
    '이후', '그녀', '그는', '에서의', '있는지', '중심', '된다', '있으며',
    '된다', '된다면', '위한','스타일링', '스타일', '아이템', '패션', '브랜드',
    '컬렉션', '코디', '컬러', '트렌드', '디자이너', '쇼핑', '코디', '코디네이터', '코디법', '코디추천', '코디아이템', '박소현', '황기애', '정혜미', '진정',
    '무드', '느낌', '분위기', '매력', '활용', '완성', '연출', '선택', '조합', '포인트', '다양', '모습', '자신', '사람', '마음',
    '제품', '디자인', '에디터', '정윤', '보그', '년대', '등장' '시즌', '스타일링', '스타일', '아이템', '패션', '브랜드', '장진영', '윤다희', '강미', '박은아', 
])

# 시각화 설정
VISUALIZATION_CONFIG = {
    'network_graph': {
        'node_size': 600,
        'edge_width': 2,
        'font_size': 10
    },
    'wordcloud': {
        'width': 800,
        'height': 400,
        'max_words': 100
    },
    'category_chart': {
        'figsize': (10, 6),
        'colors': ['#36D6BE', '#6B5AED', '#FF5A5A', '#4A78E1', '#FFA26B']
    },
    'trend_chart': {
        'figsize': (12, 6),
        'marker_size': 8,
        'line_width': 2
    }
}

# 기타 설정
DEFAULT_LIMIT = 1000
MAX_KEYWORDS = 20