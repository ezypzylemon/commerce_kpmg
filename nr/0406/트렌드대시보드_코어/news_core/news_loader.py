"""
뉴스 데이터 로더 모듈
뉴스 데이터를 불러오고 처리하는 기능을 담당합니다.
"""

import mysql.connector
import pandas as pd
import json
import logging
import os
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
import plotly.graph_objects as go
import networkx as nx

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsDataLoader:
    """뉴스 데이터 로드 및 처리 클래스"""
    
    def __init__(self, mysql_config):
        """초기화"""
        self.period = '7일'
        self.mysql_config = mysql_config
        self.positive_words = set(['좋은', '훌륭한', '우수한', '성공', '혁신', '성장', '발전', '향상', '개선'])
        self.negative_words = set(['나쁜', '부족한', '실패', '하락', '위기', '문제', '악화', '감소', '위험'])
    
    def _get_days_from_period(self, period):
        """기간을 일수로 변환"""
        days = 0
        if period.endswith('일'):
            days = int(period.replace('일', ''))
        elif period == '1주일':
            days = 7
        elif period == '2주':
            days = 14
        elif period == '3주':
            days = 21
        elif period == '1달' or period == '1개월':
            days = 30
        elif period == '3달' or period == '3개월':
            days = 90
        elif period == '6개월':
            days = 180
        elif period == '1년':
            days = 365
        else:
            days = 7  # 기본값
        return days
    
    def set_period(self, period):
        """기간 설정"""
        self.period = period
        return self
        
    def load_news_data(self):
        """뉴스 데이터 로드"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            
            # 기간에 따른 날짜 범위 계산
            days = self._get_days_from_period(self.period)
                
            # knews_articles와 tokenised 테이블 조인하여 데이터 가져오기
            query = """
                SELECT k.title, k.content, k.link, k.published as upload_date, t.tokens
                FROM dump_migration.knews_articles k
                LEFT JOIN dump_migration.tokenised t ON k.id = t.id
                WHERE k.published >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY k.published DESC
            """
            
            df = pd.read_sql(query, conn, params=[days])
            conn.close()
            
            if len(df) == 0:
                logger.warning(f"{self.period} 기간 동안 뉴스 데이터가 없습니다.")
                return None
            
            # 토큰 데이터 전처리
            df['tokens'] = df['tokens'].apply(lambda x: eval(x) if isinstance(x, str) else [])
            
            logger.info(f"뉴스 데이터 로드 완료: {len(df)}개 기사")
            return df
            
        except Exception as e:
            logger.error(f"뉴스 데이터 로드 중 오류 발생: {str(e)}")
            return None
    
    def get_latest_articles(self, df, count=5):
        """최신 뉴스 기사 가져오기"""
        if df is None or df.empty:
            return []
        
        latest = df.head(count)[['title', 'content', 'link', 'upload_date']].to_dict('records')
        return latest
    
    def get_top_keywords(self, df, count=5):
        """가장 많이 언급된 키워드 추출"""
        if df is None or df.empty:
            return []
            
        all_tokens = []
        for tokens in df['tokens']:
            if isinstance(tokens, list):
                all_tokens.extend(tokens)
                    
        word_counts = Counter(all_tokens)
        return word_counts.most_common(count)
    
    def analyze_time_trend(self):
        """시간별 트렌드 분석"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 기간에 따른 날짜 범위 계산
            days = self._get_days_from_period(self.period)
            
            # 토큰 데이터 조회
            query = """
                SELECT tokens, upload_date
                FROM dump_migration.tokenised
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
                    count = sum(1 for tokens in month_data['tokens'] if tokens and keyword in (json.loads(tokens) if isinstance(tokens, str) else tokens))
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

    def generate_network_graph(self):
        """키워드 네트워크 그래프 생성"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 기간에 따른 날짜 범위 계산
            days = self._get_days_from_period(self.period)
            
            # 토큰 데이터 조회
            query = """
                SELECT tokens
                FROM dump_migration.tokenised
                WHERE upload_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            cursor.execute(query, (days,))
            rows = cursor.fetchall()
            
            # 토큰 데이터 처리
            all_tokens = []
            for row in rows:
                if row['tokens']:
                    tokens = json.loads(row['tokens']) if isinstance(row['tokens'], str) else row['tokens']
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
                    tokens = json.loads(row['tokens']) if isinstance(row['tokens'], str) else row['tokens']
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

    def generate_tfidf_wordcloud(self):
        """TF-IDF 기반 워드클라우드 생성"""
        try:
            # MySQL 연결
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 기간에 따른 날짜 범위 계산
            days = self._get_days_from_period(self.period)
            
            # 토큰 데이터 조회
            query = """
                SELECT tokens
                FROM dump_migration.tokenised
                WHERE upload_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            cursor.execute(query, (days,))
            rows = cursor.fetchall()
            
            # 문서-토큰 데이터 준비
            documents = []
            for row in rows:
                if row['tokens']:
                    try:
                        tokens = json.loads(row['tokens']) if isinstance(row['tokens'], str) else row['tokens']
                        if isinstance(tokens, list):
                            # 토큰 리스트를 공백으로 구분된 문자열로 변환
                            documents.append(' '.join(tokens))
                    except (json.JSONDecodeError, TypeError):
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
    
    def analyze_sentiment(self, df):
        """감성 분석 수행"""
        try:
            if df is None or df.empty:
                return {'positive_articles': [], 'negative_articles': []}
                
            # 기사별 감성 점수 계산
            sentiment_scores = []
            for idx, row in df.iterrows():
                tokens = row['tokens']
                if not isinstance(tokens, list):
                    continue
                
                pos_count = sum(1 for token in tokens if token in self.positive_words)
                neg_count = sum(1 for token in tokens if token in self.negative_words)
                
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
            logger.error(f"감성 분석 중 오류 발생: {str(e)}")
            return {'positive_articles': [], 'negative_articles': []} 