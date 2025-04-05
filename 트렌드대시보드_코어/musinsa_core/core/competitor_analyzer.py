import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os

def load_competitor_data(file_path):
    """무신사 데이터 로드 및 전처리"""
    try:
        df = pd.read_csv(file_path)
        
        # 날짜 컬럼 처리
        date_columns = ['date', 'published_at', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                break
        
        return df
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")
        return None

def filter_by_period(df, period):
    """기간별 데이터 필터링"""
    if df is None or df.empty:
        return None
    
    today = datetime.now()
    
    period_map = {
        '1주일': timedelta(days=7),
        '1개월': timedelta(days=30),
        '3개월': timedelta(days=90),
        '6개월': timedelta(days=180),
        '1년': timedelta(days=365),
        '2년': timedelta(days=730)
    }
    
    if period not in period_map:
        return df
    
    start_date = today - period_map[period]
    date_col = next((col for col in ['date', 'published_at', 'created_at'] if col in df.columns), None)
    
    if date_col:
        return df[df[date_col] >= start_date]
    
    return df

def filter_by_date_range(df, start_date, end_date):
    """날짜 범위로 데이터 필터링"""
    if df is None or df.empty:
        return None
    
    date_col = next((col for col in ['date', 'published_at', 'created_at'] if col in df.columns), None)
    
    if date_col:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return df[(df[date_col] >= start) & (df[date_col] <= end)]
    
    return df

def create_brand_trend_chart(df, save_path):
    """브랜드별 트렌드 차트 생성"""
    plt.figure(figsize=(12, 6))
    
    # 브랜드별 데이터 집계
    brand_data = df.groupby('brand').size().sort_values(ascending=False).head(10)
    
    # 막대 그래프 생성
    sns.barplot(x=brand_data.values, y=brand_data.index)
    plt.title('상위 10개 브랜드 트렌드')
    plt.xlabel('상품 수')
    plt.ylabel('브랜드')
    
    # 차트 저장
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def create_category_trend_chart(df, save_path):
    """카테고리별 트렌드 차트 생성"""
    plt.figure(figsize=(12, 6))
    
    # 카테고리별 데이터 집계
    category_data = df.groupby('category').size().sort_values(ascending=False)
    
    # 파이 차트 생성
    plt.pie(category_data.values, labels=category_data.index, autopct='%1.1f%%')
    plt.title('카테고리별 분포')
    
    # 차트 저장
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def create_price_trend_chart(df, save_path):
    """가격대별 트렌드 차트 생성"""
    plt.figure(figsize=(12, 6))
    
    # 가격대 구분
    df['price_range'] = pd.cut(df['price'], 
                              bins=[0, 10000, 30000, 50000, 100000, float('inf')],
                              labels=['1만원 이하', '1-3만원', '3-5만원', '5-10만원', '10만원 이상'])
    
    # 가격대별 데이터 집계
    price_data = df.groupby('price_range').size()
    
    # 막대 그래프 생성
    sns.barplot(x=price_data.index, y=price_data.values)
    plt.title('가격대별 분포')
    plt.xlabel('가격대')
    plt.ylabel('상품 수')
    plt.xticks(rotation=45)
    
    # 차트 저장
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def generate_competitor_analysis(file_path, period='1개월'):
    """경쟁사 분석 데이터 생성"""
    # 데이터 로드
    df = load_competitor_data(file_path)
    if df is None:
        return None
    
    # 기간 필터링
    df = filter_by_period(df, period)
    if df is None or df.empty:
        return None
    
    # 차트 저장 디렉토리 생성
    chart_dir = os.path.join('static', 'images', 'competitor')
    os.makedirs(chart_dir, exist_ok=True)
    
    # 차트 생성
    create_brand_trend_chart(df, os.path.join(chart_dir, 'brand_trend.png'))
    create_category_trend_chart(df, os.path.join(chart_dir, 'category_trend.png'))
    create_price_trend_chart(df, os.path.join(chart_dir, 'price_trend.png'))
    
    # 분석 결과 반환
    return {
        'brand_trend': 'images/competitor/brand_trend.png',
        'category_trend': 'images/competitor/category_trend.png',
        'price_trend': 'images/competitor/price_trend.png',
        'total_items': len(df),
        'total_brands': df['brand'].nunique(),
        'total_categories': df['category'].nunique(),
        'avg_price': df['price'].mean(),
        'top_brands': df.groupby('brand').size().sort_values(ascending=False).head(10).to_dict()
    }

def generate_competitor_analysis_by_date(file_path, start_date, end_date):
    """날짜 범위로 경쟁사 분석 데이터 생성"""
    # 데이터 로드
    df = load_competitor_data(file_path)
    if df is None:
        return None
    
    # 날짜 범위 필터링
    df = filter_by_date_range(df, start_date, end_date)
    if df is None or df.empty:
        return None
    
    # 차트 저장 디렉토리 생성
    chart_dir = os.path.join('static', 'images', 'competitor')
    os.makedirs(chart_dir, exist_ok=True)
    
    # 차트 생성
    create_brand_trend_chart(df, os.path.join(chart_dir, 'brand_trend.png'))
    create_category_trend_chart(df, os.path.join(chart_dir, 'category_trend.png'))
    create_price_trend_chart(df, os.path.join(chart_dir, 'price_trend.png'))
    
    # 분석 결과 반환
    return {
        'brand_trend': 'images/competitor/brand_trend.png',
        'category_trend': 'images/competitor/category_trend.png',
        'price_trend': 'images/competitor/price_trend.png',
        'total_items': len(df),
        'total_brands': df['brand'].nunique(),
        'total_categories': df['category'].nunique(),
        'avg_price': df['price'].mean(),
        'top_brands': df.groupby('brand').size().sort_values(ascending=False).head(10).to_dict()
    } 