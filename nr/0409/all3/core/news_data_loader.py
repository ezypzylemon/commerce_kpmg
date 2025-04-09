from sqlalchemy import create_engine
import pandas as pd
import logging
from datetime import datetime, timedelta
import mysql.connector
from .config import NEWS_DB_CONFIG, PERIOD_DAYS
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from collections import Counter
import networkx as nx
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import os
import matplotlib.font_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsDataLoader:
    """뉴스 데이터 로드 및 처리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.data = None
        self.period = '7일'
        self.db_connection = None
        self.cursor = None
        self.mysql_config = NEWS_DB_CONFIG
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
            logging.info("뉴스 데이터베이스 연결 성공")
        except Exception as e:
            logging.error(f"뉴스 데이터베이스 연결 실패: {e}")
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
                    a.id,
                    a.keyword,
                    a.title,
                    a.content,
                    a.published,
                    a.source,
                    t.tokens
                FROM knews_articles a
                LEFT JOIN tokenised t ON a.id = t.id
                WHERE a.published >= %s
                ORDER BY a.published DESC
            """
            
            self.cursor.execute(query, (start_date,))
            rows = self.cursor.fetchall()
            
            if not rows:
                logging.warning(f"{period} 기간 동안 뉴스 데이터가 없습니다.")
                self.data = pd.DataFrame(columns=['id', 'keyword', 'title', 'content', 'published', 'source', 'tokens'])
                return self.data
            
            # DataFrame 생성
            self.data = pd.DataFrame(rows)
            
            # tokens 컬럼의 JSON 문자열을 리스트로 변환
            self.data['tokens'] = self.data['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            # published를 datetime으로 변환
            self.data['published'] = pd.to_datetime(self.data['published'])
            
            logging.info(f"뉴스 데이터 로드 완료: {len(self.data)}개 문서")
            return self.data
            
        except Exception as e:
            logging.error(f"뉴스 데이터 로드 중 오류 발생: {e}")
            self.data = pd.DataFrame(columns=['id', 'keyword', 'title', 'content', 'published', 'source', 'tokens'])
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
                    a.id,
                    a.keyword,
                    a.title,
                    a.content,
                    a.published,
                    a.source,
                    t.tokens
                FROM knews_articles a
                LEFT JOIN tokenised t ON a.id = t.id
                WHERE a.published BETWEEN %s AND %s
                ORDER BY a.published DESC
            """
            
            self.cursor.execute(query, (start_date, end_date))
            rows = self.cursor.fetchall()
            
            if not rows:
                logging.warning(f"{start_date}부터 {end_date}까지의 데이터가 없습니다.")
                self.data = pd.DataFrame(columns=['id', 'keyword', 'title', 'content', 'published', 'source', 'tokens'])
                return self.data
            
            # DataFrame 생성
            self.data = pd.DataFrame(rows)
            
            # tokens 컬럼의 JSON 문자열을 리스트로 변환
            self.data['tokens'] = self.data['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            # published를 datetime으로 변환
            self.data['published'] = pd.to_datetime(self.data['published'])
            
            logging.info(f"뉴스 데이터 로드 완료: {len(self.data)}개 문서")
            return self.data
            
        except Exception as e:
            logging.error(f"뉴스 데이터 로드 중 오류 발생: {e}")
            self.data = pd.DataFrame(columns=['id', 'keyword', 'title', 'content', 'published', 'source', 'tokens'])
            return self.data

    def generate_visualizations(self, data=None):
        """시각화 생성"""
        try:
            if data is None:
                data = self.data

            if data is None or data.empty:
                return None

            visualizations = {}

            # 1. 단어 빈도 분석 및 워드클라우드
            word_freq = self.analyze_word_frequency(data)
            visualizations['wordcloud'] = self.generate_wordcloud(word_freq)

            # 2. 시계열 분석
            visualizations['time_series'] = self.analyze_time_series(data)

            # 3. 토픽 모델링
            visualizations['topics'] = self.analyze_topics(data)

            # 4. 단어 연관성 네트워크
            visualizations['network'] = self.analyze_word_association(data)

            # 5. TF-IDF 분석
            visualizations['tfidf'] = self.analyze_tfidf(data)

            return visualizations

        except Exception as e:
            logger.error(f"시각화 생성 중 오류 발생: {e}")
            return None

    def analyze_word_frequency(self, data):
        """단어 빈도 분석"""
        try:
            all_tokens = []
            for tokens in data['tokens']:
                if isinstance(tokens, list):
                    all_tokens.extend(tokens)
            
            word_freq = Counter(all_tokens)
            return word_freq

        except Exception as e:
            logger.error(f"단어 빈도 분석 중 오류 발생: {e}")
            return Counter()

    def generate_wordcloud(self, word_freq):
        """워드클라우드 생성"""
        try:
            if not word_freq:
                return None

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
            font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break

            # 폰트를 찾지 못한 경우 기본 폰트 사용
            if font_path is None:
                font_path = matplotlib.font_manager.findfont(
                    matplotlib.font_manager.FontProperties(family=['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'Gulim'])
                )

            # 워드클라우드 생성
            wordcloud = WordCloud(
                font_path=font_path,
                width=800,
                height=400,
                background_color='white',
                prefer_horizontal=0.7,
                min_font_size=10,
                max_font_size=100,
                relative_scaling=0.5
            ).generate_from_frequencies(word_freq)

            # 이미지로 변환
            plt.figure(figsize=(10, 5))
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

        except Exception as e:
            logger.error(f"워드클라우드 생성 중 오류 발생: {e}")
            return None

    def analyze_time_series(self, data):
        """시계열 분석"""
        try:
            # 일별 기사 수 집계
            daily_counts = data.groupby(data['published'].dt.date).size()

            # Plotly 그래프 생성
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_counts.index,
                y=daily_counts.values,
                mode='lines+markers',
                name='일별 기사 수'
            ))

            fig.update_layout(
                title='일별 뉴스 기사 수',
                xaxis_title='날짜',
                yaxis_title='기사 수',
                template='plotly_white'
            )

            return fig.to_html(full_html=False)

        except Exception as e:
            logger.error(f"시계열 분석 중 오류 발생: {e}")
            return None

    def analyze_topics(self, data, num_topics=5):
        """토픽 모델링"""
        try:
            # TF-IDF 벡터화
            vectorizer = TfidfVectorizer(max_features=1000)
            tfidf = vectorizer.fit_transform([' '.join(tokens) for tokens in data['tokens']])

            # LDA 수행
            lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
            lda.fit(tfidf)

            # 토픽별 주요 단어 추출
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            for topic_idx, topic in enumerate(lda.components_):
                top_words = [feature_names[i] for i in topic.argsort()[:-10-1:-1]]
                topics.append({
                    'topic': f'토픽 {topic_idx + 1}',
                    'words': top_words
                })

            # Plotly 그래프 생성
            fig = make_subplots(rows=num_topics, cols=1, subplot_titles=[t['topic'] for t in topics])

            for idx, topic in enumerate(topics, 1):
                fig.add_trace(
                    go.Bar(x=topic['words'], y=lda.components_[idx-1][np.argsort(lda.components_[idx-1])[-10:]]),
                    row=idx, col=1
                )

            fig.update_layout(height=200*num_topics, showlegend=False)

            return fig.to_html(full_html=False)

        except Exception as e:
            logger.error(f"토픽 모델링 중 오류 발생: {e}")
            return None

    def analyze_word_association(self, data):
        """단어 연관성 분석"""
        try:
            # 동시 출현 단어 쌍 계산
            word_pairs = []
            for tokens in data['tokens']:
                if isinstance(tokens, list):
                    for i, word1 in enumerate(tokens):
                        for word2 in tokens[i+1:]:
                            word_pairs.append(tuple(sorted([word1, word2])))

            # 동시 출현 빈도 계산
            pair_freq = Counter(word_pairs)

            # 네트워크 그래프 생성
            G = nx.Graph()
            for (word1, word2), freq in pair_freq.most_common(50):
                G.add_edge(word1, word2, weight=freq)

            # 노드 크기 계산
            node_freq = Counter([word for pair in pair_freq.keys() for word in pair])
            nx.set_node_attributes(G, node_freq, 'size')

            # Plotly 그래프 생성
            pos = nx.spring_layout(G)
            
            edge_trace = go.Scatter(
                x=[], y=[],
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')

            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_trace['x'] += (x0, x1, None)
                edge_trace['y'] += (y0, y1, None)

            node_trace = go.Scatter(
                x=[], y=[],
                text=[],
                mode='markers+text',
                hoverinfo='text',
                marker=dict(
                    showscale=True,
                    colorscale='YlOrRd',
                    size=[],
                ))

            for node in G.nodes():
                x, y = pos[node]
                node_trace['x'] += (x,)
                node_trace['y'] += (y,)
                node_trace['text'] += (node,)
                node_trace['marker']['size'] += (G.nodes[node]['size']*2,)

            fig = go.Figure(data=[edge_trace, node_trace],
                          layout=go.Layout(
                              showlegend=False,
                              hovermode='closest',
                              margin=dict(b=20,l=5,r=5,t=40),
                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              height=600
                          ))

            return fig.to_html(full_html=False)

        except Exception as e:
            logger.error(f"단어 연관성 분석 중 오류 발생: {e}")
            return None

    def analyze_tfidf(self, data):
        """TF-IDF 분석"""
        try:
            # TF-IDF 벡터화
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([' '.join(tokens) for tokens in data['tokens']])

            # 단어별 평균 TF-IDF 점수 계산
            mean_tfidf = np.array(tfidf_matrix.mean(axis=0)).flatten()
            feature_names = vectorizer.get_feature_names_out()

            # 상위 20개 단어 선택
            top_indices = mean_tfidf.argsort()[-20:][::-1]
            top_words = feature_names[top_indices]
            top_scores = mean_tfidf[top_indices]

            # Plotly 그래프 생성
            fig = go.Figure(data=[
                go.Bar(
                    x=top_scores,
                    y=top_words,
                    orientation='h'
                )
            ])

            fig.update_layout(
                title='상위 20개 중요 단어 (TF-IDF)',
                xaxis_title='TF-IDF 점수',
                yaxis_title='단어',
                height=600
            )

            return fig.to_html(full_html=False)

        except Exception as e:
            logger.error(f"TF-IDF 분석 중 오류 발생: {e}")
            return None

    def __del__(self):
        """소멸자: 데이터베이스 연결 종료"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.db_connection:
                self.db_connection.close()
        except Exception as e:
            logging.error(f"데이터베이스 연결 종료 중 오류 발생: {e}") 