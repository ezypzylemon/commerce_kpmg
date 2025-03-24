import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import re
from collections import Counter
import os
from PIL import Image

# 페이지 설정
st.set_page_config(
    page_title="무신사 패션 트렌드 대시보드",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 전처리 함수
def extract_price(price_str):
    """가격 문자열에서 숫자만 추출"""
    if pd.isna(price_str) or price_str == 'N/A':
        return np.nan
    
    try:
        nums = re.findall(r'\d+', str(price_str).replace(',', ''))
        if nums:
            return int(''.join(nums))
        return np.nan
    except:
        return np.nan

def extract_keywords(name):
    """상품명에서 주요 키워드 추출"""
    if pd.isna(name) or name == 'N/A':
        return []
    
    # 불용어 정의
    stopwords = {'더', '단독', '할인', '신상', '데일리', '베이직', '예약', '당일',
                 '발송', '세일', '판매', '배송', '무료', '이벤트', '오늘', '기본'}
    
    # 텍스트 전처리 및 단어 추출
    text = str(name).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = re.findall(r'[a-zA-Z]+|[가-힣]+', text)
    
    # 불용어 및 짧은 단어 제거
    keywords = [word for word in words if word not in stopwords and len(word) >= 2]
    return keywords

# 데이터 로드 및 전처리
@st.cache_data
def load_data(file_path):
    """CSV 파일 로드 및 전처리"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # 가격 숫자로 변환
        df['price_numeric'] = df['price'].apply(extract_price)
        
        # 상품명에서 키워드 추출
        df['keywords'] = df['name'].apply(extract_keywords)
        
        # 결측치 처리
        for col in ['rating', 'review_count']:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # 가격대 범주화
        price_ranges = [0, 10000, 30000, 50000, 100000, 200000, 500000, float('inf')]
        price_labels = ['~1만원', '1~3만원', '3~5만원', '5~10만원', '10~20만원', '20~50만원', '50만원~']
        df['price_range'] = pd.cut(df['price_numeric'], bins=price_ranges, labels=price_labels, right=False)
        
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return None

# 메인 함수
def main():
    # 사이드바 설정
    st.sidebar.title("무신사 패션 트렌드 대시보드")
    st.sidebar.image("https://image.msscdn.net/mfile_s01/_brand/free_medium/musinsastandard.png", width=200)
    
    # 파일 업로더
    uploaded_file = st.sidebar.file_uploader("무신사 크롤링 CSV 파일 업로드", type=["csv"])
    
    if uploaded_file is not None:
        # 데이터 로드
        data = load_data(uploaded_file)
        
        if data is not None:
            # 사이드바 메뉴
            analysis_option = st.sidebar.radio(
                "분석 카테고리 선택",
                ["데이터 개요", "카테고리 분석", "브랜드 분석", "가격 분석", "키워드 분석"]
            )
            
            # 데이터 개요
            if analysis_option == "데이터 개요":
                st.title("무신사 패션 데이터 개요")
                
                # 기본 통계
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("총 상품 수", f"{len(data):,}개")
                with col2:
                    st.metric("브랜드 수", f"{data['brand'].nunique():,}개")
                with col3:
                    st.metric("카테고리 수", f"{data['category'].nunique():,}개")
                
                # 데이터 샘플
                st.subheader("데이터 샘플")
                st.dataframe(data.head(10))
                
                # 기본 통계 정보
                st.subheader("기본 통계 정보")
                st.write(data.describe())
                
                # 결측치 정보
                st.subheader("결측치 정보")
                missing_data = pd.DataFrame({
                    '결측치 수': data.isnull().sum(),
                    '결측 비율(%)': (data.isnull().sum() / len(data) * 100).round(2)
                })
                st.table(missing_data[missing_data['결측치 수'] > 0])
            
            # 카테고리 분석
            elif analysis_option == "카테고리 분석":
                st.title("카테고리 분석")
                
                # 카테고리별 상품 수
                st.subheader("카테고리별 상품 수")
                category_counts = data['category'].value_counts().reset_index()
                category_counts.columns = ['category', 'count']
                
                fig = px.bar(
                    category_counts.sort_values('count', ascending=False),
                    x='category', y='count',
                    color='count',
                    color_continuous_scale='blues',
                    labels={'count': '상품 수', 'category': '카테고리'}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # 카테고리별 평균 가격
                st.subheader("카테고리별 평균 가격")
                category_prices = data.groupby('category')['price_numeric'].mean().reset_index()
                category_prices.columns = ['category', 'avg_price']
                
                fig = px.bar(
                    category_prices.sort_values('avg_price', ascending=False),
                    x='category', y='avg_price',
                    color='avg_price',
                    color_continuous_scale='reds',
                    labels={'avg_price': '평균 가격(원)', 'category': '카테고리'}
                )
                fig.update_layout(height=500)
                fig.update_traces(hovertemplate='%{y:,.0f}원')
                st.plotly_chart(fig, use_container_width=True)
                
                # 카테고리별 평점 분포 (평점 데이터가 있는 경우)
                if 'rating' in data.columns and data['rating'].max() > 0:
                    st.subheader("카테고리별 평균 평점")
                    category_ratings = data.groupby('category')['rating'].mean().reset_index()
                    
                    fig = px.bar(
                        category_ratings.sort_values('rating', ascending=False),
                        x='category', y='rating',
                        color='rating',
                        color_continuous_scale='greens',
                        labels={'rating': '평균 평점', 'category': '카테고리'}
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
            
            # 브랜드 분석
            elif analysis_option == "브랜드 분석":
                st.title("브랜드 분석")
                
                # 상위 브랜드 수 선택
                top_n = st.slider("상위 브랜드 수 선택", min_value=5, max_value=50, value=20, step=5)
                
                # 인기 브랜드
                st.subheader(f"인기 브랜드 TOP {top_n}")
                top_brands = data['brand'].value_counts().head(top_n).reset_index()
                top_brands.columns = ['brand', 'count']
                
                fig = px.bar(
                    top_brands.sort_values('count', ascending=False),
                    x='brand', y='count',
                    color='count',
                    color_continuous_scale='viridis',
                    labels={'count': '상품 수', 'brand': '브랜드'}
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                # 브랜드별 평균 가격
                st.subheader(f"브랜드별 평균 가격 (TOP {top_n})")
                top_brand_prices = data[data['brand'].isin(top_brands['brand'])].groupby('brand')['price_numeric'].mean().reset_index()
                top_brand_prices = top_brand_prices.sort_values('price_numeric', ascending=False)
                
                fig = px.bar(
                    top_brand_prices,
                    x='brand', y='price_numeric',
                    color='price_numeric',
                    color_continuous_scale='plasma',
                    labels={'price_numeric': '평균 가격(원)', 'brand': '브랜드'}
                )
                fig.update_layout(height=600)
                fig.update_traces(hovertemplate='%{y:,.0f}원')
                st.plotly_chart(fig, use_container_width=True)
                
                # 브랜드별 카테고리 분포
                st.subheader("브랜드별 카테고리 분포")
                selected_brand = st.selectbox(
                    "브랜드 선택",
                    options=top_brands['brand'].tolist()
                )
                
                brand_categories = data[data['brand'] == selected_brand]['category'].value_counts().reset_index()
                brand_categories.columns = ['category', 'count']
                
                fig = px.pie(
                    brand_categories,
                    values='count',
                    names='category',
                    title=f'{selected_brand} 브랜드의 카테고리 분포',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            # 가격 분석
            elif analysis_option == "가격 분석":
                st.title("가격 분석")
                
                # 가격대별 상품 수
                st.subheader("가격대별 상품 수")
                price_range_counts = data['price_range'].value_counts().reset_index()
                price_range_counts.columns = ['price_range', 'count']
                
                # 가격대 순서 정렬
                price_order = ['~1만원', '1~3만원', '3~5만원', '5~10만원', '10~20만원', '20~50만원', '50만원~']
                price_range_counts['price_range'] = pd.Categorical(
                    price_range_counts['price_range'], 
                    categories=price_order, 
                    ordered=True
                )
                price_range_counts = price_range_counts.sort_values('price_range')
                
                fig = px.bar(
                    price_range_counts,
                    x='price_range', y='count',
                    color='count',
                    color_continuous_scale='blues',
                    labels={'count': '상품 수', 'price_range': '가격대'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 카테고리별 가격 분포
                st.subheader("카테고리별 가격 분포")
                
                # 카테고리 선택
                selected_categories = st.multiselect(
                    "카테고리 선택 (여러 개 선택 가능, 비워두면 전체 선택)",
                    options=data['category'].unique().tolist(),
                    default=[]
                )
                
                if not selected_categories:
                    filtered_data = data
                else:
                    filtered_data = data[data['category'].isin(selected_categories)]
                
                # 박스플롯으로 가격 분포 시각화
                fig = px.box(
                    filtered_data,
                    x='category', y='price_numeric',
                    color='category',
                    labels={'price_numeric': '가격(원)', 'category': '카테고리'},
                    title='카테고리별 가격 분포'
                )
                fig.update_layout(showlegend=False, height=600)
                fig.update_yaxes(tickformat=",")
                st.plotly_chart(fig, use_container_width=True)
                
                # 카테고리별 가격대 분포 히트맵
                st.subheader("카테고리별 가격대 분포")
                
                # 크로스탭 생성
                price_category_crosstab = pd.crosstab(
                    filtered_data['category'], 
                    filtered_data['price_range'],
                    normalize='index'
                )
                
                # 가격대 순서 정렬
                price_category_crosstab = price_category_crosstab.reindex(columns=price_order)
                
                # 히트맵 생성
                fig = px.imshow(
                    price_category_crosstab,
                    labels=dict(x="가격대", y="카테고리", color="비율"),
                    x=price_category_crosstab.columns,
                    y=price_category_crosstab.index,
                    color_continuous_scale='blues',
                    aspect="auto"
                )
                fig.update_layout(height=600)
                fig.update_traces(text=np.around(price_category_crosstab.values, 2), texttemplate="%{text:.1%}")
                st.plotly_chart(fig, use_container_width=True)
            
            # 키워드 분석
            elif analysis_option == "키워드 분석":
                st.title("키워드 분석")
                
                # 모든 키워드 추출
                all_keywords = []
                for keywords in data['keywords']:
                    all_keywords.extend(keywords)
                
                # 키워드 빈도 계산
                keyword_counts = Counter(all_keywords)
               

                                # 워드클라우드 부분 수정 코드

                # 한글 폰트 경로 설정
                import matplotlib.font_manager as fm
                import platform

                def get_korean_font():
                    """시스템에 맞는 한글 폰트 경로 반환"""
                    system = platform.system()
                    
                    if system == 'Darwin':  # macOS
                        font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
                        if not os.path.exists(font_path):
                            font_path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'
                    elif system == 'Windows':  # Windows
                        font_path = 'C:/Windows/Fonts/malgun.ttf'  # 맑은 고딕
                    else:  # Linux 등
                        font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
                        if not os.path.exists(font_path):
                            # 나눔고딕이 없는 경우 다른 폰트 시도
                            font_candidates = [f for f in fm.findSystemFonts() if 'gothic' in f.lower() or 'nanum' in f.lower()]
                            if font_candidates:
                                font_path = font_candidates[0]
                            else:
                                st.warning("한글 폰트를 찾을 수 없습니다. 워드클라우드에 한글이 깨질 수 있습니다.")
                                font_path = None
                    
                    return font_path

                # 워드클라우드 생성 부분 (키워드 분석 탭 내에서)
                st.subheader("인기 키워드 워드클라우드")

                # 한글 폰트 경로 가져오기
                font_path = get_korean_font()

                # 워드클라우드 생성
                wordcloud = WordCloud(
                    font_path=font_path,  # 한글 폰트 경로 지정
                    width=800, 
                    height=400, 
                    background_color='white',
                    max_words=100,
                    colormap='viridis',
                    contour_width=1,
                    contour_color='steelblue'
                )
                wordcloud.generate_from_frequencies(keyword_counts)

                # 이미지로 변환
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.tight_layout()

                st.pyplot(plt)
                

                
                # 인기 키워드 막대 그래프
                st.subheader("인기 키워드 TOP 20")
                top_keywords = keyword_counts.most_common(20)
                keywords_df = pd.DataFrame(top_keywords, columns=['keyword', 'count'])
                
                fig = px.bar(
                    keywords_df.sort_values('count', ascending=True),
                    y='keyword', x='count',
                    orientation='h',
                    color='count',
                    color_continuous_scale='viridis',
                    labels={'count': '빈도', 'keyword': '키워드'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 카테고리별 키워드 분석
                st.subheader("카테고리별 키워드 분석")
                
                # 카테고리 선택
                selected_category = st.selectbox(
                    "카테고리 선택",
                    options=data['category'].unique().tolist()
                )
                
                # 선택된 카테고리의 키워드 분석
                cat_data = data[data['category'] == selected_category]
                
                cat_keywords = []
                for keywords in cat_data['keywords']:
                    cat_keywords.extend(keywords)
                
                cat_keyword_counts = Counter(cat_keywords)
                
                # 상위 15개 키워드 선택
                top_cat_keywords = cat_keyword_counts.most_common(15)
                cat_kw_df = pd.DataFrame(top_cat_keywords, columns=['keyword', 'count'])
                
                # 막대 그래프 생성
                fig = px.bar(
                    cat_kw_df.sort_values('count', ascending=True),
                    y='keyword', x='count',
                    orientation='h',
                    color='count',
                    color_continuous_scale='cividis',
                    labels={'count': '빈도', 'keyword': '키워드'},
                    title=f'{selected_category} 카테고리 인기 키워드'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 가격대별 키워드 분석
                st.subheader("가격대별 키워드 분석")
                
                # 가격대 선택
                selected_price_range = st.selectbox(
                    "가격대 선택",
                    options=data['price_range'].dropna().unique().tolist()
                )
                
                # 선택된 가격대의 키워드 분석
                price_data = data[data['price_range'] == selected_price_range]
                
                price_keywords = []
                for keywords in price_data['keywords']:
                    price_keywords.extend(keywords)
                
                price_keyword_counts = Counter(price_keywords)
                
                # 상위 15개 키워드 선택
                top_price_keywords = price_keyword_counts.most_common(15)
                price_kw_df = pd.DataFrame(top_price_keywords, columns=['keyword', 'count'])
                
                # 막대 그래프 생성
                fig = px.bar(
                    price_kw_df.sort_values('count', ascending=True),
                    y='keyword', x='count',
                    orientation='h',
                    color='count',
                    color_continuous_scale='plasma',
                    labels={'count': '빈도', 'keyword': '키워드'},
                    title=f'{selected_price_range} 가격대 인기 키워드'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        # 파일 미업로드 시 소개 페이지 표시
        st.title("무신사 패션 트렌드 대시보드")
        st.write("이 대시보드는 무신사 크롤링 데이터를 분석하여 패션 트렌드를 시각화합니다.")
        st.write("사용 방법: 좌측 사이드바에서 CSV 파일을 업로드하세요.")
        
        st.info("이 대시보드를 통해 다음과 같은 분석을 수행할 수 있습니다:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("✅ 카테고리별 상품 수와 평균 가격 분석")
            st.write("✅ 인기 브랜드 및 브랜드별 가격 분석")
            
        with col2:
            st.write("✅ 가격대별 상품 분포 분석")
            st.write("✅ 인기 키워드 워드클라우드 및 패션 트렌드 분석")
    
    # 푸터
    st.sidebar.markdown("---")
    st.sidebar.info("Fashion Trend Dashboard © 2025")

if __name__ == "__main__":
    main()