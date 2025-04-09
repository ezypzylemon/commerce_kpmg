import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (서버 환경용)
import matplotlib.font_manager as fm
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 다른 한글 폰트 경로들
font_paths = [
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/Library/Fonts/NanumGothic.ttf',
    'C:/Windows/Fonts/malgun.ttf'
]

for path in font_paths:
    if os.path.exists(path):
        plt.rcParams['font.family'] = fm.FontProperties(fname=path).get_name()
        break

# 기간별 매핑
period_map = {
    '7일': 7,
    '2주': 14,
    '1개월': 30,
    '3개월': 90,
    '6개월': 180,
    '1년': 365
}

def load_competitor_data(file_path):
    """무신사 데이터 로드 및 전처리"""
    try:
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return None
        
        # CSV 파일 로드
        df = pd.read_csv(file_path)
        
        # crawled_at을 날짜 컬럼으로 사용
        df['crawled_at'] = pd.to_datetime(df['crawled_at'], errors='coerce')
        
        # 날짜 컬럼 표준화 - date 컬럼에 crawled_at 복사
        df['date'] = df['crawled_at']
        
        # 가격 컬럼 숫자로 변환 (한글 '원' 제거 및 쉼표 제거)
        def convert_price(price):
            try:
                # 문자열이 아니면 그대로 반환 (이미 숫자인 경우)
                if not isinstance(price, str):
                    # NaN 체크
                    if pd.isna(price):
                        return 0.0
                    return float(price)
                
                # '원' 제거, 쉼표 제거 후 변환
                price_str = price.replace('원', '').replace(',', '').strip()
                if not price_str:  # 빈 문자열 체크
                    return 0.0
                return float(price_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"가격 변환 실패: {price}, 오류: {e}")
                return 0.0
        
        df['price'] = df['price'].apply(convert_price)
        
        # 필수 컬럼 확인 및 추가
        required_columns = ['brand', 'category', 'price']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"필수 컬럼이 없습니다: {col}")
                df[col] = None
        
        return df
    
    except Exception as e:
        logger.error(f"데이터 로드 중 오류 발생: {e}")
        return None

def filter_by_period(df, period):
    """기간별 데이터 필터링"""
    try:
        if df is None or df.empty:
            return df
        
        # 날짜 컬럼 확인
        date_col = 'crawled_at' if 'crawled_at' in df.columns else 'date'
        if date_col not in df.columns:
            logger.warning("날짜 컬럼이 존재하지 않습니다.")
            return df
        
        # 기준 날짜 설정 (현재 날짜)
        today = pd.Timestamp.now()
        
        # 기간 매핑에서 일수 가져오기
        days = period_map.get(period)
        if days is None:
            logger.warning(f"지원하지 않는 기간: {period}, 기본값 30일로 설정")
            days = 30
        
        # 시작 날짜 계산
        start_date = today - timedelta(days=days)
        
        # 날짜 필터링
        filtered_df = df[
            (df[date_col] >= start_date) & 
            (df[date_col].notna())
        ]
        
        if filtered_df.empty:
            logger.warning(f"{period} 기간 동안 데이터가 없습니다.")
            return None
        
        return filtered_df
    except Exception as e:
        logger.error(f"기간별 필터링 중 오류 발생: {e}")
        return None

def filter_by_date_range(df, start_date, end_date):
    """날짜 범위로 데이터 필터링"""
    try:
        if df is None or df.empty:
            return df
        
        # 날짜 컬럼 확인
        date_col = 'crawled_at' if 'crawled_at' in df.columns else 'date'
        if date_col not in df.columns:
            logger.warning("날짜 컬럼이 존재하지 않습니다.")
            return df
        
        # 문자열 날짜를 datetime으로 변환
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        # 날짜 필터링
        filtered_df = df[
            (df[date_col] >= start_date) & 
            (df[date_col] <= end_date) & 
            (df[date_col].notna())
        ]
        
        if filtered_df.empty:
            logger.warning(f"{start_date}부터 {end_date}까지 데이터가 없습니다.")
            return None
        
        return filtered_df
    except Exception as e:
        logger.error(f"날짜 범위 필터링 중 오류 발생: {e}")
        return None

