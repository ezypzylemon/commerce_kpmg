import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

def time_series_analysis(df, font_path):
    st.subheader("시계열 분석")
    
    # 날짜 컬럼 추가
    df['year_month'] = df['upload_date'].dt.strftime('%Y-%m')
    df['year_week'] = df['upload_date'].dt.strftime('%Y-%U')
    df['year'] = df['upload_date'].dt.year
    df['month'] = df['upload_date'].dt.month
    df['day'] = df['upload_date'].dt.day
    
    # 기사 발행 빈도 분석
    st.write("### 기사 발행 빈도 분석")
    
    tab1, tab2 = st.tabs(["월별 기사 수", "일별 기사 수"])
    
    with tab1:
        # 월별 기사 수
        monthly_counts = df.groupby('year_month').size().reset_index(name='기사 수')
        
        fig = px.bar(
            monthly_counts,
            x='year_month',
            y='기사 수',
            color='기사 수',
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        fig.update_layout(
            title='월별 기사 발행 빈도',
            xaxis_title='년-월',
            yaxis_title='기사 수',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # 일별 기사 수
        daily_counts = df.groupby(df['upload_date'].dt.date).size().reset_index(name='기사 수')
        daily_counts.columns = ['날짜', '기사 수']
        
        fig = px.line(
            daily_counts,
            x='날짜',
            y='기사 수',
            markers=True
        )
        
        fig.update_layout(
            title='일별 기사 발행 빈도',
            xaxis_title='날짜',
            yaxis_title='기사 수',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 키워드 트렌드 분석
    st.write("### 키워드 트렌드 분석")
    
    # 분석할 키워드 선택
    all_tokens = []
    for tokens in df['token_list']:
        all_tokens.extend(tokens)
    
    word_counts = Counter(all_tokens)
    top_words = [word for word, _ in word_counts.most_common(50)]
    
    default_keywords = ['브랜드', '패션', '컬렉션', '디지털', '지속가능', '온라인', '메타버스']
    default_keywords = [k for k in default_keywords if k in top_words]
    
    selected_keywords = st.multiselect(
        "분석할 키워드 선택",
        options=top_words,
        default=default_keywords[:5]
    )
    
    if not selected_keywords:
        st.warning("키워드를 선택해주세요.")
    else:
        # 시간 단위 선택
        time_unit = st.radio(
            "시간 단위 선택",
            options=["월별", "주별"],
            horizontal=True
        )
        
        # 각 키워드별 시간 단위 빈도 계산
        if time_unit == "월별":
            time_col = 'year_month'
            time_label = '년-월'
        else:  # 주별
            time_col = 'year_week'
            time_label = '년-주'
        
        # 키워드별 빈도 계산
        keyword_trends = {}
        
        for keyword in selected_keywords:
            # 해당 키워드가 포함된 기사 확인
            df[f'has_{keyword}'] = df['token_list'].apply(lambda tokens: 1 if keyword in tokens else 0)
            
            # 시간 단위별 집계
            trend = df.groupby(time_col)[f'has_{keyword}'].sum().reset_index()
            trend.columns = [time_col, 'frequency']
            
            keyword_trends[keyword] = trend
        
        # 트렌드 시각화
        fig = go.Figure()
        
        for keyword, trend_df in keyword_trends.items():
            fig.add_trace(
                go.Scatter(
                    x=trend_df[time_col],
                    y=trend_df['frequency'],
                    mode='lines+markers',
                    name=keyword
                )
            )
        
        fig.update_layout(
            title=f'주요 키워드 {time_unit} 트렌드',
            xaxis_title=time_label,
            yaxis_title='언급 기사 수',
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
    
    # 시간 구간 비교 분석
    st.write("### 시간 구간 비교 분석")
    
    # 구간 분할 기준일 선택
    min_date = df['upload_date'].min().date()
    max_date = df['upload_date'].max().date()
    mid_date = min_date + (max_date - min_date) / 2
    
    split_date = st.date_input(
        "구간 분할 기준일",
        value=mid_date,
        min_value=min_date,
        max_value=max_date
    )
    
    # 구간별 데이터 분할
    early_period = df[df['upload_date'].dt.date < split_date]
    late_period = df[df['upload_date'].dt.date >= split_date]
    
    # 구간별 키워드 빈도 계산
    if not selected_keywords:
        st.warning("키워드를 선택해주세요.")
    else:
        early_freq = {}
        late_freq = {}
        
        for keyword in selected_keywords:
            early_count = sum(1 for tokens in early_period['token_list'] if keyword in tokens)
            late_count = sum(1 for tokens in late_period['token_list'] if keyword in tokens)
            
            # 기사 수로 정규화
            early_freq[keyword] = early_count / len(early_period) if len(early_period) > 0 else 0
            late_freq[keyword] = late_count / len(late_period) if len(late_period) > 0 else 0
        
        # 비교 데이터 준비
        compare_data = []
        for keyword in selected_keywords:
            compare_data.extend([
                {'키워드': keyword, '구간': '초기 구간', '정규화된 빈도': early_freq[keyword]},
                {'키워드': keyword, '구간': '후기 구간', '정규화된 빈도': late_freq[keyword]}
            ])
        
        compare_df = pd.DataFrame(compare_data)
        
        # 시각화
        fig = px.bar(
            compare_df,
            x='키워드',
            y='정규화된 빈도',
            color='구간',
            barmode='group',
            color_discrete_sequence=['#5A9BD5', '#FF9966']
        )
        
        fig.update_layout(
            title=f'시간 구간 비교 분석 (기준일: {split_date})',
            xaxis_title='키워드',
            yaxis_title='정규화된 빈도 (기사 수 대비)',
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
        
        # 구간별 기사 수 표시
        col1, col2 = st.columns(2)
        col1.metric("초기 구간 기사 수", f"{len(early_period):,}개")
        col2.metric("후기 구간 기사 수", f"{len(late_period):,}개")

def analyze_time_trend(data):
    try:
        # 데이터프레임 복사
        df = data.copy()
        
        # upload_date를 datetime으로 변환
        df['upload_date'] = pd.to_datetime(df['upload_date'])
        
        # 월별 기사 수 계산
        monthly_counts = df.groupby(df['upload_date'].dt.to_period('M')).size().reset_index()
        monthly_counts.columns = ['period', 'count']
        monthly_counts['date'] = monthly_counts['period'].dt.to_timestamp()
        
        # 상위 키워드 추출
        all_tokens = []
        for tokens in df['tokens']:
            if isinstance(tokens, list):
                all_tokens.extend(tokens)
        
        top_keywords = pd.Series(all_tokens).value_counts().head(5).index.tolist()
        
        # 키워드별 월간 트렌드 계산
        keyword_trends = []
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']  # 선명한 색상
        
        for idx, keyword in enumerate(top_keywords):
            keyword_counts = []
            for period in monthly_counts['period']:
                period_data = df[df['upload_date'].dt.to_period('M') == period]
                count = sum(1 for tokens in period_data['tokens'] if keyword in tokens)
                keyword_counts.append(count)
            
            # 트렌드 라인 추가
            keyword_trends.append(
                go.Scatter(
                    x=monthly_counts['date'],
                    y=keyword_counts,
                    name=keyword,
                    line=dict(color=colors[idx], width=3),
                    mode='lines+markers'
                )
            )
        
        # 레이아웃 설정
        layout = go.Layout(
            title='키워드별 언급 추이',
            xaxis=dict(title='날짜', gridcolor='#E2E2E2'),
            yaxis=dict(title='언급 횟수', gridcolor='#E2E2E2'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=14),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#E2E2E2'
            )
        )
        
        # 그래프 생성
        fig = go.Figure(data=keyword_trends, layout=layout)
        
        return fig.to_html(full_html=False)
        
    except Exception as e:
        print(f"시간별 트렌드 분석 중 오류 발생: {e}")
        return None