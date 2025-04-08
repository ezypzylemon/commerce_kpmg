import streamlit as st
import pandas as pd
import mysql.connector
from config import MYSQL_CONFIG
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx
from collections import Counter
from itertools import combinations
from io import BytesIO
import matplotlib.font_manager as fm
import plotly.graph_objects as go
from datetime import datetime, timedelta


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
    '제품', '디자인', '에디터', '정윤', '보그', '년대', '등장'
])

def remove_stopwords(tokens):
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

# ------------------------
# 데이터 로드 함수
# ------------------------
def get_mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

@st.cache_data
def load_data():
    conn = get_mysql_connection()
    query = "SELECT category, upload_date, tokens, source FROM tokenised;"
    df = pd.read_sql(query, conn)
    conn.close()
    df['tokens'] = df['tokens'].apply(eval)
    df['upload_date'] = pd.to_datetime(df['upload_date'])
    return df

df = load_data()

# ------------------------
# 사이드바 필터
# ------------------------
st.sidebar.title("필터")
category = st.sidebar.selectbox("카테고리", df['category'].unique())
filtered_df = df[df['category'] == category]

# ------------------------
# 탭 구성
# ------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 키워드 트렌드", "📈 TF-IDF 분석", "🕸️ 키워드 네트워크", "📉 아이템 증감률 분석", "📰 매거진별 분석", "🖼️ 카드뉴스", "👔 MD 인사이트"
])


# ------------------------
# 📊 탭 1: 트렌드
# ------------------------
with tab1:
    st.subheader(f"{category.upper()} 상위 키워드 Top 20")
    all_tokens = [token for tokens in filtered_df['tokens'] for token in remove_stopwords(tokens)]
    token_counts = pd.Series(all_tokens).value_counts().head(20).reset_index()
    token_counts.columns = ['token', 'count']
    fig = px.bar(token_counts, x='token', y='count')
    st.plotly_chart(fig)

    st.subheader("워드클라우드")
    wordcloud = WordCloud(
        font_path="C:/Windows/Fonts/malgun.ttf",
        background_color="white",
        width=800,
        height=400
    ).generate(' '.join(all_tokens))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

# ------------------------
# 📈 탭 2: TF-IDF
# ------------------------
with tab2:
    st.subheader("TF-IDF 핵심 키워드")
    filtered_df = filtered_df.reset_index(drop=True)
    article_idx = st.selectbox("기사 선택 (인덱스)", range(len(filtered_df)))
    
    docs = filtered_df['tokens'].apply(lambda x: ' '.join(remove_stopwords(x))).tolist()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix[article_idx].toarray()[0]
    top_n = scores.argsort()[-20:][::-1]
    top_keywords = [(feature_names[i], scores[i]) for i in top_n if scores[i] > 0]

    if top_keywords:
        tk_df = pd.DataFrame(top_keywords, columns=['token', 'tfidf'])
        fig = px.bar(tk_df, x='token', y='tfidf')
        st.plotly_chart(fig)
    else:
        st.info("TF-IDF 키워드가 없습니다.")

# ------------------------
# 🕸️ 탭 3: 네트워크
# ------------------------
with tab3:
    st.subheader("키워드 네트워크 시각화")

    font_path = "C:/Windows/Fonts/malgun.ttf"
    font_prop = fm.FontProperties(fname=font_path)
    font_name = font_prop.get_name()

    edge_counter = Counter()
    for tokens in filtered_df['tokens']:
        cleaned = remove_stopwords(tokens)
        unique_tokens = list(set(cleaned))
        if len(unique_tokens) >= 2:
            edge_counter.update(combinations(unique_tokens, 2))
    top_edges = edge_counter.most_common(30)

    G = nx.Graph()
    G.add_edges_from([(a, b, {'weight': w}) for (a, b), w in top_edges])

    pos = nx.spring_layout(G, k=0.5, seed=42)
    weights = [G[u][v]['weight'] for u, v in G.edges()]
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=600)
    nx.draw_networkx_edges(G, pos, edge_color=weights, edge_cmap=plt.cm.Blues, width=2)
    nx.draw_networkx_labels(G, pos, font_family=font_name, font_size=10)
    st.pyplot(plt.gcf())


