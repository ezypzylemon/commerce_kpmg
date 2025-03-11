import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import platform
import os
from collections import Counter
import re

# 운영체제에 따라 폰트 경로 자동 설정
def get_font_path():
    system_name = platform.system()
    if system_name == "Windows":
        return "C:/Windows/Fonts/malgun.ttf"  # Windows 기본 한글 폰트
    elif system_name == "Darwin":  # macOS
        return "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    else:  # Linux (Ubuntu 등)
        return "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_path = get_font_path()

# 불용어 리스트 (제외할 단어들)
stopwords = set(["있다", "하는", "및", "그", "더", "이", "한", "수", "것", "있습니다", "때문에", "입니다", "다", "등", "그리고", "합니다", "특히", "어떤", "역시", "다른", "새로운", "다양한", "스타일을", "년대",
                 "미정으로", "그는", "입고", "브랜드", "가지", "여기에", "주는", "룩을", "대한", "함께", "제품", "더해진", "컬렉션을", "컬렉션은", "지난", "바로",
                 "오늘", "패션", "마리", "끌", "레르", "에디터", "트렌드", "대하", "이번", "더욱", "가장", "겁니다", "같은", "가", "의", "을", "를", "에", "와", "으로", "로", "이라는", "라는", "으로는", "에서", "이라고", "라고", "에게",
                 "이라며", "라며", "라고도", "이라고도", "있는", "은", "는", "가", "건", "두", "통해", "특히", "어떤", "역시", "다른", "새로운", "다양한", "스타일을", "년대", "미정으로", "그는", "입고", "브랜드", "가지", 
                 "여기에", "주는", "룩을", "대한", "함께", "제품", "더해진", "컬렉션을", "컬렉션은", "지난", "바로", "영감을", "스타일의", "돋보이는", "잘", "게", "듯한", "입은", "옷을", "중", "대신", "보이는", "그녀의", "모든", "하지만", "않습니다", "위에", "아래", "루", "몇", "따라", "또한", "걸", "오히려", "오는", "어느", "한껏", "활용한"])

# 텍스트 전처리 함수 (불용어 제거 및 정리)
def preprocess_text(text):
    words = re.findall(r'\b[가-힣]+\b', text)  # 한글 단어만 추출
    words = [word for word in words if word not in stopwords]  # 불용어 제거
    return " ".join(words)

# 데이터 불러오기
file_path = "2025.03.11_merged_fashion_trends.csv"
df = pd.read_csv(file_path, encoding='utf-8')  # 한글 깨짐 방지

# 날짜 형식 변환 및 정렬
df['업로드 날짜'] = pd.to_datetime(df['업로드 날짜'], format='%Y.%m.%d')
df = df.sort_values(by='업로드 날짜', ascending=False)

# 스트림릿 앱 시작
st.set_page_config(page_title="패션 트렌드 기사", layout="wide")
st.title("패션 트렌드 기사 모음")

# 매거진 선택
magazines = df['매거진 명'].unique()
import streamlit as st

# 매거진 선택 (가로 탭으로 표시)
selected_magazine = st.radio("매거진 선택", list(magazines), horizontal=True)  # 해당 인덱스의 매거진 이름 가져오기

# 선택된 매거진의 기사 필터링
filtered_df = df[df['매거진 명'] == selected_magazine]

# 레이아웃 설정
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"{selected_magazine} 기사 목록")
    for _, row in filtered_df.iterrows():
        with st.container():
            st.markdown(
                f"""
                <div style='padding: 10px; border-radius: 10px; background-color: #f0f0f0; margin-bottom: 10px;'>
                    <a href='{row['기사 URL']}' target='_blank' style='text-decoration: none; color: black;'>
                        <h6 style='margin: 0;'>{row['제목']}</h6>
                    </a>
                    <p style='margin: 5px 0 0; font-size: 12px; color: gray;'>🗓 {row['업로드 날짜'].date()}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        # st.markdown(f"##### [{row['제목']}]({row['기사 URL']})")
        # st.write(f"🗓 업로드 날짜: {row['업로드 날짜'].date()}")
        st.write("---")

with col2:
    # 전체 기사 내용 기반 워드클라우드 생성
    st.markdown("<h5>📰 전체 기사 키워드 워드클라우드</h5>", unsafe_allow_html=True)
    if '본문' in df.columns:
        text_content = " ".join(df['본문'].dropna())
        processed_content = preprocess_text(text_content)
        wordcloud_content = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate(processed_content)
        
        # 워드클라우드 출력
        fig_content, ax_content = plt.subplots(figsize=(5, 5))
        ax_content.imshow(wordcloud_content, interpolation='bilinear')
        ax_content.axis("off")
        st.pyplot(fig_content)
    else:
        st.write("기사 내용 데이터가 없습니다.")
