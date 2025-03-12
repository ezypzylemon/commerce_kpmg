import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hmac
import hashlib
import base64

# 한글 폰트 설정
import platform
if platform.system() == 'Windows':
    font_path = 'C:/Windows/Fonts/malgun.ttf'  # 윈도우의 경우
elif platform.system() == 'Darwin':  # macOS
    font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
else:  # Linux 등
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

# 설정 및 레이아웃
st.set_page_config(
    page_title="네이버 데이터랩 패션 트렌드",
    page_icon="👔",
    layout="wide"
)

# CSS 스타일 추가
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTitle {
        font-weight: bold;
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    .stSubheader {
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .data-container {
        background-color: #f7f7f7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .keyword-item {
        display: flex;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .keyword-rank {
        width: 2rem;
        font-weight: bold;
        color: #03c75a;
    }
</style>
""", unsafe_allow_html=True)

# API 키 직접 설정
# 여기에 발급받은 API 키를 입력하세요
DATALAB_CLIENT_ID = "VNSlK9G0Yb04xGkH61NR"
DATALAB_CLIENT_SECRET = "tyXWkAQ4mF"
AD_API_KEY = "01000000007b70b51bf10e3ddd6448533dc02cc517b75b9cc778cbf02bc9a3d384026a1073"  # 선택 사항
AD_SECRET_KEY = "AQAAAAB7cLUb8Q493WRIUz3ALMUXOz1JB1YlXR9SWgWUJhxi4g=="  # 선택 사항
AD_CUSTOMER_ID = "3413173"  # 선택 사항

# 페이지 제목
st.title("네이버 데이터랩 패션 카테고리 트렌드")

# 사이드바 컨트롤
st.sidebar.header("검색 설정")

# 카테고리 선택
category = st.sidebar.selectbox(
    "패션 카테고리 선택",
    [
        "패션의류", "카디건", "자켓", "코트", "티셔츠", "청바지", "원피스",
        "스웨터", "니트", "블라우스", "셔츠", "스커트", "팬츠", "속옷", "양말"
    ]
)

# 기간 선택
today = datetime.now()
date_options = {
    "최근 1년": (today - timedelta(days=365)).strftime("%Y-%m-%d"),
    "최근 6개월": (today - timedelta(days=180)).strftime("%Y-%m-%d"),
    "최근 3개월": (today - timedelta(days=90)).strftime("%Y-%m-%d"),
    "최근 1개월": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
}
selected_period = st.sidebar.selectbox("기간 선택", list(date_options.keys()))
start_date = date_options[selected_period]
end_date = today.strftime("%Y-%m-%d")

# 시간 단위 설정
time_unit_options = {
    "최근 1년": "month",
    "최근 6개월": "month",
    "최근 3개월": "week",
    "최근 1개월": "date"
}
time_unit = time_unit_options[selected_period]

# 실행 버튼
run_button = st.sidebar.button("트렌드 분석 실행")

# 데이터랩 API 호출 함수
def get_naver_datalab_trend(client_id, client_secret, category, start_date, end_date, time_unit):
    url = "https://openapi.naver.com/v1/datalab/search"
    
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {
                "groupName": category,
                "keywords": [category]
            }
        ]
    }
    
    try:
        st.write(f"트렌드 API 요청: {body}")
        response = requests.post(url, headers=headers, data=json.dumps(body))
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.error(f"API 호출 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {str(e)}")
        return None

# 데이터랩 성별/연령별 데이터 함수 (mock 데이터 사용)
def get_mock_demographic_data(category):
    """인구통계 데이터 모의 생성 함수 (API 대체용)"""
    
    # 기기별 데이터 (모바일과 PC)
    device_data = [
        {"device": "mo", "ratio": 85 + np.random.randint(-5, 6)},
        {"device": "pc", "ratio": 15 + np.random.randint(-5, 6)}
    ]
    
    # 성별 데이터
    if category in ["원피스", "블라우스", "스커트"]:
        gender_data = [
            {"gender": "f", "ratio": 90 + np.random.randint(-5, 6)},
            {"gender": "m", "ratio": 10 + np.random.randint(-5, 6)}
        ]
    elif category in ["넥타이", "정장"]:
        gender_data = [
            {"gender": "f", "ratio": 30 + np.random.randint(-5, 6)},
            {"gender": "m", "ratio": 70 + np.random.randint(-5, 6)}
        ]
    else:
        gender_data = [
            {"gender": "f", "ratio": 65 + np.random.randint(-10, 11)},
            {"gender": "m", "ratio": 35 + np.random.randint(-10, 11)}
        ]
    
    # 연령별 데이터
    age_ratios = {
        "카디건": [5, 35, 30, 20, 8, 2],
        "자켓": [5, 25, 35, 25, 8, 2],
        "코트": [3, 30, 35, 20, 10, 2],
        "티셔츠": [15, 40, 25, 15, 4, 1],
        "청바지": [20, 35, 25, 15, 4, 1],
        "원피스": [10, 40, 30, 15, 4, 1],
        "스웨터": [8, 30, 35, 20, 5, 2],
        "니트": [5, 30, 35, 20, 8, 2],
        "블라우스": [3, 25, 40, 25, 5, 2],
        "셔츠": [5, 25, 35, 25, 8, 2],
        "스커트": [10, 35, 30, 20, 4, 1],
        "팬츠": [5, 30, 35, 20, 8, 2],
        "속옷": [10, 30, 30, 20, 8, 2],
        "양말": [15, 25, 25, 20, 10, 5]
    }
    
    default_ratios = [10, 30, 30, 20, 8, 2]
    category_ratios = age_ratios.get(category, default_ratios)
    
    # 약간의 랜덤 편차 추가
    age_ratios_with_noise = []
    for ratio in category_ratios:
        noise = np.random.randint(-3, 4)  # -3에서 3까지의 랜덤 노이즈
        adjusted_ratio = max(1, ratio + noise)  # 최소 1% 보장
        age_ratios_with_noise.append(adjusted_ratio)
    
    # 합이 100%가 되도록 정규화
    total = sum(age_ratios_with_noise)
    normalized_ratios = [ratio * 100 / total for ratio in age_ratios_with_noise]
    
    age_data = [
        {"age": "1", "ratio": normalized_ratios[0]},
        {"age": "2", "ratio": normalized_ratios[1]},
        {"age": "3", "ratio": normalized_ratios[2]},
        {"age": "4", "ratio": normalized_ratios[3]},
        {"age": "5", "ratio": normalized_ratios[4]},
        {"age": "6", "ratio": normalized_ratios[5]}
    ]
    
    # 모의 데이터 구조 생성
    result = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "month",
        "results": [
            {
                "title": category,
                "data": device_data + gender_data + age_data
            }
        ]
    }
    
    return result

# 네이버 검색광고 API 모의 데이터 생성 함수
def get_mock_keyword_data(category):
    """검색광고 API 모의 데이터 생성 함수"""
    # 실제 검색 패턴을 반영한 기본 키워드 세트
    base_keywords = {
        "카디건": ["가디건", "니트", "봄", "가을", "겨울", "남자", "여성", "브랜드", "코디", "쇼핑몰"],
        "자켓": ["남자", "여성", "청자켓", "가죽", "봄", "가을", "코디", "브랜드", "쇼핑몰", "레더"],
        "코트": ["트렌치코트", "겨울", "가을", "남자", "여성", "모직", "롱", "숏", "브랜드", "코디"],
        "티셔츠": ["반팔", "긴팔", "무지", "브랜드", "남자", "여성", "오버핏", "슬림핏", "코디", "쇼핑몰"],
        "청바지": ["남자", "여성", "슬림핏", "스키니", "일자", "와이드", "연청", "흑청", "브랜드", "쇼핑몰"],
        "원피스": ["여름", "겨울", "니트", "롱", "미니", "플라워", "하객", "오피스", "브랜드", "쇼핑몰"],
        "스웨터": ["니트", "울", "캐시미어", "겨울", "남자", "여성", "브랜드", "오버핏", "코디", "쇼핑몰"],
        "니트": ["스웨터", "가디건", "울", "캐시미어", "남자", "여성", "브랜드", "봄", "가을", "겨울"],
        "블라우스": ["여성", "오피스", "실크", "쉬폰", "봄", "가을", "브랜드", "쇼핑몰", "화이트", "코디"],
        "셔츠": ["남자", "여성", "옥스포드", "스트라이프", "화이트", "블루", "정장", "캐주얼", "브랜드", "코디"],
        "스커트": ["미니", "롱", "플리츠", "플레어", "타이트", "테니스", "여성", "브랜드", "쇼핑몰", "코디"],
        "팬츠": ["슬랙스", "면바지", "스판", "남자", "여성", "와이드", "조거", "브랜드", "쇼핑몰", "코디"],
        "속옷": ["남자", "여성", "브라", "팬티", "세트", "브랜드", "쇼핑몰", "면", "레이스", "기능성"],
        "양말": ["남자", "여성", "스포츠", "패션", "발목", "중목", "니삭스", "브랜드", "쇼핑몰", "면"]
    }
    
    default_keywords = ["브랜드", "쇼핑몰", "남자", "여성", "봄", "여름", "가을", "겨울", "코디", "패션"]
    category_keywords = base_keywords.get(category, default_keywords)
    
    # 카테고리 이름을 키워드 조합에 사용
    keyword_list = []
    for keyword in category_keywords:
        combined_keyword = f"{category} {keyword}"
        
        # 검색량 설정 (실제 패턴 모방)
        pc_count = np.random.randint(1000, 5000)
        mobile_count = int(pc_count * (3 + np.random.random() * 2))  # 모바일 검색량은 PC의 3~5배
        
        keyword_list.append({
            "relKeyword": combined_keyword,
            "monthlyPcQcCnt": pc_count,
            "monthlyMobileQcCnt": mobile_count,
            "competitionIndex": np.random.choice(["높음", "중간", "낮음"])
        })
    
    # 일반 카테고리 키워드
    keyword_list.append({
        "relKeyword": category,
        "monthlyPcQcCnt": np.random.randint(5000, 20000),
        "monthlyMobileQcCnt": np.random.randint(20000, 80000),
        "competitionIndex": "높음"
    })
    
    # 브랜드와 결합된 키워드 추가
    brands = ["유니클로", "자라", "H&M", "나이키", "아디다스", "무신사", "노스페이스", "게스", "지오다노", "스파오"]
    for brand in brands[:5]:  # 상위 5개 브랜드만 사용
        combined_keyword = f"{brand} {category}"
        pc_count = np.random.randint(800, 3000)
        mobile_count = int(pc_count * (3 + np.random.random() * 2))
        
        keyword_list.append({
            "relKeyword": combined_keyword,
            "monthlyPcQcCnt": pc_count,
            "monthlyMobileQcCnt": mobile_count,
            "competitionIndex": np.random.choice(["높음", "중간"])
        })
    
    # 계절과 결합된 키워드 추가
    seasons = ["봄", "여름", "가을", "겨울"]
    for season in seasons:
        combined_keyword = f"{season} {category}"
        pc_count = np.random.randint(800, 3000)
        mobile_count = int(pc_count * (3 + np.random.random() * 2))
        
        keyword_list.append({
            "relKeyword": combined_keyword,
            "monthlyPcQcCnt": pc_count,
            "monthlyMobileQcCnt": mobile_count,
            "competitionIndex": np.random.choice(["높음", "중간", "낮음"])
        })
    
    # 결과 반환
    return {
        "keywordList": keyword_list
    }

# 네이버 검색광고 API 호출 함수 (관련 키워드)
def get_related_keywords(api_key, secret_key, customer_id, keyword):
    if not (api_key and secret_key and customer_id):
        return None
        
    # API 호출 대신 모의 데이터 사용
    st.write("검색광고 API 대신 모의 데이터를 사용합니다.")
    return get_mock_keyword_data(keyword)


# 데이터 처리 및 시각화
if run_button:
    # 로딩 표시
    with st.spinner("데이터를 불러오는 중입니다..."):
        # 1. 검색 트렌드 데이터 가져오기
        trend_data = get_naver_datalab_trend(
            DATALAB_CLIENT_ID, DATALAB_CLIENT_SECRET, 
            category, start_date, end_date, time_unit
        )
        
        # 2. 인구통계 데이터 가져오기 (모의 데이터 사용)
        demographic_data = get_mock_demographic_data(category)
        
        # 3. 관련 키워드 데이터 가져오기 (모의 데이터 사용)
        related_keywords = get_mock_keyword_data(category)

    # 검색 트렌드 시각화
    if trend_data:
        st.header("📈 검색 트렌드 분석")
        
        # 데이터프레임 생성
        trend_df = pd.DataFrame(trend_data['results'][0]['data'])
        trend_df['period'] = pd.to_datetime(trend_df['period'])
        
        # 기간 표시
        st.markdown(f"<div style='color:#666; font-size:0.9rem; margin-bottom:1rem;'>{start_date} ~ {end_date}</div>", unsafe_allow_html=True)
        
        # 그래프 생성
        fig = px.line(
            trend_df, x='period', y='ratio', 
            title=f"{category} 검색 트렌드",
            labels={'period': '기간', 'ratio': '검색량 (상대적 비율)'},
            markers=True
        )
        fig.update_layout(
            title_font_size=20,
            xaxis_title_font_size=16,
            yaxis_title_font_size=16
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 트렌드 데이터 표시
        with st.expander("트렌드 원본 데이터 보기"):
            st.dataframe(trend_df)
    
    # 인구통계 데이터 시각화
    if demographic_data:
        st.header("👥 기기별 / 성별 / 연령별 비중")
        
        # 데이터 추출 및 처리
        demo_data = demographic_data['results'][0]['data']
        
        device_data = []
        gender_data = []
        age_data = []
        
        for item in demo_data:
            if 'device' in item:
                # 기기별 데이터
                device_label = '모바일' if item['device'] == 'mo' else 'PC'
                device_data.append({'device': device_label, 'ratio': item['ratio']})
            elif 'gender' in item:
                # 성별 데이터
                gender_label = 'female' if item['gender'] == 'f' else 'male'
                gender_data.append({'gender': gender_label, 'ratio': item['ratio']})
            elif 'age' in item:
                # 연령별 데이터
                age_label = {
                    '1': '10대', '2': '20대', '3': '30대', 
                    '4': '40대', '5': '50대', '6': '60대 이상'
                }.get(item['age'], f'{item["age"]}0대')
                age_data.append({'age': age_label, 'ratio': item['ratio']})
        
        # 데이터프레임 변환
        device_df = pd.DataFrame(device_data)
        gender_df = pd.DataFrame(gender_data)
        age_df = pd.DataFrame(age_data)
        
        # 데이터가 있는 경우만 처리
        if not device_df.empty or not gender_df.empty or not age_df.empty:
            demo_cols = st.columns(3)
            
            # 1. 기기별 데이터
            if not device_df.empty:
                with demo_cols[0]:
                    st.subheader("기기별 비중")
                    device_fig = px.pie(
                        device_df, names='device', values='ratio',
                        color='device', 
                        color_discrete_map={'모바일': '#4CAF50', 'PC': '#FFA000'}
                    )
                    device_fig.update_traces(textinfo='percent+label')
                    st.plotly_chart(device_fig, use_container_width=True)
            
            # 2. 성별 데이터
            if not gender_df.empty:
                with demo_cols[1]:
                    st.subheader("성별 비중")
                    gender_fig = px.pie(
                        gender_df, names='gender', values='ratio',
                        color='gender',
                        color_discrete_map={'female': '#E91E63', 'male': '#2196F3'}
                    )
                    gender_fig.update_traces(textinfo='percent+label')
                    st.plotly_chart(gender_fig, use_container_width=True)
            
            # 3. 연령별 데이터
            if not age_df.empty and len(age_df) > 1:
                with demo_cols[2]:
                    st.subheader("연령별 비중")
                    # 연령 순서대로 정렬
                    age_order = ['10대', '20대', '30대', '40대', '50대', '60대 이상']
                    age_df['age'] = pd.Categorical(age_df['age'], categories=age_order, ordered=True)
                    age_df = age_df.sort_values('age')
                    
                    age_fig = px.bar(
                        age_df, x='age', y='ratio',
                        text_auto='.1f',
                        color='ratio',
                        color_continuous_scale='Blues'
                    )
                    age_fig.update_layout(xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(age_fig, use_container_width=True)
    
    # 관련 키워드 시각화 (네이버 검색광고 API)
    if related_keywords:
        st.header("🔍 관련 인기 검색어")
        
        # 데이터 추출 및 처리
        keywords = related_keywords.get('keywordList', [])
        if keywords:
            # 월간 검색수 기준으로 정렬
            keywords.sort(key=lambda x: x.get('monthlyPcQcCnt', 0) + x.get('monthlyMobileQcCnt', 0), reverse=True)
            
            # 상위 20개만 추출
            top_keywords = keywords[:20]
            
            # 데이터프레임 생성
            keyword_df = pd.DataFrame([
                {
                    "키워드": kw.get('relKeyword', ''),
                    "월간 PC 검색량": kw.get('monthlyPcQcCnt', 0),
                    "월간 모바일 검색량": kw.get('monthlyMobileQcCnt', 0),
                    "총 검색량": kw.get('monthlyPcQcCnt', 0) + kw.get('monthlyMobileQcCnt', 0),
                    "경쟁정도": kw.get('competitionIndex', ''),
                }
                for kw in top_keywords
            ])
            
            # 키워드 목록 표시
            keyword_cols = st.columns(2)
            with keyword_cols[0]:
                st.markdown("<h3>TOP 10 검색어</h3>", unsafe_allow_html=True)
                for i, (_, row) in enumerate(keyword_df.iloc[:10].iterrows()):
                    st.markdown(
                        f"""
                        <div class='keyword-item'>
                            <span class='keyword-rank'>{i+1}</span>
                            <span>{row['키워드']}</span>
                            <span style='margin-left: auto;'>{row['총 검색량']:,}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            with keyword_cols[1]:
                st.markdown("<h3>TOP 11-20 검색어</h3>", unsafe_allow_html=True)
                for i, (_, row) in enumerate(keyword_df.iloc[10:20].iterrows()):
                    st.markdown(
                        f"""
                        <div class='keyword-item'>
                            <span class='keyword-rank'>{i+11}</span>
                            <span>{row['키워드']}</span>
                            <span style='margin-left: auto;'>{row['총 검색량']:,}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            # 키워드 검색량 시각화
            st.subheader("인기 검색어 검색량 비교")
            top10_df = keyword_df.iloc[:10].copy()
            top10_df = top10_df.sort_values('총 검색량')
            
            fig = px.bar(
                top10_df,
                x='총 검색량',
                y='키워드',
                orientation='h',
                color='총 검색량',
                color_continuous_scale='Viridis',
                text='총 검색량'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # 전체 데이터 표시
            with st.expander("전체 관련 키워드 데이터 보기"):
                st.dataframe(keyword_df)
        else:
            st.info("관련 키워드 데이터가 없습니다.")
    
    # 데이터가 없는 경우
    if not trend_data and not demographic_data and not related_keywords:
        st.warning("데이터를 가져오지 못했습니다. API 키를 확인하고 다시 시도해주세요.")
else:
    # 앱 처음 실행 시 안내 메시지
    st.info("왼쪽 사이드바에서 패션 카테고리와 기간을 선택한 후 '트렌드 분석 실행' 버튼을 클릭하세요.")
    
    # 간단한 앱 소개
    st.header("네이버 데이터랩 패션 트렌드 분석기")
    st.markdown("""
    이 애플리케이션은 네이버 데이터랩 API를 활용하여 패션 카테고리 검색어의 트렌드를 분석합니다.
    
    **주요 기능:**
    
    1. 검색어 트렌드 추이 분석 (1개월 ~ 1년)
    2. 기기별(PC/모바일) 사용 비중 분석
    3. 성별 및 연령별 검색 비중 분석
    4. 관련 인기 검색어 TOP 20 추출 및 분석
    
    왼쪽 사이드바에서 분석하고 싶은 패션 카테고리와 기간을 선택한 후,
    '트렌드 분석 실행' 버튼을 클릭하면 분석 결과가 표시됩니다.
    """)
    
    # 샘플 이미지
    st.image("https://ssl.pstatic.net/static/datalab/img/intro/img_search.png", caption="네이버 데이터랩 이미지")

# 푸터
st.markdown("""
---
네이버 데이터랩 API와 Streamlit을 활용한 패션 트렌드 분석 대시보드
""")