def create_brand_trend_chart(df, save_path):
    """브랜드별 트렌드 차트 생성"""
    try:
        plt.figure(figsize=(12, 6))
        
        # 배경색 설정
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
        
        # 상위 10개 브랜드 선택
        top_brands = df['brand'].value_counts().head(10)
        
        # 막대 그래프 생성 - 색상 변경
        ax = top_brands.plot(kind='bar', color='#36D6BE')
        
        # 텍스트 색상 설정
        plt.title('인기 브랜드 TOP 10', fontsize=14, color='black', fontweight='bold')
        plt.xlabel('브랜드', fontsize=12, color='black')
        plt.ylabel('상품 수', fontsize=12, color='black')
        
        # 눈금 색상 설정
        ax.tick_params(axis='x', colors='black', labelrotation=45)
        ax.tick_params(axis='y', colors='black')
        
        # 눈금선 설정
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        # 차트 저장 - DPI 향상
        plt.savefig(save_path, dpi=200)
        plt.close()
    except Exception as e:
        logger.error(f"브랜드 트렌드 차트 생성 중 오류 발생: {e}")
        # 기본 에러 이미지 생성
        create_error_chart(save_path, "브랜드 차트 생성 실패")

def create_category_trend_chart(df, save_path):
    """카테고리별 트렌드 차트 생성"""
    try:
        plt.figure(figsize=(12, 6))
        
        # 배경색 설정
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
        
        # 상위 10개 카테고리 선택
        top_categories = df['category'].value_counts().head(10)
        
        # 막대 그래프 생성 - 색상 변경
        ax = top_categories.plot(kind='bar', color='#6B5AED')
        
        # 텍스트 색상 설정
        plt.title('인기 카테고리 TOP 10', fontsize=14, color='black', fontweight='bold')
        plt.xlabel('카테고리', fontsize=12, color='black')
        plt.ylabel('상품 수', fontsize=12, color='black')
        
        # 눈금 색상 설정
        ax.tick_params(axis='x', colors='black', labelrotation=45)
        ax.tick_params(axis='y', colors='black')
        
        # 눈금선 설정
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        # 차트 저장 - DPI 향상
        plt.savefig(save_path, dpi=200)
        plt.close()
    except Exception as e:
        logger.error(f"카테고리 트렌드 차트 생성 중 오류 발생: {e}")
        # 기본 에러 이미지 생성
        create_error_chart(save_path, "카테고리 차트 생성 실패")

def create_price_trend_chart(df, save_path):
    """가격대별 트렌드 차트 생성"""
    try:
        plt.figure(figsize=(12, 6))
        
        # 배경색 설정
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
        
        # 가격이 숫자형인지 확인하고 아니면 변환
        if df['price'].dtype != 'float64' and df['price'].dtype != 'int64':
            logger.warning(f"가격 데이터 타입이 숫자가 아닙니다: {df['price'].dtype}")
            try:
                df['price'] = df['price'].astype(float)
            except Exception as e:
                logger.error(f"가격 데이터 타입 변환 실패: {e}")
                # 기본 에러 이미지 생성
                create_error_chart(save_path, "가격 데이터 변환 실패")
                return
        
        # 가격대 구분 (price 컬럼 사용)
        df['price_range'] = pd.cut(df['price'], 
                                  bins=[0, 10000, 30000, 50000, 100000, float('inf')],
                                  labels=['1만원 이하', '1-3만원', '3-5만원', '5-10만원', '10만원 이상'])
        
        # 가격대별 데이터 집계
        price_data = df.groupby('price_range').size()
        
        # 데이터가 없는 경우 처리
        if price_data.empty:
            logger.warning("가격대별 데이터가 없습니다.")
            create_error_chart(save_path, "가격대별 데이터가 없습니다.")
            return
        
        # 막대 그래프 생성 - 색상 변경
        ax = price_data.plot(kind='bar', color='#FF5A5A')
        
        # 텍스트 색상 설정
        plt.title('가격대별 분포', fontsize=14, color='black', fontweight='bold')
        plt.xlabel('가격대', fontsize=12, color='black')
        plt.ylabel('상품 수', fontsize=12, color='black')
        
        # 눈금 색상 설정
        ax.tick_params(axis='x', colors='black', labelrotation=45)
        ax.tick_params(axis='y', colors='black')
        
        # 눈금선 설정
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        # 차트 저장 - DPI 향상
        plt.savefig(save_path, dpi=200)
        plt.close()
    except Exception as e:
        logger.error(f"가격대 트렌드 차트 생성 중 오류 발생: {e}")
        # 기본 에러 이미지 생성
        create_error_chart(save_path, "가격대 차트 생성 실패")

def create_error_chart(save_path, error_message="차트 생성 실패"):
    """에러 메시지를 표시하는 기본 차트 생성"""
    try:
        plt.figure(figsize=(8, 4))
        plt.text(0.5, 0.5, error_message, ha='center', va='center', fontsize=12, color='black', fontweight='bold')
        plt.axis('off')
        
        # 배경색 설정
        plt.rcParams['figure.facecolor'] = 'white'
        
        plt.savefig(save_path, dpi=150)
        plt.close()
    except Exception as e:
        logger.error(f"에러 차트 생성 중 오류 발생: {e}")

