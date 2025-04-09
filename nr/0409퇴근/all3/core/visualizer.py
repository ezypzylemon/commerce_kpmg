import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (서버 환경용)
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import numpy as np
import networkx as nx
from wordcloud import WordCloud
from datetime import datetime, timedelta
import pandas as pd
import os
from io import BytesIO
import base64
from flask import url_for
import logging
from collections import Counter, defaultdict
from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
import platform
import plotly.graph_objects as go
import plotly.express as px

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 색상 팔레트 - 흰색 배경
COLORS = {
    'bg_dark': '#ffffff',       # 배경색을 흰색으로 변경
    'card_bg': '#ffffff',       # 카드 배경색
    'primary': '#36D6BE',       # 주요 색상
    'teal': '#36D6BE',          # 주요 청록색 
    'teal_gradient': '#8AEFDB', # 청록색 그라데이션 끝
    'purple': '#6B5AED',        # 보라색
    'red': '#FF5A5A',           # 빨간색
    'blue': '#4A78E1',          # 파란색
    'orange': '#FFA26B',        # 주황색
    'text': '#1e2b3c',          # 텍스트 색상
    'text_dark': '#000000',     # 어두운 텍스트 색상 (검은색으로 변경)
    'text_secondary': '#6c7293',# 보조 텍스트 색상
    'light_bg': '#f8f9fc',      # 연한 배경색
    'border': '#e4e9f2',        # 테두리 색상
}

def get_font_path():
    """폰트 경로 반환"""
    system = platform.system()
    if system == "Darwin":  # macOS
        return "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    elif system == "Windows":
        return "C:/Windows/Fonts/malgun.ttf"
    return None

FONT_PATH = get_font_path()
PLOTLY_FONT = "AppleSDGothicNeo" if platform.system() == "Darwin" else "Malgun Gothic"

plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# Stopwords 정의
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

def remove_stopwords(tokens):
    """불용어 제거"""
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

def ensure_static_dirs():
    """정적 디렉토리 생성"""
    static_dir = os.path.join('static')
    img_dir = os.path.join(static_dir, 'images')
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    
    return img_dir

def generate_network_graph(data):
    """네트워크 그래프 생성"""
    try:
        G = nx.Graph()
        
        # 노드 추가
        for node in data['nodes']:
            G.add_node(node)
        
        # 엣지 추가
        for edge in data['edges']:
            G.add_edge(edge[0], edge[1])
        
        # 레이아웃 계산
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # 엣지 트레이스
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # 노드 트레이스
        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=20,
                color=[len(list(G.neighbors(node))) for node in G.nodes()],
                colorbar=dict(
                    title='연결 수',
                    thickness=15,
                    x=1.1
                )
            ),
            textfont=dict(family=PLOTLY_FONT, color=COLORS['text_dark'])
        )
        
        # 레이아웃 생성
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='브랜드의 연관어 네트워크',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           template='plotly_dark',
                           font=dict(family=PLOTLY_FONT, color=COLORS['text_dark']),
                           plot_bgcolor='rgba(0,0,0,0)',
                           paper_bgcolor='rgba(0,0,0,0)'
                       ))
        
        return fig.to_html(full_html=False)
    
    except Exception as e:
        print(f"네트워크 그래프 생성 오류: {e}")
        return None

def generate_category_chart(data):
    """카테고리 차트 생성"""
    try:
        fig = go.Figure(data=[go.Pie(
            labels=data['categories'],
            values=data['values'],
            hole=.3,
            textinfo='label+percent',
            textposition='inside',
            textfont=dict(family=PLOTLY_FONT, color=COLORS['text_dark'])
        )])
        
        fig.update_layout(
            title='카테고리별 분포',
            template='plotly_dark',
            font=dict(family=PLOTLY_FONT, color=COLORS['text_dark']),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True
        )
        
        return fig.to_html(full_html=False)
    
    except Exception as e:
        print(f"카테고리 차트 생성 오류: {e}")
        return None

def generate_wordcloud(word_freq):
    """워드클라우드 생성"""
    try:
        wordcloud = WordCloud(
            font_path=FONT_PATH,
            width=800,
            height=400,
            background_color='white',  # 배경색을 흰색으로 변경
            colormap='plasma',         # 텍스트 색상을 더 진하게 보이는 컬러맵으로 변경
            contour_width=1,           # 단어 주변에 경계선 추가
            contour_color='black',     # 경계선 색상
            max_font_size=100,         # 최대 폰트 크기
            min_font_size=10,          # 최소 폰트 크기
            prefer_horizontal=0.9      # 가로 방향 단어 비율 (가독성 향상)
        ).generate_from_frequencies(word_freq)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=300)  # 해상도 향상
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        
        return f'<div style="text-align: center;"><img src="data:image/png;base64,{graphic}" style="max-width:100%;"/></div>'
    
    except Exception as e:
        print(f"워드클라우드 생성 오류: {e}")
        return None

