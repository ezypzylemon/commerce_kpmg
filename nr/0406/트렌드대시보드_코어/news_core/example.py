"""
news_core 패키지 사용 예제

이 스크립트는 news_core 패키지를 사용하여 뉴스 분석 웹 애플리케이션을 실행하는 방법을 보여줍니다.
"""

from flask import Flask, render_template
import mysql.connector
from news_core import NewsDataLoader, register_news_routes

# Flask 앱 초기화
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# MySQL 설정
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 실제 비밀번호로 변경해야 합니다
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

# 메인 페이지 라우트
@app.route('/')
def dashboard():
    """메인 대시보드"""
    return render_template('base.html', period='7일')

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 