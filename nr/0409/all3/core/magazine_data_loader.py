# magazine_data_loader.py
from sqlalchemy import create_engine
import pandas as pd
import logging
from datetime import datetime, timedelta
from .db_connector import DBConnector
from .analyzer import Analyzer
from .visualizer import (
    generate_network_graph,
    generate_category_chart,
    generate_wordcloud,
    generate_tfidf_chart,
    generate_trend_chart
)
import mysql.connector
from .config import MYSQL_CONFIG, PERIOD_DAYS
from itertools import combinations
from collections import defaultdict
import json
from collections import Counter
import os
import io
import base64
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from wordcloud import WordCloud
import requests
from bs4 import BeautifulSoup

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 카테고리별 키워드 정의
CATEGORY_KEYWORDS = {
    '의류': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
    '신발': ['구두', '샌들', '부츠', '스니커즈', '로퍼', '플립플롭', '슬리퍼', '펌프스'],
    '액세서리': ['목걸이', '귀걸이', '반지', '브레이슬릿', '시계', '선글라스', '스카프', '벨트', '가방'],
    '가방': ['백팩', '토트백', '크로스백', '클러치', '숄더백', '에코백'],
    '기타': ['화장품', '향수', '주얼리', '선글라스', '시계']
}

# 매거진 이름 매핑
MAGAZINE_MAPPING = {
    'JENTESTORE': ['jentestore'],
    'MARIECLAIRE': ['marieclaire'],
    'VOGUE': ['vogue'],
    'W KOREA': ['wkorea', 'w'],
    'WWD KOREA': ['wwdkorea']
}