def generate_trend_chart(data, selected_magazines, focus_keywords):
    """트렌드 차트 생성"""
    try:
        # 데이터가 비어있는 경우 처리
        if data.empty:
            logger.warning("트렌드 차트 생성을 위한 데이터가 없습니다.")
            return None

        # 날짜 형식 변환
        data['upload_date'] = pd.to_datetime(data['upload_date'])

        # Plotly 그래프 생성
        fig = go.Figure()

        # 각 키워드별로 매거진 데이터 추가
        for keyword in focus_keywords:
            keyword_data = data[data['keyword'] == keyword]
            for magazine in selected_magazines:
                magazine_data = keyword_data[keyword_data['magazine_name'] == magazine]
                if not magazine_data.empty:
                    fig.add_trace(go.Scatter(
                        x=magazine_data['upload_date'],
                        y=magazine_data['count'],
                        name=f'{magazine} - {keyword}',
                        mode='lines+markers',
                        line=dict(width=2),
                        marker=dict(size=6),
                    ))

        # 레이아웃 설정
        fig.update_layout(
            title='키워드별 매거진 언급 추이',
            xaxis_title='날짜',
            yaxis_title='언급 횟수',
            template='plotly_dark',
            font=dict(family='Noto Sans KR', color=COLORS['text_dark']),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.3)',
                font=dict(color=COLORS['text_dark'])
            )
        )

        # x축 날짜 포맷 설정
        fig.update_xaxes(
            tickformat='%Y-%m-%d',
            gridcolor='rgba(128,128,128,0.1)',
            zerolinecolor='rgba(128,128,128,0.2)',
            tickfont=dict(color=COLORS['text_dark'])
        )

        # y축 설정
        fig.update_yaxes(
            gridcolor='rgba(128,128,128,0.1)',
            zerolinecolor='rgba(128,128,128,0.2)',
            tickfont=dict(color=COLORS['text_dark'])
        )

        return fig.to_html(full_html=False, include_plotlyjs=True)

    except Exception as e:
        logger.error(f"트렌드 차트 생성 오류: {e}")
        return None

def generate_tfidf_chart(data):
    """TF-IDF 차트 생성"""
    try:
        # TF-IDF 계산
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([' '.join(tokens) for tokens in data['tokens']])
        feature_names = vectorizer.get_feature_names_out()
        
        # 평균 TF-IDF 값 계산
        mean_tfidf = np.array(tfidf_matrix.mean(axis=0)).flatten()
        
        # 상위 20개 키워드 선택
        top_indices = mean_tfidf.argsort()[-20:][::-1]
        top_keywords = [feature_names[i] for i in top_indices]
        top_scores = [mean_tfidf[i] for i in top_indices]
        
        # Plotly 바 차트 생성
        fig = go.Figure(data=[
            go.Bar(
                x=top_keywords,
                y=top_scores,
                marker_color=COLORS['primary']
            )
        ])
        
        fig.update_layout(
            title="TF-IDF 상위 키워드",
            template='plotly_dark',
            font=dict(family=PLOTLY_FONT, color=COLORS['text_dark']),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="키워드",
            yaxis_title="TF-IDF 점수",
            showlegend=False
        )
        
        # x축과 y축 텍스트 색상 설정
        fig.update_xaxes(tickfont=dict(color=COLORS['text_dark']))
        fig.update_yaxes(tickfont=dict(color=COLORS['text_dark']))
        
        return fig.to_html(full_html=False)
    
    except Exception as e:
        print(f"TF-IDF 차트 생성 오류: {e}")
        return None

# 카테고리별 키워드 정의
CATEGORY_KEYWORDS = {
    '의류': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
    '신발': ['구두', '샌들', '부츠', '스니커즈', '로퍼', '플립플롭', '슬리퍼', '펌프스'],
    '액세서리': ['목걸이', '귀걸이', '반지', '브레이슬릿', '시계', '선글라스', '스카프', '벨트', '가방'],
    '가방': ['백팩', '토트백', '크로스백', '클러치', '숄더백', '에코백'],
    '기타': ['화장품', '향수', '주얼리', '선글라스', '시계']
}