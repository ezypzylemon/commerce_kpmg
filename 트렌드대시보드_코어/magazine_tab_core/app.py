from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime, timedelta
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import mysql.connector
from config import MYSQL_CONFIG
from magazine_data_loader import MagazineDataLoader
from visualizer import (
    generate_network_graph,
    generate_category_chart,
    generate_wordcloud,
    generate_tfidf_chart,
    generate_trend_chart
)
from config import DB_CONFIG

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

def load_magazine_articles():
    conn = get_mysql_connection()
    query = """
        SELECT title, upload_date, article_url
        FROM all_trends
        ORDER BY upload_date DESC
        LIMIT 30;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def extract_og_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        og_img = soup.find("meta", property="og:image")
        return og_img["content"] if og_img else None
    except:
        return None

# 데이터 로더 초기화
data_loader = MagazineDataLoader()

@app.route('/')
def dashboard():
    """메인 대시보드"""
    try:
        period = request.args.get('period', '7일')
        data = data_loader.load_data_by_period(period)
        
        if data is None or data.empty:
            logger.warning(f"{period} 기간 동안 데이터가 없습니다.")
            return render_template('dashboard.html', 
                                error="데이터가 없습니다.",
                                magazine_data={},
                                fig_network=None,
                                fig_category=None,
                                fig_wordcloud=None,
                                fig_tfidf=None)
        
        # 시각화 생성
        fig_network = generate_network_graph(data)
        fig_category = generate_category_chart(data)
        fig_wordcloud = generate_wordcloud(data)
        fig_tfidf = generate_tfidf_chart(data)
        
        # 매거진별 데이터 수집
        magazine_data = {}
        for magazine in data['magazine_name'].unique():
            keywords = data_loader.get_magazine_keywords(magazine)
            card_news = data_loader.get_card_news(magazine)
            if keywords:
                magazine_data[magazine] = {
                    'keywords': keywords,
                    'card_news': card_news
                }
        
        return render_template('dashboard.html',
                             period=period,
                             fig_network=fig_network,
                             fig_category=fig_category,
                             fig_wordcloud=fig_wordcloud,
                             fig_tfidf=fig_tfidf,
                             magazine_data=magazine_data)
    
    except Exception as e:
        logger.error(f"대시보드 로딩 중 오류 발생: {e}")
        return render_template('dashboard.html', 
                             error="데이터 로딩 중 오류가 발생했습니다.",
                             magazine_data={},
                             fig_network=None,
                             fig_category=None,
                             fig_wordcloud=None,
                             fig_tfidf=None)

@app.route('/cardnews')
def cardnews():
    """카드뉴스 페이지"""
    try:
        # 매거진 매핑 정의 (URL 이름 -> DB source 값)
        magazine_mapping = {
            'vogue': ['vogue', 'voguekorea', 'VOGUE'],
            'wkorea': ['wkorea', 'w korea', 'w매거진', 'W KOREA'],
            'marieclaire': ['marieclaire', 'marie claire', 'MARIECLAIRE'],
            'jentestore': ['jentestore', 'jente', 'JENTESTORE'],
            'wwdkorea': ['wwdkorea', 'wwd korea', 'WWD KOREA', 'WWD']
        }
        
        # 매거진 표시 이름 매핑
        display_names = {
            'vogue': 'VOGUE',
            'wkorea': 'W KOREA',
            'jentestore': 'JENTESTORE',
            'marieclaire': 'MARIECLAIRE',
            'wwdkorea': 'WWD KOREA'
        }
        
        # 매거진 목록
        magazines = list(magazine_mapping.keys())
        
        # 선택된 매거진
        selected_magazine = request.args.get('magazine', '')
        logger.info(f"선택된 매거진: {selected_magazine}")
        
        # 데이터베이스 연결
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        if selected_magazine and selected_magazine in magazine_mapping:
            # 특정 매거진이 선택된 경우
            source_variants = magazine_mapping[selected_magazine]
            placeholders = ','.join(['%s'] * len(source_variants))
            query = """
                SELECT title, upload_date, article_url, source
                FROM all_trends
                WHERE source IN ({})
                ORDER BY upload_date DESC
                LIMIT 30
            """.format(placeholders)
            cursor.execute(query, source_variants)
            logger.info(f"매거진 필터링: {source_variants}")
        else:
            # 전체 매거진 조회
            all_sources = []
            for variants in magazine_mapping.values():
                all_sources.extend(variants)
            placeholders = ','.join(['%s'] * len(all_sources))
            query = """
                SELECT title, upload_date, article_url, source
                FROM all_trends
                WHERE source IN ({})
                ORDER BY upload_date DESC
                LIMIT 30
            """.format(placeholders)
            cursor.execute(query, all_sources)
            logger.info(f"전체 매거진 조회: {all_sources}")
        
        articles = cursor.fetchall()
        logger.info(f"검색된 기사 수: {len(articles)}")
        
        cursor.close()
        conn.close()
        
        if not articles:
            return render_template('cardnews.html',
                                magazines=magazines,
                                display_names=display_names,
                                selected_magazine=selected_magazine,
                                articles=[],
                                info="해당 매거진의 기사가 없습니다.")
        
        # 각 기사 처리
        processed_articles = []
        for article in articles:
            try:
                # 이미지 URL 추출
                image_url = extract_og_image(article['article_url'])
                article['image_url'] = image_url
                
                # 매거진 이름을 표시용 이름으로 변환
                source = article['source']
                article['source'] = display_names.get(source, source)
                
                # 날짜 포맷팅
                if isinstance(article['upload_date'], datetime):
                    article['upload_date'] = article['upload_date'].strftime('%Y.%m.%d')
                
                processed_articles.append(article)
            except Exception as e:
                logger.error(f"기사 처리 중 오류 발생: {str(e)}")
                continue
        
        return render_template('cardnews.html',
                             articles=processed_articles,
                             magazines=magazines,
                             display_names=display_names,
                             selected_magazine=selected_magazine)
    
    except Exception as e:
        logger.error(f"카드뉴스 페이지 로딩 중 오류 발생: {str(e)}")
        return render_template('cardnews.html', error="데이터 로딩 중 오류가 발생했습니다.")

@app.route('/competitor')
def competitor_analysis():
    """경쟁사 분석 페이지"""
    try:
        period = request.args.get('period', '7일')
        data = data_loader.load_data_by_period(period)
        
        if data is None or data.empty:
            return render_template('competitor_analysis.html', error="데이터가 없습니다.")
        
        popular_brands = data_loader.get_popular_brands(period)
        price_heatmap = data_loader.get_price_heatmap(period)
        
        return render_template('competitor_analysis.html',
                             period=period,
                             popular_brands=popular_brands,
                             price_heatmap=price_heatmap)
    
    except Exception as e:
        logger.error(f"경쟁사 분석 페이지 로딩 중 오류 발생: {e}")
        return render_template('competitor_analysis.html', error="데이터 로딩 중 오류가 발생했습니다.")

@app.route('/magazine')
def magazine():
    """매거진 분석 페이지"""
    try:
        period = request.args.get('period', '7일')
        selected_magazines = request.args.get('magazines', 'jentestore,marieclaire,vogue,wkorea,wwdkorea').split(',')
        
        # 매거진 데이터 로드
        data = data_loader.load_data_by_period(period)
        
        # 매거진별 키워드 데이터 가져오기
        magazine_data = {}
        all_keywords = []
        
        # 카드뉴스 데이터 로드
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 매거진 매핑 정의
        magazine_mapping = {
            'vogue': ['vogue', 'voguekorea', 'VOGUE'],
            'wkorea': ['wkorea', 'w korea', 'w매거진', 'W KOREA'],
            'marieclaire': ['marieclaire', 'marie claire', 'MARIECLAIRE'],
            'jentestore': ['jentestore', 'jente', 'JENTESTORE'],
            'wwdkorea': ['wwdkorea', 'wwd korea', 'WWD KOREA', 'WWD']
        }
        
        # 모든 가능한 source 값을 리스트로 만들기
        source_values = []
        for variants in magazine_mapping.values():
            source_values.extend(variants)
        
        # 최근 기사 30개 가져오기
        query = """
            SELECT title, upload_date, article_url, source
            FROM all_trends
            WHERE LOWER(source) IN ({})
            ORDER BY upload_date DESC
            LIMIT 30;
        """.format(','.join(['%s'] * len(source_values)))
        
        cursor.execute(query, source_values)
        articles = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # source 값 정규화
        for article in articles:
            source = article['source'].lower()
            for magazine_name, variants in magazine_mapping.items():
                if source in variants:
                    article['source'] = magazine_name
                    break
            
            # 이미지 URL 추출 및 날짜 포맷팅
            article['image_url'] = extract_og_image(article['article_url'])
            if isinstance(article['upload_date'], datetime):
                article['upload_date'] = article['upload_date'].strftime('%Y-%m-%d')
        
        # 매거진별 데이터 처리
        for magazine_name in selected_magazines:
            keywords = data_loader.get_magazine_keywords(magazine_name)
            if keywords:
                # 해당 매거진의 카드뉴스 필터링
                magazine_articles = [
                    article for article in articles 
                    if article['source'] == magazine_name
                ][:5]  # 각 매거진당 최대 5개
                
                magazine_data[magazine_name] = {
                    'keywords': keywords,
                    'card_news': magazine_articles
                }
                all_keywords.extend([kw['keyword'] for kw in keywords])
        
        # 공통 키워드 찾기 (빈도수 기준으로 정렬)
        keyword_count = {}
        for keyword in all_keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # 공통 키워드를 빈도수 기준으로 정렬하고 상위 5개 선택
        common_keywords = sorted(
            [(keyword, count) for keyword, count in keyword_count.items() if count >= len(selected_magazines)],
            key=lambda x: x[1],
            reverse=True
        )
        common_keywords = [kw for kw, _ in common_keywords[:5]]
        
        # 시각화 생성
        visualizations = data_loader.generate_visualizations(
            data=data,
            selected_magazines=selected_magazines,
            focus_keywords=common_keywords
        )
        
        if visualizations:
            fig_trend = visualizations.get('trend')
            fig_wordcloud = visualizations.get('wordcloud')
            fig_network = visualizations.get('network')
            fig_category = visualizations.get('category')
        else:
            fig_trend = fig_wordcloud = fig_network = fig_category = None
            logger.warning("시각화 생성 실패")
        
        return render_template('magazine.html', 
                             period=period, 
                             magazine_data=magazine_data,
                             selected_magazines=selected_magazines,
                             common_keywords=common_keywords,
                             fig_trend=fig_trend, 
                             fig_wordcloud=fig_wordcloud,
                             fig_network=fig_network, 
                             fig_category=fig_category,
                             articles=articles)
                            
    except Exception as e:
        logger.error(f"매거진 페이지 로드 중 오류 발생: {e}")
        return render_template('magazine.html', 
                             period=period, 
                             magazine_data={},
                             selected_magazines=selected_magazines,
                             common_keywords=[],
                             fig_trend=None, 
                             fig_wordcloud=None, 
                             fig_network=None, 
                             fig_category=None,
                             articles=[])

@app.route('/news')
def news():
    """뉴스 분석 페이지"""
    try:
        period = request.args.get('period', '7일')
        data = data_loader.load_data_by_period(period)
        
        if data is None or data.empty:
            return render_template('news.html', error="데이터가 없습니다.")
        
        headlines = data_loader.get_news_headlines(period)
        positive_articles = data_loader.get_sentiment_articles(period, 'positive')
        negative_articles = data_loader.get_sentiment_articles(period, 'negative')
        
        return render_template('news.html',
                             period=period,
                             headlines=headlines,
                             positive_articles=positive_articles,
                             negative_articles=negative_articles)
    
    except Exception as e:
        logger.error(f"뉴스 페이지 로딩 중 오류 발생: {e}")
        return render_template('news.html', error="데이터 로딩 중 오류가 발생했습니다.")

@app.route('/trend')
def trend():
    """트렌드 분석 페이지"""
    try:
        keyword = request.args.get('keyword', '')
        period = request.args.get('period', '7일')
        chart_type = request.args.get('chart_type', 'line')
        
        if not keyword:
            return render_template('trend.html')
        
        data = data_loader.load_data_by_period(period)
        if data is None or data.empty:
            return render_template('trend.html', error="데이터가 없습니다.")
        
        trend_chart = data_loader.generate_trend_chart(keyword, chart_type)
        if not trend_chart:
            return render_template('trend.html', error="트렌드 차트 생성에 실패했습니다.")
        
        return render_template('trend.html',
                             keyword=keyword,
                             period=period,
                             chart_type=chart_type,
                             trend_chart=trend_chart)
    
    except Exception as e:
        logger.error(f"트렌드 페이지 로딩 중 오류 발생: {e}")
        return render_template('trend.html', error="데이터 로딩 중 오류가 발생했습니다.")

@app.route('/api/keywords')
def get_keywords():
    """키워드 API"""
    try:
        period = request.args.get('period', '7일')
        data = data_loader.load_data_by_period(period)
        
        if data is None or data.empty:
            return jsonify([])
        
        all_tokens = [token for tokens in data['tokens'] for token in tokens]
        token_counts = pd.Series(all_tokens).value_counts().head(20)
        
        keywords = [{'text': key, 'count': int(value)} 
                   for key, value in token_counts.items()]
        
        return jsonify(keywords)
    
    except Exception as e:
        logger.error(f"키워드 API 오류: {e}")
        return jsonify([])

@app.route('/api/magazine-data')
def get_magazine_data():
    """매거진 데이터 API"""
    try:
        magazine = request.args.get('magazine')
        period = request.args.get('period', '7일')
        
        if not magazine:
            return jsonify({'error': '매거진 이름이 필요합니다.'})
        
        data = data_loader.load_data_by_period(period)
        if data is None or data.empty:
            return jsonify({'error': '데이터가 없습니다.'})
        
        keywords = data_loader.get_magazine_keywords(magazine)
        card_news = data_loader.get_card_news(magazine)
        
        return jsonify({
            'keywords': keywords,
            'card_news': card_news
        })
    
    except Exception as e:
        logger.error(f"매거진 데이터 API 오류: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)