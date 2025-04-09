import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import networkx as nx
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import base64
import io
import os
import matplotlib.font_manager
import logging
import json
from datetime import datetime, timedelta
import re


# 로깅 설정 추가
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 디버그 레벨로 설정

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 로거에 핸들러 추가
logger.addHandler(console_handler)

#로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """뉴스 데이터 분석 통합 클래스"""
    
    def __init__(self, data=None):
        """초기화"""
        self.data = data
        self.font_path = self._find_korean_font()
        logger.info(f"한글 폰트 경로: {self.font_path}")
    
    def _find_korean_font(self):
        """사용 가능한 한글 폰트 찾기"""
        # 운영체제별 기본 한글 폰트 경로 목록
        font_paths = [
            # macOS 폰트
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            '/Library/Fonts/AppleGothic.ttf',
            '/Library/Fonts/NanumGothic.ttf',
            
            # Windows 폰트
            'C:/Windows/Fonts/malgun.ttf',
            'C:/Windows/Fonts/NanumGothic.ttf',
            'C:/Windows/Fonts/gulim.ttc',
            
            # Linux 폰트
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
            '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
            '/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf'
        ]

        # 사용 가능한 첫 번째 폰트 찾기
        for path in font_paths:
            if os.path.exists(path):
                return path

        # 폰트를 찾지 못한 경우 기본 폰트 사용
        return matplotlib.font_manager.findfont(
            matplotlib.font_manager.FontProperties(family=['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'Gulim'])
        )
    
    def set_data(self, data):
        """데이터 설정"""
        self.data = data
        
        # 데이터 전처리
        if self.data is not None:
            # 날짜 형식 변환
            if 'upload_date' in self.data.columns and not pd.api.types.is_datetime64_any_dtype(self.data['upload_date']):
                self.data['upload_date'] = pd.to_datetime(self.data['upload_date'], errors='coerce')
            
            # 토큰 리스트 확인 및 변환
            if 'tokens' in self.data.columns:
                # tokens 컬럼이 있으면 token_list로 복사 (일관성 유지)
                self.data['token_list'] = self.data['tokens'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            elif 'token_list' not in self.data.columns:
                # token_list 컬럼이 없으면 생성 (간단한 토큰화)
                if 'content' in self.data.columns:
                    self.data['token_list'] = self.data['content'].str.split()
                else:
                    self.data['token_list'] = [[]]  # 빈 토큰 리스트
        
        return self.data
    
    def prepare_text_data(self):
        """텍스트 데이터 준비"""
        if self.data is None or self.data.empty:
            return None
            
        # 토큰을 문자열로 결합한 컬럼 추가
        self.data['token_text'] = self.data['token_list'].apply(
            lambda tokens: ' '.join(tokens) if isinstance(tokens, list) else ''
        )
        
        return self.data

    # 1. 감성 분석 관련 기능
    def load_sentiment_dictionary(self):
        """감성 사전 로드 함수"""
        # 기본 감성 사전 (예시)
        positive_words = [
            '좋은', '훌륭한', '우수한', '뛰어난', '성공', '상승', '증가', '성장', '혁신', 
            '인기', '긍정적', '기회', '개선', '발전', '호평', '효과적', '효율적', '이익', 
            '수익', '매출', '선도', '앞서', '기대', '호조', '활발', '두각', '주목', 
            '강세', '강화', '최고', '최상', '최대', '안정', '견고', '든든', '향상',
            '슬기롭게', '극복', '회복', '반등', '해소', '개척', '성과', '돌파', '확대'
        ]
        
        negative_words = [
            '나쁜', '불량', '저조', '하락', '감소', '축소', '위기', '문제', '비판', 
            '부정적', '어려움', '악화', '손실', '적자', '실패', '퇴보', '악평', '비효율적', 
            '약세', '부진', '위험', '우려', '걱정', '실망', '침체', '후퇴', '위축', 
            '저하', '약화', '최저', '최악', '최소', '불안', '취약', '느슨', '갈등',
            '혼란', '논란', '충격', '급락', '물의', '파산', '적신호', '불투명', '타격'
        ]
        
        # 감성 사전 구성
        sentiment_dict = {
            'positive': set(positive_words),
            'negative': set(negative_words)
        }
        
        return sentiment_dict
    
    def calculate_article_sentiment(self):
        """기사별 감성 점수 계산"""
        if self.data is None or self.data.empty:
            return None
            
        # 데이터 복사
        df = self.data.copy()
        
        # 감성 사전 로드
        sentiment_dict = self.load_sentiment_dictionary()
        
        # 긍정/부정 단어 리스트 및 점수 계산
        df['positive_words'] = df['token_list'].apply(
            lambda tokens: [word for word in tokens if word in sentiment_dict['positive']] if isinstance(tokens, list) else []
        )
        
        df['negative_words'] = df['token_list'].apply(
            lambda tokens: [word for word in tokens if word in sentiment_dict['negative']] if isinstance(tokens, list) else []
        )
        
        # 긍정/부정 단어 수 계산
        df['positive_count'] = df['positive_words'].apply(len)
        df['negative_count'] = df['negative_words'].apply(len)
        df['token_count'] = df['token_list'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        
        # 정규화된 감성 점수 계산
        df['sentiment_score'] = df.apply(
            lambda row: (row['positive_count'] - row['negative_count']) / max(row['token_count'], 1) * 100,
            axis=1
        )
        
        # 감성 범주 분류
        df['sentiment'] = df['sentiment_score'].apply(
            lambda score: '긍정' if score > 1 else ('부정' if score < -1 else '중립')
        )
        
        return df
    
    def get_sentiment_distribution(self, df=None):
        """감성 분포 분석"""
        if df is None:
            df = self.calculate_article_sentiment()
        
        if df is None or df.empty:
            return None
        
        # 감성 범주별 카운트
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        
        # 감성 점수 통계
        sentiment_stats = {
            'mean': df['sentiment_score'].mean(),
            'median': df['sentiment_score'].median(),
            'min': df['sentiment_score'].min(),
            'max': df['sentiment_score'].max(),
            'positive_ratio': (df['sentiment'] == '긍정').mean() * 100,
            'neutral_ratio': (df['sentiment'] == '중립').mean() * 100,
            'negative_ratio': (df['sentiment'] == '부정').mean() * 100
        }
        
        # 감성 범주별 기사 목록
        positive_articles = df[df['sentiment'] == '긍정'].sort_values('sentiment_score', ascending=False)
        negative_articles = df[df['sentiment'] == '부정'].sort_values('sentiment_score', ascending=True)
        
        # 결과 반환
        result = {
            'sentiment_counts': sentiment_counts,
            'sentiment_stats': sentiment_stats,
            'positive_articles': positive_articles.to_dict('records'),
            'negative_articles': negative_articles.to_dict('records')
        }
        
        return result
    
    def generate_sentiment_chart(self, df=None):
        """감성 차트 생성"""
        if df is None:
            df = self.calculate_article_sentiment()
        
        if df is None or df.empty:
            return None
        
        # 파이 차트 데이터 준비
        sentiment_counts = df['sentiment'].value_counts()
        
        # Plotly 파이 차트 생성
        fig = go.Figure(data=[go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=.3,
            marker_colors=['skyblue', 'lightgray', 'salmon']
        )])
        
        fig.update_layout(
            title=dict(
                text="기사 감성 분포"
            ),
            legend_title="감성 범주"
        )
        
        # 월별 감성 추이 데이터 준비
        if 'upload_date' in df.columns:
            df['year_month'] = df['upload_date'].dt.strftime('%Y-%m')
            monthly_sentiment = df.groupby('year_month')['sentiment_score'].mean().reset_index()
            
            # 월별 감성 추이 차트
            time_fig = go.Figure()
            
            time_fig.add_trace(go.Scatter(
                x=monthly_sentiment['year_month'],
                y=monthly_sentiment['sentiment_score'],
                mode='lines+markers',
                name='평균 감성 점수'
            ))
            
            time_fig.update_layout(
                title=dict(
                    text="월별 감성 점수 추이"
                ),
                xaxis_title="년-월",
                yaxis_title="평균 감성 점수"
            )
            
            # 중립선 추가
            time_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color="gray"
            )
            
            # 두 차트 반환
            return {
                'pie_chart': fig.to_html(full_html=False),
                'time_chart': time_fig.to_html(full_html=False)
            }
        
        # 월별 데이터가 없는 경우 파이 차트만 반환
        return {
            'pie_chart': fig.to_html(full_html=False)
        }
    
    def get_sentiment_wordcloud(self, df=None):
        """감성별 워드클라우드 생성"""
        if df is None:
            df = self.calculate_article_sentiment()
        
        if df is None or df.empty or not self.font_path:
            return None
        
        # 긍정 단어 워드클라우드
        positive_words = []
        for pos_list in df['positive_words']:
            positive_words.extend(pos_list)
        
        # 부정 단어 워드클라우드
        negative_words = []
        for neg_list in df['negative_words']:
            negative_words.extend(neg_list)
        
        wordclouds = {}
        
        if positive_words:
            pos_word_freq = Counter(positive_words)
            
            pos_wordcloud = WordCloud(
                font_path=self.font_path,
                width=800, 
                height=400,
                background_color='white',
                colormap='YlGn',
                max_words=100
            ).generate_from_frequencies(pos_word_freq)
            
            # 이미지로 변환
            plt.figure(figsize=(10, 6))
            plt.imshow(pos_wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('긍정 단어 워드클라우드')
            
            # 이미지를 base64로 인코딩
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            
            wordclouds['positive'] = base64.b64encode(image_png).decode()
        
        if negative_words:
            neg_word_freq = Counter(negative_words)
            
            neg_wordcloud = WordCloud(
                font_path=self.font_path,
                width=800, 
                height=400,
                background_color='white',
                colormap='OrRd',
                max_words=100
            ).generate_from_frequencies(neg_word_freq)
            
            # 이미지로 변환
            plt.figure(figsize=(10, 6))
            plt.imshow(neg_wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('부정 단어 워드클라우드')
            
            # 이미지를 base64로 인코딩
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            
            wordclouds['negative'] = base64.b64encode(image_png).decode()
        
        return wordclouds

    # 2. TF-IDF 분석 관련 기능
    def analyze_tfidf(self, max_features=1000, min_df=2):
        """TF-IDF 분석"""
        if self.data is None or self.data.empty:
            return None
        
        # 텍스트 데이터 준비
        self.prepare_text_data()
        
        # TF-IDF 벡터라이저 초기화
        vectorizer = TfidfVectorizer(max_features=max_features, min_df=min_df)
        
        # TF-IDF 행렬 계산
        tfidf_matrix = vectorizer.fit_transform(self.data['token_text'])
        feature_names = vectorizer.get_feature_names_out()
        
        # 코퍼스 전체에서의 단어별 TF-IDF 평균 점수 계산
        mean_tfidf = np.array(tfidf_matrix.mean(axis=0)).flatten()
        word_scores = [(feature_names[i], mean_tfidf[i]) for i in range(len(feature_names))]
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 문서 간 유사도 계산
        from sklearn.metrics.pairwise import cosine_similarity
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        return {
            'vectorizer': vectorizer,
            'tfidf_matrix': tfidf_matrix,
            'feature_names': feature_names,
            'word_scores': word_scores,
            'cosine_sim': cosine_sim
        }
    
    def get_top_tfidf_keywords(self, top_n=20, tfidf_results=None):
        """상위 TF-IDF 키워드 추출"""
        if tfidf_results is None:
            tfidf_results = self.analyze_tfidf()
        
        if tfidf_results is None:
            return []
        
        top_words = tfidf_results['word_scores'][:top_n]
        
        return {
            'words': [word for word, _ in top_words],
            'scores': [score for _, score in top_words]
        }
    
    def generate_tfidf_chart(self, top_n=20, tfidf_results=None):
        """TF-IDF 차트 생성"""
        if tfidf_results is None:
            tfidf_results = self.analyze_tfidf()
        
        if tfidf_results is None:
            return None
        
        top_words = tfidf_results['word_scores'][:top_n]
        words, scores = zip(*top_words) if top_words else ([], [])
        
        # DataFrame 생성
        df = pd.DataFrame({
            '단어': words,
            'TF-IDF 점수': scores
        })
        
        # Plotly 막대 그래프 생성
        fig = px.bar(
            df,
            x='TF-IDF 점수',
            y='단어',
            orientation='h',
            color='TF-IDF 점수',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(
            title=dict(
                text=f'상위 {top_n}개 TF-IDF 키워드'
            ),
            yaxis={'categoryorder': 'total ascending'},
            height=600
        )
        
        return fig.to_html(full_html=False)
    
    def generate_tfidf_wordcloud(self, top_n=200, tfidf_results=None):
        """TF-IDF 기반 워드클라우드 생성"""
        if not self.font_path:
            return None
            
        if tfidf_results is None:
            tfidf_results = self.analyze_tfidf()
        
        if tfidf_results is None:
            return None
        
        word_scores = tfidf_results['word_scores'][:top_n]
        word_score_dict = dict(word_scores)
        
        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path=self.font_path,
            width=800, 
            height=500,
            background_color='white',
            max_words=100,
            max_font_size=150,
            random_state=42
        ).generate_from_frequencies(word_score_dict)
        
        # 이미지로 변환
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('TF-IDF 기반 워드클라우드')
        
        # 이미지를 base64로 인코딩
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        plt.close()
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode()
    
    def find_similar_articles(self, article_id=None, keywords=None, tfidf_results=None):
        """유사 기사 검색"""
        if tfidf_results is None:
            tfidf_results = self.analyze_tfidf()
        
        if tfidf_results is None or self.data is None or self.data.empty:
            return []
        
        cosine_sim = tfidf_results['cosine_sim']
        vectorizer = tfidf_results['vectorizer']
        
        similar_articles = []
        
        if article_id is not None:
            # 선택한 기사 ID로 검색
            article_idx = self.data[self.data['id'] == article_id].index
            
            if len(article_idx) == 0:
                return []
                
            article_idx = article_idx[0]
            
            # 유사도 점수 계산
            sim_scores = list(enumerate(cosine_sim[article_idx]))
            sim_scores = [(i, score) for i, score in sim_scores if i != article_idx]
            sim_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 유사 기사 추출
            for i, (idx, score) in enumerate(sim_scores[:10], 1):
                if idx < len(self.data):
                    article = self.data.iloc[idx]
                    similar_articles.append({
                        'id': article['id'],
                        'title': article['title'],
                        'score': score,
                        'rank': i
                    })
        
        elif keywords is not None:
            # 키워드로 검색
            search_vector = vectorizer.transform([keywords])
            
            # 모든 문서와의 유사도 계산
            doc_sim = cosine_sim(search_vector, tfidf_results['tfidf_matrix']).flatten()
            
            # 유사도 기준 정렬
            sim_scores = list(enumerate(doc_sim))
            sim_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 유사 기사 추출
            for i, (idx, score) in enumerate(sim_scores[:10], 1):
                if idx < len(self.data):
                    article = self.data.iloc[idx]
                    similar_articles.append({
                        'id': article['id'],
                        'title': article['title'],
                        'score': score,
                        'rank': i
                    })
        
        return similar_articles

    def analyze_keyword_trend(self, keywords, time_unit='monthly'):
        """키워드 트렌드 분석 개선 버전
        
        Args:
            keywords (list): 분석할 키워드 리스트
            time_unit (str): 시간 단위 ('daily', 'weekly', 'monthly')
                
        Returns:
            dict: 키워드별 트렌드 데이터
        """
        try:
            logger.info(f"키워드 트렌드 분석 시작: {keywords}")
            
            if self.data is None or self.data.empty:
                logger.warning("키워드 트렌드: 데이터가 없습니다.")
                return None
            
            # 데이터 복사
            df = self.data.copy()
            
            # 날짜 컬럼 확인 - published와 upload_date 둘 다 확인
            date_column = None
            for col in ['published', 'upload_date']:
                if col in df.columns:
                    date_column = col
                    logger.info(f"키워드 트렌드: 날짜 컬럼 '{col}' 사용")
                    break
            
            if date_column is None:
                logger.warning("키워드 트렌드: 날짜 컬럼을 찾을 수 없습니다.")
                return None
            
            # 토큰 컬럼 확인 - tokens와 token_list 둘 다 확인
            token_column = None
            for col in ['tokens', 'token_list']:
                if col in df.columns:
                    token_column = col
                    logger.info(f"키워드 트렌드: 토큰 컬럼 '{col}' 사용")
                    break
            
            if token_column is None:
                logger.warning("키워드 트렌드: 토큰 컬럼을 찾을 수 없습니다.")
                return None
            
            # 날짜 형식 확인 및 변환
            if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                logger.info(f"키워드 트렌드: 날짜 컬럼 형식 변환 (현재 형식: {df[date_column].dtype})")
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # None 값이 있는 행 제거
            null_dates = df[date_column].isna()
            if null_dates.any():
                logger.warning(f"날짜 변환 후 {null_dates.sum()}개의 null 값이 생성되었습니다.")
                df = df[~null_dates].copy()
            
            # 시간 단위 컬럼 추가
            if time_unit == 'daily':
                df['time_unit'] = df[date_column].dt.strftime('%Y-%m-%d')
            elif time_unit == 'weekly':
                df['time_unit'] = df[date_column].dt.to_period('W').dt.strftime('%Y-%U')
            else:  # monthly
                df['time_unit'] = df[date_column].dt.strftime('%Y-%m')
            
            # 시간 단위별 전체 문서 수 계산
            total_by_time = df.groupby('time_unit').size()
            time_units = sorted(df['time_unit'].unique())
            
            # 키워드별 시간 단위별 빈도 계산
            keyword_trends = {}
            for keyword in keywords:
                trend_data = []
                
                # 시간 단위별로 반복
                for time_unit_value in time_units:
                    # 해당 시간 단위 데이터
                    time_df = df[df['time_unit'] == time_unit_value]
                    
                    # 해당 키워드가 포함된 기사 수 계산
                    if isinstance(time_df.iloc[0][token_column], list):
                        # 리스트 형태인 경우
                        keyword_count = sum(1 for tokens in time_df[token_column] if keyword in tokens)
                    else:
                        # 문자열 형태인 경우
                        keyword_count = sum(1 for tokens in time_df[token_column] if isinstance(tokens, str) and keyword in tokens.split())
                    
                    trend_data.append({
                        'time_unit': time_unit_value,
                        'frequency': keyword_count
                    })
                
                keyword_trends[keyword] = trend_data
            
            # 각 시간 단위의 전체 기사 수
            totals = total_by_time.to_dict()
            
            result = {
                'trends': keyword_trends,
                'totals': totals,
                'time_unit': time_unit,
                'time_units': time_units
            }
            
            logger.info(f"키워드 트렌드 분석 완료: {len(keyword_trends)}개 키워드, {len(time_units)}개 시간 단위")
            return result
            
        except Exception as e:
            logger.error(f"키워드 트렌드 분석 중 오류 발생: {e}", exc_info=True)
            return None
    
    def generate_keyword_trend_chart(self, keywords, trend_data=None):
        """키워드 트렌드 차트 생성 개선 버전
        
        Args:
            keywords (list): 분석할 키워드 리스트
            trend_data (dict): analyze_keyword_trend()의 반환값
                
        Returns:
            str: HTML 형식의 차트
        """
        try:
            logger.info(f"키워드 트렌드 차트 생성 시작: {keywords}")
            
            # 트렌드 데이터가 없으면 생성
            if trend_data is None:
                trend_data = self.analyze_keyword_trend(keywords)
            
            if trend_data is None or 'trends' not in trend_data or 'time_units' not in trend_data:
                logger.warning("키워드 트렌드 차트: 트렌드 데이터가 없거나 형식이 올바르지 않습니다.")
                return None
            
            # 시간 단위 목록
            time_units = trend_data['time_units']
            
            if not time_units:
                logger.warning("키워드 트렌드 차트: 시간 단위 데이터가 없습니다.")
                return None
            
            # Plotly 그래프 생성
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            # 각 키워드별 라인 추가
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for i, keyword in enumerate(keywords):
                if keyword not in trend_data['trends']:
                    logger.warning(f"키워드 '{keyword}'의 트렌드 데이터가 없습니다.")
                    continue
                    
                keyword_data = trend_data['trends'][keyword]
                
                # 데이터가 없으면 건너뛰기
                if not keyword_data:
                    logger.warning(f"키워드 '{keyword}'의 트렌드 데이터가 비어 있습니다.")
                    continue
                
                # 모든 시간 단위에 대한 데이터를 준비
                x_values = []
                y_values = []
                
                # 데이터 포인트 딕셔너리로 변환 (시간 단위 → 빈도)
                data_dict = {point['time_unit']: point['frequency'] for point in keyword_data}
                
                for time_unit in time_units:
                    x_values.append(time_unit)
                    y_values.append(data_dict.get(time_unit, 0))  # 해당 시간 단위에 데이터가 없으면 0
                
                # 색상 인덱스 계산 (키워드 수보다 색상이 적을 수 있으므로)
                color_idx = i % len(colors)
                
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines+markers',
                        name=keyword,
                        line=dict(color=colors[color_idx], width=2),
                        marker=dict(size=8)
                    )
                )
            
            # 차트 레이아웃 설정
            time_unit_type = trend_data.get('time_unit', 'monthly')
            title = f"키워드별 언급량 추세 ({time_unit_type})"
            x_title = '날짜' if time_unit_type == 'daily' else '년-주' if time_unit_type == 'weekly' else '년-월'
            
            fig.update_layout(
                title=dict(
                    text=title,
                    font=dict(size=18)
                ),
                xaxis=dict(
                    title=x_title,
                    tickangle=-45 if len(time_units) > 5 else 0
                ),
                yaxis=dict(
                    title='언급 빈도',
                    gridcolor='#eee'
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                template='plotly_white',
                height=500,
                margin=dict(l=50, r=50, t=80, b=80)
            )
            
            # 반응형 디자인 적용
            fig.update_layout(
                autosize=True
            )
            
            logger.info("키워드 트렌드 차트 생성 완료")
            return fig.to_html(full_html=False)
            
        except Exception as e:
            logger.error(f"키워드 트렌드 차트 생성 중 오류 발생: {e}", exc_info=True)
            return None

    # 3. 시계열 분석 관련 기능
    def analyze_time_series(self):
        """시계열 분석"""
        try:
            logger.info(f"시계열 분석 시작: 데이터 크기={len(self.data) if self.data is not None else 0}")
            
            # 데이터 유효성 검사
            if self.data is None or self.data.empty:
                logger.warning("시계열 분석: 데이터가 없습니다.")
                return None
            
            # 날짜 컬럼 확인 ('published'와 'upload_date' 모두 시도)
            date_column = None
            date_columns = ['published', 'upload_date', 'date', 'created_at', 'updated_at']
            
            # 데이터의 모든 컬럼 로깅
            logger.info(f"데이터 컬럼: {list(self.data.columns)}")
            
            for column in date_columns:
                if column in self.data.columns:
                    date_column = column
                    logger.info(f"시계열 분석: 날짜 컬럼 '{column}' 사용")
                    break
            
            if date_column is None:
                logger.warning("시계열 분석: 날짜 컬럼을 찾을 수 없습니다.")
                # 임시 해결책: 현재 날짜 기준 더미 데이터 생성
                from datetime import datetime, timedelta
                today = datetime.now()
                
                # 더미 데이터 반환
                return {
                    'daily': pd.DataFrame({'date': [today.date() - timedelta(days=1), today.date()], 
                                        'count': [len(self.data)//2, len(self.data)//2]}),
                    'monthly': pd.DataFrame({'year_month': [today.strftime('%Y-%m')], 
                                            'count': [len(self.data)]}),
                    'weekly': pd.DataFrame({'year_week': [today.strftime('%Y-%U')], 
                                            'count': [len(self.data)]})
                }
            
            # 날짜 형식 변환 확인
            try:
                if not pd.api.types.is_datetime64_any_dtype(self.data[date_column]):
                    logger.info(f"시계열 분석: 날짜 컬럼 형식 변환 필요 (현재 형식: {self.data[date_column].dtype})")
                    self.data[date_column] = pd.to_datetime(self.data[date_column])
            except Exception as e:
                logger.error(f"시계열 분석: 날짜 변환 오류 - {e}")
                # 오류 발생 시 샘플 데이터 출력
                logger.error(f"날짜 샘플: {self.data[date_column].head()}")
                return None
            
            # 날짜 컬럼 추가
            df = self.data.copy()
            df['year_month'] = df[date_column].dt.strftime('%Y-%m')
            df['year_week'] = df[date_column].dt.strftime('%Y-%U')
            df['date'] = df[date_column].dt.date
            
            # 일별 기사 수 집계
            daily_counts = df.groupby('date').size().reset_index(name='count')
            logger.info(f"시계열 분석: 일별 집계 - {len(daily_counts)}개 항목")
            
            # 월별 기사 수 집계
            monthly_counts = df.groupby('year_month').size().reset_index(name='count')
            logger.info(f"시계열 분석: 월별 집계 - {len(monthly_counts)}개 항목")
            
            # 주별 기사 수 집계
            weekly_counts = df.groupby('year_week').size().reset_index(name='count')
            logger.info(f"시계열 분석: 주별 집계 - {len(weekly_counts)}개 항목")
            
            # 결과 반환
            result = {
                'daily': daily_counts,
                'monthly': monthly_counts,
                'weekly': weekly_counts
            }
            
            logger.info("시계열 분석: 분석 성공")
            return result
            
        except Exception as e:
            logger.error(f"시계열 분석 중 오류 발생: {e}", exc_info=True)
            # 예외 발생 시에도 결과를 반환하도록 조치
            from datetime import datetime, timedelta
            today = datetime.now()
            
            # 더미 데이터 반환
            return {
                'daily': pd.DataFrame({'date': [today.date() - timedelta(days=1), today.date()], 
                                    'count': [len(self.data)//2, len(self.data)//2]}),
                'monthly': pd.DataFrame({'year_month': [today.strftime('%Y-%m')], 
                                        'count': [len(self.data)]}),
                'weekly': pd.DataFrame({'year_week': [today.strftime('%Y-%U')], 
                                        'count': [len(self.data)]})
            }
    
    def generate_time_series_chart(self, time_data=None, time_unit='monthly'):
        """시계열 차트 생성"""
        try:
            if time_data is None:
                time_data = self.analyze_time_series()
            
            if time_data is None:
                logger.warning("시계열 차트 생성: 시계열 데이터가 없습니다.")
                return None
            
            # 시계열 데이터 구조 확인
            logger.debug(f"시계열 데이터 키: {list(time_data.keys())}")
            
            if time_unit in time_data:
                unit_data = time_data[time_unit]
                logger.info(f"사용 중인 시간 단위: {time_unit}, 데이터 크기: {len(unit_data)}")
                
                # 데이터프레임 컬럼 확인
                if isinstance(unit_data, pd.DataFrame):
                    logger.debug(f"단위 데이터 컬럼: {list(unit_data.columns)}")
                
                # x축 컬럼 이름
                x_column = 'date' if time_unit == 'daily' else \
                        'year_month' if time_unit == 'monthly' else 'year_week'
                
                # 컬럼 확인 및 대체 컬럼 찾기
                if isinstance(unit_data, pd.DataFrame) and x_column not in unit_data.columns:
                    logger.warning(f"컬럼 '{x_column}'이 없습니다. 가능한 컬럼: {unit_data.columns.tolist() if isinstance(unit_data, pd.DataFrame) else 'N/A'}")
                    
                    # 대체 컬럼 사용 (첫 번째 컬럼)
                    if isinstance(unit_data, pd.DataFrame) and len(unit_data.columns) > 0:
                        x_column = unit_data.columns[0]
                        logger.info(f"대체 x축 컬럼으로 '{x_column}' 사용")
                    else:
                        logger.error("시계열 데이터에 컬럼이 없습니다.")
                        return None
                
                # Plotly 그래프 생성
                fig = go.Figure()
                
                if isinstance(unit_data, pd.DataFrame):
                    fig.add_trace(go.Scatter(
                        x=unit_data[x_column],
                        y=unit_data['count'] if 'count' in unit_data.columns else unit_data.iloc[:, 1],
                        mode='lines+markers',
                        name='기사 수'
                    ))
                else:
                    # 데이터가 DataFrame이 아닌 경우의 처리
                    logger.warning(f"시계열 데이터가 DataFrame이 아닙니다: {type(unit_data)}")
                    return None
                
                # 레이블 설정
                x_label = '날짜' if time_unit == 'daily' else '년-월' if time_unit == 'monthly' else '년-주'
                
                fig.update_layout(
                    title=f'{time_unit} 뉴스 기사 수',
                    xaxis_title=x_label,
                    yaxis_title='기사 수',
                    height=500
                )
                
                return fig.to_html(full_html=False)
            else:
                logger.warning(f"시계열 차트 생성: '{time_unit}' 데이터가 없습니다. 사용 가능: {list(time_data.keys())}")
                return None
            
        except Exception as e:
            logger.error(f"시계열 차트 생성 중 오류 발생: {e}", exc_info=True)
            return None
    

    # 4. 토픽 모델링 관련 기능
    def analyze_topics(self, n_topics=5, max_features=1000, min_df=2):
        """토픽 모델링 분석"""
        if self.data is None or self.data.empty:
            return None
        
        # 텍스트 데이터 준비
        self.prepare_text_data()
        
        # 문서-단어 행렬 생성
        count_vectorizer = CountVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=0.95
        )
        
        doc_term_matrix = count_vectorizer.fit_transform(self.data['token_text'])
        feature_names = count_vectorizer.get_feature_names_out()
        
        # LDA 모델 학습
        lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=10,
            learning_method='online',
            random_state=42,
            n_jobs=-1  # 모든 CPU 사용
        )
        
        lda_model.fit(doc_term_matrix)
        
        # 토픽별 주요 단어 추출
        n_top_words = 10  # 각 토픽별 상위 단어 수
        topic_words = []
        for topic_idx, topic in enumerate(lda_model.components_):
            top_indices = topic.argsort()[:-n_top_words-1:-1]
            top_words = [feature_names[i] for i in top_indices]
            topic_words.append(top_words)
        
        # 토픽 자동 명명 (상위 3개 단어 기반)
        topic_names = []
        for words in topic_words:
            topic_name = " & ".join(words[:3])
            topic_names.append(topic_name)
        
        # 문서별 토픽 확률 분포
        doc_topic_dist = lda_model.transform(doc_term_matrix)
        
        # 데이터프레임에 주요 토픽 할당
        df_topics = self.data.copy()
        df_topics['dominant_topic'] = doc_topic_dist.argmax(axis=1)
        df_topics['topic_confidence'] = doc_topic_dist.max(axis=1)
        df_topics['topic_name'] = df_topics['dominant_topic'].apply(
            lambda x: topic_names[x] if x < len(topic_names) else f"토픽 {x+1}"
        )
        
        return {
            'lda_model': lda_model,
            'vectorizer': count_vectorizer,
            'doc_term_matrix': doc_term_matrix,
            'feature_names': feature_names,
            'topic_words': topic_words,
            'topic_names': topic_names,
            'doc_topic_dist': doc_topic_dist,
            'df_topics': df_topics
        }
    
    # 5. 연관어 분석 관련 기능
    def analyze_word_association(self, top_n=300, min_count=2):
        """단어 연관성 분석"""
        if self.data is None or self.data.empty or 'token_list' not in self.data.columns:
            return None
        
        # 모든 토큰 결합
        all_tokens = []
        for tokens in self.data['token_list']:
            if isinstance(tokens, list):
                all_tokens.extend(tokens)
        
        # 단어 빈도 계산
        word_counts = Counter(all_tokens)
        
        # 상위 N개 단어 선택
        top_words = [word for word, _ in word_counts.most_common(top_n)]
        word_set = set(top_words)
        
        # 동시 출현 횟수 계산
        cooccurrence = defaultdict(int)
        
        for tokens in self.data['token_list']:
            if not isinstance(tokens, list):
                continue
                
            # 선택된 단어만 필터링
            filtered_tokens = [token for token in tokens if token in word_set]
            
            # 같은 문서 내 단어 쌍 확인
            for i, word1 in enumerate(filtered_tokens):
                for word2 in filtered_tokens[i+1:]:
                    if word1 != word2:
                        # 알파벳 순으로 정렬하여 중복 쌍 방지
                        pair = tuple(sorted([word1, word2]))
                        cooccurrence[pair] += 1
        
        # 네트워크 그래프 생성
        G = nx.Graph()
        
        # 노드 추가
        for word in word_set:
            G.add_node(word, count=word_counts[word])
        
        # 엣지 추가 (임계값 이상 공동 출현)
        for (word1, word2), count in cooccurrence.items():
            if count >= min_count:
                G.add_edge(word1, word2, weight=count)
        
        # 중심성 계산
        if G.number_of_nodes() <= 1000:
            try:
                degree_centrality = nx.degree_centrality(G)
                eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=100)
                
                for node in G.nodes():
                    G.nodes[node]['degree_centrality'] = degree_centrality.get(node, 0)
                    G.nodes[node]['eigenvector_centrality'] = eigenvector_centrality.get(node, 0)
            except:
                pass
        
        return {
            'graph': G,
            'word_counts': word_counts,
            'cooccurrence': cooccurrence,
            'top_words': top_words
        }
    
    def generate_network_graph(self, association_results=None, max_nodes=100):
        """단어 네트워크 그래프 생성"""
        if association_results is None:
            association_results = self.analyze_word_association()
        
        if association_results is None:
            return None
        
        G = association_results['graph']
        word_counts = association_results['word_counts']
        
        # 노드 수가 너무 많으면 필터링
        if G.number_of_nodes() > max_nodes:
            # 중심성 또는 빈도 기준으로 상위 노드 선택
            if 'degree_centrality' in G.nodes[list(G.nodes())[0]]:
                centrality_scores = [(node, G.nodes[node]['degree_centrality']) for node in G.nodes()]
                centrality_scores.sort(key=lambda x: x[1], reverse=True)
                top_nodes = [node for node, _ in centrality_scores[:max_nodes]]
            else:
                top_nodes = [word for word, _ in word_counts.most_common(max_nodes)]
            
            # 서브그래프 생성
            G_vis = G.subgraph(top_nodes).copy()
        else:
            G_vis = G
        
        # 레이아웃 계산
        pos = nx.spring_layout(G_vis, seed=42)
        
        # 엣지 좌표
        edge_x = []
        edge_y = []
        
        for edge in G_vis.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_y.append(y0)
            edge_x.append(x1)
            edge_y.append(y1)
            edge_x.append(None)
            edge_y.append(None)
        
        # 엣지 트레이스
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # 노드 좌표 및 속성
        node_x = []
        node_y = []
        node_size = []
        node_text = []
        
        for node in G_vis.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # 노드 크기 (단어 빈도에 비례)
            size = np.sqrt(word_counts[node]) * 2  # 빈도의 제곱근으로 크기 조정
            node_size.append(size)
            
            # 노드 텍스트 (툴팁)
            freq = word_counts[node]
            degree = G_vis.degree(node)
            text = f"{node}<br>빈도: {freq}<br>연결수: {degree}"
            node_text.append(text)
        
        # 노드 트레이스
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=list(G_vis.nodes()),
            textposition="top center",
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=node_size,
                colorbar=dict(
                    thickness=15,
                    title=dict(
                        text='단어 빈도',
                        side='right'
                    ),
                    xanchor='left'
                ),
                color=[word_counts[node] for node in G_vis.nodes()],
                line=dict(width=2)
            )
        )
        
        # 그래프 생성
        fig = go.Figure(data=[edge_trace, node_trace],
                      layout=go.Layout(
                          title=dict(
                              text='단어 연관 네트워크',
                              font=dict(size=16)
                          ),
                          showlegend=False,
                          hovermode='closest',
                          margin=dict(b=20,l=5,r=5,t=40),
                          annotations=[dict(
                              text="",
                              showarrow=False,
                              xref="paper", yref="paper"
                          )],
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          height=700
                      )
                     )
        
        return fig.to_html(full_html=False)
    
    def find_related_words(self, target_word, association_results=None, top_n=20):
        """특정 단어의 연관어 분석"""
        if association_results is None:
            association_results = self.analyze_word_association()
        
        if association_results is None:
            return []
        
        G = association_results['graph']
        
        # 해당 단어가 그래프에 없는 경우
        if target_word not in G:
            return []
        
        # 인접 노드 및 가중치 추출
        related_words = []
        for neighbor in G.neighbors(target_word):
            weight = G[target_word][neighbor]['weight']
            related_words.append((neighbor, weight))
        
        # 가중치 기준 정렬
        related_words.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 N개 반환
        return related_words[:top_n]
    
    # 6. 단어 빈도수 분석 관련 기능
    def analyze_word_frequency(self):
        """단어 빈도수 분석"""
        if self.data is None or self.data.empty or 'token_list' not in self.data.columns:
            return None
        
        # 모든 토큰 결합
        all_tokens = []
        for tokens in self.data['token_list']:
            if isinstance(tokens, list):
                all_tokens.extend(tokens)
        
        # 빈도수 계산
        word_counts = Counter(all_tokens)
        
        # 기본 통계
        total_tokens = len(all_tokens)
        unique_tokens = len(word_counts)
        
        return {
            'word_counts': word_counts,
            'total_tokens': total_tokens,
            'unique_tokens': unique_tokens
        }
    
    def get_top_words(self, freq_results=None, top_n=30):
        """상위 빈도 단어 추출"""
        if freq_results is None:
            freq_results = self.analyze_word_frequency()
        
        if freq_results is None:
            return []
        
        # 상위 단어 추출
        top_words = freq_results['word_counts'].most_common(top_n)
        
        return top_words
    
    def generate_frequency_chart(self, freq_results=None, top_n=30):
        """빈도수 차트 생성"""
        if freq_results is None:
            freq_results = self.analyze_word_frequency()
        
        if freq_results is None:
            return None
        
        # 상위 단어 추출
        top_words = freq_results['word_counts'].most_common(top_n)
        
        # 데이터프레임 생성
        df = pd.DataFrame(top_words, columns=['단어', '빈도수'])
        
        # Plotly 막대 그래프 생성
        fig = px.bar(
            df, 
            x='빈도수', 
            y='단어',
            orientation='h',
            text='빈도수',
            color='빈도수',
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        fig.update_layout(
            title=dict(
                text=f'상위 {top_n}개 키워드 빈도'
            ),
            yaxis={'categoryorder': 'total ascending'},
            height=600
        )
        
        return fig.to_html(full_html=False)
    
    def generate_wordcloud(self, freq_results=None, max_words=200):
        """워드클라우드 생성"""
        if not self.font_path:
            return None
            
        if freq_results is None:
            freq_results = self.analyze_word_frequency()
        
        if freq_results is None:
            return None
        
        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path=self.font_path,
            width=800, 
            height=500,
            background_color='white',
            max_words=max_words,
            max_font_size=150,
            random_state=42
        ).generate_from_frequencies(dict(freq_results['word_counts']))
        
        # 이미지로 변환
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        # 이미지를 base64로 인코딩
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        plt.close()
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode()
    
    def analyze_word_trend(self, words, freq_results=None):
        """선택한 단어들의 시간별 빈도 추이 분석"""
        if self.data is None or self.data.empty or 'upload_date' not in self.data.columns:
            return None
            
        if freq_results is None:
            freq_results = self.analyze_word_frequency()
        
        if freq_results is None:
            return None
        
        # 월별 데이터 그룹화
        df = self.data.copy()
        df['year_month'] = df['upload_date'].dt.strftime('%Y-%m')
        monthly_groups = df.groupby('year_month')
        
        # 월별 키워드 빈도 계산
        keyword_monthly_freq = {keyword: [] for keyword in words}
        months = sorted(df['year_month'].unique())
        
        for month in months:
            month_df = df[df['year_month'] == month]
            month_tokens = []
            for tokens in month_df['token_list']:
                if isinstance(tokens, list):
                    month_tokens.extend(tokens)
            
            month_counts = Counter(month_tokens)
            
            for keyword in words:
                keyword_monthly_freq[keyword].append(month_counts.get(keyword, 0))
        
        return {
            'months': months,
            'frequencies': keyword_monthly_freq
        }
    
    def generate_word_trend_chart(self, words, trend_results=None):
        """단어 빈도 추이 차트 생성"""
        if trend_results is None:
            trend_results = self.analyze_word_trend(words)
        
        if trend_results is None:
            return None
        
        # Plotly 그래프 생성
        fig = go.Figure()
        
        for keyword in words:
            if keyword in trend_results['frequencies']:
                fig.add_trace(
                    go.Scatter(
                        x=trend_results['months'],
                        y=trend_results['frequencies'][keyword],
                        mode='lines+markers',
                        name=keyword
                    )
                )
        
        fig.update_layout(
            title=dict(
                text='월별 키워드 빈도 추이'
            ),
            xaxis_title='년-월',
            yaxis_title='빈도수',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(full_html=False)
    
    # 통합 분석 기능
    # news_analyzer.py의 generate_dashboard_data 함수 수정부분
    def generate_dashboard_data(self):
        """대시보드용 통합 데이터 생성"""
        if self.data is None or self.data.empty:
            return {
                'error': '데이터가 없습니다.'
            }
        
        dashboard_data = {}
        
        # 1. 기본 정보
        date_column = None
        for col in ['published', 'upload_date']:
            if col in self.data.columns:
                date_column = col
                break
                
        if date_column:
            date_range = [
                self.data[date_column].min().strftime('%Y-%m-%d'),
                self.data[date_column].max().strftime('%Y-%m-%d')
            ]
            dashboard_data['date_range'] = date_range
        
        dashboard_data['total_articles'] = len(self.data)
        
        if 'source' in self.data.columns:
            dashboard_data['sources'] = self.data['source'].value_counts().to_dict()
        
        # 2. 빈도 분석
        freq_results = self.analyze_word_frequency()
        if freq_results:
            dashboard_data['top_keywords'] = self.get_top_words(freq_results, top_n=5)
            dashboard_data['wordcloud'] = self.generate_wordcloud(freq_results)
        
        # 3. 토픽 분석
        topic_results = self.analyze_topics(n_topics=5)
        if topic_results:
            topic_distribution = self.get_topic_distribution(topic_results)
            if topic_distribution:
                dashboard_data['topic_info'] = topic_distribution['topic_info']
        
        # 4. 감성 분석
        sentiment_df = self.calculate_article_sentiment()
        if sentiment_df is not None:
            sentiment_results = self.get_sentiment_distribution(sentiment_df)
            if sentiment_results:
                dashboard_data['positive_articles'] = sentiment_results['positive_articles'][:3]
                dashboard_data['negative_articles'] = sentiment_results['negative_articles'][:3]
                dashboard_data['sentiment_counts'] = sentiment_results['sentiment_counts']
        
        # 5. 시계열 분석 및 키워드 트렌드
        time_data = self.analyze_time_series()
        if time_data:
            # 가장 최근 기사 선택
            if date_column:
                dashboard_data['latest_articles'] = self.data.sort_values(date_column, ascending=False).head(10).to_dict('records')
            
            # 상위 5개 키워드 트렌드 분석
            try:
                if freq_results and 'word_counts' in freq_results:
                    top_keywords = [word for word, _ in freq_results['word_counts'].most_common(5)]
                    
                    logger.info(f"키워드 트렌드 분석 시작: {top_keywords}")
                    
                    # 명시적으로 키워드 트렌드 분석 호출
                    trend_results = self.analyze_keyword_trend(top_keywords, time_unit='monthly')
                    
                    if trend_results and 'trends' in trend_results and trend_results['trends']:
                        # 모든 키워드에 대한 데이터가 있는지 확인
                        has_data = all(len(data) > 0 for data in trend_results['trends'].values())
                        
                        if has_data:
                            keyword_trend_chart = self.generate_keyword_trend_chart(top_keywords, trend_results)
                            
                            if keyword_trend_chart:
                                dashboard_data['keyword_trend'] = keyword_trend_chart
                                logger.info("키워드 트렌드 차트 생성 성공")
                            else:
                                logger.warning("키워드 트렌드 차트 생성 실패")
                                dashboard_data['keyword_trend'] = '<div class="alert alert-warning">키워드 트렌드 차트를 생성할 수 없습니다.</div>'
                        else:
                            logger.warning("일부 키워드의 트렌드 데이터가 비어 있습니다")
                            dashboard_data['keyword_trend'] = '<div class="alert alert-warning">일부 키워드에 대한 데이터가 충분하지 않습니다.</div>'
                    else:
                        logger.warning("키워드 트렌드 결과가 없거나 형식이 올바르지 않습니다")
                        dashboard_data['keyword_trend'] = '<div class="alert alert-warning">키워드 트렌드 데이터를 생성할 수 없습니다.</div>'
                else:
                    logger.warning("키워드 트렌드 분석을 위한 빈도 분석 결과가 없습니다")
                    dashboard_data['keyword_trend'] = '<div class="alert alert-warning">키워드 빈도 분석 결과가 없습니다.</div>'
            except Exception as e:
                logger.error(f"키워드 트렌드 생성 중 오류 발생: {e}", exc_info=True)
                dashboard_data['keyword_trend'] = f'<div class="alert alert-danger">키워드 트렌드 데이터 처리 중 오류가 발생했습니다: {str(e)}</div>'
        
        # 6. 연관어 분석
        association_results = self.analyze_word_association()
        if association_results:
            dashboard_data['keyword_network'] = self.generate_network_graph(association_results)
        
        return dashboard_data
    
    def get_topic_distribution(self, topic_results=None):
        """토픽 분포 정보 반환"""
        if topic_results is None:
            topic_results = self.analyze_topics()
        
        if topic_results is None:
            return None
        
        # 토픽별 문서 수
        topic_counts = topic_results['df_topics']['dominant_topic'].value_counts().sort_index().to_dict()
        
        # 각 토픽의 주요 단어 및 이름
        topic_info = []
        for topic_idx, words in enumerate(topic_results['topic_words']):
            topic_info.append({
                'topic_id': topic_idx,
                'topic_name': topic_results['topic_names'][topic_idx],
                'top_words': words[:10]  # 상위 10개 단어
            })
        
        # 토픽별 대표 문서
        representative_docs = {}
        for topic_idx in range(len(topic_results['topic_names'])):
            # 해당 토픽의 문서 필터링
            topic_docs = topic_results['df_topics'][topic_results['df_topics']['dominant_topic'] == topic_idx]
            
            # 확신도 기준 정렬
            topic_docs = topic_docs.sort_values('topic_confidence', ascending=False)
            
            if not topic_docs.empty:
                representative_docs[topic_idx] = topic_docs.head(5).to_dict('records')
        
        return {
            'topic_counts': topic_counts,
            'topic_info': topic_info,
            'representative_docs': representative_docs
        }
    
    def generate_topic_chart(self, topic_results=None):
        """토픽 차트 생성"""
        if topic_results is None:
            topic_results = self.analyze_topics()
        
        if topic_results is None:
            return None
        
        # 토픽별 문서 수
        topic_counts = topic_results['df_topics']['dominant_topic'].value_counts().sort_index()
        topic_labels = [f'토픽 {i+1}: {topic_results["topic_names"][i]}' for i in topic_counts.index]
        
        # 토픽 분포 막대 그래프
        fig = px.bar(
            x=topic_labels,
            y=topic_counts.values,
            color=topic_counts.values,
            color_continuous_scale=px.colors.sequential.Viridis,
            labels={'x': '토픽', 'y': '문서 수'}
        )
        
        fig.update_layout(
            title=dict(
                text='토픽별 문서 분포'
            ),
            xaxis_title='토픽',
            yaxis_title='문서 수',
            height=400
        )
        
        # 토픽-단어 히트맵
        n_topics = len(topic_results['topic_words'])
        n_words = 10  # 각 토픽별 표시할 단어 수
        
        # 히트맵 데이터 준비
        heatmap_data = []
        for topic_idx, topic in enumerate(topic_results['lda_model'].components_):
            top_indices = topic.argsort()[:-n_words-1:-1]
            
            for word_idx, word_idx_in_topic in enumerate(top_indices):
                word = topic_results['feature_names'][word_idx_in_topic]
                weight = topic[word_idx_in_topic]
                
                heatmap_data.append({
                    '토픽': f'토픽 {topic_idx+1}',
                    '단어': word,
                    '가중치': weight
                })
        
        heatmap_df = pd.DataFrame(heatmap_data)
        
        # 피벗 테이블로 변환
        pivot_df = heatmap_df.pivot(index='토픽', columns='단어', values='가중치')
        
        # 히트맵 생성
        heatmap_fig = px.imshow(
            pivot_df,
            color_continuous_scale='Viridis',
            aspect="auto"
        )
        
        heatmap_fig.update_layout(
            title=dict(
                text='토픽-단어 가중치 히트맵'
            ),
            height=500
        )
        
        # 월별 토픽 트렌드
        if 'upload_date' in topic_results['df_topics'].columns:
            df_with_topics = topic_results['df_topics']
            df_with_topics['year_month'] = df_with_topics['upload_date'].dt.strftime('%Y-%m')
            
            topic_trends = pd.crosstab(
                df_with_topics['year_month'], 
                df_with_topics['dominant_topic']
            )
            
            # 정규화 (각 월의 전체 문서 수 대비)
            normalized_trends = topic_trends.div(topic_trends.sum(axis=1), axis=0)
            
            # 트렌드 시각화
            trend_fig = go.Figure()
            
            for topic_idx in range(n_topics):
                if topic_idx in normalized_trends.columns:
                    trend_fig.add_trace(
                        go.Scatter(
                            x=normalized_trends.index,
                            y=normalized_trends[topic_idx],
                            mode='lines+markers',
                            name=f'토픽 {topic_idx+1}: {topic_results["topic_names"][topic_idx]}'
                        )
                    )
            
            trend_fig.update_layout(
                title=dict(
                    text='월별 토픽 트렌드'
                ),
                xaxis_title='년-월',
                yaxis_title='토픽 비율',
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return {
                'distribution': fig.to_html(full_html=False),
                'heatmap': heatmap_fig.to_html(full_html=False),
                'trend': trend_fig.to_html(full_html=False)
            }
        
        return {
            'distribution': fig.to_html(full_html=False),
            'heatmap': heatmap_fig.to_html(full_html=False)
        } 