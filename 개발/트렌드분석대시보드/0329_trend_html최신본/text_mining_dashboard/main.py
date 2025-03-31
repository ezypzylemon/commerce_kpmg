import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.font_manager as fm

# 분석 모듈 임포트
from word_frequency import word_frequency_analysis
from time_series import time_series_analysis
from tfidf_analysis import tfidf_analysis
from topic_modeling import topic_modeling_analysis
from word_association import word_association_analysis
from sentiment_analysis import sentiment_analysis

# 한글 폰트 설정
def setup_korean_font():
    # 맥OS 기본 한글 폰트
    font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
    if os.path.exists(font_path):
        plt.rcParams['font.family'] = 'AppleGothic'
        return font_path
    
    # 다른 한글 폰트 찾기
    try:
        font_files = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        korean_fonts = [f for f in font_files if any(name in f.lower() for name in 
                                                ['gothic', 'gulim', 'malgun', 'batang', 'dotum'])]
        if korean_fonts:
            font_path = korean_fonts[0]
            plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()
            return font_path
    except:
        pass
    
    st.warning("한글 폰트를 찾을 수 없습니다. 한글이 깨져 보일 수 있습니다.")
    return None

# 데이터 로딩 함수
@st.cache_data
def load_data():
    try:
        # 데이터가 이미 CSV로 저장되어 있다면 불러오기
        if os.path.exists('news_data.csv'):
            df = pd.read_csv('news_data.csv', parse_dates=['upload_date'])
            df['token_list'] = df['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else [])
            return df
        
        # MySQL에서 데이터 로드 (MySQL 연결 정보 필요)
        import mysql.connector
        
        # MySQL 연결 설정
        MYSQL_CONFIG = {
            'host': 'localhost',
            'user': 'root',
            'password': '9999',
            'database': 'hyungtaeso',
            'charset': 'utf8mb4'
        }
        
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        query = """
        SELECT id, category, title, tokens, content, upload_date 
        FROM tokenised 
        WHERE category = 'knews_articles'
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # 데이터 전처리
        df['upload_date'] = pd.to_datetime(df['upload_date'])
        df['token_list'] = df['tokens'].apply(lambda x: json.loads(x) if isinstance(x, str) else [])
        
        # CSV로 저장
        df.to_csv('news_data.csv', index=False)
        
        return df
    
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        # 샘플 데이터 생성
        st.warning("샘플 데이터를 생성합니다.")
        sample_df = pd.DataFrame({
            'id': range(1, 11),
            'category': ['knews_articles'] * 10,
            'title': [f'샘플 기사 {i}' for i in range(1, 11)],
            'tokens': ['["브랜드", "패션", "디자인"]'] * 10,
            'content': [f'샘플 내용 {i}' for i in range(1, 11)],
            'upload_date': pd.date_range(start='2025-01-01', periods=10)
        })
        sample_df['token_list'] = sample_df['tokens'].apply(json.loads)
        return sample_df

# 메인 앱
def main():
    st.set_page_config(
        page_title="한국섬유신문 데이터 분석",
        page_icon="📊",
        layout="wide"
    )
    
    # 한글 폰트 설정
    font_path = setup_korean_font()
    
    # 앱 제목
    st.title("한국섬유신문 데이터 분석 대시보드")
    st.markdown("---")
    
    # 데이터 로드
    with st.spinner("데이터를 불러오는 중입니다..."):
        df = load_data()
    
    # 데이터 기본 정보
    st.subheader("데이터 기본 정보")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 기사 수", f"{len(df):,}개")
    col2.metric("기간", f"{df['upload_date'].min().strftime('%Y-%m-%d')} ~ {df['upload_date'].max().strftime('%Y-%m-%d')}")
    col3.metric("평균 토큰 수", f"{df['token_list'].apply(len).mean():.1f}개")
    
    # 분석 선택
    st.markdown("---")
    st.subheader("분석 방법 선택")
    analysis_options = [
        "단어 빈도수 분석",
        "시계열 분석",
        "TF-IDF 분석",
        "토픽 모델링",
        "연관어 분석",
        "감성 분석"
    ]
    
    selected_analysis = st.selectbox(
        "분석 방법을 선택하세요:",
        analysis_options
    )
    
    # 선택한 분석 실행
    if selected_analysis == "단어 빈도수 분석":
        word_frequency_analysis(df, font_path)
    elif selected_analysis == "시계열 분석":
        time_series_analysis(df, font_path)
    elif selected_analysis == "TF-IDF 분석":
        tfidf_analysis(df, font_path)
    elif selected_analysis == "토픽 모델링":
        topic_modeling_analysis(df, font_path)
    elif selected_analysis == "연관어 분석":
        word_association_analysis(df, font_path)
    elif selected_analysis == "감성 분석":
        sentiment_analysis(df, font_path)
    
    # 푸터
    st.markdown("---")
    st.caption("© 2025 한국섬유신문 데이터 분석 프로젝트")

if __name__ == "__main__":
    main()