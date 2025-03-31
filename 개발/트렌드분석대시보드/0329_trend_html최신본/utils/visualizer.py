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
import io
import base64
from flask import url_for
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 색상 팔레트 - 흰색 배경
COLORS = {
    'bg_dark': '#ffffff',       # 배경색을 흰색으로 변경
    'card_bg': '#ffffff',       # 카드 배경색
    'teal': '#36D6BE',          # 주요 청록색 
    'teal_gradient': '#8AEFDB', # 청록색 그라데이션 끝
    'purple': '#6B5AED',        # 보라색
    'red': '#FF5A5A',           # 빨간색
    'blue': '#4A78E1',          # 파란색
    'orange': '#FFA26B',        # 주황색
    'text_dark': '#1e2b3c',     # 어두운 텍스트 색상
    'text_secondary': '#6c7293',# 보조 텍스트 색상
    'light_bg': '#f8f9fc',      # 연한 배경색
    'border': '#e4e9f2',        # 테두리 색상
}

class Visualizer:
    """시각화 기능을 제공하는 클래스"""
    
    @staticmethod
    def get_font_path():
        """OS별 폰트 경로 자동 설정"""
        import platform
        
        system = platform.system()
        if system == "Windows":
            return "C:/Windows/Fonts/malgun.ttf"
        elif system == "Darwin":  # macOS
            mac_fonts = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleGothic.ttf",
                "/Library/Fonts/NanumGothic.ttf"
            ]
            for path in mac_fonts:
                if os.path.exists(path):
                    return path
            logger.warning("macOS에서 한글 폰트를 찾을 수 없습니다.")
        elif system == "Linux":
            linux_fonts = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]
            for path in linux_fonts:
                if os.path.exists(path):
                    return path
            logger.warning("Linux에서 기본 폰트를 찾을 수 없습니다.")
        
        # 기본 폰트 반환
        return None
    
    @staticmethod
    def ensure_static_dirs():
        """정적 디렉토리 확인 및 생성"""
        img_dir = os.path.join('static', 'images')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        return img_dir
    
    @staticmethod
    def create_gradient_color(c1, c2, n=100):
        """두 색상 사이의 그라데이션 색상 생성"""
        c1_rgb = mcolors.to_rgb(c1)
        c2_rgb = mcolors.to_rgb(c2)
        
        mix_pcts = [i/(n-1) for i in range(n)]
        rgb_colors = [tuple(x*(1-pct) + y*pct for x, y in zip(c1_rgb, c2_rgb)) for pct in mix_pcts]
        
        return rgb_colors
    
    @staticmethod
    def apply_modern_style(ax, title=None):
        """모던 스타일을 차트에 적용"""
        # 배경색 설정
        ax.set_facecolor(COLORS['card_bg'])
        
        # 그리드 스타일 설정
        ax.grid(True, linestyle='--', alpha=0.2, color=COLORS['text_secondary'], axis='y')
        ax.set_axisbelow(True)  # 그리드를 데이터 아래에 배치
        
        # 테두리 제거
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # 틱 설정
        ax.tick_params(axis='x', colors=COLORS['text_secondary'], length=0)
        ax.tick_params(axis='y', colors=COLORS['text_secondary'], length=0)
        
        # x축 레이블 간격 설정
        if len(ax.get_xticklabels()) > 10:
            for i, label in enumerate(ax.get_xticklabels()):
                if i % 2 != 0:
                    label.set_visible(False)
        
        # 타이틀 설정
        if title:
            ax.set_title(title, fontsize=15, fontweight='bold', color=COLORS['text_dark'], pad=15)
        
        # 레이블 설정
        if ax.get_xlabel():
            ax.set_xlabel(ax.get_xlabel(), fontsize=12, color=COLORS['text_secondary'], labelpad=10)
        if ax.get_ylabel():
            ax.set_ylabel(ax.get_ylabel(), fontsize=12, color=COLORS['text_secondary'], labelpad=10)
    
    @staticmethod
    def generate_network_graph(df, period):
        """
        키워드 네트워크 그래프 생성
        
        Args:
            df (DataFrame): 토큰화된 데이터
            period (str): 기간 설정
            
        Returns:
            str: 그래프 이미지 URL
        """
        try:
            from analyzer import Analyzer
            
            # 네트워크 데이터 생성
            graph_data = Analyzer.generate_network_data(df)
            
            if not graph_data['nodes']:
                # 노드가 없는 경우 기본 더미 데이터 사용
                G = nx.Graph()
                G.add_node("데이터 없음")
            else:
                # 그래프 객체 생성
                G = nx.Graph()
                
                # 노드 추가
                for node in graph_data['nodes']:
                    G.add_node(node['id'])
                
                # 엣지 추가
                for link in graph_data['links']:
                    G.add_edge(link['source'], link['target'], weight=link['weight'])
            
            # 그래프 렌더링
            plt.figure(figsize=(8, 6), facecolor=COLORS['card_bg'])
            
            if len(G.nodes) > 1:  # 노드가 2개 이상인 경우
                # 레이아웃 계산
                pos = nx.spring_layout(G, k=0.5, seed=42)
                
                # 엣지 가중치
                edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
                max_weight = max(edge_weights) if edge_weights else 1
                normalized_weights = [1.5 + 2.5 * (w / max_weight) for w in edge_weights]
                
                # 노드 크기 계산
                node_sizes = []
                for node in G.nodes():
                    degree = len(G.edges(node))
                    max_degree = max([len(G.edges(n)) for n in G.nodes()]) if G.nodes() else 1
                    size = 800 + 400 * (degree / max(1, max_degree))
                    node_sizes.append(size)
                
                # 색상 할당
                node_colors = []
                color_options = [COLORS['teal'], COLORS['purple'], COLORS['blue'], COLORS['red']]
                for i, node in enumerate(G.nodes()):
                    color_idx = i % len(color_options)
                    node_colors.append(color_options[color_idx])
                
                # 엣지 그리기
                for i, (u, v) in enumerate(G.edges()):
                    alpha = 0.3 + 0.4 * (edge_weights[i] / max_weight)
                    nx.draw_networkx_edges(
                        G, pos, 
                        edgelist=[(u, v)],
                        width=normalized_weights[i], 
                        alpha=alpha, 
                        edge_color=COLORS['text_secondary']
                    )
                
                # 노드 그리기
                nx.draw_networkx_nodes(
                    G, pos, 
                    node_size=node_sizes, 
                    node_color=node_colors, 
                    alpha=0.9,
                    edgecolors='white',
                    linewidths=2
                )
                
                # 노드 라벨 그리기
                font_path = Visualizer.get_font_path()
                if font_path:
                    font_prop = fm.FontProperties(fname=font_path)
                    nx.draw_networkx_labels(
                        G, pos, 
                        font_size=11, 
                        font_family=font_prop.get_name(), 
                        font_weight='bold',
                        font_color='white'
                    )
                else:
                    nx.draw_networkx_labels(
                        G, pos, 
                        font_size=11, 
                        font_weight='bold',
                        font_color='white'
                    )
            else:  # 노드가 1개 이하인 경우 (데이터 없음)
                plt.text(0.5, 0.5, "데이터가 부족하여 네트워크를 생성할 수 없습니다.",
                        ha='center', va='center', fontsize=12, color=COLORS['text_dark'])
            
            # 레이아웃 조정
            plt.axis('off')
            plt.tight_layout()
            
            # 이미지 저장
            img_dir = Visualizer.ensure_static_dirs()
            filename = f'network_graph_{period}.png'
            file_path = os.path.join(img_dir, filename)
            plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
            plt.close()
            
            return url_for('static', filename=f'images/{filename}')
        
        except Exception as e:
            logger.error(f"네트워크 그래프 생성 오류: {e}")
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def generate_wordcloud(df, period):
        """
        워드클라우드 생성
        
        Args:
            df (DataFrame): 토큰화된 데이터
            period (str): 기간 설정
            
        Returns:
            str: 워드클라우드 이미지 URL
        """
        try:
            from analyzer import Analyzer
            
            if df.empty:
                # 데이터가 없는 경우 빈 워드클라우드 생성
                text = "데이터가 부족합니다"
            else:
                # 모든 토큰 추출 및 불용어 제거
                all_tokens = []
                for tokens in df['tokens']:
                    all_tokens.extend(Analyzer.remove_stopwords(tokens))
                
                # 텍스트 생성
                text = " ".join(all_tokens)
            
            # 색상 맵 생성
            def teal_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                # 글자 크기에 따른 색상 변환
                if font_size > 40:
                    return COLORS['teal']
                elif font_size > 30:
                    return COLORS['blue']
                elif font_size > 20:
                    return COLORS['purple']
                else:
                    return COLORS['red']
            
            # 워드클라우드 생성
            font_path = Visualizer.get_font_path()
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color=COLORS['card_bg'],
                color_func=teal_color_func,
                max_words=100,
                prefer_horizontal=0.9,
                relative_scaling=0.6,
                font_path=font_path,
                max_font_size=120,
                min_font_size=8,
                mask=None,
                contour_width=0,
                contour_color=None,
                repeat=False
            ).generate(text)
            
            # 이미지 표시
            plt.figure(figsize=(10, 5), facecolor=COLORS['card_bg'])
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('키워드 빈도 워드클라우드', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=20)
            plt.tight_layout()
            
            # 이미지 저장
            img_dir = Visualizer.ensure_static_dirs()
            filename = f'wordcloud_{period}.png'
            file_path = os.path.join(img_dir, filename)
            plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
            plt.close()
            
            return url_for('static', filename=f'images/{filename}')
        
        except Exception as e:
            logger.error(f"워드클라우드 생성 오류: {e}")
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def generate_tfidf_chart(df, period):
        """
        TF-IDF 차트 생성
        
        Args:
            df (DataFrame): 토큰화된 데이터
            period (str): 기간 설정
            
        Returns:
            str: 차트 이미지 URL
        """
        try:
            from analyzer import Analyzer
            
            if df.empty:
                # 데이터가 없는 경우 기본 더미 데이터 사용
                keywords = ["데이터가", "부족하여", "TF-IDF", "분석을", "수행할", "수", "없습니다"]
                values = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            else:
                # TF-IDF 분석 실행
                top_keywords = Analyzer.analyze_tfidf(df, 0, 10)
                
                if not top_keywords:
                    # 분석 결과가 없는 경우
                    keywords = ["데이터가", "부족하여", "TF-IDF", "분석을", "수행할", "수", "없습니다"]
                    values = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
                else:
                    # 키워드와 값 추출
                    keywords = [kw for kw, _ in top_keywords]
                    values = [val for _, val in top_keywords]
            
            # 데이터 정렬 (내림차순)
            sorted_indices = np.argsort(values)[::-1]
            keywords = [keywords[i] for i in sorted_indices]
            values = [values[i] for i in sorted_indices]
            
            # 차트 생성
            plt.figure(figsize=(8, 6), facecolor=COLORS['card_bg'])
            ax = plt.subplot(111)
            
            # 그라데이션 색상 생성
            num_bars = len(keywords)
            colors = plt.cm.cool(np.linspace(0.3, 0.7, num_bars))
            
            # 수평 막대 그래프
            bars = plt.barh(keywords, values, color=colors, height=0.6)
            
            # 모던 스타일 적용
            Visualizer.apply_modern_style(ax, title='키워드 중요도 (TF-IDF)')
            
            # 축 설정
            plt.xlim(0, max(values) * 1.15)  # 여백 추가
            plt.xlabel('TF-IDF 값')
            
            # 막대 끝에 값 표시
            for i, v in enumerate(values):
                plt.text(v + 0.02, i, f'{v:.2f}', color=COLORS['text_secondary'], 
                         va='center', ha='left', fontsize=10, fontweight='bold')
            
            # 레이아웃 설정
            plt.tight_layout()
            
            # 이미지 저장
            img_dir = Visualizer.ensure_static_dirs()
            filename = f'tfidf_chart_{period}.png'
            file_path = os.path.join(img_dir, filename)
            plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
            plt.close()
            
            return url_for('static', filename=f'images/{filename}')
            
        except Exception as e:
            logger.error(f"TF-IDF 차트 생성 오류: {e}")
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def generate_trend_chart(df, keyword, period, chart_type='type1'):
        """
        키워드 트렌드 차트 생성
        
        Args:
            df (DataFrame): 토큰화된 데이터
            keyword (str): 키워드
            period (str): 기간 설정
            chart_type (str): 차트 유형 ('type1' 또는 'type2')
            
        Returns:
            str: 차트 이미지 URL
        """
        try:
            from analyzer import Analyzer
            
            # 기간에 따른 날짜 범위 계산
            today = datetime.now()
            delta_map = {
                '7일': 7, '2주': 14, '3주': 21, '1달': 30, '3달': 90, '6개월': 180, '1년': 365,
                '1주일': 7, '2주일': 14, '1개월': 30, '3개월': 90, '6개월': 180, '1년': 365, '2년': 730
            }
            delta = delta_map.get(period, 30)
            
            # 날짜 범위 설정
            start_date = today - timedelta(days=delta)
            df_filtered = df[(df['upload_date'] >= start_date) & (df['upload_date'] <= today)]
            
            if df_filtered.empty:
                # 데이터가 없는 경우 기본 더미 데이터 사용
                dates = [today - timedelta(days=i) for i in range(delta, 0, -1)]
                values = np.zeros(len(dates))
            else:
                # 중복 날짜 제거 및 정렬
                dates = sorted(df_filtered['upload_date'].dt.date.unique())
                
                # 날짜별 키워드 빈도 계산
                values = []
                for date in dates:
                    date_df = df_filtered[df_filtered['upload_date'].dt.date == date]
                    
                    # 해당 날짜의 모든 토큰 추출
                    tokens = []
                    for doc_tokens in date_df['tokens']:
                        tokens.extend(Analyzer.remove_stopwords(doc_tokens))
                    
                    # 키워드 빈도 계산
                    token_counts = pd.Series(tokens).value_counts()
                    values.append(token_counts.get(keyword, 0))
                
                # 날짜 객체를 datetime으로 변환
                dates = [datetime.combine(date, datetime.min.time()) for date in dates]
            
            if chart_type == 'type1':
                # 첫 번째 차트: 키워드 언급 빈도
                plt.figure(figsize=(8, 4), facecolor=COLORS['card_bg'])
                ax = plt.subplot(111)
                
                # 영역 채우기 그래프
                ax.fill_between(
                    dates, 
                    values, 
                    alpha=0.3, 
                    color=COLORS['teal'],
                    linewidth=0
                )
                
                # 선 그래프
                line = ax.plot(
                    dates, 
                    values, 
                    linewidth=3, 
                    color=COLORS['teal'],
                )[0]
                
                # 데이터 포인트 (원)
                ax.scatter(
                    dates, 
                    values, 
                    s=70, 
                    color=COLORS['teal'], 
                    zorder=4, 
                    edgecolors='white', 
                    linewidth=1.5
                )
                
                # 모던 스타일 적용
                Visualizer.apply_modern_style(ax)
                
                # 축 설정
                plt.xlabel('날짜')
                plt.ylabel('언급 빈도')
                plt.title(f'"{keyword}" 키워드 언급 추이', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=15)
                
                # x축 날짜 포맷 설정
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, delta // 15)))
                
                # 최대값 지점 강조
                if len(values) > 0:
                    max_idx = np.argmax(values)
                    plt.scatter(
                        dates[max_idx], 
                        values[max_idx], 
                        s=120, 
                        color=COLORS['teal'], 
                        zorder=5,
                        edgecolors='white',
                        linewidth=2
                    )
                    plt.annotate(
                        f'최대: {values[max_idx]:.1f}',
                        (dates[max_idx], values[max_idx]),
                        xytext=(10, 10),
                        textcoords='offset points',
                        fontsize=10,
                        fontweight='bold',
                        color=COLORS['text_dark'],
                        backgroundcolor='white',
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLORS['teal'], alpha=0.9)
                    )
                
                # 레이아웃 설정
                plt.tight_layout()
                
                # 이미지 저장
                img_dir = Visualizer.ensure_static_dirs()
                filename = f'trend_chart_1_{keyword}_{period}.png'
                file_path = os.path.join(img_dir, filename)
                plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
                plt.close()
                
                return url_for('static', filename=f'images/{filename}')
            
            else:
                # 두 번째 차트: 매체별 키워드 언급 추이
                plt.figure(figsize=(8, 4), facecolor=COLORS['card_bg'])
                ax = plt.subplot(111)
                
                # 각 매체별 필터링 및 시각화
                media = ['매거진', '뉴스', '무신사']
                colors = [COLORS['teal'], COLORS['purple'], COLORS['red']]
                
                for i, medium in enumerate(media):
                    if i < len(colors):  # 색상 인덱스 범위 체크
                        # 해당 매체 데이터만 필터링
                        medium_df = df_filtered[df_filtered['doc_domain'] == medium]
                        
                        if not medium_df.empty:
                            # 날짜별 키워드 빈도 계산
                            medium_dates = sorted(medium_df['upload_date'].dt.date.unique())
                            medium_values = []
                            
                            for date in medium_dates:
                                date_df = medium_df[medium_df['upload_date'].dt.date == date]
                                tokens = []
                                for doc_tokens in date_df['tokens']:
                                    tokens.extend(Analyzer.remove_stopwords(doc_tokens))
                                
                                token_counts = pd.Series(tokens).value_counts()
                                medium_values.append(token_counts.get(keyword, 0))
                            
                            # 날짜 객체 변환
                            medium_dates = [datetime.combine(date, datetime.min.time()) for date in medium_dates]
                            
                            # 시각화
                            if medium_dates and medium_values:
                                # 영역 채우기
                                ax.fill_between(
                                    medium_dates, 
                                    medium_values, 
                                    alpha=0.1, 
                                    color=colors[i],
                                    linewidth=0
                                )
                                
                                # 선 그래프
                                line = ax.plot(
                                    medium_dates, 
                                    medium_values, 
                                    linestyle='-', 
                                    label=medium, 
                                    color=colors[i], 
                                    linewidth=2.5, 
                                )[0]
                                
                                # 마지막 포인트 강조
                                if len(medium_values) > 0:
                                    last_idx = len(medium_values) - 1
                                    ax.scatter(
                                        medium_dates[last_idx], 
                                        medium_values[last_idx], 
                                        s=70, 
                                        color=colors[i], 
                                        zorder=4, 
                                        edgecolors='white', 
                                        linewidth=1.5
                                    )
                
                # 모던 스타일 적용
                Visualizer.apply_modern_style(ax)
                
                # 축 설정
                plt.xlabel('날짜')
                plt.ylabel('언급 수')
                plt.title(f'"{keyword}" 매체별 언급 추이', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=15)
                
                # 범례 설정
                legend = plt.legend(
                    frameon=True, 
                    facecolor=COLORS['card_bg'], 
                    edgecolor=COLORS['border'],
                    fontsize=10,
                    loc='upper left'
                )
                
                # x축 날짜 포맷 설정
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, delta // 15)))
                
                # 레이아웃 설정
                plt.tight_layout()
                
                # 이미지 저장
                img_dir = Visualizer.ensure_static_dirs()
                filename = f'trend_chart_2_{keyword}_{period}.png'
                file_path = os.path.join(img_dir, filename)
                plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
                plt.close()
                
                return url_for('static', filename=f'images/{filename}')
        
        except Exception as e:
            logger.error(f"트렌드 차트 생성 오류: {e}")
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def generate_category_chart(df, period):
        """
        카테고리 파이 차트 생성
        
        Args:
            df (DataFrame): 토큰화된 데이터
            period (str): 기간 설정
            
        Returns:
            str: 차트 이미지 URL
        """
        try:
            # 카테고리별 아이템 정의
            categories = {
                '상의': ['티셔츠', '블라우스', '셔츠', '니트', '맨투맨', '후드'],
                '하의': ['팬츠', '스커트', '청바지', '슬랙스', '레깅스'],
                '아우터': ['재킷', '코트', '가디건', '패딩', '점퍼'],
                '원피스': ['드레스', '점프수트'],
                '액세서리': ['가방', '신발', '모자', '벨트', '스카프', '장갑']
            }
            
            from analyzer import Analyzer
            
            if df.empty:
                # 데이터가 없는 경우 기본 더미 데이터 사용
                sizes = [45, 25, 15, 10, 5]
            else:
                # 카테고리별 언급량 집계
                all_tokens = []
                for tokens in df['tokens']:
                    all_tokens.extend(Analyzer.remove_stopwords(tokens))
                
                token_counts = pd.Series(all_tokens).value_counts()
                
                # 카테고리별 합계 계산
                category_counts = {}
                for category, items in categories.items():
                    category_counts[category] = sum(token_counts.get(item, 0) for item in items)
                
                # 결과 정렬 (내림차순)
                sizes = list(category_counts.values())
            
            # 색상 설정
            categories_list = list(categories.keys())
            colors = [COLORS['teal'], COLORS['purple'], COLORS['red'], COLORS['blue'], COLORS['orange']]
            
            # 그래프 생성
            plt.figure(figsize=(7, 5), facecolor=COLORS['card_bg'])
            ax = plt.subplot(111)
            
            # 파이 차트 생성
            wedges, texts, autotexts = plt.pie(
                sizes, 
                labels=None, 
                colors=colors, 
                autopct='%1.1f%%', 
                startangle=90, 
                wedgeprops=dict(edgecolor='white', linewidth=2),
                textprops=dict(color='white', fontweight='bold', fontsize=12)
            )
            
            # 텍스트 스타일 설정
            for autotext in autotexts:
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            
            # 범례 추가
            plt.legend(
                wedges, 
                categories_list,
                title="카테고리",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=10
            )
            
            # 레이아웃 설정
            plt.axis('equal')
            plt.title('카테고리별 분포', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=20)
            plt.tight_layout()
            
            # 이미지 저장
            img_dir = Visualizer.ensure_static_dirs()
            filename = f'category_chart_{period}.png'
            file_path = os.path.join(img_dir, filename)
            plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
            plt.close()
            
            return url_for('static', filename=f'images/{filename}')
            
        except Exception as e:
            logger.error(f"카테고리 차트 생성 오류: {e}")
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def generate_category_item_chart(category_type, season):
        """
        카테고리별 차트 생성 (아이템, 컬러, 소재, 프린트, 스타일)
        
        Args:
            category_type (str): 카테고리 유형 ('item', 'color', 'material', 'print', 'style')
            season (str): 시즌 ('25SS', '24FW', '24SS', etc.)
            
        Returns:
            str: 차트 이미지 URL
        """
        try:
            # 카테고리별 더미 데이터
            data = {
                'item': {
                    '25SS': {
                        'items': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
                        'counts': [5200, 2300, 1800, 1750, 1200, 1100, 800, 700, 650, 550, 450, 400, 300, 200, 150, 100],
                        'growth': [130, 80, 45, 30, 15, 10, 5, 0, -5, -10, -15, -20, 49.82, -25, -30, -35]
                    },
                    '24FW': {
                        'items': ['코트', '니트웨어', '패딩', '재킷', '팬츠', '청바지', '스웨터', '스커트', '블라우스', '셔츠', '탑', '드레스', '점퍼', '베스트', '후드', '레깅스'],
                        'counts': [4800, 3500, 3200, 2100, 1600, 1400, 1300, 1000, 900, 800, 600, 500, 400, 300, 200, 100],
                        'growth': [95, 65, 50, 35, 20, 15, 10, 5, 0, -5, -10, -15, -20, -25, -30, -35]
                    },
                    '24SS': {
                        'items': ['드레스', '블라우스', '팬츠', '스커트', '셔츠', '티셔츠', '재킷', '점프수트', '탑', '수영복', '청바지', '캐주얼상의', '쇼츠', '맨투맨', '베스트', '가디건'],
                        'counts': [5500, 4200, 3800, 3300, 2800, 2500, 2200, 1800, 1500, 1300, 1100, 900, 700, 500, 300, 200],
                        'growth': [85, 70, 60, 50, 40, 35, 25, 20, 15, 10, 5, 0, -5, -10, -15, -20]
                    },
                    '25SSM': {
                        'items': ['셔츠', '팬츠', '티셔츠', '재킷', '청바지', '쇼츠', '맨투맨', '후드', '폴로', '니트웨어', '캐주얼상의', '패딩', '점퍼', '베스트', '코트', '트레이닝복'],
                        'counts': [4800, 4500, 4200, 3800, 3500, 3100, 2800, 2500, 2200, 1900, 1700, 1400, 1100, 900, 700, 500],
                        'growth': [90, 75, 65, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0, -5]
                    }
                },
                'color': {
                    '25SS': {
                        'items': ['화이트', '블랙', '블루', '그린', '레드', '옐로우', '핑크', '퍼플', '오렌지', '브라운', '그레이', '베이지', '네이비', '라벤더', '민트'],
                        'counts': [4500, 4300, 3200, 2800, 2500, 2300, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400],
                        'growth': [75, 65, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0, -5, -10]
                    }
                },
                'material': {
                    '25SS': {
                        'items': ['코튼', '린넨', '실크', '폴리에스터', '데님', '울', '스웨이드', '레이온', '나일론', '스웨이드', '저지', '트윌', '캐시미어', '벨벳', '시퀸'],
                        'counts': [5500, 3800, 3600, 3400, 3200, 2800, 2600, 2400, 2200, 2000, 1800, 1600, 1400, 1200, 1000],
                        'growth': [85, 70, 60, 55, 45, 40, 35, 30, 25, 15, 10, 5, 0, -5, -10]
                    }
                },
                'print': {
                    '25SS': {
                        'items': ['솔리드', '스트라이프', '플로럴', '도트', '체크', '그래픽', '애니멀', '기하학', '추상', '타이다이', '페이즐리', '레터링', '카모', '보더', '아가일'],
                        'counts': [6500, 3200, 3000, 2800, 2600, 2400, 2200, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600],
                        'growth': [90, 75, 65, 55, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0, -5]
                    }
                },
                'style': {
                    '25SS': {
                        'items': ['캐주얼', '미니멀', '페미닌', '스포티', '보헤미안', '프레피', '클래식', '스트리트', '밀리터리', '레트로', '로맨틱', '아방가르드', '힙스터', '그런지', '모던'],
                        'counts': [4800, 4200, 3600, 3400, 3200, 3000, 2800, 2600, 2400, 2200, 2000, 1800, 1600, 1400, 1200],
                        'growth': [80, 70, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0]
                    }
                }
            }
            
            # 해당 카테고리와 시즌 데이터 가져오기
            if category_type in data and season in data[category_type]:
                category_data = data[category_type][season]
            else:
                # 기본값으로 아이템 카테고리의 25SS 시즌 데이터 사용
                category_data = data['item']['25SS']
            
            # 데이터 추출
            items = category_data['items']
            counts = category_data['counts']
            growth_rates = category_data['growth']
            
            # 강조할 항목 선택 (가장 큰 성장률을 보이는 항목)
            highlight_idx = np.argmax(growth_rates)
            highlight_item = items[highlight_idx]
            
            # 2행 1열 구조의 그래프 생성
            plt.figure(figsize=(12, 8), facecolor=COLORS['card_bg'])
            
            # 상단: 항목별 수량 차트
            ax1 = plt.subplot(2, 1, 1)
            bars1 = ax1.bar(items, counts, color='#333333')
            ax1.set_ylabel("아이템 수", fontsize=12)
            ax1.set_title(f"{season} {category_type.capitalize()} 카테고리 분포", fontsize=14, fontweight='bold', loc='left')
            ax1.tick_params(axis='x', rotation=45)
            
            # 모던 스타일 적용
            Visualizer.apply_modern_style(ax1)
            
            # 하단: 전년 대비, 증감률 차트
            ax2 = plt.subplot(2, 1, 2)
            colors = ['#999999' if val < 0 else '#333333' for val in growth_rates]
            bars2 = ax2.bar(items, growth_rates, color=colors)
            ax2.axhline(0, color='black', linestyle='--', linewidth=0.8)
            ax2.set_ylabel("전년 대비 증감률 (%)", fontsize=12)
            ax2.tick_params(axis='x', rotation=45)
            
            # 모던 스타일 적용
            Visualizer.apply_modern_style(ax2)
            
            # 강조 표시
            ax2.annotate(f"{highlight_item}\n{growth_rates[highlight_idx]}%", 
                        xy=(highlight_idx, growth_rates[highlight_idx]), 
                        xytext=(highlight_idx, growth_rates[highlight_idx] + 10),
                        ha='center',
                        fontsize=10,
                        fontweight='bold',
                        arrowprops=dict(facecolor='black', arrowstyle='->'))
            
            plt.tight_layout()
            
            # 이미지 저장
            img_dir = Visualizer.ensure_static_dirs()
            filename = f'category_{category_type}_{season}_chart.png'
            file_path = os.path.join(img_dir, filename)
            plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
            plt.close()
            
            return url_for('static', filename=f'images/{filename}')
            
        except Exception as e:
            logger.error(f"카테고리 아이템 차트 생성 오류: {e}", exc_info=True)
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def generate_magazine_comparison_chart(df, magazine_data, period):
        """
        매거진별 비교 차트 생성
        
        Args:
            df (DataFrame): 전체 토큰화된 데이터
            magazine_data (dict): 매거진별 상위 키워드 데이터
            period (str): 기간 설정
            
        Returns:
            str: 차트 이미지 URL
        """
        try:
            # 매거진별 상위 키워드 데이터
            top_tokens_per_mag = magazine_data.get('top_tokens_per_mag', {})
            
            if not top_tokens_per_mag:
                # 데이터가 없는 경우
                plt.figure(figsize=(10, 6), facecolor=COLORS['card_bg'])
                plt.text(0.5, 0.5, "매거진 비교 데이터가 부족합니다.", 
                         ha='center', va='center', fontsize=14, color=COLORS['text_dark'])
                plt.axis('off')
                
                # 이미지 저장
                img_dir = Visualizer.ensure_static_dirs()
                filename = f'magazine_comparison_{period}.png'
                file_path = os.path.join(img_dir, filename)
                plt.savefig(file_path, facecolor=COLORS['card_bg'], dpi=100)
                plt.close()
                
                return url_for('static', filename=f'images/{filename}')
            
            # 매거진 목록
            magazines = list(top_tokens_per_mag.keys())
            
            # 최대 5개 매거진으로 제한
            magazines = magazines[:5]
            
            # 각 매거진별 상위 10개 키워드 추출
            top10_keywords = {}
            for mag in magazines:
                if not top_tokens_per_mag[mag].empty:
                    top10_keywords[mag] = top_tokens_per_mag[mag].head(10)
            
            # 그래프 생성
            fig = plt.figure(figsize=(12, 6), facecolor=COLORS['card_bg'])
            
            # 매거진별 색상 할당
            colors = [COLORS['teal'], COLORS['purple'], COLORS['red'], COLORS['blue'], COLORS['orange']]
            
            # 각 매거진별 상위 키워드 막대 그래프 생성
            for i, mag in enumerate(magazines):
                if mag in top10_keywords:
                    keywords = top10_keywords[mag].index.tolist()
                    values = top10_keywords[mag].values.tolist()
                    
                    # 데이터 정렬 (내림차순)
                    sorted_idx = np.argsort(values)[::-1]
                    keywords = [keywords[idx] for idx in sorted_idx]
                    values = [values[idx] for idx in sorted_idx]
                    
                    # 서브플롯 생성
                    ax = fig.add_subplot(len(magazines), 1, i+1)
                    bars = ax.barh(keywords, values, color=colors[i % len(colors)])
                    
                    # 모던 스타일 적용
                    Visualizer.apply_modern_style(ax)
                    
                    # 제목 설정
                    ax.set_title(f"{mag} 상위 키워드", fontsize=12, fontweight='bold', 
                                 color=COLORS['text_dark'], loc='left')
                    
                    # y축 레이블 제거
                    ax.set_ylabel('')
                    
                    # 값 표시
                    for bar in bars:
                        width = bar.get_width()
                        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{int(width)}',
                               ha='left', va='center', fontsize=9)
            
            plt.tight_layout()
            
            # 이미지 저장
            img_dir = Visualizer.ensure_static_dirs()
            filename = f'magazine_comparison_{period}.png'
            file_path = os.path.join(img_dir, filename)
            plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
            plt.close()
            
            return url_for('static', filename=f'images/{filename}')
            
        except Exception as e:
            logger.error(f"매거진 비교 차트 생성 오류: {e}")
            return url_for('static', filename='images/error.png')