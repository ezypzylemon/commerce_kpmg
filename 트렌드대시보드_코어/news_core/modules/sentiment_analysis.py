import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def sentiment_analysis(df, font_path):
    st.subheader("감성 분석")
    
    st.info("이 분석은 간단한 감성 사전을 사용한 기본적인 감성 분석입니다. 정확한 감성 분석을 위해서는 더 고급 기법이 필요할 수 있습니다.")
    
    # 감성 사전 로드
    sentiment_dict = load_sentiment_dictionary()
    
    # 데이터 준비
    df = prepare_sentiment_data(df)
    
    # 감성 분석 실행
    with st.spinner("기사 감성 분석 중..."):
        df = calculate_article_sentiment(df, sentiment_dict)
    
    # 분석 옵션
    sentiment_options = [
        "감성 분포 분석",
        "시간에 따른 감성 변화",
        "키워드별 감성 분석",
        "대표 기사 분석"
    ]
    
    selected_sentiment_option = st.radio(
        "분석 옵션 선택",
        options=sentiment_options,
        horizontal=True
    )
    
    if selected_sentiment_option == "감성 분포 분석":
        # 감성 분포 분석
        st.subheader("감성 분포 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 감성 점수 히스토그램
            fig = px.histogram(
                df,
                x='sentiment_score',
                nbins=50,
                color_discrete_sequence=['royalblue'],
                marginal='box'
            )
            
            fig.add_vline(
                x=0,
                line_dash="dash",
                line_color="red",
                annotation_text="중립",
                annotation_position="top"
            )
            
            fig.update_layout(
                title='기사 감성 점수 분포',
                xaxis_title='감성 점수',
                yaxis_title='기사 수',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 감성 범주 파이 차트
            sentiment_counts = df['sentiment'].value_counts()
            
            fig = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color=sentiment_counts.index,
                color_discrete_map={
                    '긍정': 'skyblue',
                    '중립': 'lightgray',
                    '부정': 'salmon'
                }
            )
            
            fig.update_layout(
                title='기사 감성 분포',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 감성별 워드클라우드
        if font_path:
            st.subheader("감성별 주요 단어")
            
            tab1, tab2 = st.tabs(["긍정 단어", "부정 단어"])
            
            with tab1:
                # 긍정 단어 워드클라우드
                positive_words = []
                for pos_list in df['positive_words']:
                    positive_words.extend(pos_list)
                
                if positive_words:
                    pos_word_freq = Counter(positive_words)
                    
                    wordcloud = WordCloud(
                        font_path=font_path,
                        width=800, 
                        height=400,
                        background_color='white',
                        colormap='YlGn',
                        max_words=100
                    ).generate_from_frequencies(pos_word_freq)
                    
                    plt.figure(figsize=(10, 6))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    plt.title('긍정 단어 워드클라우드')
                    st.pyplot(plt)
                    
                    # 상위 긍정 단어
                    st.write("**상위 긍정 단어:**")
                    pos_df = pd.DataFrame(pos_word_freq.most_common(15), columns=['단어', '빈도'])
                    st.dataframe(pos_df, use_container_width=True)
                else:
                    st.info("긍정 단어가 없습니다.")
            
            with tab2:
                # 부정 단어 워드클라우드
                negative_words = []
                for neg_list in df['negative_words']:
                    negative_words.extend(neg_list)
                
                if negative_words:
                    neg_word_freq = Counter(negative_words)
                    
                    wordcloud = WordCloud(
                        font_path=font_path,
                        width=800, 
                        height=400,
                        background_color='white',
                        colormap='OrRd',
                        max_words=100
                    ).generate_from_frequencies(neg_word_freq)
                    
                    plt.figure(figsize=(10, 6))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    plt.title('부정 단어 워드클라우드')
                    st.pyplot(plt)
                    
                    # 상위 부정 단어
                    st.write("**상위 부정 단어:**")
                    neg_df = pd.DataFrame(neg_word_freq.most_common(15), columns=['단어', '빈도'])
                    st.dataframe(neg_df, use_container_width=True)
                else:
                    st.info("부정 단어가 없습니다.")
    
    elif selected_sentiment_option == "시간에 따른 감성 변화":
        # 시간에 따른 감성 변화 분석
        st.subheader("시간에 따른 감성 변화")
        
        # 월별 감성 점수 평균
        df['year_month'] = df['upload_date'].dt.strftime('%Y-%m')
        monthly_sentiment = df.groupby('year_month')['sentiment_score'].agg(['mean', 'count']).reset_index()
        monthly_sentiment.columns = ['year_month', 'avg_sentiment', 'article_count']
        
        # 시각화
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 감성 점수 라인
        fig.add_trace(
            go.Scatter(
                x=monthly_sentiment['year_month'],
                y=monthly_sentiment['avg_sentiment'],
                mode='lines+markers',
                name='평균 감성 점수',
                line=dict(color='royalblue', width=3)
            ),
            secondary_y=False
        )
        
        # 기사 수 바 차트
        fig.add_trace(
            go.Bar(
                x=monthly_sentiment['year_month'],
                y=monthly_sentiment['article_count'],
                name='기사 수',
                marker=dict(color='lightgray', opacity=0.7)
            ),
            secondary_y=True
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title='시간에 따른 감성 변화',
            xaxis_title='년-월',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="평균 감성 점수", secondary_y=False)
        fig.update_yaxes(title_text="기사 수", secondary_y=True)
        
        # 중립선 추가
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            opacity=0.7,
            secondary_y=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 월별 감성 분포
        st.subheader("월별 감성 분포")
        
        # 월별 감성 범주 비율
        sentiment_by_month = pd.crosstab(
            df['year_month'], 
            df['sentiment'],
            normalize='index'
        ) * 100
        
        # 시각화
        fig = px.area(
            sentiment_by_month,
            color_discrete_map={
                '긍정': 'skyblue',
                '중립': 'lightgray',
                '부정': 'salmon'
            }
        )
        
        fig.update_layout(
            title='월별 감성 분포 변화',
            xaxis_title='년-월',
            yaxis_title='비율 (%)',
            height=500,
            legend_title="감성"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_sentiment_option == "키워드별 감성 분석":
        # 키워드별 감성 분석
        st.subheader("키워드별 감성 분석")
        
        # 분석할 키워드 선택
        all_tokens = []
        for tokens in df['token_list']:
            all_tokens.extend(tokens)
        
        word_counts = Counter(all_tokens)
        top_words = [word for word, _ in word_counts.most_common(100)]
        
        default_keywords = ['브랜드', '패션', '컬렉션', '디자인', '온라인', '지속가능', '매출', '투자', '위기', '성장']
        default_keywords = [k for k in default_keywords if k in top_words]
        
        selected_keywords = st.multiselect(
            "분석할 키워드 선택",
            options=top_words,
            default=default_keywords[:5]
        )
        
        if not selected_keywords:
            st.warning("키워드를 선택해주세요.")
        else:
            # 키워드별 감성 분석
            keyword_sentiments = {}
            
            for keyword in selected_keywords:
                # 해당 키워드가 포함된 기사 필터링
                contains_keyword = df['token_list'].apply(lambda tokens: keyword in tokens)
                keyword_articles = df[contains_keyword]
                
                if len(keyword_articles) > 0:
                    # 감성 점수 통계
                    avg_sentiment = keyword_articles['sentiment_score'].mean()
                    pos_pct = (keyword_articles['sentiment'] == '긍정').mean() * 100
                    neg_pct = (keyword_articles['sentiment'] == '부정').mean() * 100
                    neutral_pct = (keyword_articles['sentiment'] == '중립').mean() * 100
                    
                    keyword_sentiments[keyword] = {
                        'avg_score': avg_sentiment,
                        'positive_pct': pos_pct,
                        'negative_pct': neg_pct,
                        'neutral_pct': neutral_pct,
                        'count': len(keyword_articles)
                    }
            
            # 결과 시각화
            if keyword_sentiments:
                # 평균 감성 점수 막대 그래프
                score_data = []
                for keyword, stats in keyword_sentiments.items():
                    score_data.append({
                        'keyword': keyword,
                        'avg_score': stats['avg_score'],
                        'count': stats['count']
                    })
                
                score_df = pd.DataFrame(score_data)
                
                fig = px.bar(
                    score_df,
                    x='keyword',
                    y='avg_score',
                    color='avg_score',
                    color_continuous_scale='RdBu',
                    text='avg_score',
                    size='count',
                    hover_data=['count']
                )
                
                fig.update_traces(
                    texttemplate='%{text:.2f}',
                    textposition='outside'
                )
                
                fig.update_layout(
                    title='키워드별 평균 감성 점수',
                    xaxis_title='키워드',
                    yaxis_title='평균 감성 점수',
                    coloraxis_colorbar_title='감성 점수',
                    height=500
                )
                
                # 중립선 추가
                fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color="gray",
                    opacity=0.7
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 키워드별 감성 분포 차트
                st.subheader("키워드별 감성 분포")
                
                sentiment_data = []
                for keyword, stats in keyword_sentiments.items():
                    sentiment_data.append({
                        'keyword': keyword,
                        '긍정': stats['positive_pct'],
                        '중립': stats['neutral_pct'],
                        '부정': stats['negative_pct'],
                        'count': stats['count']
                    })
                
                sentiment_df = pd.DataFrame(sentiment_data)
                
                fig = go.Figure()
                
                for sentiment in ['긍정', '중립', '부정']:
                    fig.add_trace(go.Bar(
                        x=sentiment_df['keyword'],
                        y=sentiment_df[sentiment],
                        name=sentiment,
                        text=sentiment_df[sentiment].apply(lambda x: f'{x:.1f}%'),
                        textposition='inside',
                        marker_color={
                            '긍정': 'skyblue',
                            '중립': 'lightgray',
                            '부정': 'salmon'
                        }[sentiment]
                    ))
                
                fig.update_layout(
                    title='키워드별 감성 분포',
                    xaxis_title='키워드',
                    yaxis_title='비율 (%)',
                    barmode='stack',
                    height=500,
                    legend_title="감성"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 키워드별 기사 수 표시
                st.write("**키워드별 분석 기사 수:**")
                count_df = pd.DataFrame({
                    '키워드': list(keyword_sentiments.keys()),
                    '기사 수': [stats['count'] for stats in keyword_sentiments.values()]
                })
                st.dataframe(count_df, use_container_width=True)
    
    elif selected_sentiment_option == "대표 기사 분석":
        # 대표 기사 분석
        st.subheader("대표 기사 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 가장 긍정적인 기사
            st.write("### 가장 긍정적인 기사")
            
            most_positive = df.loc[df['sentiment_score'].idxmax()]
            display_sample_article(most_positive, "긍정")
        
        with col2:
            # 가장 부정적인 기사
            st.write("### 가장 부정적인 기사")
            
            most_negative = df.loc[df['sentiment_score'].idxmin()]
            display_sample_article(most_negative, "부정")
    
    return df

def load_sentiment_dictionary():
    """감성 사전 로드 함수"""
    # 기본 감성 사전 (예시)
    # 실제 구현에서는 외부 파일이나 데이터베이스에서 로드할 수 있음
    
    positive_words = [
        '좋은', '훌륭한', '우수한', '뛰어난', '성공', '상승', '증가', '성장', '혁신', 
        '인기', '긍정적', '기회', '개선', '발전', '호평', '효과적', '효율적', '이익', 
        '수익', '매출', '선도', '앞서', '기대', '호조', '활발', '두각', '주목', 
        '강세', '강화', '최고', '최상', '최대', '안정', '견고', '든든', '향상',
        '슬기롭게', '극복', '회복', '반등', '해소', '개척', '성과', '돌파', '확대'
    ]
    
    negative_words = [
        '나쁜', '불량', '저조', '하락', '감소', '축소', '위기', '문제', '비판', 
        '부정적', '어려움', '악화', '손실', '적자', '실패', '퇴보', '악평', '비효율적', 
        '약세', '부진', '위험', '우려', '걱정', '실망', '침체', '후퇴', '위축', 
        '저하', '약화', '최저', '최악', '최소', '불안', '취약', '느슨', '갈등',
        '혼란', '논란', '충격', '급락', '물의', '파산', '적신호', '불투명', '타격'
    ]
    
    # 감성 사전 구성
    sentiment_dict = {
        'positive': set(positive_words),
        'negative': set(negative_words)
    }
    
    return sentiment_dict

def prepare_sentiment_data(df):
    """감성 분석을 위한 데이터 준비 함수"""
    # 필요한 열이 없는 경우 추가
    if 'token_list' not in df.columns:
        # 토큰화 데이터가 없는 경우, 간단한 토큰화 수행
        df['token_list'] = df['content'].str.split()
    
    # 날짜 데이터 확인 및 변환
    if 'upload_date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['upload_date']):
        df['upload_date'] = pd.to_datetime(df['upload_date'], errors='coerce')
    
    return df

def calculate_article_sentiment(df, sentiment_dict):
    """기사별 감성 점수 계산 함수"""
    # 긍정/부정 단어 리스트 및 점수 계산
    df['positive_words'] = df['token_list'].apply(
        lambda tokens: [word for word in tokens if word in sentiment_dict['positive']]
    )
    
    df['negative_words'] = df['token_list'].apply(
        lambda tokens: [word for word in tokens if word in sentiment_dict['negative']]
    )
    
    # 감성 점수 계산 (긍정 단어 수 - 부정 단어 수) / 토큰 총 수
    df['positive_count'] = df['positive_words'].apply(len)
    df['negative_count'] = df['negative_words'].apply(len)
    df['token_count'] = df['token_list'].apply(len)
    
    # 정규화된 감성 점수 계산
    df['sentiment_score'] = df.apply(
        lambda row: (row['positive_count'] - row['negative_count']) / max(row['token_count'], 1) * 100,
        axis=1
    )
    
    # 감성 범주 분류
    df['sentiment'] = df['sentiment_score'].apply(
        lambda score: '긍정' if score > 1 else ('부정' if score < -1 else '중립')
    )
    
    return df

def display_sample_article(article, sentiment_type):
    """샘플 기사 표시 함수"""
    st.markdown(f"**제목:** {article.get('title', '제목 없음')}")
    st.markdown(f"**날짜:** {article.get('upload_date', '날짜 정보 없음')}")
    st.markdown(f"**감성 점수:** {article['sentiment_score']:.2f}")
    
    # 하이라이트할 단어 목록
    if sentiment_type == "긍정":
        highlight_words = article['positive_words']
        highlight_color = "rgba(0, 255, 0, 0.3)"  # 연한 녹색
    else:
        highlight_words = article['negative_words']
        highlight_color = "rgba(255, 0, 0, 0.3)"  # 연한 빨간색
    
    # 내용 하이라이트 처리
    content = article.get('content', '내용 없음')
    
    # 내용이 너무 긴 경우 일부만 표시
    if len(content) > 500:
        content = content[:500] + "..."
    
    # 하이라이트된 내용 표시
    st.markdown("**내용 미리보기:**")
    
    # 하이라이트 스타일 적용
    highlighted_content = content
    for word in highlight_words:
        highlighted_content = highlighted_content.replace(
            word, 
            f'<span style="background-color: {highlight_color};">{word}</span>'
        )
    
    st.markdown(highlighted_content, unsafe_allow_html=True)
    
    # 감성 단어 표시
    st.markdown(f"**{sentiment_type} 단어:** {', '.join(highlight_words[:10])}" + 
                ("..." if len(highlight_words) > 10 else ""))