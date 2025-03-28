import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go

def word_frequency_analysis(df, font_path):
    st.subheader("단어 빈도수 분석")
    
    # 모든 토큰 결합
    all_tokens = []
    for tokens in df['token_list']:
        all_tokens.extend(tokens)
    
    # 빈도수 계산
    word_counts = Counter(all_tokens)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write(f"총 {len(all_tokens):,}개의 토큰이 추출되었습니다.")
        st.write(f"고유 토큰 수: {len(word_counts):,}개")
        
        # 상위 단어 수 선택
        top_n = st.slider("표시할 상위 단어 수", 10, 50, 30)
        
        # 상위 단어 테이블
        top_words = word_counts.most_common(top_n)
        top_words_df = pd.DataFrame(top_words, columns=['단어', '빈도수'])
        st.dataframe(top_words_df, use_container_width=True)
    
    with col2:
        tab1, tab2 = st.tabs(["막대 그래프", "워드클라우드"])
        
        with tab1:
            # 상위 단어 막대 그래프
            fig = px.bar(
                top_words_df, 
                x='빈도수', 
                y='단어',
                orientation='h',
                text='빈도수',
                color='빈도수',
                color_continuous_scale=px.colors.sequential.Blues
            )
            fig.update_layout(
                title=f'상위 {top_n}개 키워드 빈도',
                yaxis={'categoryorder': 'total ascending'},
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # 워드클라우드
            if font_path:
                wordcloud = WordCloud(
                    font_path=font_path,
                    width=800, 
                    height=500,
                    background_color='white',
                    max_words=200,
                    max_font_size=150,
                    random_state=42
                ).generate_from_frequencies(dict(word_counts))
                
                plt.figure(figsize=(10, 6))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                st.pyplot(plt)
            else:
                st.warning("워드클라우드를 생성하려면 한글 폰트가 필요합니다.")
    
    # 시간에 따른 주요 단어 빈도 변화
    st.subheader("시간에 따른 주요 단어 빈도 변화")
    
    # 분석할 키워드 선택
    default_keywords = ['브랜드', '패션', '컬렉션', '디자인', '지속가능']
    top_words_only = [word for word, _ in word_counts.most_common(50)]
    selected_keywords = st.multiselect(
        "분석할 키워드 선택",
        options=top_words_only,
        default=default_keywords
    )
    
    if not selected_keywords:
        st.warning("키워드를 선택해주세요.")
    else:
        # 월별 데이터 그룹화
        df['year_month'] = df['upload_date'].dt.strftime('%Y-%m')
        monthly_groups = df.groupby('year_month')
        
        # 월별 키워드 빈도 계산
        keyword_monthly_freq = {keyword: [] for keyword in selected_keywords}
        months = sorted(df['year_month'].unique())
        
        for month in months:
            month_df = df[df['year_month'] == month]
            month_tokens = []
            for tokens in month_df['token_list']:
                month_tokens.extend(tokens)
            
            month_counts = Counter(month_tokens)
            
            for keyword in selected_keywords:
                keyword_monthly_freq[keyword].append(month_counts.get(keyword, 0))
        
        # 월별 추이 그래프
        fig = go.Figure()
        
        for keyword in selected_keywords:
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=keyword_monthly_freq[keyword],
                    mode='lines+markers',
                    name=keyword
                )
            )
        
        fig.update_layout(
            title='월별 키워드 빈도 추이',
            xaxis_title='년-월',
            yaxis_title='빈도수',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 카테고리별 키워드 비교
        st.subheader("카테고리별 키워드 비교")
        
        categories = {
            '브랜드': ['나이키', '아디다스', '구찌', '샤넬', '자라', '아더에러', '루이비통', '한세'],
            '소재': ['면', '니트', '울', '데님', '코튼', '실크', '가죽', '폴리에스터'],
            '스타일': ['캐주얼', '포멀', '빈티지', '미니멀', '스트릿', '클래식', '컨템포러리']
        }
        
        selected_category = st.selectbox(
            "카테고리 선택",
            options=list(categories.keys())
        )
        
        # 카테고리별 키워드 빈도 계산
        category_words = categories[selected_category]
        category_counts = {word: sum(1 for tokens in df['token_list'] if word in tokens) for word in category_words}
        
        # 카테고리 키워드 막대 그래프
        category_df = pd.DataFrame({
            '키워드': list(category_counts.keys()),
            '빈도수': list(category_counts.values())
        }).sort_values('빈도수', ascending=False)
        
        fig = px.bar(
            category_df,
            x='키워드',
            y='빈도수',
            color='빈도수',
            color_continuous_scale=px.colors.sequential.Viridis,
            text='빈도수'
        )
        
        fig.update_layout(
            title=f'{selected_category} 관련 키워드 빈도',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)