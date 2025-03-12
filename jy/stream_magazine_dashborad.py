import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob
from collections import Counter
from wordcloud import WordCloud
import platform

# ✅ 한글 폰트 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
# plt.rcParams['font.family'] = 'AppleGothic'  # Mac
# plt.rcParams['font.family'] = 'NanumGothic'  # Ubuntu
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 📌 파일 불러오기 함수
@st.cache_data
def load_data():
    file_paths = sorted(glob.glob("2025-03-12_merged_fashion_trends.csv"))
    df_list = [pd.read_csv(file, encoding='utf-8-sig') for file in file_paths]
    df = pd.concat(df_list).drop_duplicates(subset=['제목', '기사 URL', '업로드 날짜'], keep='first').reset_index(drop=True)
    df['업로드 날짜'] = pd.to_datetime(df['업로드 날짜'], errors='coerce')
    return df

df = load_data()

# 📌 운영체제에 따른 한글 폰트 설정
def get_font_path():
    system_name = platform.system()
    if system_name == "Windows":
        return "C:/Windows/Fonts/malgun.ttf"
    elif system_name == "Darwin":
        return "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    else:
        return "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_path = get_font_path()

# 📌 불용어 리스트
stopwords = set(["있다", "하는", "및", "그", "더", "이", "한", "수", "것", "있습니다", "때문에", "입니다", "다", "등", "그리고", "합니다", "특히", "어떤", "역시", "다른", "새로운", "다양한", "스타일을", "년대",
                 "미정으로", "그는", "입고", "브랜드", "가지", "여기에", "주는", "룩을", "대한", "함께", "제품", "더해진", "컬렉션을", "컬렉션은", "지난", "바로",
                 "오늘", "패션", "마리", "끌", "레르", "에디터", "트렌드", "대하", "이번", "더욱", "가장", "겁니다", "같은", "가", "의", "을", "를", "에", "와", "으로", "로", "이라는", "라는", "으로는", "에서", "이라고", "라고", "에게",
                 "이라며", "라며", "라고도", "이라고도", "있는", "은", "는", "가", "건", "두", "통해", "특히", "어떤", "역시", "다른", "새로운", "다양한", "스타일을", "년대", "미정으로", "그는", "입고", "브랜드", "가지", 
                 "여기에", "주는", "룩을", "대한", "함께", "제품", "더해진", "컬렉션을", "컬렉션은", "지난", "바로", "영감을", "스타일의", "돋보이는", "잘", "게", "듯한", "입은", "옷을", "중", "대신", "보이는", "그녀의", "모든", "하지만", "않습니다", "위에", "아래", "루", "몇", "따라", "또한", "걸", "오히려", "오는", "어느", "한껏", "활용한",
                 "것이다", "매치해", "여러", "선보였습니다", "만든", "지닌", "대하여", "시절의", "선보인다", "자신의", "넘어", "첫", "선보였다", "활용해", "더했다", "만나볼", "룩에", "연출했다", "이어가고", "가지고",
                 "없이", "때", "아닙니다", "없는", "만큼", "비슷한", "패션을", "될", "다가올", "지금", "맞는", "이미", "것이", "특유의", "한층", "전했다", "더해", "위한", "될", "번째", "바탕으로", "했다", "위해",
                 "있네요", "오늘도", "최근", "이렇게나", "거의", "보일", "그의", "마리끌레르", "살짝", "만한", "없으니까요", "스크롤을", "내려보세요", "스크롤을 내려보세요", "이런", "아니라", "있죠", "시절", "모두", "이제", "무엇을", "만한", "종류의", "이란", "쓴", "보세요", "않고", "마치", "그녀는", "연출한", "보세요", "아닌", "살짝", "제대로", "않은", "것도", "그녀가", "다시", "완성했습니다", "듯", "선보인", "예정이다", "이어", "중요한", "추천합니다", "자주", "또", "날을 맞아", "완성하는", "그녀가", "넘치는", "강조했다", "선보이며", "가치를", "들이", "그들의"])