# ------------------------
# 📉 탭 4: 아이템 증감률 분석
# ------------------------
with tab4:
    st.subheader("🧥 아이템 트렌드 변화 (기간별 비교)")

    # 기준 선택
    keyword_type = st.radio("기준:", ["아이템", "컬러", "소재", "프린트", "스타일"], horizontal=True)

    # 키워드 리스트 정의 (동의어/유사어 묶기)
    keyword_dict = {
        "아이템": ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
        "컬러": ['블랙', '화이트', '베이지', '브라운', '그레이', '블루', '스카이블루', '네이비', '옐로우', '핑크', '레드', '카키', '라벤더', '그린', '퍼플', '민트', '오렌지', '와인', '멀티'],
        "소재": ['합성섬유', '면', '가죽', '시폰', '니트', '데님', '레이스', '시퀸/글리터', '캐시미어/울', '스웨이드', '벨벳', '스판덱스', '퍼', '트위드', '비닐/PVC', '메시', '린넨', '자카드', '저지', '코듀로이', '네오프렌', '플리스', '무스탕', '앙고라', '실크'],
        "프린트": ['무지', '플로럴', '스트라이프', '체크', '그래픽', '도트', '레터링', '페이즐리', '호피', '그라데이션', '타이다이', '카무플라쥬/카모플라쥬', '지그재그', '지브라', '해골', '멀티'],
        "스타일": ['컨트리', '웨딩', '프레피', '히피', '아웃도어', '밀리터리', '복고', '페미닌', '캐주얼', '마린', '에스닉', '오피스룩', '파티', '리조트', '펑크']
    }

    keyword_aliases = {
        '시퀸/글리터': ['시퀸', '글리터'],
        '캐시미어/울': ['캐시미어', '울'],
        '비닐/PVC': ['비닐', 'pvc', 'PVC'],
        '카무플라쥬/카모플라쥬': ['카무플라쥬', '카모플라쥬']
    }

    ITEM_KEYWORDS = keyword_dict[keyword_type]

    st.markdown("### 📆 분석 기간 설정")
    period_option = st.selectbox("비교 기간을 선택하세요", ['1주일', '2주일', '1개월', '3개월', '6개월', '1년', '2년', '직접 설정'])

    today = pd.to_datetime(datetime.today().date())
    if period_option == '직접 설정':
        col1, col2 = st.columns(2)
        with col1:
            curr_start = st.date_input("현재 시작일", value=today - timedelta(days=30))
            curr_end = st.date_input("현재 종료일", value=today)
        with col2:
            prev_start = st.date_input("이전 시작일", value=today - timedelta(days=60))
            prev_end = st.date_input("이전 종료일", value=today - timedelta(days=31))
    else:
        delta_map = {
            '1주일': 7,
            '2주일': 14,
            '1개월': 30,
            '3개월': 90,
            '6개월': 180,
            '1년': 365,
            '2년': 730
        }
        delta = timedelta(days=delta_map[period_option])
        curr_end = today
        curr_start = today - delta
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - delta + timedelta(days=1)

    # 기간별 데이터 필터링
    df_before = filtered_df[
        (filtered_df['upload_date'] >= pd.to_datetime(prev_start)) &
        (filtered_df['upload_date'] <= pd.to_datetime(prev_end))
    ]
    df_current = filtered_df[
        (filtered_df['upload_date'] >= pd.to_datetime(curr_start)) &
        (filtered_df['upload_date'] <= pd.to_datetime(curr_end))
    ]

    def count_items(df):
        all_tokens = [token for tokens in df['tokens'] for token in remove_stopwords(tokens)]
        counts = pd.Series(all_tokens).value_counts()
        result = {}
        for item in ITEM_KEYWORDS:
            if item in keyword_aliases:
                result[item] = sum(counts.get(alias, 0) for alias in keyword_aliases[item])
            else:
                result[item] = counts.get(item, 0)
        return result

    counts_current = count_items(df_current)
    counts_before = count_items(df_before)

    # 결과 데이터프레임 생성
    trend_df = pd.DataFrame({
        'item': ITEM_KEYWORDS,
        '현재 언급량': [counts_current[i] for i in ITEM_KEYWORDS],
        '이전 언급량': [counts_before[i] for i in ITEM_KEYWORDS]
    })
    trend_df['증감률(%)'] = ((trend_df['현재 언급량'] - trend_df['이전 언급량']) /
                         trend_df['이전 언급량'].replace(0, 1)) * 100

    # 시각화 ① 이전 vs 현재 언급량
    st.markdown("### 📊 이전 vs 현재 언급량 비교")
    fig_compare = px.bar(
        trend_df.melt(id_vars='item', value_vars=['이전 언급량', '현재 언급량'], 
                      var_name='기간', value_name='언급량')
        .replace({
            '이전 언급량': f"{prev_start.strftime('%Y.%m.%d')}~{prev_end.strftime('%Y.%m.%d')}",
            '현재 언급량': f"{curr_start.strftime('%Y.%m.%d')}~{curr_end.strftime('%Y.%m.%d')}"
        }),
        x='item', y='언급량', color='기간',
        barmode='group', title=f"{keyword_type}별 언급량 (이전 vs 현재)",
        labels={'item': keyword_type}
    )
    st.plotly_chart(fig_compare)

    # 시각화 ② 증감률
    st.markdown("### 📈 증감률(%) 변화")
    fig_pct = px.bar(
        trend_df.sort_values("증감률(%)", ascending=False),
        x="item", y="증감률(%)", title=f"{keyword_type}별 증감률(%) 변화",
        labels={"item": keyword_type}
    )
    st.plotly_chart(fig_pct)


    # 시각화 ③ 라인그래프: 기간별 언급량 추세
    st.markdown("### 📉 기간별 언급량 추세 (라인 그래프)")
    freq_option = st.selectbox("그래프 기준 기간 선택 (일자 기준)", ['1주일', '1개월', '3개월', '6개월', '1년'], index=1)

    freq_days = {
        '1주일': 7,
        '1개월': 30,
        '3개월': 90,
        '6개월': 180,
        '1년': 365
    }
    graph_delta = timedelta(days=freq_days[freq_option])
    graph_start = today - graph_delta
    df_graph = filtered_df[(filtered_df['upload_date'] >= graph_start) & (filtered_df['upload_date'] <= today)].copy()
    df_graph['upload_date'] = pd.to_datetime(df_graph['upload_date'])

    # 집계
    def count_weekly_mentions(df, keyword_list):
        df['week'] = df['upload_date'].dt.to_period('W').apply(lambda r: r.start_time)
        rows = []
        for week, group in df.groupby('week'):
            tokens = [token for tokens in group['tokens'] for token in remove_stopwords(tokens)]
            counts = pd.Series(tokens).value_counts()
            row = {'week': week}
            for kw in keyword_list:
                aliases = keyword_aliases.get(kw, [kw])
                row[kw] = sum(counts.get(a, 0) for a in aliases)
            rows.append(row)
        return pd.DataFrame(rows).sort_values('week')

    df_line = count_weekly_mentions(df_graph, ITEM_KEYWORDS)
    df_line_melted = df_line.melt(id_vars='week', var_name='키워드', value_name='언급량')

    # 키워드 필터 추가
    selected_keywords = st.multiselect("확인할 키워드를 선택하세요", ITEM_KEYWORDS, default=ITEM_KEYWORDS[:5])
    df_line_melted = df_line_melted[df_line_melted['키워드'].isin(selected_keywords)]

    fig_line = px.line(
        df_line_melted,
        x='week', y='언급량', color='키워드',
        title=f"{keyword_type}별 {freq_option}간 주간 언급량 추세",
        labels={'week': '주차'}
    )
    st.plotly_chart(fig_line)

    # 테이블 출력
    st.dataframe(trend_df.sort_values("현재 언급량", ascending=False), use_container_width=True)


