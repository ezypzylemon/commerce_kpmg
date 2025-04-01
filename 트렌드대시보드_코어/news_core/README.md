# News Core

뉴스 분석 기능을 제공하는 Flask 웹 애플리케이션 코어 패키지입니다.

## 개요

이 패키지는 뉴스 데이터를 수집하고 분석하는 기능을 제공합니다:

- 토큰화된 뉴스 데이터 로드
- 키워드 추출 및 빈도 분석
- TF-IDF 워드클라우드 생성
- 키워드 네트워크 분석
- 감성 분석
- 시계열 분석

## 디렉토리 구조

```
news_core/
├── __init__.py          # 패키지 초기화 파일
├── news_loader.py       # 뉴스 데이터 로더 클래스
├── news_routes.py       # Flask 라우트 등록 함수
├── example.py           # 사용 예제
├── README.md            # 이 문서
├── modules/             # 분석 모듈
│   ├── time_series.py        # 시계열 분석
│   ├── topic_modeling.py     # 토픽 모델링
│   ├── sentiment_analysis.py # 감성 분석
│   ├── tfidf_analysis.py     # TF-IDF 분석
│   ├── word_association.py   # 연관어 분석
│   └── word_frequency.py     # 단어 빈도 분석
├── static/              # 정적 파일 (CSS, JS, 이미지)
└── templates/           # HTML 템플릿
    ├── base.html        # 기본 템플릿
    └── news.html        # 뉴스 분석 페이지 템플릿
```

## 설치 및 사용법

### 1. 의존성 설치

```bash
pip install flask mysql-connector-python pandas numpy matplotlib scikit-learn wordcloud plotly networkx
```

### 2. MySQL 데이터베이스 설정

이 패키지는 MySQL 데이터베이스를 사용합니다. 다음과 같은 테이블 구조가 필요합니다:

- `dump_migration.knews_articles`: 뉴스 기사 정보 (id, title, content, link, published)
- `dump_migration.tokenised`: 토큰화된 데이터 (id, tokens, upload_date)

### 3. 사용 예시

```python
from flask import Flask
import mysql.connector
from news_core import NewsDataLoader, register_news_routes

# Flask 앱 초기화
app = Flask(__name__, 
           template_folder='news_core/templates',
           static_folder='news_core/static')

# MySQL 설정
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'fashion_trends',
    'port': 3306
}

# MySQL 연결 함수
def get_mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

# 뉴스 데이터 로더 초기화
news_loader = NewsDataLoader(MYSQL_CONFIG)

# 뉴스 라우트 등록
register_news_routes(app, news_loader, get_mysql_connection)

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True)
```

## 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다. 