class MagazineDataLoader:
    """매거진 데이터 로드 및 처리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.data = None
        self.period = '7일'
        self.db_connection = None
        self.cursor = None
        self.mysql_config = MYSQL_CONFIG
        self.engine = create_engine(
            f"mysql+pymysql://{self.mysql_config['user']}:{self.mysql_config['password']}@{self.mysql_config['host']}/{self.mysql_config['database']}"
        )
        self.connect_db()
        self.visualizations = {}
    
    def connect_db(self):
        """데이터베이스 연결"""
        try:
            self.db_connection = mysql.connector.connect(**self.mysql_config)
            self.cursor = self.db_connection.cursor(dictionary=True)
            logging.info("데이터베이스 연결 성공")
        except Exception as e:
            logging.error(f"데이터베이스 연결 실패: {e}")
            self.db_connection = None
            self.cursor = None
    
    def load_data_by_period(self, period='7일'):
        """기간별 데이터 로드"""
        try:
            if not self.cursor:
                self.connect_db()
                if not self.cursor:
                    raise Exception("데이터베이스 연결이 없습니다.")

            self.period = period
            days = PERIOD_DAYS.get(period, 7)
            
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT 
                    doc_id,
                    doc_domain,
                    source,
                    upload_date,
                    title,
                    content,
                    tokens
                FROM magazine_tokenised
                WHERE upload_date >= %s
                ORDER BY upload_date DESC
            """
            
            self.cursor.execute(query, (start_date,))
            rows = self.cursor.fetchall()
            
            if not rows:
                logging.warning(f"{period} 기간 동안 데이터가 없습니다.")
                self.data = pd.DataFrame(columns=['doc_id', 'doc_domain', 'source', 'upload_date', 'title', 'content', 'tokens'])
                return self.data
            
            # DataFrame 생성
            self.data = pd.DataFrame(rows)
            
            # tokens 컬럼의 JSON 문자열을 리스트로 변환
            self.data['tokens'] = self.data['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            # source 컬럼을 소문자로 변환
            self.data['source'] = self.data['source'].str.lower()
            
            # magazine_name 컬럼 추가 및 정규화
            self.data['magazine_name'] = self.data['source'].apply(self._get_normalized_magazine_name)
            
            # 매거진 이름 매핑 확인을 위한 로깅
            unique_sources = self.data['source'].unique()
            unique_magazines = self.data['magazine_name'].unique()
            logging.info(f"원본 소스: {unique_sources}")
            logging.info(f"매핑된 매거진: {unique_magazines}")
            
            logging.info(f"데이터 로드 완료: {len(self.data)}개 문서")
            return self.data
            
        except Exception as e:
            logging.error(f"데이터 로드 중 오류 발생: {e}")
            self.data = pd.DataFrame(columns=['doc_id', 'doc_domain', 'source', 'upload_date', 'title', 'content', 'tokens'])
            return self.data
    
    def load_data_by_date_range(self, start_date, end_date):
        """직접 설정한 날짜 범위의 데이터 로드"""
        try:
            if not self.cursor:
                self.connect_db()
                if not self.cursor:
                    raise Exception("데이터베이스 연결이 없습니다.")

            query = """
                SELECT 
                    doc_id,
                    doc_domain,
                    source,
                    upload_date,
                    title,
                    content,
                    tokens
                FROM fashion_trends.magazine_tokenised
                WHERE DATE(upload_date) BETWEEN DATE(%s) AND DATE(%s)
                ORDER BY upload_date DESC
            """
            
            self.cursor.execute(query, (start_date, end_date))
            rows = self.cursor.fetchall()
            
            if not rows:
                logging.warning(f"{start_date}부터 {end_date}까지의 데이터가 없습니다.")
                self.data = pd.DataFrame(columns=['doc_id', 'doc_domain', 'source', 'upload_date', 'title', 'content', 'tokens'])
                return self.data
            
            # DataFrame 생성
            self.data = pd.DataFrame(rows)
            
            # tokens 컬럼의 JSON 문자열을 리스트로 변환
            self.data['tokens'] = self.data['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            # source 컬럼을 소문자로 변환
            self.data['source'] = self.data['source'].str.lower()
            
            # magazine_name 컬럼 추가 및 정규화
            self.data['magazine_name'] = self.data['source'].apply(self._get_normalized_magazine_name)
            
            # upload_date를 datetime으로 변환
            self.data['upload_date'] = pd.to_datetime(self.data['upload_date'])
            
            logging.info(f"매거진 데이터 로드 완료: {len(self.data)}개 문서")
            return self.data
            
        except Exception as e:
            logging.error(f"매거진 데이터 로드 중 오류 발생: {e}")
            self.data = pd.DataFrame(columns=['doc_id', 'doc_domain', 'source', 'upload_date', 'title', 'content', 'tokens'])
            return self.data
    
    def __del__(self):
        """소멸자: 데이터베이스 연결 종료"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.db_connection:
                self.db_connection.close()
        except Exception as e:
            logging.error(f"데이터베이스 연결 종료 중 오류 발생: {e}")
    
    def filter_by_magazine(self, df, magazine_name):
        """매거진별 데이터 필터링"""
        try:
            # source 컬럼을 기준으로 필터링
            filtered_df = df[df['source'].str.lower() == magazine_name.lower()]
            
            if len(filtered_df) == 0:
                logging.warning(f"매거진 '{magazine_name}'에 대한 데이터가 없습니다")
                return None
                
            return filtered_df
            
        except Exception as e:
            logging.error(f"매거진 필터링 중 오류 발생: {e}")
            return None
    
    def get_category_keywords(self, category):
        """카테고리별 키워드 통계"""
        if self.data is None or self.data.empty:
            return None
        
        category_data = self.data[self.data['category'] == category]
        if category_data.empty:
            return None
        
        all_tokens = [token for tokens in category_data['tokens'] for token in tokens]
        return pd.Series(all_tokens).value_counts().head(10)
    
    def get_card_news(self, magazine_name=None):
        """카드뉴스 아이템 추출"""
        try:
            if not self.cursor:
                self.connect_db()
                if not self.cursor:
                    raise Exception("데이터베이스 연결이 없습니다.")
            
            # 매거진 필터링 조건 설정
            filter_condition = ""
            params = []
            
            if magazine_name:
                # 매거진 이름 소문자 변환
                magazine_name_lower = magazine_name.lower()
                
                # 매거진 이름이 정확히 일치하는 경우만 필터링
                filter_condition = "AND LOWER(source) = %s"
                params = [magazine_name_lower]
            
            # 카드뉴스 데이터 쿼리
            query = f"""
                SELECT title, upload_date, article_url, source
                FROM fashion_trends.all_trends
                WHERE 1=1 {filter_condition}
                ORDER BY upload_date DESC
                LIMIT 12;
            """
            
            self.cursor.execute(query, params)
            articles = self.cursor.fetchall()
            
            # 결과가 없는 경우
            if not articles:
                logger.warning(f"카드뉴스 데이터 없음: {magazine_name}")
                return []
            
            # 각 기사 처리
            processed_articles = []
            for article in articles:
                try:
                    # 이미지 URL 추출
                    image_url = self.extract_og_image(article['article_url'])
                    article['image_url'] = image_url or '/static/images/default.jpg'
                    
                    # 날짜 포맷팅
                    if isinstance(article['upload_date'], datetime):
                        article['upload_date'] = article['upload_date'].strftime('%Y-%m-%d')
                    
                    processed_articles.append(article)
                except Exception as e:
                    logger.error(f"기사 처리 중 오류 발생: {str(e)}")
                    continue
            
            return processed_articles
        
        except Exception as e:
            logger.error(f"카드뉴스 로드 중 오류 발생: {str(e)}")
            return []

    def extract_og_image(self, url):
        """기사 URL에서 OG 이미지 추출"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            og_img = soup.find("meta", property="og:image")
            return og_img["content"] if og_img else None
        except Exception as e:
            logger.error(f"OG 이미지 추출 중 오류: {str(e)}")
            return None
    
    def get_magazine_keywords(self, magazine_name):
        """매거진별 키워드 통계"""
        # 임시 데이터 반환
        temp_data = {
            'jentestore': [
                {'keyword': '데님', 'percent': 15.2},
                {'keyword': '드레스', 'percent': 12.8},
                {'keyword': '동장', 'percent': 10.5},
                {'keyword': '디테일', 'percent': 8.7},
                {'keyword': '러닝', 'percent': 7.9},
                {'keyword': '로고', 'percent': 6.5},
                {'keyword': '펄라', 'percent': 5.8},
                {'keyword': '부츠', 'percent': 5.2},
                {'keyword': '블랙', 'percent': 4.8},
                {'keyword': '빈티지', 'percent': 4.2}
            ],
            'marieclaire': [
                {'keyword': '가죽', 'percent': 14.5},
                {'keyword': '글로벌', 'percent': 12.1},
                {'keyword': '니트', 'percent': 9.8},
                {'keyword': '데님', 'percent': 8.5},
                {'keyword': '디테일', 'percent': 7.2},
                {'keyword': '디지털', 'percent': 6.8},
                {'keyword': '럭비', 'percent': 5.9},
                {'keyword': '블랙', 'percent': 5.4},
                {'keyword': '사랑', 'percent': 4.9},
                {'keyword': '생각', 'percent': 4.2}
            ],
            'vogue': [
                {'keyword': '가방', 'percent': 14.5},
                {'keyword': '겨울', 'percent': 12.1},
                {'keyword': '제킷', 'percent': 9.8},
                {'keyword': '데님', 'percent': 8.5},
                {'keyword': '디테일', 'percent': 7.2},
                {'keyword': '럼메이', 'percent': 6.8},
                {'keyword': '블랙', 'percent': 5.9},
                {'keyword': '버퍼다', 'percent': 5.4},
                {'keyword': '버터', 'percent': 4.9},
                {'keyword': '부츠', 'percent': 4.2}
            ],
            'wkorea': [
                {'keyword': '골드', 'percent': 14.5},
                {'keyword': '니트', 'percent': 12.1},
                {'keyword': '다이아몬드', 'percent': 9.8},
                {'keyword': '데님', 'percent': 8.5},
                {'keyword': '드레스', 'percent': 7.2},
                {'keyword': '디테일', 'percent': 6.8},
                {'keyword': '블랙', 'percent': 5.9},
                {'keyword': '명수', 'percent': 5.4},
                {'keyword': '미니', 'percent': 4.9},
                {'keyword': '부츠', 'percent': 4.2}
            ],
            'wwdkorea': [
                {'keyword': '가방', 'percent': 14.5},
                {'keyword': '감각', 'percent': 12.1},
                {'keyword': '감성', 'percent': 9.8},
                {'keyword': '데님', 'percent': 8.5},
                {'keyword': '디테일', 'percent': 7.2},
                {'keyword': '블랙', 'percent': 6.8},
                {'keyword': '글로벌', 'percent': 5.9},
                {'keyword': '드레스', 'percent': 5.4},
                {'keyword': '부츠', 'percent': 4.9},
                {'keyword': '디테일', 'percent': 4.2}
            ]
        }
        
        if magazine_name in temp_data:
            keywords = temp_data[magazine_name]
            
            # 공통 키워드 찾기
            all_keywords = {mag: set(k['keyword'] for k in kws) for mag, kws in temp_data.items()}
            common_keywords = set.intersection(*all_keywords.values())
            
            # 키워드에 공통 키워드 여부 표시 추가
            for kw in keywords:
                kw['is_common'] = kw['keyword'] in common_keywords
            
            return keywords
        
        return [{'keyword': '데이터 없음', 'percent': 0, 'is_common': False}] * 10
    
    def get_top_items_by_gender(self, gender):
        """성별별 TOP 아이템"""
        if self.data is None or self.data.empty:
            return None
        
        gender_data = self.data[self.data['gender'] == gender]
        if gender_data.empty:
            return None
        
        all_tokens = [token for tokens in gender_data['tokens'] for token in tokens]
        return pd.Series(all_tokens).value_counts().head(10)
    
    def generate_visualizations(self, data, selected_magazines, focus_keywords=None):
        """시각화 생성"""
        try:
            logger.info("시각화 생성 시작")
            visualizations = {}
            
            # focus_keywords가 None이면 빈 리스트로 초기화
            if focus_keywords is None:
                focus_keywords = []
                logger.info("focus_keywords가 None으로 전달되어 빈 리스트로 초기화")
            
            # 키워드가 없고 데이터가 있는 경우 키워드 자동 추출
            if not focus_keywords and data is not None and not data.empty:
                # 상위 토큰 5개를 키워드로 사용
                all_tokens = []
                for doc in data['tokens']:
                    if isinstance(doc, list):
                        all_tokens.extend(doc)
                token_counts = pd.Series(all_tokens).value_counts()
                focus_keywords = token_counts.head(5).index.tolist()
                logger.info(f"자동 추출된 키워드: {focus_keywords}")

            # 트렌드 차트 데이터 준비
            trend_data_list = []
            
            # 데이터가 있는지 확인
            if data is not None and not data.empty and focus_keywords:
                logger.info(f"선택된 매거진: {selected_magazines}")
                logger.info(f"분석할 키워드: {focus_keywords}")
                
                # 매거진 이름 정규화
                normalized_magazines = [self._get_normalized_magazine_name(mag) for mag in selected_magazines]
                logger.info(f"정규화된 매거진 이름: {normalized_magazines}")
                
                # 데이터의 고유한 매거진 이름 확인
                unique_magazines = data['magazine_name'].unique()
                logger.info(f"데이터에 있는 매거진 이름: {unique_magazines}")
                
                for magazine in normalized_magazines:
                    mag_data = data[data['magazine_name'] == magazine]
                    logger.info(f"매거진 '{magazine}' 데이터 수: {len(mag_data)}")
                    
                    if not mag_data.empty:
                        for keyword in focus_keywords:
                            # 각 문서의 토큰에서 키워드 검색
                            for _, row in mag_data.iterrows():
                                tokens = row['tokens']
                                if isinstance(tokens, list):  # tokens가 리스트인지 확인
                                    # 대소문자 구분 없이 키워드 매칭
                                    count = sum(1 for token in tokens if token.lower() == keyword.lower())
                                    if count > 0:
                                        trend_data_list.append({
                                            'upload_date': row['upload_date'],
                                            'count': count,
                                            'magazine_name': magazine,
                                            'keyword': keyword
                                        })
                                        logger.debug(f"키워드 '{keyword}' 발견: {count}회 ({magazine}, {row['upload_date']})")
            
            # 데이터프레임으로 변환
            if trend_data_list:
                logger.info(f"트렌드 데이터 생성됨: {len(trend_data_list)}개 항목")
                trend_df = pd.DataFrame(trend_data_list)
                try:
                    visualizations['trend'] = generate_trend_chart(trend_df, normalized_magazines, focus_keywords)
                    logger.info("트렌드 차트 생성 완료")
                except Exception as e:
                    logger.error(f"트렌드 차트 생성 오류: {e}")
                    visualizations['trend'] = None
            else:
                logger.warning("트렌드 데이터가 없습니다.")
                visualizations['trend'] = None

            # 네트워크 그래프 데이터 준비
            try:
                # 상위 10개 키워드 추출
                all_tokens = []
                for doc in data['tokens']:
                    if isinstance(doc, list):
                        all_tokens.extend(doc)
                top_tokens = pd.Series(all_tokens).value_counts().head(10).index.tolist()
                
                # 엣지 생성
                edges = []
                weights = []
                for doc_tokens in data['tokens']:
                    if not isinstance(doc_tokens, list):
                        continue
                    doc_top_tokens = [t for t in doc_tokens if t in top_tokens]
                    for t1, t2 in combinations(set(doc_top_tokens), 2):
                        edges.append((t1, t2))
                        weights.append(1)
                
                network_data = {
                    'nodes': top_tokens,
                    'edges': edges,
                    'weights': weights
                }
                
                visualizations['network'] = generate_network_graph(network_data)
                logger.info("네트워크 그래프 생성 완료")
            except Exception as e:
                logger.error(f"네트워크 그래프 생성 오류: {e}")
                visualizations['network'] = None

            # 카테고리 차트 데이터 준비
            try:
                category_counts = defaultdict(int)
                for tokens in data['tokens']:
                    if not isinstance(tokens, list):
                        continue
                    for token in tokens:
                        for category, keywords in CATEGORY_KEYWORDS.items():
                            if token in keywords:
                                category_counts[category] += 1
                
                category_data = {
                    'categories': list(category_counts.keys()),
                    'values': list(category_counts.values())
                }
                
                visualizations['category'] = generate_category_chart(category_data)
                logger.info("카테고리 차트 생성 완료")
            except Exception as e:
                logger.error(f"카테고리 차트 생성 오류: {e}")
                visualizations['category'] = None

            # 워드클라우드 데이터 준비
            try:
                all_tokens = []
                for doc in data['tokens']:
                    if isinstance(doc, list):
                        all_tokens.extend(doc)
                word_freq = Counter(all_tokens)
                
                visualizations['wordcloud'] = generate_wordcloud(word_freq)
                logger.info("워드클라우드 생성 완료")
            except Exception as e:
                logger.error(f"워드클라우드 생성 오류: {e}")
                visualizations['wordcloud'] = None

            # 생성된 시각화 키 로깅
            logger.info(f"생성된 시각화: {list(visualizations.keys())}")
            for key, value in visualizations.items():
                if value is None:
                    logger.warning(f"시각화 '{key}'가 None입니다.")

            logger.info("모든 시각화 생성 완료")
            return visualizations

        except Exception as e:
            logger.error(f"시각화 생성 중 오류 발생: {e}")
            return None
    
    def generate_trend_chart(self, keyword, chart_type='line'):
        """키워드 트렌드 차트 생성"""
        if self.data is None or self.data.empty:
            return None
        
        try:
            return generate_trend_chart(self.data, keyword, self.period, chart_type)
        except Exception as e:
            logger.error(f"트렌드 차트 생성 오류: {e}")
            return None

    @staticmethod
    def get_category_keywords(period):
        """카테고리별 키워드 통계"""
        try:
            df = MagazineDataLoader.load_data_by_period(period)
            all_tokens = [token for tokens in df['tokens'] for token in tokens]
            token_counts = pd.Series(all_tokens).value_counts()
            
            # 카테고리별 집계
            categories = {
                '의류': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
                '신발': ['구두', '샌들', '부츠', '스니커즈', '로퍼', '플립플롭', '슬리퍼', '펌프스'],
                '액세서리': ['목걸이', '귀걸이', '반지', '브레이슬릿', '시계', '선글라스', '스카프', '벨트', '가방'],
                '가방': ['백팩', '토트백', '크로스백', '클러치', '숄더백', '에코백'],
                '기타': ['화장품', '향수', '주얼리', '선글라스', '시계']
            }
            
            results = []
            total_count = token_counts.sum()
            
            for category, keywords in categories.items():
                count = sum(token_counts.get(kw, 0) for kw in keywords)
                percent = (count / total_count * 100) if total_count > 0 else 0
                results.append({
                    'name': category,
                    'percent': round(percent, 2)
                })
            
            return results
        except Exception as e:
            logger.error(f"카테고리 키워드 통계 오류: {e}")
            return [{'name': '데이터 없음', 'percent': 0}]

    @staticmethod
    def get_top_items(gender, period):
        """성별별 상위 아이템"""
        try:
            df = MagazineDataLoader.load_data_by_period(period)
            all_tokens = [token for tokens in df['tokens'] for token in tokens]
            token_counts = pd.Series(all_tokens).value_counts()
            
            # 성별별 키워드 필터링
            gender_keywords = {
                '여성': ['드레스', '스커트', '블라우스', '니트웨어', '팬츠'],
                '남성': ['재킷', '셔츠', '청바지', '수트', '티셔츠']
            }
            
            results = []
            for item in gender_keywords.get(gender, []):
                count = token_counts.get(item, 0)
                results.append({'name': item, 'count': count})
            
            return sorted(results, key=lambda x: x['count'], reverse=True)[:5]
        except Exception as e:
            logger.error(f"상위 아이템 로드 오류: {e}")
            return [{'name': '데이터 없음', 'count': 0}] * 5

    @staticmethod
    def get_news_headlines(period):
        return [
            {
                'title': '2025년 패션 트렌드 예측',
                'summary': '패션 전문가들이 전망하는 내년 패션계 움직임',
                'date': '2025-01-10',
                'link': '#'
            },
            {
                'title': '지속가능한 패션의 부상',
                'summary': '친환경 소재와 윤리적 생산이 주목받는 이유',
                'date': '2025-01-05',
                'link': '#'
            }
        ]
    
    # @staticmethod
    # def get_sentiment_articles(period, sentiment):
    #     articles = []
    #     for i in range(3):
    #         articles.append({
    #             'date': '2025-01-15',
    #             'source': 'Fashion Times',
    #             'content': f'{"긍정적" if sentiment == "positive" else "부정적"} 내용의 기사 {i+1}입니다.',
    #             'keywords': ['트렌드', '컬렉션', '소재'] if sentiment == 'positive' else ['위기', '불확실성', '가격상승']
    #         })
    #     return articles
    
    # @staticmethod
    # def get_magazine_cards(period):
    #     return [
    #         {
    #             'title': 'Vogue 최신호 하이라이트',
    #             'date': '2025-01-20',
    #             'magazine': 'vogue',
    #             'image_url': '/static/images/card1.jpg'
    #         },
    #         {
    #             'title': 'W 매거진 특집기사',
    #             'date': '2025-01-15',
    #             'magazine': 'w',
    #             'image_url': '/static/images/card1.jpg'
    #         },
    #         {
    #             'title': 'Harper\'s BAZAAR 컬렉션 리뷰',
    #             'date': '2025-01-10',
    #             'magazine': 'harpers',
    #             'image_url': '/static/images/card1.jpg'
    #         }
    #     ]
    
    @staticmethod
    def get_category_timeseries_chart(gender, period):
        from flask import url_for
        return url_for('static', filename='images/error.png')
    
    @staticmethod
    def get_popular_brands(period):
        brands = ['Nike', 'Adidas', 'Gucci', 'Prada', 'H&M', 'Zara', 'Uniqlo', 'Balenciaga', 'Louis Vuitton', 'Dior',
                 'Chanel', 'Hermès', 'Burberry', 'Saint Laurent', 'Off-White', 'Supreme', 'Fendi', 'Versace', 'Calvin Klein', 'Ralph Lauren']
        return [{'id': i, 'name': brand, 'count': 200 - i*8, 
                'category': '스포츠' if i < 2 else '럭셔리' if i < 10 else '캐주얼', 
                'price_range': '고가' if i < 10 else '중가' if i < 15 else '저가', 
                'gender': '남녀공용'} for i, brand in enumerate(brands)]
    
    @staticmethod
    def get_price_heatmap(period):
        from flask import url_for
        return url_for('static', filename='images/error.png')

    def _get_normalized_magazine_name(self, magazine_name):
        """매거진 이름 정규화"""
        magazine_name = magazine_name.lower()
        for display_name, variants in MAGAZINE_MAPPING.items():
            if magazine_name in variants:
                return display_name
        return magazine_name.upper()

    def analyze_time_trend(self, data):
        """시간별 트렌드 분석"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 토큰 데이터 조회 (테이블명 수정)
            if data is None:
                # 데이터가 제공되지 않으면 DB에서 직접 가져옴
                # 기간을 일수로 변환
                days = 0
                if self.period.endswith('일'):
                    days = int(self.period.replace('일', ''))
                elif self.period == '1주일':
                    days = 7
                elif self.period == '2주':
                    days = 14
                elif self.period == '3주':
                    days = 21
                elif self.period == '1달' or self.period == '1개월':
                    days = 30
                elif self.period == '3달' or self.period == '3개월':
                    days = 90
                elif self.period == '6개월':
                    days = 180
                elif self.period == '1년':
                    days = 365
                else:
                    days = 7  # 기본값
                
                query = """
                    SELECT tokens, upload_date
                    FROM fashion_trends.magazine_tokenised
                    WHERE upload_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    ORDER BY upload_date ASC
                """
                cursor.execute(query, (days,))
                rows = cursor.fetchall()
                
                if not rows:
                    logger.warning("트렌드 분석을 위한 데이터가 없습니다.")
                    return None
                
                # 데이터프레임 생성
                df = pd.DataFrame(rows)
                df['upload_date'] = pd.to_datetime(df['upload_date'])
            else:
                # 데이터가 제공된 경우
                df = data.copy()
                df['upload_date'] = pd.to_datetime(df['upload_date'])
            
            # 토큰 처리 및 상위 키워드 추출
            all_tokens = []
            for row in df['tokens']:
                if row:
                    # 토큰 데이터가 문자열인 경우 JSON으로 변환 시도
                    if isinstance(row, str):
                        try:
                            tokens = json.loads(row)
                        except json.JSONDecodeError:
                            tokens = []
                    else:
                        tokens = row
                    
                    if isinstance(tokens, list):
                        all_tokens.extend(tokens)
            
            word_counts = Counter(all_tokens)
            top_keywords = [word for word, _ in word_counts.most_common(5)]
            
            # 월별 키워드 빈도 계산
            df['year_month'] = df['upload_date'].dt.strftime('%Y-%m')
            monthly_trends = {}
            
            for keyword in top_keywords:
                trend = []
                for month in sorted(df['year_month'].unique()):
                    month_data = df[df['year_month'] == month]
                    count = sum(1 for tokens in month_data['tokens'] if tokens and keyword in json.loads(tokens))
                    trend.append((month, count))
                monthly_trends[keyword] = trend
            
            # Plotly 그래프 생성
            fig = go.Figure()
            
            for keyword, trend in monthly_trends.items():
                months, counts = zip(*trend)
                fig.add_trace(go.Scatter(
                    x=months,
                    y=counts,
                    name=keyword,
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title='키워드별 월간 트렌드',
                xaxis_title='년-월',
                yaxis_title='언급 횟수',
                height=400,
                showlegend=True
            )
            
            return fig.to_html(full_html=False)
            
        except Exception as e:
            logger.error(f"시간별 트렌드 분석 중 오류 발생: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def generate_network_graph(self, data):
        """키워드 네트워크 그래프 생성"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 데이터 로드
            if data is None:
                # 데이터가 제공되지 않으면 DB에서 직접 가져옴
                # 기간을 일수로 변환
                days = 0
                if self.period.endswith('일'):
                    days = int(self.period.replace('일', ''))
                elif self.period == '1주일':
                    days = 7
                elif self.period == '2주':
                    days = 14
                elif self.period == '3주':
                    days = 21
                elif self.period == '1달' or self.period == '1개월':
                    days = 30
                elif self.period == '3달' or self.period == '3개월':
                    days = 90
                elif self.period == '6개월':
                    days = 180
                elif self.period == '1년':
                    days = 365
                else:
                    days = 7  # 기본값
                
                # 토큰 데이터 조회
                query = """
                    SELECT tokens
                    FROM fashion_trends.magazine_tokenised
                    WHERE upload_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                """
                cursor.execute(query, (days,))
                rows = cursor.fetchall()
            else:
                # 제공된 데이터 사용
                rows = [{'tokens': tokens} for tokens in data['tokens']]
            
            # 토큰 데이터 처리
            all_tokens = []
            for row in rows:
                if row['tokens']:
                    tokens = json.loads(row['tokens'])
                    if isinstance(tokens, list):
                        all_tokens.extend(tokens)
            
            if not all_tokens:
                logger.warning("네트워크 그래프 생성을 위한 토큰이 없습니다.")
                return None
            
            # 단어 빈도수 계산 및 상위 50개 선택
            word_freq = Counter(all_tokens)
            top_words = [word for word, _ in word_freq.most_common(50)]
            
            # 동시 출현 횟수 계산
            cooccurrence = {}
            for row in rows:
                if row['tokens']:
                    tokens = json.loads(row['tokens'])
                    if not isinstance(tokens, list):
                        continue
                    # 상위 단어만 고려
                    tokens = [t for t in tokens if t in top_words]
                    for i, word1 in enumerate(tokens):
                        for word2 in tokens[i+1:]:
                            if word1 != word2:
                                pair = tuple(sorted([word1, word2]))
                                cooccurrence[pair] = cooccurrence.get(pair, 0) + 1
            
            # 네트워크 그래프 생성
            G = nx.Graph()
            
            # 노드 추가
            for word in top_words:
                G.add_node(word, size=word_freq[word])
            
            # 엣지 추가 (가중치가 2 이상인 경우만)
            for (word1, word2), weight in cooccurrence.items():
                if weight >= 2:
                    G.add_edge(word1, word2, weight=weight)
            
            # 노드 위치 계산
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Plotly 그래프 생성
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.8, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            node_x = []
            node_y = []
            node_text = []
            node_size = []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node)
                node_size.append(G.nodes[node]['size'] * 2)
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="top center",
                marker=dict(
                    showscale=True,
                    colorscale='YlOrRd',
                    size=node_size,
                    color=node_size,
                    line=dict(width=2)
                )
            )
            
            # 레이아웃 설정
            layout = go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=400
            )
            
            # 그래프 생성
            fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
            
            return fig.to_html(full_html=False)
            
        except Exception as e:
            logger.error(f"네트워크 그래프 생성 중 오류 발생: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def generate_tfidf_wordcloud(self, data):
        """TF-IDF 기반 워드클라우드 생성"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 데이터 로드
            if data is None:
                # 데이터가 제공되지 않으면 DB에서 직접 가져옴
                # 기간을 일수로 변환
                days = 0
                if self.period.endswith('일'):
                    days = int(self.period.replace('일', ''))
                elif self.period == '1주일':
                    days = 7
                elif self.period == '2주':
                    days = 14
                elif self.period == '3주':
                    days = 21
                elif self.period == '1달' or self.period == '1개월':
                    days = 30
                elif self.period == '3달' or self.period == '3개월':
                    days = 90
                elif self.period == '6개월':
                    days = 180
                elif self.period == '1년':
                    days = 365
                else:
                    days = 7  # 기본값
                
                # 토큰 데이터 조회
                query = """
                    SELECT tokens
                    FROM fashion_trends.magazine_tokenised
                    WHERE upload_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                """
                cursor.execute(query, (days,))
                rows = cursor.fetchall()
            else:
                # 제공된 데이터 사용
                rows = [{'tokens': tokens} for tokens in data['tokens']]
            
            # 문서-토큰 데이터 준비
            documents = []
            for row in rows:
                if row['tokens']:
                    try:
                        tokens = json.loads(row['tokens'])
                        if isinstance(tokens, list):
                            # 토큰 리스트를 공백으로 구분된 문자열로 변환
                            documents.append(' '.join(tokens))
                    except json.JSONDecodeError:
                        continue
            
            if not documents:
                logger.warning("워드클라우드 생성을 위한 문서가 없습니다.")
                return None
            
            # TF-IDF 벡터라이저 초기화 및 적용
            vectorizer = TfidfVectorizer(max_features=100)
            tfidf_matrix = vectorizer.fit_transform(documents)
            
            # 각 단어의 평균 TF-IDF 점수 계산
            feature_names = vectorizer.get_feature_names_out()
            mean_tfidf_scores = np.array(tfidf_matrix.mean(axis=0)).flatten()
            
            # 단어와 TF-IDF 점수를 딕셔너리로 변환
            word_scores = {word: score for word, score in zip(feature_names, mean_tfidf_scores)}
            
            # 한글 폰트 설정
            font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
            if not os.path.exists(font_path):
                font_path = '/System/Library/Fonts/AppleGothic.ttf'
            
            if not os.path.exists(font_path):
                logger.error("한글 폰트를 찾을 수 없습니다.")
                return None
            
            # 워드클라우드 생성
            wordcloud = WordCloud(
                font_path=font_path,
                width=1200,
                height=800,
                background_color='white',
                max_words=100,
                max_font_size=200,
                min_font_size=10,
                prefer_horizontal=0.7,
                colormap='viridis'
            ).generate_from_frequencies(word_scores)
            
            # 이미지 생성
            plt.figure(figsize=(12, 8), facecolor='white')
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            
            # 이미지를 base64로 인코딩
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
            plt.close()
            buffer.seek(0)
            
            # HTML에서 사용할 수 있는 형식으로 반환
            image_data = base64.b64encode(buffer.getvalue()).decode()
            return f'data:image/png;base64,{image_data}'
            
        except Exception as e:
            logger.error(f"워드클라우드 생성 중 오류 발생: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def analyze_sentiment(self, data):
        """감성 분석 수행"""
        try:
            # 감성 사전 로드
            positive_words = set(['좋은', '훌륭한', '우수한', '성공', '혁신', '성장', '발전', '향상', '개선'])
            negative_words = set(['나쁜', '부족한', '실패', '하락', '위기', '문제', '악화', '감소', '위험'])
            
            # 기사별 감성 점수 계산
            sentiment_scores = []
            for idx, row in data.iterrows():
                tokens = row['tokens']
                if not isinstance(tokens, list):
                    continue
                
                pos_count = sum(1 for token in tokens if token in positive_words)
                neg_count = sum(1 for token in tokens if token in negative_words)
                
                score = (pos_count - neg_count) / (len(tokens) + 1)  # 정규화
                sentiment_scores.append({
                    'index': idx,
                    'score': score,
                    'title': row['title'],
                    'upload_date': row['upload_date']
                })
            
            # 점수 기준으로 정렬
            sentiment_scores.sort(key=lambda x: x['score'])
            
            # 긍정/부정 기사 추출
            negative_articles = [
                {'title': article['title'], 'upload_date': article['upload_date']}
                for article in sentiment_scores[:5]  # 가장 부정적인 5개
            ]
            
            positive_articles = [
                {'title': article['title'], 'upload_date': article['upload_date']}
                for article in reversed(sentiment_scores[-5:])  # 가장 긍정적인 5개
            ]
            
            return {
                'positive_articles': positive_articles,
                'negative_articles': negative_articles
            }
            
        except Exception as e:
            logger.error(f"감성 분석 중 오류 발생: {e}")
            return {'positive_articles': [], 'negative_articles': []}

    def get_category_data(self, category_type, period):
        """카테고리별 데이터 (언급량 및 증감률) 가져오기"""
        try:
            logger.info(f"카테고리 데이터 요청: 타입={category_type}, 기간={period}")
            
            # 현재 기간 데이터 로드
            if period.endswith('개월') or period.endswith('달'):
                # 개월 단위 처리
                months = int(period.replace('개월', '').replace('달', ''))
                current_data = self.load_data_by_months(months)
                
                # 이전 기간은 2배로 설정
                prev_data = self.load_data_by_months(months * 2)
                prev_period = f"{months * 2}개월"
            elif period.endswith('주'):
                # 주 단위 처리
                weeks = int(period.replace('주', ''))
                current_data = self.load_data_by_weeks(weeks)
                
                # 이전 기간은 2배로 설정
                prev_data = self.load_data_by_weeks(weeks * 2)
                prev_period = f"{weeks * 2}주"
            elif period.endswith('일'):
                # 일 단위 처리
                days = int(period.replace('일', ''))
                current_data = self.load_data_by_days(days)
                
                # 이전 기간은 2배로 설정
                prev_data = self.load_data_by_days(days * 2)
                prev_period = f"{days * 2}일"
            elif period == '1년':
                # 1년 처리
                current_data = self.load_data_by_months(12)
                prev_data = self.load_data_by_months(24)
                prev_period = "2년"
            elif period == 'custom' and hasattr(self, 'custom_start_date') and hasattr(self, 'custom_end_date'):
                # 직접 설정 기간 처리
                current_data = self.load_data_by_date_range(self.custom_start_date, self.custom_end_date)
                
                # 이전 기간을 계산 (현재 기간과 동일한 길이)
                from datetime import datetime, timedelta
                start_date = datetime.strptime(self.custom_start_date, '%Y-%m-%d')
                end_date = datetime.strptime(self.custom_end_date, '%Y-%m-%d')
                days_diff = (end_date - start_date).days
                
                prev_end_date = start_date - timedelta(days=1)
                prev_start_date = prev_end_date - timedelta(days=days_diff)
                
                prev_data = self.load_data_by_date_range(
                    prev_start_date.strftime('%Y-%m-%d'), 
                    prev_end_date.strftime('%Y-%m-%d')
                )
                prev_period = f"이전 {days_diff}일"
            else:
                # 기본값 (7일)
                logger.warning(f"지원하지 않는 기간 형식: {period}, 기본값 7일로 설정")
                current_data = self.load_data_by_days(7)
                prev_data = self.load_data_by_days(14)
                prev_period = "14일"
            
            # 로깅 추가
            logger.info(f"카테고리 데이터: 현재 기간({period}) 데이터 수: {len(current_data) if not current_data.empty else 0}")
            logger.info(f"카테고리 데이터: 이전 기간({prev_period}) 데이터 수: {len(prev_data) if not prev_data.empty else 0}")
            
            # 토큰 데이터 확인
            if current_data.empty or 'tokens' not in current_data.columns:
                logger.warning("토큰 데이터가 없거나 토큰 컬럼이 없습니다.")
                return None
            
            # 카테고리 매핑 가져오기
            category_mapping = self._get_category_mapping(category_type)
            
            # 카테고리별 토큰 출현 횟수 계산
            current_counts, prev_counts = self._calculate_category_counts(
                current_data, prev_data, category_mapping
            )
            
            # 결과 형식화 및 반환
            result = self._format_category_result(current_counts, prev_counts)
            logger.info(f"카테고리 데이터 처리 완료: {len(result['categories'])}개 카테고리")
            return result
            
        except Exception as e:
            logger.error(f"카테고리 데이터 처리 중 오류 발생: {e}", exc_info=True)
            return None
            
    def load_data_by_days(self, days):
        """일 단위로 데이터 로드"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT 
                    doc_id,
                    doc_domain,
                    source,
                    upload_date,
                    title,
                    content,
                    tokens
                FROM fashion_trends.magazine_tokenised
                WHERE upload_date >= %s AND upload_date <= %s
                ORDER BY upload_date DESC
            """
            
            self.cursor.execute(query, (start_date, end_date))
            rows = self.cursor.fetchall()
            
            if not rows:
                logger.warning(f"{days}일 기간 동안 데이터가 없습니다.")
                return pd.DataFrame(columns=['doc_id', 'doc_domain', 'source', 'upload_date', 'title', 'content', 'tokens'])
            
            data = pd.DataFrame(rows)
            
            # tokens 컬럼 처리
            if 'tokens' in data.columns:
                data['tokens'] = data['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            # source 컬럼 소문자 변환
            if 'source' in data.columns:
                data['source'] = data['source'].str.lower()
            
            # magazine_name 컬럼 추가
            if 'source' in data.columns:
                data['magazine_name'] = data['source'].apply(self._get_normalized_magazine_name)
            
            return data
        
        except Exception as e:
            logger.error(f"{days}일 기간 데이터 로드 중 오류 발생: {e}", exc_info=True)
            return pd.DataFrame(columns=['doc_id', 'doc_domain', 'source', 'upload_date', 'title', 'content', 'tokens'])

    def load_data_by_weeks(self, weeks):
        """주 단위로 데이터 로드"""
        return self.load_data_by_days(weeks * 7)

    def load_data_by_months(self, months):
        """월 단위로 데이터 로드"""
        return self.load_data_by_days(months * 30)  # 근사값으로 30일 사용
            
    def _get_category_mapping(self, category_type):
        """카테고리 타입에 따른 매핑 반환"""
        category_mappings = {
            'item': {
                '드레스': ['드레스', '원피스'],
                '재킷': ['재킷', '자켓', '코트'],
                '팬츠': ['팬츠', '바지', '슬랙스', '진'],
                '스커트': ['스커트', '스윙스커트'],
                '코트': ['코트', '트렌치코트', '오버코트'],
                '블라우스': ['블라우스', '셔츠'],
                '니트웨어': ['니트', '스웨터', '카디건'],
                '티셔츠': ['티셔츠', '티', '탑'],
                '청바지': ['청바지', '데님', '진'],
                '수영복': ['수영복', '비키니'],
                '점퍼': ['점퍼', '윈드브레이커'],
                '베스트': ['베스트', '질렛'],
                '패딩': ['패딩', '다운재킷'],
                '수트': ['수트', '정장'],
                '후드': ['후드', '후디']
            },
            'color': {
                '블랙': ['블랙', '검정', '검은색'],
                '화이트': ['화이트', '하얀', '하얀색'],
                '그레이': ['그레이', '회색'],
                '레드': ['레드', '빨간', '빨간색'],
                '블루': ['블루', '파란', '파란색'],
                '그린': ['그린', '초록', '초록색'],
                '옐로우': ['옐로우', '노란', '노란색'],
                '퍼플': ['퍼플', '보라', '보라색'],
                '핑크': ['핑크', '분홍', '분홍색'],
                '브라운': ['브라운', '갈색', '브라운'],
                '베이지': ['베이지', '베이지색'],
                '네이비': ['네이비', '남색'],
                '오렌지': ['오렌지', '주황', '주황색'],
                '카키': ['카키', '카키색'],
                '실버': ['실버', '은색']
            },
            'material': {
                '니트': ['니트', '뜨개'],
                '레더': ['레더', '가죽'],
                '코튼': ['코튼', '면', '면직물'],
                '실크': ['실크', '명주'],
                '린넨': ['린넨', '마', '마직물'],
                '데님': ['데님', '진'],
                '벨벳': ['벨벳', '벨벳'],
                '트위드': ['트위드'],
                '울': ['울', '모', '모직물'],
                '캐시미어': ['캐시미어'],
                '수영복': ['수영복 원단', '스판덱스'],
                '시폰': ['시폰'],
                '새틴': ['새틴', '공단'],
                '저지': ['저지'],
                '퍼': ['퍼', '모피']
            },
            'print': {
                '플로럴': ['플로럴', '꽃무늬'],
                '스트라이프': ['스트라이프', '줄무늬'],
                '체크': ['체크', '격자무늬'],
                '도트': ['도트', '물방울무늬'],
                '애니멀': ['애니멀', '동물무늬', '레오파드', '지브라'],
                '카모': ['카모', '카모플라주', '위장무늬'],
                '페이즐리': ['페이즐리'],
                '그래픽': ['그래픽', '그래피티'],
                '기하학': ['기하학', '기하학적', '모던'],
                '아트': ['아트', '그림', '페인팅'],
                '추상': ['추상', '추상적'],
                '모노그램': ['모노그램', '로고'],
                '스타': ['스타', '별무늬'],
                '하트': ['하트', '하트무늬'],
                '에스닉': ['에스닉', '민족적']
            },
            'style': {
                '캐주얼': ['캐주얼', '데일리'],
                '미니멀': ['미니멀', '심플', '단순한'],
                '빈티지': ['빈티지', '레트로'],
                '스트릿': ['스트릿', '스트리트'],
                '스포티': ['스포티', '스포츠', '애슬레저'],
                '로맨틱': ['로맨틱', '페미닌'],
                '글램': ['글램', '글래머러스'],
                '보헤미안': ['보헤미안', '보헤미안'],
                '클래식': ['클래식', '고전적'],
                '아방가르드': ['아방가르드', '실험적'],
                '에스닉': ['에스닉', '민족적'],
                '프레피': ['프레피', '프레피'],
                '밀리터리': ['밀리터리', '군사적'],
                '힙합': ['힙합'],
                '펑크': ['펑크', '펑크록']
            }
        }
        
        return category_mappings.get(category_type, {})
    
    def _calculate_category_counts(self, current_data, prev_data, category_mapping):
        """카테고리별 토큰 출현 횟수 계산"""
        current_counts = {category: 0 for category in category_mapping.keys()}
        prev_counts = {category: 0 for category in category_mapping.keys()}
        
        # 현재 기간 데이터 처리
        if not current_data.empty and 'tokens' in current_data.columns:
            for _, row in current_data.iterrows():
                tokens = row['tokens']
                if isinstance(tokens, list):
                    for token in tokens:
                        for category, keywords in category_mapping.items():
                            if any(kw.lower() in token.lower() for kw in keywords):
                                current_counts[category] += 1
        
        # 이전 기간 데이터 처리
        if not prev_data.empty and 'tokens' in prev_data.columns:
            for _, row in prev_data.iterrows():
                tokens = row['tokens']
                if isinstance(tokens, list):
                    for token in tokens:
                        for category, keywords in category_mapping.items():
                            if any(kw.lower() in token.lower() for kw in keywords):
                                prev_counts[category] += 1
        
        return current_counts, prev_counts
    
    def _format_category_result(self, current_counts, prev_counts):
        """카테고리 결과 포맷팅"""
        categories = list(current_counts.keys())
        
        # 증감률 계산
        growth_rates = {}
        for category in categories:
            prev = prev_counts.get(category, 0)
            curr = current_counts.get(category, 0)
            
            if prev > 0:
                growth = ((curr - prev) / prev) * 100
            else:
                growth = 0 if curr == 0 else 100  # 이전에 없었다면 100% 증가로 처리
            
            growth_rates[category] = round(growth, 2)
        
        # 언급량 기준 정렬
        sorted_categories = sorted(categories, key=lambda x: current_counts.get(x, 0), reverse=True)
        
        # 결과 데이터 구성
        result = {
            'categories': sorted_categories,
            'counts': [current_counts.get(cat, 0) for cat in sorted_categories],
            'growth_rates': [growth_rates.get(cat, 0) for cat in sorted_categories],
            'prev_counts': [prev_counts.get(cat, 0) for cat in sorted_categories]
        }
        
        return result