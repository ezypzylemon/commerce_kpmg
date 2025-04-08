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
import platform
import os


# ------------------------
# OS별 폰트 경로 자동 설정
# ------------------------
def get_font_path():
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
        raise FileNotFoundError("macOS에서 한글 폰트를 찾을 수 없습니다.")
    elif system == "Linux":
        linux_fonts = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        for path in linux_fonts:
            if os.path.exists(path):
                return path
        raise FileNotFoundError("Linux에서 기본 폰트를 찾을 수 없습니다.")
    else:
        raise OSError("지원하지 않는 운영체제입니다.")

FONT_PATH = get_font_path()

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
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

# ------------------------
# 데이터 로드 함수
# ------------------------
def get_mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

@st.cache_data
def load_data():
    conn = get_mysql_connection()
    query = "SELECT doc_domain, upload_date, tokens, source FROM magazine_tokenised;"
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
category = st.sidebar.selectbox("카테고리", df['doc_domain'].unique())
filtered_df = df[df['doc_domain'] == category]

# ------------------------
# 탭 구성
# ------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 키워드 트렌드", "📈 TF-IDF 분석", "🕸️ 키워드 네트워크", "📉 아이템 증감률 분석", "📰 매거진별 분석"
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
        font_path=FONT_PATH,
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

    font_path = FONT_PATH
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