# ------------------------
# 📰 탭 5: 매거진 비교
# ------------------------
with tab5:
    st.subheader("📰 매거진별 트렌드 비교 분석")

    # 매거진 선택
    magazines = sorted(filtered_df['source'].unique())
    selected_magazines = st.multiselect("매거진 선택", magazines, default=magazines[:3])

    # 분석 기간 설정
    date_range = st.selectbox("분석 기간", ['1개월', '3개월', '6개월', '1년', '전체'] )
    today = pd.to_datetime(datetime.today().date())
    days_map = {'1개월': 30, '3개월': 90, '6개월': 180, '1년': 365}
    if date_range != '전체':
        start_date = today - timedelta(days=days_map[date_range])
        df_mag = filtered_df[(filtered_df['upload_date'] >= start_date)]
    else:
        df_mag = filtered_df.copy()

    df_mag = df_mag[df_mag['source'].isin(selected_magazines)]

    # ------------------------
    # 1️⃣ 상위 키워드 비교
    # ------------------------
    st.markdown("### 🔍 매거진별 상위 키워드 TOP 30")
    top_tokens_per_mag = {}
    for mag in selected_magazines:
        tokens = [token for tokens in df_mag[df_mag['source'] == mag]['tokens'] for token in remove_stopwords(tokens)]
        top_tokens_per_mag[mag] = pd.Series(tokens).value_counts().head(30)

    fig_top = go.Figure()
    for mag in selected_magazines:
        fig_top.add_trace(go.Bar(
            x=top_tokens_per_mag[mag].index,
            y=top_tokens_per_mag[mag].values,
            name=mag
        ))
    fig_top.update_layout(barmode='group', title="매거진별 상위 키워드 비교", xaxis_title="키워드", yaxis_title="언급량")
    st.plotly_chart(fig_top)

    # ------------------------
    # 2️⃣ 공통 vs 고유 키워드
    # ------------------------
    st.markdown("### 🧬 공통 키워드 vs 고유 키워드")
    token_sets = {mag: set(top_tokens_per_mag[mag].index) for mag in selected_magazines}
    common_tokens = set.intersection(*token_sets.values()) if len(token_sets) > 1 else set()
    unique_tokens = {mag: token_sets[mag] - common_tokens for mag in selected_magazines}

    st.markdown("#### 🧩 공통 키워드")
    if common_tokens:
        tags_html = "".join([
            f"<span style='background:#E0F7FA; padding:6px 12px; border-radius:15px; margin:4px; display:inline-block;'>{kw}</span>"
            for kw in sorted(common_tokens)
        ])
        st.markdown(tags_html, unsafe_allow_html=True)
    else:
        st.markdown("-")

    st.markdown("#### ✴️ 매거진별 고유 키워드")
    col_count = 3 if len(selected_magazines) >= 3 else len(selected_magazines)
    cols = st.columns(col_count)
    colors = ["#3CB371", "#1E90FF", "#FF6347", "#9370DB"]  # 카드 색상
    for idx, mag in enumerate(selected_magazines):
        with cols[idx % col_count]:
            st.markdown(f"""
                <div style='background-color:{colors[idx % len(colors)]}; padding: 10px 15px; border-radius: 10px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h5 style='color:white; text-align:center; font-size:18px; margin-bottom:8px;'>{mag}</h5>
                    <ol style='color:white; font-size:15px;'>
                        {''.join(f'<li>{kw}</li>' for kw in sorted(unique_tokens[mag])[:10])}
                    </ol>
                </div>
            """, unsafe_allow_html=True)

    # ------------------------
    # 3️⃣ TF-IDF 고유 키워드 분석
    # ------------------------
    st.markdown("### 🧠 매거진별 TF-IDF 대표 키워드")
    mag_groups = df_mag.groupby("source")['tokens'].apply(lambda x: [w for lst in x for w in remove_stopwords(lst)])
    docs = [" ".join(tokens) for tokens in mag_groups]
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(docs)
    feature_names = tfidf.get_feature_names_out()

    col_count = 3 if len(selected_magazines) >= 3 else len(selected_magazines)
    cols = st.columns(col_count)
    colors = ["#3CB371", "#1E90FF", "#FF6347", "#9370DB"]

    for i, mag in enumerate(mag_groups.index):
        row = tfidf_matrix[i].toarray().flatten()
        top_n = row.argsort()[-10:][::-1]
        keywords = [(feature_names[j], round(row[j], 4)) for j in top_n]
        with cols[i % col_count]:
            st.markdown(f"""
                <div style='background-color:{colors[i % len(colors)]}; padding: 10px 15px; border-radius: 10px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h5 style='color:white; text-align:center; font-size:18px; margin-bottom:8px;'>{mag}</h5>
                    <ol style='color:white; font-size:15px;'>
                        {''.join(f'<li>{kw[0]} ({kw[1]})</li>' for kw in keywords)}
                    </ol>
                </div>
            """, unsafe_allow_html=True)

    # ------------------------
    # 4️⃣ 키워드별 매거진 언급량 추세 (라인그래프)
    # ------------------------
    st.markdown("### 📈 키워드별 매거진 언급량 추세")
    focus_keywords_input = st.text_input("분석할 키워드 입력 (쉼표로 구분)", value='블랙, 시어, 클래식')
    focus_keywords = [kw.strip() for kw in focus_keywords_input.split(',') if kw.strip()]

    df_mag['week'] = df_mag['upload_date'].dt.to_period('W').apply(lambda r: r.start_time)
    trend_rows = []

    for mag in selected_magazines:
        mag_df = df_mag[df_mag['source'] == mag]
        for week, group in mag_df.groupby('week'):
            all_tokens = [token for tokens in group['tokens'] for token in remove_stopwords(tokens)]
            token_counts = pd.Series(all_tokens).value_counts()
            for kw in focus_keywords:
                trend_rows.append({
                    'week': week,
                    'keyword': kw,
                    'count': token_counts.get(kw, 0),
                    'magazine': mag
                })

    df_kw_trend = pd.DataFrame(trend_rows)
    fig_kw_line = px.line(
        df_kw_trend,
        x='week', y='count', color='magazine',
        facet_col='keyword', facet_col_wrap=2,
        markers=True,
        title='선택 키워드별 매거진 언급량 추세',
        labels={'count': '언급량', 'week': '주차', 'magazine': '매거진'}
    )
    st.plotly_chart(fig_kw_line)


import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import mysql.connector
from config import MYSQL_CONFIG

@st.cache_data
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

@st.cache_data
def extract_og_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        og_img = soup.find("meta", property="og:image")
        return og_img["content"] if og_img else None
    except:
        return None

