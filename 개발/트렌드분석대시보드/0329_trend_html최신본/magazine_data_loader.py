# magazine_data_loader.py
from sqlalchemy import create_engine
import pandas as pd
import logging
from datetime import datetime, timedelta
from db_connector import DBConnector
from analyzer import Analyzer
from visualizer import (
    generate_network_graph,
    generate_category_chart,
    generate_wordcloud,
    generate_tfidf_chart,
    generate_trend_chart
)
import mysql.connector
from config import DB_CONFIG, PERIOD_DAYS
from itertools import combinations
from collections import defaultdict
import json
from collections import Counter

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
        self.connect_db()
        self.visualizations = {}
    
    def connect_db(self):
        """데이터베이스 연결"""
        try:
            self.db_connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
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
        if self.data is None or self.data.empty:
            return None
        
        if magazine_name:
            magazine_data = self.filter_by_magazine(self.data, magazine_name)
        else:
            magazine_data = self.data
        
        if magazine_data is None or magazine_data.empty:
            return None
        
        # 카드뉴스 데이터가 없으므로 임시로 빈 리스트 반환
        return []
    
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
    
    def generate_visualizations(self, data, selected_magazines, focus_keywords):
        """시각화 생성"""
        try:
            logger.info("시각화 생성 시작")
            visualizations = {}

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
                all_tokens = [token for doc in data['tokens'] for token in doc]
                top_tokens = pd.Series(all_tokens).value_counts().head(10).index.tolist()
                
                # 엣지 생성
                edges = []
                weights = []
                for doc_tokens in data['tokens']:
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
                all_tokens = [token for doc in data['tokens'] for token in doc]
                word_freq = Counter(all_tokens)
                
                visualizations['wordcloud'] = generate_wordcloud(word_freq)
                logger.info("워드클라우드 생성 완료")
            except Exception as e:
                logger.error(f"워드클라우드 생성 오류: {e}")
                visualizations['wordcloud'] = None

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
    
    @staticmethod
    def get_sentiment_articles(period, sentiment):
        articles = []
        for i in range(3):
            articles.append({
                'date': '2025-01-15',
                'source': 'Fashion Times',
                'content': f'{"긍정적" if sentiment == "positive" else "부정적"} 내용의 기사 {i+1}입니다.',
                'keywords': ['트렌드', '컬렉션', '소재'] if sentiment == 'positive' else ['위기', '불확실성', '가격상승']
            })
        return articles
    
    @staticmethod
    def get_magazine_cards(period):
        return [
            {
                'title': 'Vogue 최신호 하이라이트',
                'date': '2025-01-20',
                'magazine': 'vogue',
                'image_url': '/static/images/card1.jpg'
            },
            {
                'title': 'W 매거진 특집기사',
                'date': '2025-01-15',
                'magazine': 'w',
                'image_url': '/static/images/card1.jpg'
            },
            {
                'title': 'Harper\'s BAZAAR 컬렉션 리뷰',
                'date': '2025-01-10',
                'magazine': 'harpers',
                'image_url': '/static/images/card1.jpg'
            }
        ]
    
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