# 📌 기사 리스트 및 워드클라우드 함수
def show_article_list(filtered_df):
    st.subheader("📰 기사 목록 및 워드클라우드")
    magazines = filtered_df['매거진 명'].unique()
    selected_magazine = st.radio("매거진 선택", list(magazines), horizontal=True)

    filtered_df = filtered_df[filtered_df['매거진 명'] == selected_magazine]
    col1, col2 = st.columns([1, 1])

    with col1:
        for _, row in filtered_df.iterrows():
            st.markdown(
                f"<div style='padding: 10px; border-radius: 10px; background-color: #f0f0f0; margin-bottom: 10px;'>"
                f"<a href='{row['기사 URL']}' target='_blank' style='text-decoration: none; color: black;'>"
                f"<h6 style='margin: 0;'>{row['제목']}</h6></a>"
                f"<p style='margin: 5px 0 0; font-size: 12px; color: gray;'>🗓 {row['업로드 날짜'].date()}</p></div>",
                unsafe_allow_html=True
            )

    with col2:
        text_content = " ".join(filtered_df['본문'].dropna())
        processed_content = " ".join([word for word in re.findall(r'\b[가-힣]+\b', text_content) if word not in stopwords])
        wordcloud_content = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate(processed_content)

        fig_content, ax_content = plt.subplots(figsize=(5, 5))
        ax_content.imshow(wordcloud_content, interpolation='bilinear')
        ax_content.axis("off")
        st.pyplot(fig_content)

# 📌 키워드 트렌드 분석 함수
def analyze_keyword_trends(filtered_df):
    search_term = st.text_input("추이를 확인할 키워드를 입력하세요:", "", key="search_term")

    if search_term:
        date_trends = {}
        for _, row in filtered_df.iterrows():
            date = row['업로드 날짜']
            text = str(row['본문'])
            text = re.sub(r'[^a-zA-Z가-힣\s]', '', text.lower())
            words = text.split()
            if date not in date_trends:
                date_trends[date] = Counter()
            date_trends[date].update(words)

        date_trends_df = pd.DataFrame(date_trends).fillna(0).T
        trend_data = pd.Series(0, index=pd.date_range(start=filtered_df["업로드 날짜"].min(), end=filtered_df["업로드 날짜"].max()))
        if not date_trends_df.empty and search_term in date_trends_df.columns:
            trend_data.update(date_trends_df[search_term])

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(trend_data.index, trend_data.values, marker='o', linestyle='-', color='b')
        ax.set_xlabel("날짜")
        ax.set_ylabel("키워드 빈도")
        ax.set_title(f"'{search_term}' 키워드의 날짜별 변화 추이")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

# 📌 컬러 키워드 분석 함수
def analyze_color_trends(filtered_df):
    color_list = ["블랙", "화이트", "베이지", "브라운", "그레이", "블루", "스카이블루", "네이비",
                  "옐로우", "핑크", "레드", "카키", "라벤더", "그린", "퍼플", "민트", "오렌지"]

    color_counts = {color: filtered_df["본문"].str.contains(color, case=False, na=False).sum() for color in color_list}
    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_colors_dict = dict(sorted_colors)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(sorted_colors_dict.keys(), sorted_colors_dict.values(), color="black")
    ax.set_ylabel("빈도수")
    ax.set_xlabel("컬러")
    ax.set_title("컬러별 등장 빈도수 (내림차순)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# 📌 사이드바 - 기간 선택 필터
st.sidebar.header("📅 기간 필터")
start_date = st.sidebar.date_input("시작 날짜", df["업로드 날짜"].min())
end_date = st.sidebar.date_input("종료 날짜", df["업로드 날짜"].max())

# ✅ 선택한 기간 내 데이터 필터링
filtered_df = df[(df["업로드 날짜"] >= pd.to_datetime(start_date)) & (df["업로드 날짜"] <= pd.to_datetime(end_date))]

# 📌 Streamlit UI - 탭 메뉴 구성
st.title("📊 패션 트렌드 데이터 분석")

tab1, tab2, tab3 = st.tabs(["기사 및 워드클라우드", "키워드 트렌드", "컬러 트렌드"])

with tab1:
    show_article_list(filtered_df)

with tab2:
    analyze_keyword_trends(filtered_df)

with tab3:
    analyze_color_trends(filtered_df)