# 탭6 내부
with tab6:
    st.subheader("🖼️ 카드뉴스")

    articles = load_magazine_articles()

    for i in range(0, len(articles), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(articles):
                row = articles.iloc[i + j]
                with cols[j]:
                    img_url = extract_og_image(row['article_url'])
                    if img_url:
                        st.image(img_url, use_container_width=True)
                    else:
                        st.image("default.jpg", use_column_width=True)  # 기본 이미지 대체 가능
                    st.markdown(f"**[{row['title']}]({row['article_url']})**", unsafe_allow_html=True)
                    st.caption(f"🗓️ {row['upload_date']}")




# ------------------------
# 👔 탭 7: MD 인사이트
# ------------------------
with tab7:
    st.subheader("👔 패션 MD 인사이트 대시보드")

    # 공통 키워드 확인 (기존 탭5 로직 일부 활용)
    st.markdown("### 📋 매거진 공통 키워드 기반 분석")
    
    # 매거진 선택
    magazines = sorted(df['source'].unique())
    selected_magazines = st.multiselect("분석할 매거진 선택", magazines, default=magazines[:3])
    
    # # 분석 기간 설정
    # date_range2 = st.selectbox("분석 기간", ['1개월', '3개월', '6개월', '1년', '전체'])
    # today = pd.to_datetime(datetime.today().date())
    # days_map = {'1개월': 30, '3개월': 90, '6개월': 180, '1년': 365}
    
    if date_range  != '전체':
        start_date = today - timedelta(days=days_map[date_range])
        df_mag = df[(df['upload_date'] >= start_date)]
    else:
        df_mag = df.copy()
    
    df_mag = df_mag[df_mag['source'].isin(selected_magazines)]
    
    # 공통 키워드 추출
    if selected_magazines:
        token_sets = {}
        for mag in selected_magazines:
            tokens = [token for tokens in df_mag[df_mag['source'] == mag]['tokens'] for token in remove_stopwords(tokens)]
            top_tokens = pd.Series(tokens).value_counts().head(50).index.tolist()  # 상위 50개 키워드 기준
            token_sets[mag] = set(top_tokens)
        
        common_tokens = set.intersection(*token_sets.values()) if len(token_sets) > 1 else set()
        
        # 공통 키워드 표시
        st.markdown("#### 🧩 매거진 공통 키워드")
        if common_tokens:
            tags_html = "".join([
                f"<span style='background:#E0F7FA; padding:6px 12px; border-radius:15px; margin:4px; display:inline-block;'>{kw}</span>"
                for kw in sorted(common_tokens)
            ])
            st.markdown(tags_html, unsafe_allow_html=True)
            
            # 분석할 키워드 선택
            keyword_to_analyze = st.selectbox("분석할 공통 키워드 선택", sorted(common_tokens))
            
            # 시각화 옵션 선택
            visual_option = st.radio(
                "분석 유형 선택", 
                ["상품 기획 인사이트", "시즌 트렌드 분석", "구매 전략 시뮬레이션"], 
                horizontal=True
            )
            
            # 선택한 키워드가 포함된 문서 필터링
            filtered_docs = []
            for mag in selected_magazines:
                mag_df = df_mag[df_mag['source'] == mag]
                for _, row in mag_df.iterrows():
                    if keyword_to_analyze in remove_stopwords(row['tokens']):
                        filtered_docs.append(row)
            
            if filtered_docs:
                filtered_docs_df = pd.DataFrame(filtered_docs)
                
                # 카테고리 정의 (MD 분석용)
                categories = {
                    "아이템": ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
                    "컬러": ['블랙', '화이트', '베이지', '브라운', '그레이', '블루', '스카이블루', '네이비', '옐로우', '핑크', '레드', '카키', '라벤더', '그린', '퍼플', '민트', '오렌지', '와인', '멀티'],
                    "소재": ['합성섬유', '면', '가죽', '시폰', '니트', '데님', '레이스', '시퀸', '글리터', '캐시미어', '울', '스웨이드', '벨벳', '스판덱스', '퍼', '트위드', '비닐', 'PVC', '메시', '린넨', '자카드', '저지', '코듀로이'],
                    "스타일": ['컨트리', '웨딩', '프레피', '히피', '아웃도어', '밀리터리', '복고', '페미닌', '캐주얼', '마린', '에스닉', '오피스룩', '파티', '리조트', '펑크']
                }
                
                # 1. 상품 기획 인사이트
                if visual_option == "상품 기획 인사이트":
                    st.markdown(f"### '{keyword_to_analyze}' 상품 기획 인사이트")
                    
                    # 1-1. 연관 키워드 분석 (TF-IDF 기반)
                    st.markdown("#### 🏷️ 연관 키워드 분석")
                    
                    # 전체 코퍼스와 필터링된 문서 준비
                    all_docs = [' '.join(remove_stopwords(tokens)) for tokens in df_mag['tokens']]
                    filtered_docs_text = [' '.join(remove_stopwords(tokens)) for tokens in filtered_docs_df['tokens']]
                    
                    # TF-IDF 계산
                    vectorizer = TfidfVectorizer(min_df=2)
                    vectorizer.fit(all_docs)
                    tfidf_matrix = vectorizer.transform(filtered_docs_text)
                    
                    # 단어별 평균 TF-IDF 계산
                    feature_names = vectorizer.get_feature_names_out()
                    tfidf_scores = {}
                    
                    for i in range(tfidf_matrix.shape[0]):
                        doc_vector = tfidf_matrix[i]
                        for idx, score in zip(doc_vector.indices, doc_vector.data):
                            word = feature_names[idx]
                            if word != keyword_to_analyze:
                                tfidf_scores[word] = tfidf_scores.get(word, 0) + score
                    
                    # 평균 계산
                    for word in tfidf_scores:
                        tfidf_scores[word] = tfidf_scores[word] / len(filtered_docs_text)
                    
                    # 상위 키워드를 카테고리별로 분류
                    top_keywords = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:30]
                    
                    # 키워드를 카테고리별로 분류
                    categorized_keywords = {cat: [] for cat in categories}
                    categorized_keywords["기타"] = []
                    
                    for word, score in top_keywords:
                        categorized = False
                        for cat, words in categories.items():
                            if word in words:
                                categorized_keywords[cat].append((word, score))
                                categorized = True
                                break
                        if not categorized:
                            categorized_keywords["기타"].append((word, score))
                    
                    # 카테고리별로 결과 표시
                    cols = st.columns(len(categories) + 1)  # 카테고리 + 기타
                    
                    for i, (cat, keywords) in enumerate(categorized_keywords.items()):
                        with cols[i]:
                            st.markdown(f"**{cat}**")
                            if keywords:
                                for word, score in keywords[:5]:  # 각 카테고리별 상위 5개만
                                    st.markdown(f"- {word} ({score:.3f})")
                            else:
                                st.markdown("- 없음")
                    
                    # 1-2. 상품 기획 제안 시각화
                    st.markdown("#### 📊 상품 구성 제안")
                    
                    # 시각화 데이터 준비
                    item_counts = {}
                    color_counts = {}
                    material_counts = {}
                    style_counts = {}
                    
                    # 토큰 빈도 계산
                    all_tokens = [token for tokens in filtered_docs_df['tokens'] for token in remove_stopwords(tokens)]
                    token_counts = pd.Series(all_tokens).value_counts()
                    
                    # 카테고리별 집계
                    for item in categories["아이템"]:
                        item_counts[item] = token_counts.get(item, 0)
                    for color in categories["컬러"]:
                        color_counts[color] = token_counts.get(color, 0)
                    for material in categories["소재"]:
                        material_counts[material] = token_counts.get(material, 0)
                    for style in categories["스타일"]:
                        style_counts[style] = token_counts.get(style, 0)
                    
                    # 아이템별 비중 파이차트
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 아이템 분포
                        item_df = pd.DataFrame({
                            '아이템': list(item_counts.keys()),
                            '빈도': list(item_counts.values())
                        }).sort_values('빈도', ascending=False).head(8)  # 상위 8개만
                        
                        if item_df['빈도'].sum() > 0:
                            fig = px.pie(
                                item_df, values='빈도', names='아이템',
                                title=f"'{keyword_to_analyze}' 관련 주요 아이템 구성",
                                hole=0.4
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("아이템 데이터가 충분하지 않습니다.")
                    
                    with col2:
                        # 컬러 분포
                        color_df = pd.DataFrame({
                            '컬러': list(color_counts.keys()),
                            '빈도': list(color_counts.values())
                        }).sort_values('빈도', ascending=False).head(8)  # 상위 8개만
                        
                        if color_df['빈도'].sum() > 0:
                            fig = px.pie(
                                color_df, values='빈도', names='컬러',
                                title=f"'{keyword_to_analyze}' 관련 주요 컬러 구성",
                                hole=0.4
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("컬러 데이터가 충분하지 않습니다.")
                    
                    # 소재 및 스타일 바 차트
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 소재 분포
                        material_df = pd.DataFrame({
                            '소재': list(material_counts.keys()),
                            '빈도': list(material_counts.values())
                        }).sort_values('빈도', ascending=False).head(8)  # 상위 8개만
                        
                        if material_df['빈도'].sum() > 0:
                            fig = px.bar(
                                material_df, x='소재', y='빈도',
                                title=f"'{keyword_to_analyze}' 관련 주요 소재"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("소재 데이터가 충분하지 않습니다.")
                    
                    with col2:
                        # 스타일 분포
                        style_df = pd.DataFrame({
                            '스타일': list(style_counts.keys()),
                            '빈도': list(style_counts.values())
                        }).sort_values('빈도', ascending=False).head(8)  # 상위 8개만
                        
                        if style_df['빈도'].sum() > 0:
                            fig = px.bar(
                                style_df, x='스타일', y='빈도',
                                title=f"'{keyword_to_analyze}' 관련 주요 스타일"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("스타일 데이터가 충분하지 않습니다.")
                    
                    # 1-3. MD 핵심 인사이트 카드
                    st.markdown("#### 💡 MD 핵심 인사이트")
                    
                    # 상위 아이템, 컬러, 소재, 스타일 추출
                    top_items = item_df['아이템'].tolist()[:3] if not item_df.empty and item_df['빈도'].sum() > 0 else []
                    top_colors = color_df['컬러'].tolist()[:3] if not color_df.empty and color_df['빈도'].sum() > 0 else []
                    top_materials = material_df['소재'].tolist()[:3] if not material_df.empty and material_df['빈도'].sum() > 0 else []
                    top_styles = style_df['스타일'].tolist()[:3] if not style_df.empty and style_df['빈도'].sum() > 0 else []
                    
                    # 인사이트 카드 생성
                    cols = st.columns(2)
                    
                    with cols[0]:
                        st.markdown(f"""
                        <div style='background-color:#f0f7ff; padding:20px; border-radius:10px; border-left:5px solid #1E88E5;'>
                            <h4 style='color:#1565C0; margin-top:0;'>상품 구성 제안</h4>
                            <p><strong>주력 아이템:</strong> {', '.join(top_items) if top_items else '데이터 부족'}</p>
                            <p><strong>주요 컬러웨이:</strong> {', '.join(top_colors) if top_colors else '데이터 부족'}</p>
                            <p><strong>권장 소재:</strong> {', '.join(top_materials) if top_materials else '데이터 부족'}</p>
                            <p><strong>매거진 스타일링:</strong> {', '.join(top_styles) if top_styles else '데이터 부족'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[1]:
                        # 선택적: 관련 문서 수, 시간적 트렌드 등 추가 정보
                        st.markdown(f"""
                        <div style='background-color:#fff8e1; padding:20px; border-radius:10px; border-left:5px solid #FFA000;'>
                            <h4 style='color:#F57C00; margin-top:0;'>트렌드 인사이트</h4>
                            <p><strong>관련 기사 수:</strong> {len(filtered_docs)}</p>
                            <p><strong>언급 매거진:</strong> {', '.join(filtered_docs_df['source'].unique())}</p>
                            <p><strong>최근 게재일:</strong> {filtered_docs_df['upload_date'].max().strftime('%Y-%m-%d')}</p>
                            <p><strong>추천 MD 액션:</strong> {'빠른 시즌 도입 검토' if len(filtered_docs) > 5 else '트렌드 모니터링'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # 2. 시즌 트렌드 분석
                elif visual_option == "시즌 트렌드 분석":
                    st.markdown(f"### '{keyword_to_analyze}' 시즌 트렌드 분석")
                    
                    # 2-1. 기간별 언급 추이
                    st.markdown("#### 📈 기간별 언급 추이")
                    
                    # 월별 언급량 추이
                    filtered_docs_df['month'] = filtered_docs_df['upload_date'].dt.to_period('M')
                    monthly_counts = filtered_docs_df.groupby('month').size().reset_index(name='count')
                    monthly_counts['month_str'] = monthly_counts['month'].astype(str)
                    
                    fig = px.line(
                        monthly_counts, x='month_str', y='count',
                        title=f"'{keyword_to_analyze}' 월별 언급 추이",
                        markers=True
                    )
                    st.plotly_chart(fig)
                    
                    # 2-2. 매거진별 관심도 비교
                    st.markdown("#### 🔍 매거진별 관심도 비교")
                    
                    magazine_counts = filtered_docs_df['source'].value_counts().reset_index()
                    magazine_counts.columns = ['매거진', '언급 수']
                    
                    fig = px.bar(
                        magazine_counts, x='매거진', y='언급 수',
                        title=f"'{keyword_to_analyze}' 매거진별 관심도"
                    )
                    st.plotly_chart(fig)
                    
                    # 2-3. 시즌별 연관 키워드 비교
                    st.markdown("#### 🗓️ 시즌별 연관 키워드 비교")
                    
                    # 시즌 정의 (봄/여름/가을/겨울)
                    def get_season(month):
                        if month in [3, 4, 5]:
                            return '봄'
                        elif month in [6, 7, 8]:
                            return '여름'
                        elif month in [9, 10, 11]:
                            return '가을'
                        else:  # 12, 1, 2
                            return '겨울'
                    
                    filtered_docs_df['season'] = filtered_docs_df['upload_date'].dt.month.apply(get_season)
                    
                    # 시즌별 토큰 추출
                    season_tokens = {}
                    for season, group in filtered_docs_df.groupby('season'):
                        tokens = [token for tokens in group['tokens'] for token in remove_stopwords(tokens)]
                        tokens = [t for t in tokens if t != keyword_to_analyze]  # 분석 키워드 제외
                        season_tokens[season] = pd.Series(tokens).value_counts().head(10)
                    
                    # 시즌이 있는 경우에만 시각화
                    if season_tokens:
                        # 봄/여름/가을/겨울 컬러 정의
                        season_colors = {
                            '봄': '#4CAF50',
                            '여름': '#F44336',
                            '가을': '#FF9800',
                            '겨울': '#2196F3'
                        }
                        
                        fig = go.Figure()
                        
                        for season, counts in season_tokens.items():
                            if not counts.empty:
                                fig.add_trace(go.Bar(
                                    x=counts.index,
                                    y=counts.values,
                                    name=season,
                                    marker_color=season_colors.get(season, '#9E9E9E')
                                ))
                        
                        fig.update_layout(
                            barmode='group',
                            title=f"'{keyword_to_analyze}' 시즌별 연관 키워드 Top 10",
                            xaxis_title="연관 키워드",
                            yaxis_title="언급 빈도"
                        )
                        st.plotly_chart(fig)
                        
                        # 2-4. 시즌별 MD 추천 카드
                        st.markdown("#### 💼 시즌별 MD 액션 플랜")
                        
                        # 각 시즌별 상위 아이템/컬러
                        season_insights = {}
                        
                        for season, group in filtered_docs_df.groupby('season'):
                            season_all_tokens = [token for tokens in group['tokens'] for token in remove_stopwords(tokens)]
                            token_counts = pd.Series(season_all_tokens).value_counts()
                            
                            # 아이템, 컬러 추출
                            season_items = [item for item in categories["아이템"] if item in token_counts]
                            season_items = sorted(season_items, key=lambda x: token_counts.get(x, 0), reverse=True)[:3]
                            
                            season_colors = [color for color in categories["컬러"] if color in token_counts]
                            season_colors = sorted(season_colors, key=lambda x: token_counts.get(x, 0), reverse=True)[:3]
                            
                            season_insights[season] = {
                                'items': season_items,
                                'colors': season_colors
                            }
                        
                        # 시즌 카드 표시
                        seasons = ['봄', '여름', '가을', '겨울']
                        cols = st.columns(4)
                        
                        for i, season in enumerate(seasons):
                            insight = season_insights.get(season, {'items': [], 'colors': []})
                            
                            with cols[i]:
                                st.markdown(f"""
                                <div style='background-color:{season_colors.get(season, '#E0E0E0')}22; padding:15px; border-radius:10px; border-left:5px solid {season_colors.get(season, '#9E9E9E')};'>
                                    <h4 style='color:{season_colors.get(season, '#757575')}; margin-top:0;'>{season} 시즌</h4>
                                    <p><strong>주요 아이템:</strong><br> {', '.join(insight['items']) if insight['items'] else '데이터 부족'}</p>
                                    <p><strong>추천 컬러:</strong><br> {', '.join(insight['colors']) if insight['colors'] else '데이터 부족'}</p>
                                    <p><strong>시즌 비중:</strong><br> {len(filtered_docs_df[filtered_docs_df['season'] == season])/len(filtered_docs_df)*100:.1f}%</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("시즌별 분석을 위한 충분한 데이터가 없습니다.")
                
                # 3. 구매 전략 시뮬레이션
                elif visual_option == "구매 전략 시뮬레이션":
                    st.markdown(f"### '{keyword_to_analyze}' 구매 전략 시뮬레이션")
                    
                    # 3-1. 인터랙티브 구매 시뮬레이터
                    st.markdown("#### 🛒 구매 물량 시뮬레이터")
                    
                    # 기본 설정값
                    total_budget = st.slider("총 구매 예산 (백만원)", 10, 500, 100, 10)
                    expected_sales = st.slider("예상 판매율 (%)", 30, 100, 70, 5)
                    
                    # 아이템별 물량 비중 계산
                    all_tokens = [token for tokens in filtered_docs_df['tokens'] for token in remove_stopwords(tokens)]
                    token_counts = pd.Series(all_tokens).value_counts()
                    
                    # 아이템 목록 추출
                    items = [item for item in categories["아이템"] if token_counts.get(item, 0) > 0]
                    items = sorted(items, key=lambda x: token_counts.get(x, 0), reverse=True)[:6]  # 상위 6개 아이템
                    
                    if items:
                        # 아이템별 기본 구매 비중
                        item_weights = {item: token_counts.get(item, 0) for item in items}
                        total_weight = sum(item_weights.values())
                        item_ratios = {item: weight/total_weight for item, weight in item_weights.items()}
                        
                        # 아이템별 예상 판매가
                        st.markdown("**아이템별 예상 판매가 설정 (만원)**")
                        price_cols = st.columns(len(items))
                        item_prices = {}
                        
                        for i, item in enumerate(items):
                            with price_cols[i]:
                                item_prices[item] = st.number_input(
                                    item, min_value=1, max_value=100, value=10+i*5, step=1
                                )
                        
                        # 아이템별 물량 조정
                        st.markdown("**아이템별 구매 비중 조정 (%)**")
                        ratio_cols = st.columns(len(items))
                        adjusted_ratios = {}
                        
                        for i, item in enumerate(items):
                            with ratio_cols[i]:
                                default_pct = int(item_ratios[item] * 100)
                                adjusted_ratios[item] = st.slider(
                                    item, min_value=5, max_value=50, value=default_pct, step=5
                                ) / 100
                        
                        # 비중 정규화
                        total_adjusted = sum(adjusted_ratios.values())
                        normalized_ratios = {item: ratio/total_adjusted for item, ratio in adjusted_ratios.items()}
                        
                        # 구매 계획 계산
                        st.markdown("#### 📋 구매 계획 분석")
                        
                        # 아이템별 구매 금액
                        item_budgets = {item: total_budget * ratio for item, ratio in normalized_ratios.items()}
                        
                        # 아이템별 구매 수량
                        item_quantities = {item: int(budget / (item_prices[item] * 0.1)) for item, budget in item_budgets.items()}
                        
                        # 예상 매출 및 이익
                        total_quantity = sum(item_quantities.values())
                        expected_sold = total_quantity * (expected_sales / 100)
                        total_sales = sum(item_quantities[item] * item_prices[item] * (expected_sales / 100) for item in items)
                        
                        # 결과 표시
                        plan_df = pd.DataFrame({
                            '아이템': list(item_quantities.keys()),
                            '판매가(만원)': [item_prices[item] for item in items],
                            '구매비중(%)': [normalized_ratios[item] * 100 for item in items],
                            '구매금액(만원)': [item_budgets[item] / 10 for item in items],
                            '구매수량(개)': list(item_quantities.values()),
                            '예상판매(개)': [item_quantities[item] * (expected_sales / 100) for item in items],
                            '예상매출(만원)': [item_quantities[item] * item_prices[item] * (expected_sales / 100) for item in items]
                        })
                        
                        st.dataframe(plan_df, use_container_width=True)
                        
                        # 3-2. 시각화: 구매 계획
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 구매 수량 파이 차트
                            fig = px.pie(
                                plan_df, values='구매수량(개)', names='아이템',
                                title="아이템별 구매 수량 비중"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            # 예상 매출 파이 차트
                            fig = px.pie(
                                plan_df, values='예상매출(만원)', names='아이템',
                                title="아이템별 예상 매출 비중"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # 3-3. 구매 요약 및 KPI
                        st.markdown("#### 📊 구매 전략 요약")
                        
                        kpi_cols = st.columns(4)
                        
                        with kpi_cols[0]:
                            st.metric(
                                label="총 구매 수량",
                                value=f"{int(total_quantity)}개"
                            )
                        
                        with kpi_cols[1]:
                            st.metric(
                                label="예상 판매 수량",
                                value=f"{int(expected_sold)}개"
                            )
                        
                        with kpi_cols[2]:
                            st.metric(
                                label="투입 예산",
                                value=f"{total_budget:.1f}백만원"
                            )
                        
                        with kpi_cols[3]:
                            st.metric(
                                label="예상 매출",
                                value=f"{total_sales:.1f}만원",
                                delta=f"{total_sales - (total_budget * 100):.1f}만원"
                            )
                        
                        # 3-4. 구매 전략 추천 카드
                        st.markdown("#### 💡 MD 구매 전략 추천")
                        
                        # 가장 수익성 높은 아이템
                        profit_per_item = plan_df['예상매출(만원)'] / plan_df['구매금액(만원)']
                        plan_df['수익성'] = profit_per_item
                        best_profit_item = plan_df.loc[profit_per_item.idxmax(), '아이템']
                        
                        # 빠른 회전 예상 아이템
                        best_rotation_item = plan_df.loc[plan_df['예상판매(개)'].idxmax(), '아이템']
                        
                        # 안전 재고 비율
                        safety_stock_pct = 20  # 예: 20%
                        
                        st.markdown(f"""
                        <div style='background-color:#e8f5e9; padding:20px; border-radius:10px; border-left:5px solid #4CAF50;'>
                            <h4 style='color:#2E7D32; margin-top:0;'>MD 구매 전략 인사이트</h4>
                            <p>🔹 <strong>중점 구매 아이템:</strong> <span style='color:#1B5E20;'>{best_profit_item}</span> (수익성 {plan_df['수익성'].max():.2f}배)</p>
                            <p>🔹 <strong>빠른 회전 예상:</strong> <span style='color:#1B5E20;'>{best_rotation_item}</span></p>
                            <p>🔹 <strong>안전 재고 추천:</strong> 인기 아이템 <span style='color:#1B5E20;'>{safety_stock_pct}%</span> 추가 확보</p>
                            <p>🔹 <strong>키워드 포지셔닝:</strong> {keyword_to_analyze} 관련 상품군 <span style='color:#1B5E20;'>상승세</span> 예상</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 3-5. 경쟁 분석 (선택적)
                        st.markdown("#### 🏆 시장 비교 분석")
                        
                        # 매거진별 관심도 히트맵
                        st.markdown("**매거진별 관심도 히트맵**")
                        
                        # 아이템별 매거진 관심도 계산
                        item_magazine_matrix = []
                        
                        for item in items[:4]:  # 상위 4개 아이템만
                            for mag in selected_magazines:
                                mag_docs = filtered_docs_df[filtered_docs_df['source'] == mag]
                                mag_tokens = [token for tokens in mag_docs['tokens'] for token in remove_stopwords(tokens)]
                                count = mag_tokens.count(item)
                                item_magazine_matrix.append({
                                    '아이템': item,
                                    '매거진': mag,
                                    '언급 수': count
                                })
                        
                        if item_magazine_matrix:
                            heatmap_df = pd.DataFrame(item_magazine_matrix)
                            pivot_df = heatmap_df.pivot(index='아이템', columns='매거진', values='언급 수').fillna(0)
                            
                            fig = px.imshow(
                                pivot_df,
                                labels=dict(x="매거진", y="아이템", color="언급 수"),
                                x=pivot_df.columns,
                                y=pivot_df.index,
                                title=f"'{keyword_to_analyze}' 아이템별 매거진 관심도",
                                color_continuous_scale='Viridis'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("매거진별 아이템 관심도를 계산할 데이터가 충분하지 않습니다.")
                    else:
                        st.warning("구매 시뮬레이션을 위한 아이템 데이터가 충분하지 않습니다.")
            else:
                st.info(f"'{keyword_to_analyze}'가 포함된 문서가 없습니다.")
        else:
            st.info("공통 키워드가 없습니다. 다른 매거진이나 기간을 선택해보세요.")
    else:
        st.warning("분석을 위해 최소 두 개 이상의 매거진을 선택하세요.")
    
    # MD 트렌드 워치
    st.markdown("### 🔮 MD 트렌드 워치")
    
    # 상승세 키워드 분석
    st.markdown("#### 📈 급상승 키워드 (최근 30일)")
    
    # 날짜 기준 정의
    today = pd.to_datetime(datetime.today().date())
    last_30days = today - timedelta(days=30)
    last_60days = today - timedelta(days=60)
    
    # 최근 30일 vs 이전 30일 데이터
    df_recent = df[(df['upload_date'] >= last_30days) & (df['upload_date'] <= today)]
    df_previous = df[(df['upload_date'] >= last_60days) & (df['upload_date'] < last_30days)]
    
    # 키워드 빈도 계산
    recent_tokens = [token for tokens in df_recent['tokens'] for token in remove_stopwords(tokens)]
    previous_tokens = [token for tokens in df_previous['tokens'] for token in remove_stopwords(tokens)]
    
    recent_counts = pd.Series(recent_tokens).value_counts()
    previous_counts = pd.Series(previous_tokens).value_counts()
    
    # 상승률 계산
    growth_data = []
    for keyword, recent_count in recent_counts.items():
        if keyword in previous_counts:
            previous_count = previous_counts[keyword]
            if previous_count > 0:  # 0으로 나누기 방지
                growth_pct = ((recent_count - previous_count) / previous_count) * 100
                if recent_count >= 5:  # 최소 언급 5회 이상
                    growth_data.append({
                        '키워드': keyword,
                        '최근 빈도': recent_count,
                        '이전 빈도': previous_count,
                        '상승률(%)': growth_pct
                    })
    
    growth_df = pd.DataFrame(growth_data)
    
    if not growth_df.empty:
        # 상위 10개 상승 키워드
        top_growth = growth_df.sort_values('상승률(%)', ascending=False).head(10)
        
        fig = px.bar(
            top_growth, x='키워드', y='상승률(%)',
            title="최근 30일간 급상승 키워드 Top 10",
            color='상승률(%)',
            color_continuous_scale='Reds',
            hover_data=['최근 빈도', '이전 빈도']
        )
        st.plotly_chart(fig)
        
        # 상승 키워드 카테고리별 분류
        rising_categories = {cat: [] for cat in categories}
        rising_categories["기타"] = []
        
        for _, row in top_growth.iterrows():
            keyword = row['키워드']
            categorized = False
            for cat, words in categories.items():
                if keyword in words:
                    rising_categories[cat].append((keyword, row['상승률(%)']))
                    categorized = True
                    break
            if not categorized:
                rising_categories["기타"].append((keyword, row['상승률(%)']))
        
        # 카테고리별 상승 키워드 표시
        st.markdown("#### 📊 카테고리별 급상승 트렌드")
        
        cat_cols = st.columns(3)
        cat_colors = {
            "아이템": "#5C6BC0",  # 인디고
            "컬러": "#26A69A",    # 틸
            "소재": "#FFA726",    # 오렌지
            "스타일": "#EC407A",   # 핑크
            "기타": "#78909C"     # 블루그레이
        }
        
        i = 0
        for cat, keywords in rising_categories.items():
            if keywords:
                with cat_cols[i % 3]:
                    st.markdown(f"""
                    <div style='background-color:{cat_colors.get(cat, "#E0E0E0")}22; padding:15px; border-radius:10px; border-left:5px solid {cat_colors.get(cat, "#9E9E9E")};'>
                        <h4 style='color:{cat_colors.get(cat, "#757575")}; margin-top:0;'>{cat}</h4>
                        {"".join([f"<p><strong>{kw}</strong>: ↑ {pct:.1f}%</p>" for kw, pct in keywords[:3]])}
                    </div>
                    """, unsafe_allow_html=True)
                    i += 1
    else:
        st.info("상승세 키워드를 분석할 충분한 데이터가 없습니다.")
    
    # MD 추천 조합
    st.markdown("#### ✨ MD 추천 트렌드 조합")
    
    # 많이 함께 등장하는 키워드 조합 찾기
    edge_counter = Counter()
    for tokens in df_recent['tokens']:
        cleaned = remove_stopwords(tokens)
        # 카테고리별 키워드만 추출
        cat_tokens = []
        for cat, words in categories.items():
            cat_tokens.extend([token for token in cleaned if token in words])
        
        unique_tokens = list(set(cat_tokens))
        if len(unique_tokens) >= 2:
            edge_counter.update(combinations(unique_tokens, 2))
    
    # 상위 조합 추출
    top_combos = edge_counter.most_common(9)  # 상위 9개 조합
    
    if top_combos:
        combo_rows = []
        for (item1, item2), count in top_combos:
            # 각 아이템의 카테고리 찾기
            cat1 = "기타"
            cat2 = "기타"
            for cat, words in categories.items():
                if item1 in words:
                    cat1 = cat
                if item2 in words:
                    cat2 = cat
            
            combo_rows.append({
                '조합': f"{item1} + {item2}",
                '카테고리': f"{cat1} + {cat2}",
                '함께 등장': count,
                '아이템1': item1,
                '아이템2': item2,
                '카테고리1': cat1,
                '카테고리2': cat2
            })
        
        combo_df = pd.DataFrame(combo_rows)
        
        # 조합 카드 표시
        cols = st.columns(3)
        for i, (_, row) in enumerate(combo_df.iterrows()):
            with cols[i % 3]:
                # 카테고리 색상 결정
                cat1_color = cat_colors.get(row['카테고리1'], "#9E9E9E")
                cat2_color = cat_colors.get(row['카테고리2'], "#9E9E9E")
                gradient = f"linear-gradient(135deg, {cat1_color}22, {cat2_color}22)"
                
                st.markdown(f"""
                <div style='background: {gradient}; padding:15px; border-radius:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>
                    <h4 style='text-align:center; margin-top:0;'>{row['아이템1']} + {row['아이템2']}</h4>
                    <p style='text-align:center;'><span style='color:{cat1_color};'>{row['카테고리1']}</span> + <span style='color:{cat2_color};'>{row['카테고리2']}</span></p>
                    <p style='text-align:center; font-weight:bold;'>함께 등장: {row['함께 등장']}회</p>
                </div>
                <br>
                """, unsafe_allow_html=True)
    else:
        st.info("추천 조합을 분석할 충분한 데이터가 없습니다.")