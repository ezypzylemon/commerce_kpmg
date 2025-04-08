"""
뉴스 라우트 모듈
Flask 애플리케이션에 뉴스 관련 라우트를 등록합니다.
"""

from flask import render_template, request
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

def register_news_routes(app, news_loader, get_mysql_connection):
    """
    Flask 애플리케이션에 뉴스 관련 라우트를 등록합니다.
    
    Args:
        app: Flask 애플리케이션 인스턴스
        news_loader: NewsDataLoader 인스턴스
        get_mysql_connection: MySQL 연결 함수
    """
    
    @app.route('/news')
    def news():
        """뉴스 분석 페이지"""
        try:
            period = request.args.get('period', '7일')
            
            # 데이터로더에 기간 설정
            news_loader.set_period(period)
            
            # 뉴스 데이터 로드
            df = news_loader.load_news_data()
            
            if df is None or df.empty:
                return render_template('news.html', error="선택한 기간에 대한 데이터가 없습니다.")
            
            # 최신 뉴스 기사 (상위 5개)
            latest_articles = news_loader.get_latest_articles(df)
            
            # 키워드 TOP 5
            top_keywords = news_loader.get_top_keywords(df)
            
            # 키워드별 언급량 추세, 워드클라우드, 네트워크 그래프 생성
            keyword_trend = news_loader.analyze_time_trend()
            tfidf_wordcloud = news_loader.generate_tfidf_wordcloud()
            keyword_network = news_loader.generate_network_graph()
            
            # 감성 분석 결과
            sentiment_results = news_loader.analyze_sentiment(df)
            
            return render_template('news.html',
                                 period=period,
                                 latest_articles=latest_articles,
                                 top_keywords=top_keywords,
                                 keyword_trend=keyword_trend,
                                 tfidf_wordcloud=tfidf_wordcloud,
                                 keyword_network=keyword_network,
                                 positive_articles=sentiment_results.get('positive_articles', [])[:3],
                                 negative_articles=sentiment_results.get('negative_articles', [])[:3])
        
        except Exception as e:
            logger.error(f"Error in news route: {e}")
            return render_template('news.html', error="데이터 처리 중 오류가 발생했습니다.") 