def generate_competitor_analysis(file_path, period='1개월'):
    """경쟁사 분석 데이터 생성"""
    try:
        # 데이터 로드
        df = load_competitor_data(file_path)
        if df is None or df.empty:
            logger.warning("로드된 데이터가 없습니다.")
            return None
        
        # 기간 필터링
        df = filter_by_period(df, period)
        if df is None or df.empty:
            logger.warning("필터링 후 데이터가 없습니다.")
            return None
        
        # 차트 저장 디렉토리 생성
        chart_dir = os.path.join('static', 'images', 'competitor')
        os.makedirs(chart_dir, exist_ok=True)
        
        # 차트 생성
        try:
            create_brand_trend_chart(df, os.path.join(chart_dir, 'brand_trend.png'))
            create_category_trend_chart(df, os.path.join(chart_dir, 'category_trend.png'))
            create_price_trend_chart(df, os.path.join(chart_dir, 'price_trend.png'))
        except Exception as e:
            logger.error(f"차트 생성 중 오류: {e}")
        
        # 분석 결과 계산
        try:
            avg_price = df['price'].mean()
            if pd.isna(avg_price):
                avg_price = 0
                logger.warning("평균 가격 계산 결과가 NaN입니다.")
        except Exception as e:
            logger.error(f"평균 가격 계산 중 오류 발생: {e}")
            avg_price = 0
            
        # 브랜드 통계 계산
        try:
            top_brands = df.groupby('brand').size().sort_values(ascending=False).head(10).to_dict()
            if not top_brands:
                logger.warning("브랜드 통계가 없습니다.")
        except Exception as e:
            logger.error(f"브랜드 통계 계산 중 오류 발생: {e}")
            top_brands = {}
            
        # 분석 결과 반환 - 절대 경로로 수정
        return {
            'brand_trend': '/static/images/competitor/brand_trend.png',
            'category_trend': '/static/images/competitor/category_trend.png',
            'price_trend': '/static/images/competitor/price_trend.png',
            'total_items': len(df),
            'total_brands': df['brand'].nunique(),
            'total_categories': df['category'].nunique(),
            'avg_price': avg_price,
            'top_brands': top_brands
        }
    except Exception as e:
        logger.error(f"경쟁사 분석 생성 중 오류 발생: {e}")
        return None

def generate_competitor_analysis_by_date(file_path, start_date, end_date):
    """날짜 범위로 경쟁사 분석 데이터 생성"""
    try:
        # 데이터 로드
        df = load_competitor_data(file_path)
        if df is None or df.empty:
            logger.warning("로드된 데이터가 없습니다.")
            return None
        
        # 날짜 범위 필터링
        df = filter_by_date_range(df, start_date, end_date)
        if df is None or df.empty:
            logger.warning(f"{start_date}부터 {end_date}까지 데이터가 없습니다.")
            return None
        
        # 차트 저장 디렉토리 생성
        chart_dir = os.path.join('static', 'images', 'competitor')
        os.makedirs(chart_dir, exist_ok=True)
        
        # 차트 생성
        try:
            create_brand_trend_chart(df, os.path.join(chart_dir, 'brand_trend.png'))
            create_category_trend_chart(df, os.path.join(chart_dir, 'category_trend.png'))
            create_price_trend_chart(df, os.path.join(chart_dir, 'price_trend.png'))
        except Exception as e:
            logger.error(f"차트 생성 중 오류: {e}")
        
        # 분석 결과 계산
        try:
            avg_price = df['price'].mean()
            if pd.isna(avg_price):
                avg_price = 0
                logger.warning("평균 가격 계산 결과가 NaN입니다.")
        except Exception as e:
            logger.error(f"평균 가격 계산 중 오류 발생: {e}")
            avg_price = 0
            
        # 브랜드 통계 계산
        try:
            top_brands = df.groupby('brand').size().sort_values(ascending=False).head(10).to_dict()
            if not top_brands:
                logger.warning("브랜드 통계가 없습니다.")
        except Exception as e:
            logger.error(f"브랜드 통계 계산 중 오류 발생: {e}")
            top_brands = {}
            
        # 분석 결과 반환 - 절대 경로로 수정
        return {
            'brand_trend': '/static/images/competitor/brand_trend.png',
            'category_trend': '/static/images/competitor/category_trend.png',
            'price_trend': '/static/images/competitor/price_trend.png',
            'total_items': len(df),
            'total_brands': df['brand'].nunique(),
            'total_categories': df['category'].nunique(),
            'avg_price': avg_price,
            'top_brands': top_brands
        }
    except Exception as e:
        logger.error(f"날짜 범위 경쟁사 분석 생성 중 오류 발생: {e}")
        return None 