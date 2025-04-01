import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import numpy as np
from matplotlib.ticker import MaxNLocator
import io
import base64
import networkx as nx
from wordcloud import WordCloud
from datetime import datetime, timedelta
import os
from flask import url_for

# 색상 팔레트 - 흰색 배경으로 변경
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

# 시각화를 위한 폴더 생성
def ensure_static_dirs():
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    img_dir = os.path.join(static_dir, 'images')
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    
    return img_dir

# 그라데이션 색상 생성 헬퍼 함수
def create_gradient_color(c1, c2, n=100):
    """두 색상 사이의 그라데이션 색상 생성"""
    c1_rgb = mcolors.to_rgb(c1)
    c2_rgb = mcolors.to_rgb(c2)
    
    mix_pcts = [i/(n-1) for i in range(n)]
    rgb_colors = [tuple(x*(1-pct) + y*pct for x, y in zip(c1_rgb, c2_rgb)) for pct in mix_pcts]
    
    return rgb_colors

# 모던 차트 스타일 적용
def apply_modern_style(ax, title=None):
    """모던 다크 테마 스타일을 차트에 적용"""
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

# 1. 키워드 네트워크 그래프 생성
def generate_network_graph(period):
    # 더미 데이터로 네트워크 그래프 생성
    G = nx.Graph()
    
    # 키워드 노드 추가
    keywords = ['브랜드', '패션', '한국', '섬유', '제품', 'Y2K', '스트리트웨어', '뉴트로', '미니멀', '오버사이즈']
    
    # 노드 추가
    for kw in keywords:
        G.add_node(kw)
    
    # 엣지 추가 (관계)
    edges = [
        ('브랜드', '패션', 5), ('브랜드', '한국', 3), ('패션', '제품', 4),
        ('Y2K', '뉴트로', 6), ('스트리트웨어', '오버사이즈', 4), ('미니멀', '패션', 3),
        ('한국', '패션', 4), ('섬유', '제품', 5), ('Y2K', '패션', 3),
        ('브랜드', '제품', 2), ('한국', 'Y2K', 1), ('패션', '스트리트웨어', 4)
    ]
    
    for source, target, weight in edges:
        G.add_edge(source, target, weight=weight)
    
    # 그래프 그리기
    plt.figure(figsize=(8, 6), facecolor=COLORS['card_bg'])
    
    # 노드 위치 계산
    pos = nx.spring_layout(G, seed=42)
    
    # 엣지 가중치에 따른 두께와 색상
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    normalized_weights = [1.5 + 2.5 * (w / max(edge_weights)) for w in edge_weights]
    
    # 노드 크기와 색상
    node_sizes = [800 + 400 * (len(G.edges(node)) / max(1, max([len(G.edges(n)) for n in G.nodes()]))) for node in G.nodes()]
    
    # 색상 할당 (순환)
    node_colors = []
    color_options = [COLORS['teal'], COLORS['purple'], COLORS['blue'], COLORS['red']]
    for i in range(len(G.nodes())):
        color_idx = i % len(color_options)
        node_colors.append(color_options[color_idx])
    
    # 엣지 그리기 (그라데이션 효과)
    for i, (u, v, w) in enumerate(G.edges(data=True)):
        alpha = 0.3 + 0.4 * (w.get('weight', 1) / max([e[2].get('weight', 1) for e in G.edges(data=True)]))
        edge_color = COLORS['text_secondary']
        nx.draw_networkx_edges(
            G, pos, 
            edgelist=[(u, v)],
            width=normalized_weights[i], 
            alpha=alpha, 
            edge_color=edge_color
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
    nx.draw_networkx_labels(
        G, pos, 
        font_size=11, 
        font_family='sans-serif', 
        font_weight='bold',
        font_color='white'
    )
    
    # 레이아웃 조정
    plt.axis('off')
    plt.tight_layout()
    
    # 이미지 저장
    img_dir = ensure_static_dirs()
    file_path = os.path.join(img_dir, 'network_graph.png')
    plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
    plt.close()
    
    return url_for('static', filename='images/network_graph.png')

# 2. 카테고리 파이 차트 생성
def generate_category_chart(period):
    # 더미 데이터
    categories = ['의류', '신발', '액세서리', '가방', '기타']
    sizes = [45, 25, 15, 10, 5]
    
    # 색상 설정
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
        categories,
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
    img_dir = ensure_static_dirs()
    file_path = os.path.join(img_dir, 'category_chart.png')
    plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
    plt.close()
    
    return url_for('static', filename='images/category_chart.png')

# 3. 워드클라우드 생성
def generate_wordcloud(period):
    # 더미 텍스트 데이터
    text = "브랜드 패션 한국 섬유 제품 Y2K 스트리트웨어 뉴트로 미니멀 오버사이즈 빈티지 스트라이프 파스텔 스포티 플로럴 네온 아방가르드 테크웨어 플랫폼 레이어링 브랜드 브랜드 패션 패션 패션 한국 한국 Y2K Y2K Y2K 스트리트웨어 스트리트웨어 미니멀 오버사이즈 오버사이즈"
    
    # 색상 맵 생성 (청록색 그라데이션)
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
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color=COLORS['card_bg'],
        color_func=teal_color_func,
        max_words=100,
        prefer_horizontal=0.9,
        relative_scaling=0.6,
        font_path=None,
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
    img_dir = ensure_static_dirs()
    file_path = os.path.join(img_dir, 'wordcloud.png')
    plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
    plt.close()
    
    return url_for('static', filename='images/wordcloud.png')

# 4. TF-IDF 차트 생성
def generate_tfidf_chart(period):
    # 더미 데이터 (키워드와 TF-IDF 값)
    keywords = ['브랜드', '패션', '한국', 'Y2K', '스트리트웨어', '뉴트로', '섬유', '제품', '미니멀', '오버사이즈']
    values = [0.85, 0.78, 0.72, 0.68, 0.65, 0.63, 0.58, 0.55, 0.52, 0.48]
    
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
    apply_modern_style(ax, title='키워드 중요도 (TF-IDF)')
    
    # 축 설정
    plt.xlim(0, max(values) * 1.15)  # 여백 추가
    plt.xlabel('TF-IDF 값')
    
    # 막대 끝에 값 표시
    for i, v in enumerate(values):
        plt.text(v + 0.02, i, f'{v:.2f}', color=COLORS['text_secondary'], va='center', ha='left', fontsize=10, fontweight='bold')
    
    # 레이아웃 설정
    plt.tight_layout()
    
    # 이미지 저장
    img_dir = ensure_static_dirs()
    file_path = os.path.join(img_dir, 'tfidf_chart.png')
    plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
    plt.close()
    
    return url_for('static', filename='images/tfidf_chart.png')

# 5. 키워드 트렌드 차트 생성
def generate_trend_chart(period, keyword, chart_type):
    # 더미 데이터 생성
    today = datetime.now()
    dates = [today - timedelta(days=i) for i in range(30, 0, -1)]
    
    if chart_type == 'type1':
        # 첫 번째 차트: 키워드 언급 빈도
        values = np.concatenate([
            np.linspace(10, 20, 10),
            np.linspace(20, 40, 10),
            np.linspace(40, 30, 10)
        ])
        
        # 차트 생성
        plt.figure(figsize=(8, 4), facecolor=COLORS['card_bg'])
        ax = plt.subplot(111)
        
        # 그라데이션 영역 채우기
        gradient_colors = create_gradient_color(COLORS['teal'], COLORS['teal_gradient'])
        n_values = len(values)
        
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
        apply_modern_style(ax)
        
        # 축 설정
        plt.xlabel('날짜')
        plt.ylabel('언급 빈도')
        plt.title(f'"{keyword}" 키워드 언급 추이', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=15)
        
        # x축 날짜 포맷 설정
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        
        # 최대값 지점 강조
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
        img_dir = ensure_static_dirs()
        file_path = os.path.join(img_dir, f'trend_chart_1_{keyword}.png')
        plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
        plt.close()
        
        return url_for('static', filename=f'images/trend_chart_1_{keyword}.png')
    
    else:
        # 두 번째 차트: 키워드 관련 데이터 (관련 매체별 언급 수)
        media_data = {
            '뉴스': np.concatenate([np.linspace(5, 10, 10), np.linspace(10, 25, 10), np.linspace(25, 20, 10)]),
            '매거진': np.concatenate([np.linspace(3, 8, 10), np.linspace(8, 15, 10), np.linspace(15, 10, 10)]),
            '무신사': np.concatenate([np.linspace(2, 5, 10), np.linspace(5, 15, 10), np.linspace(15, 5, 10)])
        }
        
        # 차트 색상
        colors = [COLORS['teal'], COLORS['purple'], COLORS['red']]
        
        # 차트 생성
        plt.figure(figsize=(8, 4), facecolor=COLORS['card_bg'])
        ax = plt.subplot(111)
        
        # 각 매체별 선 그래프
        for i, (medium, data) in enumerate(media_data.items()):
            # 영역 채우기
            ax.fill_between(
                dates, 
                data, 
                alpha=0.1, 
                color=colors[i],
                linewidth=0
            )
            
            # 선 그래프
            line = ax.plot(
                dates, 
                data, 
                linestyle='-', 
                label=medium, 
                color=colors[i], 
                linewidth=2.5, 
            )[0]
            
            # 마지막 포인트 강조
            last_idx = len(data) - 1
            ax.scatter(
                dates[last_idx], 
                data[last_idx], 
                s=70, 
                color=colors[i], 
                zorder=4, 
                edgecolors='white', 
                linewidth=1.5
            )
        
        # 모던 스타일 적용
        apply_modern_style(ax)
        
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
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        
        # 레이아웃 설정
        plt.tight_layout()
        
        # 이미지 저장
        img_dir = ensure_static_dirs()
        file_path = os.path.join(img_dir, f'trend_chart_2_{keyword}.png')
        plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
        plt.close()
        
        return url_for('static', filename=f'images/trend_chart_2_{keyword}.png') [COLORS['teal'], COLORS['purple'], COLORS['blue'], COLORS['red']]



def plot_item_growth(selected_items, all_items, item_counts, growth_rates, save_path='static/item_growth.png'):
    import matplotlib.pyplot as plt

    # 선택 항목 필터링
    indices = [i for i, item in enumerate(all_items) if item in selected_items]
    filtered_items = [all_items[i] for i in indices]
    filtered_counts = [item_counts[i] for i in indices]
    filtered_growth = [growth_rates[i] for i in indices]

    # 시각화 구성
    fig, axs = plt.subplots(2, 1, figsize=(12, 6), gridspec_kw={'height_ratios': [2, 1]})

    # 상단: 아이템 수
    axs[0].bar(filtered_items, filtered_counts, color='black')
    axs[0].set_ylabel("아이템 수")
    axs[0].set_title("아이템별 수량", loc='left')
    axs[0].tick_params(axis='x', rotation=45)

    # 하단: 증감률
    colors = ['gray' if val < 0 else 'black' for val in filtered_growth]
    axs[1].bar(filtered_items, filtered_growth, color=colors)
    axs[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
    axs[1].set_ylabel("전년 대비 증감률 (%)")
    axs[1].tick_params(axis='x', rotation=45)

    # 강조 표시 (예: 수영복)
    for i, item in enumerate(filtered_items):
        if item == '수영복':
            axs[1].annotate(f"{item}\n{filtered_growth[i]}%", 
                            xy=(i, filtered_growth[i]), 
                            xytext=(i, filtered_growth[i] + 10),
                            ha='center',
                            arrowprops=dict(facecolor='black', arrowstyle='->'))

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()


def generate_category_item_chart(category_type, season):
    """
    카테고리별 차트 생성 (아이템, 컬러, 소재, 프린트, 스타일)
    
    Args:
        category_type (str): 카테고리 유형 ('item', 'color', 'material', 'print', 'style')
        season (str): 시즌 ('25SS', '24FW', '24SS', etc.)
        
    Returns:
        tuple: 항목별 수량 차트와 증감률 차트의 URL
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import numpy as np
    import os
    
    # 모던한 스타일 설정
    plt.style.use('ggplot')
    mpl.rcParams['font.family'] = 'NanumGothic, Arial'
    mpl.rcParams['axes.grid'] = True
    mpl.rcParams['axes.axisbelow'] = True
    mpl.rcParams['axes.edgecolor'] = '#333333'
    mpl.rcParams['axes.facecolor'] = 'white'
    mpl.rcParams['figure.facecolor'] = 'white'
    mpl.rcParams['grid.color'] = '#dddddd'
    
    # 카테고리별 더미 데이터
    data = {
        'item': {
            '25SS': {
                'items': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '재킷하이웨이', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '랩드', '페딩'],
                'counts': [5200, 2300, 1800, 1750, 1200, 1100, 800, 700, 650, 550, 450, 400, 300, 200, 150],
                'growth': [130, 80, 45, 30, 15, 10, 5, 0, -5, -10, -15, 49.82, -25, -30, -35]
            },
            '24FW': {
                'items': ['코트', '니트웨어', '패딩', '재킷', '팬츠', '청바지', '스웨터', '스커트', '블라우스', '셔츠', '탑', '드레스', '점퍼', '랩드', '후드'],
                'counts': [4800, 3500, 3200, 2100, 1600, 1400, 1300, 1000, 900, 800, 600, 500, 400, 300, 200],
                'growth': [95, 65, 50, 35, 20, 15, 10, 5, 0, -5, -10, -15, -20, -25, -30]
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
    
    items = category_data['items']
    counts = category_data['counts']
    growth_rates = category_data['growth']
    
    # 강조할 항목 선택 (가장 큰 성장률을 보이는 항목)
    highlight_idx = np.argmax(growth_rates)
    highlight_item = items[highlight_idx]
    
    # 2행 1열 구조의 그래프 생성
    fig, axs = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
    
    # 상단: 항목별 수량 차트
    axs[0].bar(items, counts, color='#333333')
    axs[0].set_ylabel("아이템 수", fontsize=12)
    axs[0].set_title(f"{season} {category_type.capitalize()} 카테고리 분포", fontsize=14, fontweight='bold', loc='left')
    axs[0].tick_params(axis='x', rotation=45)
    
    # 하단: 전년 대비, 증감률 차트
    colors = ['#999999' if val < 0 else '#333333' for val in growth_rates]
    bars = axs[1].bar(items, growth_rates, color=colors)
    axs[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
    axs[1].set_ylabel("전년 대비 증감률 (%)", fontsize=12)
    axs[1].tick_params(axis='x', rotation=45)
    
    # 강조 표시
    axs[1].annotate(f"{highlight_item}\n{growth_rates[highlight_idx]}%", 
                    xy=(highlight_idx, growth_rates[highlight_idx]), 
                    xytext=(highlight_idx, growth_rates[highlight_idx] + 10),
                    ha='center',
                    fontsize=10,
                    fontweight='bold',
                    arrowprops=dict(facecolor='black', arrowstyle='->'))
    
    plt.tight_layout()
    
    # 이미지 저장
    static_dir = ensure_static_dirs()
    chart_filename = f'category_{category_type}_{season}_chart.png'
    file_path = os.path.join(static_dir, chart_filename)
    plt.savefig(file_path, bbox_inches='tight', dpi=100)
    plt.close()
    
    return url_for('static', filename=f'images/{chart_filename}')


def generate_category_item_chart(category_type, season):
    """
    카테고리별 파이차트 생성 (아이템, 컬러, 소재, 프린트, 스타일)
    
    Args:
        category_type (str): 카테고리 유형 ('item', 'color', 'material', 'print', 'style')
        season (str): 시즌 ('25SS', '24FW', '24SS', etc.)
        
    Returns:
        str: 차트 이미지 URL
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    
    # 카테고리별 더미 데이터
    data = {
        'item': {
            '25SS': {
                'items': ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '니트웨어', '셔츠', '탑', '기타'],
                'counts': [25, 18, 15, 10, 8, 7, 6, 5, 4, 2],
                'growth': [130, 80, 45, 30, 15, 10, 5, 0, -5, -10]
            }
        },
        'color': {
            '25SS': {
                'items': ['화이트', '블랙', '블루', '그린', '레드', '옐로우', '핑크', '퍼플', '오렌지', '기타'],
                'counts': [20, 18, 12, 10, 9, 8, 7, 6, 5, 5],
                'growth': [75, 65, 50, 45, 40, 35, 30, 25, 20, 15]
            }
        },
        'material': {
            '25SS': {
                'items': ['코튼', '린넨', '실크', '폴리에스터', '데님', '울', '스웨이드', '레이온', '나일론', '기타'],
                'counts': [25, 18, 15, 12, 10, 7, 5, 4, 3, 1],
                'growth': [85, 70, 60, 55, 45, 40, 35, 30, 25, 15]
            }
        },
        'print': {
            '25SS': {
                'items': ['솔리드', '스트라이프', '플로럴', '도트', '체크', '그래픽', '애니멀', '기하학', '추상', '기타'],
                'counts': [30, 15, 12, 10, 8, 7, 6, 5, 4, 3],
                'growth': [90, 75, 65, 55, 45, 40, 35, 30, 25, 20]
            }
        },
        'style': {
            '25SS': {
                'items': ['캐주얼', '미니멀', '페미닌', '스포티', '보헤미안', '프레피', '클래식', '스트리트', '밀리터리', '기타'],
                'counts': [22, 18, 15, 12, 10, 8, 6, 5, 3, 1],
                'growth': [80, 70, 60, 55, 50, 45, 40, 35, 30, 25]
            }
        }
    }
    
    # 해당 카테고리와 시즌 데이터 가져오기
    if category_type in data and season in data[category_type]:
        category_data = data[category_type][season]
    else:
        # 기본값으로 아이템 카테고리의 25SS 시즌 데이터 사용
        category_data = data['item']['25SS']
    
    items = category_data['items']
    counts = category_data['counts']
    growth_rates = category_data['growth']
    
    # 색상 설정
    colors = [
        '#333333', '#666666', '#999999', '#cccccc', '#b3b3b3', 
        '#808080', '#595959', '#404040', '#262626', '#0d0d0d'
    ]
    
    # 파이 차트 생성
    plt.figure(figsize=(10, 8))
    
    # 파이 차트 (위쪽)
    plt.subplot(2, 1, 1)
    wedges, texts, autotexts = plt.pie(
        counts, 
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='white')
    )
    
    # 자동 텍스트 스타일 설정
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
        autotext.set_color('white')
    
    # 도넛 가운데 제목 추가
    plt.text(0, 0, f'{season}\n{category_type.upper()}', 
             ha='center', va='center', fontsize=16, fontweight='bold')
    
    # 범례 추가
    plt.legend(
        wedges, 
        items,
        title=f"{season} {category_type.capitalize()}",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=9
    )
    plt.title(f"{season} {category_type.capitalize()} 카테고리 분포", fontsize=14, fontweight='bold')
    
    # 증감률 바 차트 (아래쪽)
    plt.subplot(2, 1, 2)
    
    # 증감률에 따라 색상 지정
    bar_colors = ['#cccccc' if g < 0 else '#333333' for g in growth_rates]
    
    # 항목 이름과 증감률 값을 함께 표시할 라벨 생성
    labels = [f"{items[i]} ({growth_rates[i]}%)" for i in range(len(items))]
    
    # 증감률이 높은 순으로 정렬
    sorted_indices = np.argsort(growth_rates)[::-1]
    sorted_growth = [growth_rates[i] for i in sorted_indices]
    sorted_labels = [labels[i] for i in sorted_indices]
    sorted_colors = [bar_colors[i] for i in sorted_indices]
    
    # 위에서부터 5개 항목만 선택
    top_n = 5
    sorted_growth = sorted_growth[:top_n]
    sorted_labels = sorted_labels[:top_n]
    sorted_colors = sorted_colors[:top_n]
    
    plt.barh(sorted_labels, sorted_growth, color=sorted_colors)
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    plt.xlabel('전년 대비 증감률 (%)')
    plt.title('주요 항목 증감률', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # 이미지 저장
    img_dir = ensure_static_dirs()
    file_path = os.path.join(img_dir, f'category_{category_type}_{season}.png')
    plt.savefig(file_path, bbox_inches='tight')
    plt.close()
    
    return url_for('static', filename=f'images/category_{category_type}_{season}.png')


############################# 아래 코드는 주석 처리되어 있습니다. 필요시 주석을 해제하여 사용하세요.
# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# import matplotlib.colors as mcolors
# import matplotlib.dates as mdates
# import numpy as np
# from matplotlib.ticker import MaxNLocator
# import io
# import base64
# import networkx as nx
# from wordcloud import WordCloud
# from datetime import datetime, timedelta
# import os
# from flask import url_for

# # 색상 팔레트 - 흰색 배경으로 변경
# COLORS = {
#     'bg_dark': '#ffffff',       # 배경색을 흰색으로 변경
#     'card_bg': '#ffffff',       # 카드 배경색
#     'teal': '#36D6BE',          # 주요 청록색 
#     'teal_gradient': '#8AEFDB', # 청록색 그라데이션 끝
#     'purple': '#6B5AED',        # 보라색
#     'red': '#FF5A5A',           # 빨간색
#     'blue': '#4A78E1',          # 파란색
#     'orange': '#FFA26B',        # 주황색
#     'text_dark': '#1e2b3c',     # 어두운 텍스트 색상
#     'text_secondary': '#6c7293',# 보조 텍스트 색상
#     'light_bg': '#f8f9fc',      # 연한 배경색
#     'border': '#e4e9f2',        # 테두리 색상
# }

# # 시각화를 위한 폴더 생성
# def ensure_static_dirs():
#     static_dir = os.path.join(os.path.dirname(__file__), 'static')
#     img_dir = os.path.join(static_dir, 'images')
    
#     if not os.path.exists(static_dir):
#         os.makedirs(static_dir)
#     if not os.path.exists(img_dir):
#         os.makedirs(img_dir)
    
#     return img_dir

# # 그라데이션 색상 생성 헬퍼 함수
# def create_gradient_color(c1, c2, n=100):
#     """두 색상 사이의 그라데이션 색상 생성"""
#     c1_rgb = mcolors.to_rgb(c1)
#     c2_rgb = mcolors.to_rgb(c2)
    
#     mix_pcts = [i/(n-1) for i in range(n)]
#     rgb_colors = [tuple(x*(1-pct) + y*pct for x, y in zip(c1_rgb, c2_rgb)) for pct in mix_pcts]
    
#     return rgb_colors

# # 모던 차트 스타일 적용
# def apply_modern_style(ax, title=None):
#     """모던 다크 테마 스타일을 차트에 적용"""
#     # 배경색 설정
#     ax.set_facecolor(COLORS['card_bg'])
    
#     # 그리드 스타일 설정
#     ax.grid(True, linestyle='--', alpha=0.2, color=COLORS['text_secondary'], axis='y')
#     ax.set_axisbelow(True)  # 그리드를 데이터 아래에 배치
    
#     # 테두리 제거
#     for spine in ax.spines.values():
#         spine.set_visible(False)
    
#     # 틱 설정
#     ax.tick_params(axis='x', colors=COLORS['text_secondary'], length=0)
#     ax.tick_params(axis='y', colors=COLORS['text_secondary'], length=0)
    
#     # x축 레이블 간격 설정
#     if len(ax.get_xticklabels()) > 10:
#         for i, label in enumerate(ax.get_xticklabels()):
#             if i % 2 != 0:
#                 label.set_visible(False)
    
#     # 타이틀 설정
#     if title:
#         ax.set_title(title, fontsize=15, fontweight='bold', color=COLORS['text_dark'], pad=15)
    
#     # 레이블 설정
#     if ax.get_xlabel():
#         ax.set_xlabel(ax.get_xlabel(), fontsize=12, color=COLORS['text_secondary'], labelpad=10)
#     if ax.get_ylabel():
#         ax.set_ylabel(ax.get_ylabel(), fontsize=12, color=COLORS['text_secondary'], labelpad=10)

# # 1. 키워드 네트워크 그래프 생성
# def generate_network_graph(period):
#     # 더미 데이터로 네트워크 그래프 생성
#     G = nx.Graph()
    
#     # 키워드 노드 추가
#     keywords = ['브랜드', '패션', '한국', '섬유', '제품', 'Y2K', '스트리트웨어', '뉴트로', '미니멀', '오버사이즈']
    
#     # 노드 추가
#     for kw in keywords:
#         G.add_node(kw)
    
#     # 엣지 추가 (관계)
#     edges = [
#         ('브랜드', '패션', 5), ('브랜드', '한국', 3), ('패션', '제품', 4),
#         ('Y2K', '뉴트로', 6), ('스트리트웨어', '오버사이즈', 4), ('미니멀', '패션', 3),
#         ('한국', '패션', 4), ('섬유', '제품', 5), ('Y2K', '패션', 3),
#         ('브랜드', '제품', 2), ('한국', 'Y2K', 1), ('패션', '스트리트웨어', 4)
#     ]
    
#     for source, target, weight in edges:
#         G.add_edge(source, target, weight=weight)
    
#     # 그래프 그리기
#     plt.figure(figsize=(8, 6), facecolor=COLORS['card_bg'])
    
#     # 노드 위치 계산
#     pos = nx.spring_layout(G, seed=42)
    
#     # 엣지 가중치에 따른 두께와 색상
#     edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
#     normalized_weights = [1.5 + 2.5 * (w / max(edge_weights)) for w in edge_weights]
    
#     # 노드 크기와 색상
#     node_sizes = [800 + 400 * (len(G.edges(node)) / max(1, max([len(G.edges(n)) for n in G.nodes()]))) for node in G.nodes()]
    
#     # 색상 할당 (순환)
#     node_colors = []
#     color_options = [COLORS['teal'], COLORS['purple'], COLORS['blue'], COLORS['red']]
#     for i in range(len(G.nodes())):
#         color_idx = i % len(color_options)
#         node_colors.append(color_options[color_idx])
    
#     # 엣지 그리기 (그라데이션 효과)
#     for i, (u, v, w) in enumerate(G.edges(data=True)):
#         alpha = 0.3 + 0.4 * (w.get('weight', 1) / max([e[2].get('weight', 1) for e in G.edges(data=True)]))
#         edge_color = COLORS['text_secondary']
#         nx.draw_networkx_edges(
#             G, pos, 
#             edgelist=[(u, v)],
#             width=normalized_weights[i], 
#             alpha=alpha, 
#             edge_color=edge_color
#         )
    
#     # 노드 그리기
#     nx.draw_networkx_nodes(
#         G, pos, 
#         node_size=node_sizes, 
#         node_color=node_colors, 
#         alpha=0.9,
#         edgecolors='white',
#         linewidths=2
#     )
    
#     # 노드 라벨 그리기
#     nx.draw_networkx_labels(
#         G, pos, 
#         font_size=11, 
#         font_family='sans-serif', 
#         font_weight='bold',
#         font_color='white'
#     )
    
#     # 레이아웃 조정
#     plt.axis('off')
#     plt.tight_layout()
    
#     # 이미지 저장
#     img_dir = ensure_static_dirs()
#     file_path = os.path.join(img_dir, 'network_graph.png')
#     plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
#     plt.close()
    
#     return url_for('static', filename='images/network_graph.png')

# # 2. 카테고리 파이 차트 생성
# def generate_category_chart(period):
#     # 더미 데이터
#     categories = ['의류', '신발', '액세서리', '가방', '기타']
#     sizes = [45, 25, 15, 10, 5]
    
#     # 색상 설정
#     colors = [COLORS['teal'], COLORS['purple'], COLORS['red'], COLORS['blue'], COLORS['orange']]
    
#     # 그래프 생성
#     plt.figure(figsize=(7, 5), facecolor=COLORS['card_bg'])
#     ax = plt.subplot(111)
    
#     # 파이 차트 생성
#     wedges, texts, autotexts = plt.pie(
#         sizes, 
#         labels=None, 
#         colors=colors, 
#         autopct='%1.1f%%', 
#         startangle=90, 
#         wedgeprops=dict(edgecolor='white', linewidth=2),
#         textprops=dict(color='white', fontweight='bold', fontsize=12)
#     )
    
#     # 텍스트 스타일 설정
#     for autotext in autotexts:
#         autotext.set_fontsize(11)
#         autotext.set_fontweight('bold')
    
#     # 범례 추가
#     plt.legend(
#         wedges, 
#         categories,
#         title="카테고리",
#         loc="center left",
#         bbox_to_anchor=(1, 0, 0.5, 1),
#         fontsize=10
#     )
    
#     # 레이아웃 설정
#     plt.axis('equal')
#     plt.title('카테고리별 분포', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=20)
#     plt.tight_layout()
    
#     # 이미지 저장
#     img_dir = ensure_static_dirs()
#     file_path = os.path.join(img_dir, 'category_chart.png')
#     plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
#     plt.close()
    
#     return url_for('static', filename='images/category_chart.png')

# # 3. 워드클라우드 생성
# def generate_wordcloud(period):
#     # 더미 텍스트 데이터
#     text = "브랜드 패션 한국 섬유 제품 Y2K 스트리트웨어 뉴트로 미니멀 오버사이즈 빈티지 스트라이프 파스텔 스포티 플로럴 네온 아방가르드 테크웨어 플랫폼 레이어링 브랜드 브랜드 패션 패션 패션 한국 한국 Y2K Y2K Y2K 스트리트웨어 스트리트웨어 미니멀 오버사이즈 오버사이즈"
    
#     # 색상 맵 생성 (청록색 그라데이션)
#     def teal_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
#         # 글자 크기에 따른 색상 변환
#         if font_size > 40:
#             return COLORS['teal']
#         elif font_size > 30:
#             return COLORS['blue']
#         elif font_size > 20:
#             return COLORS['purple']
#         else:
#             return COLORS['red']
    
#     # 워드클라우드 생성
#     wordcloud = WordCloud(
#         width=800, 
#         height=400, 
#         background_color=COLORS['card_bg'],
#         color_func=teal_color_func,
#         max_words=100,
#         prefer_horizontal=0.9,
#         relative_scaling=0.6,
#         font_path=None,
#         max_font_size=120,
#         min_font_size=8,
#         mask=None,
#         contour_width=0,
#         contour_color=None,
#         repeat=False
#     ).generate(text)
    
#     # 이미지 표시
#     plt.figure(figsize=(10, 5), facecolor=COLORS['card_bg'])
#     plt.imshow(wordcloud, interpolation='bilinear')
#     plt.axis('off')
#     plt.title('키워드 빈도 워드클라우드', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=20)
#     plt.tight_layout()
    
#     # 이미지 저장
#     img_dir = ensure_static_dirs()
#     file_path = os.path.join(img_dir, 'wordcloud.png')
#     plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
#     plt.close()
    
#     return url_for('static', filename='images/wordcloud.png')

# # 4. TF-IDF 차트 생성
# def generate_tfidf_chart(period):
#     # 더미 데이터 (키워드와 TF-IDF 값)
#     keywords = ['브랜드', '패션', '한국', 'Y2K', '스트리트웨어', '뉴트로', '섬유', '제품', '미니멀', '오버사이즈']
#     values = [0.85, 0.78, 0.72, 0.68, 0.65, 0.63, 0.58, 0.55, 0.52, 0.48]
    
#     # 데이터 정렬 (내림차순)
#     sorted_indices = np.argsort(values)[::-1]
#     keywords = [keywords[i] for i in sorted_indices]
#     values = [values[i] for i in sorted_indices]
    
#     # 차트 생성
#     plt.figure(figsize=(8, 6), facecolor=COLORS['card_bg'])
#     ax = plt.subplot(111)
    
#     # 그라데이션 색상 생성
#     num_bars = len(keywords)
#     colors = plt.cm.cool(np.linspace(0.3, 0.7, num_bars))
    
#     # 수평 막대 그래프
#     bars = plt.barh(keywords, values, color=colors, height=0.6)
    
#     # 모던 스타일 적용
#     apply_modern_style(ax, title='키워드 중요도 (TF-IDF)')
    
#     # 축 설정
#     plt.xlim(0, max(values) * 1.15)  # 여백 추가
#     plt.xlabel('TF-IDF 값')
    
#     # 막대 끝에 값 표시
#     for i, v in enumerate(values):
#         plt.text(v + 0.02, i, f'{v:.2f}', color=COLORS['text_secondary'], va='center', ha='left', fontsize=10, fontweight='bold')
    
#     # 레이아웃 설정
#     plt.tight_layout()
    
#     # 이미지 저장
#     img_dir = ensure_static_dirs()
#     file_path = os.path.join(img_dir, 'tfidf_chart.png')
#     plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
#     plt.close()
    
#     return url_for('static', filename='images/tfidf_chart.png')

# # 5. 키워드 트렌드 차트 생성
# def generate_trend_chart(period, keyword, chart_type):
#     # 더미 데이터 생성
#     today = datetime.now()
#     dates = [today - timedelta(days=i) for i in range(30, 0, -1)]
    
#     if chart_type == 'type1':
#         # 첫 번째 차트: 키워드 언급 빈도
#         values = np.concatenate([
#             np.linspace(10, 20, 10),
#             np.linspace(20, 40, 10),
#             np.linspace(40, 30, 10)
#         ])
        
#         # 차트 생성
#         plt.figure(figsize=(8, 4), facecolor=COLORS['card_bg'])
#         ax = plt.subplot(111)
        
#         # 그라데이션 영역 채우기
#         gradient_colors = create_gradient_color(COLORS['teal'], COLORS['teal_gradient'])
#         n_values = len(values)
        
#         # 영역 채우기 그래프
#         ax.fill_between(
#             dates, 
#             values, 
#             alpha=0.3, 
#             color=COLORS['teal'],
#             linewidth=0
#         )
        
#         # 선 그래프
#         line = ax.plot(
#             dates, 
#             values, 
#             linewidth=3, 
#             color=COLORS['teal'],
#         )[0]
        
#         # 데이터 포인트 (원)
#         ax.scatter(
#             dates, 
#             values, 
#             s=70, 
#             color=COLORS['teal'], 
#             zorder=4, 
#             edgecolors='white', 
#             linewidth=1.5
#         )
        
#         # 모던 스타일 적용
#         apply_modern_style(ax)
        
#         # 축 설정
#         plt.xlabel('날짜')
#         plt.ylabel('언급 빈도')
#         plt.title(f'"{keyword}" 키워드 언급 추이', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=15)
        
#         # x축 날짜 포맷 설정
#         plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
#         plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        
#         # 최대값 지점 강조
#         max_idx = np.argmax(values)
#         plt.scatter(
#             dates[max_idx], 
#             values[max_idx], 
#             s=120, 
#             color=COLORS['teal'], 
#             zorder=5,
#             edgecolors='white',
#             linewidth=2
#         )
#         plt.annotate(
#             f'최대: {values[max_idx]:.1f}',
#             (dates[max_idx], values[max_idx]),
#             xytext=(10, 10),
#             textcoords='offset points',
#             fontsize=10,
#             fontweight='bold',
#             color=COLORS['text_dark'],
#             backgroundcolor='white',
#             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLORS['teal'], alpha=0.9)
#         )
        
#         # 레이아웃 설정
#         plt.tight_layout()
        
#         # 이미지 저장
#         img_dir = ensure_static_dirs()
#         file_path = os.path.join(img_dir, f'trend_chart_1_{keyword}.png')
#         plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
#         plt.close()
        
#         return url_for('static', filename=f'images/trend_chart_1_{keyword}.png')
    
#     else:
#         # 두 번째 차트: 키워드 관련 데이터 (관련 매체별 언급 수)
#         media_data = {
#             '뉴스': np.concatenate([np.linspace(5, 10, 10), np.linspace(10, 25, 10), np.linspace(25, 20, 10)]),
#             '매거진': np.concatenate([np.linspace(3, 8, 10), np.linspace(8, 15, 10), np.linspace(15, 10, 10)]),
#             '무신사': np.concatenate([np.linspace(2, 5, 10), np.linspace(5, 15, 10), np.linspace(15, 5, 10)])
#         }
        
#         # 차트 색상
#         colors = [COLORS['teal'], COLORS['purple'], COLORS['red']]
        
#         # 차트 생성
#         plt.figure(figsize=(8, 4), facecolor=COLORS['card_bg'])
#         ax = plt.subplot(111)
        
#         # 각 매체별 선 그래프
#         for i, (medium, data) in enumerate(media_data.items()):
#             # 영역 채우기
#             ax.fill_between(
#                 dates, 
#                 data, 
#                 alpha=0.1, 
#                 color=colors[i],
#                 linewidth=0
#             )
            
#             # 선 그래프
#             line = ax.plot(
#                 dates, 
#                 data, 
#                 linestyle='-', 
#                 label=medium, 
#                 color=colors[i], 
#                 linewidth=2.5, 
#             )[0]
            
#             # 마지막 포인트 강조
#             last_idx = len(data) - 1
#             ax.scatter(
#                 dates[last_idx], 
#                 data[last_idx], 
#                 s=70, 
#                 color=colors[i], 
#                 zorder=4, 
#                 edgecolors='white', 
#                 linewidth=1.5
#             )
        
#         # 모던 스타일 적용
#         apply_modern_style(ax)
        
#         # 축 설정
#         plt.xlabel('날짜')
#         plt.ylabel('언급 수')
#         plt.title(f'"{keyword}" 매체별 언급 추이', fontsize=14, fontweight='bold', color=COLORS['text_dark'], pad=15)
        
#         # 범례 설정
#         legend = plt.legend(
#             frameon=True, 
#             facecolor=COLORS['card_bg'], 
#             edgecolor=COLORS['border'],
#             fontsize=10,
#             loc='upper left'
#         )
        
#         # x축 날짜 포맷 설정
#         plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
#         plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        
#         # 레이아웃 설정
#         plt.tight_layout()
        
#         # 이미지 저장
#         img_dir = ensure_static_dirs()
#         file_path = os.path.join(img_dir, f'trend_chart_2_{keyword}.png')
#         plt.savefig(file_path, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100)
#         plt.close()
        
#         return url_for('static', filename=f'images/trend_chart_2_{keyword}.png') [COLORS['teal'], COLORS['purple'], COLORS['blue'], COLORS['red']]
