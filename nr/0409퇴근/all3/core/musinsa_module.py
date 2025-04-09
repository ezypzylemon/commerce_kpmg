# core/musinsa_module.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime, timedelta
import logging
import re
from collections import Counter
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
import json

logger = logging.getLogger(__name__)

class MusinsaVisualizer:
    """무신사 데이터 시각화를 위한 클래스"""
    
    def __init__(self, data_dir='data', output_dir='static/images/competitor'):
        self.data_dir = data_dir
        self.output_dir = output_dir
        # 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        # 무신사 색상 테마 설정
        self.colors = {
            'primary': '#0078FF',  # 무신사 파란색
            'secondary': '#FF0000',  # 무신사 빨간색
            'accent': '#FFD700',  # 금색 (강조)
            'male': '#4A90E2',  # 남성 색상
            'female': '#FF6B6B',  # 여성 색상
            'neutral': '#555555',  # 중성 색상
            'background': '#F5F5F5'  # 배경 색상
        }
        
        # 플롯 스타일 설정
        plt.style.use('ggplot')
        plt.rcParams['font.family'] = 'AppleGothic'  # 한글 폰트
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

    def extract_price(self, price_str):
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

    def extract_keywords(self, name):
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
    
    def load_data(self, file_path=None, period='7일'):
        """데이터 로드 및 전처리 함수"""
        try:
            if file_path is None:
                file_path = os.path.join(self.data_dir, 'musinsa_data.csv')
                
            logger.info(f"데이터 로드 시도: {file_path}")
            logger.info(f"현재 작업 디렉토리: {os.getcwd()}")
            logger.info(f"데이터 디렉토리 내용: {os.listdir(self.data_dir)}")
                
            if not os.path.exists(file_path):
                logger.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
                return None
                
            # 데이터 로드
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 날짜 컬럼 확인 및 처리
            date_columns = ['date', 'crawled_at', 'upload_date', 'register_date']
            primary_date_column = None
            
            # 사용 가능한 날짜 컬럼 찾기
            for col in date_columns:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        if primary_date_column is None:
                            primary_date_column = col
                            logger.info(f"기본 날짜 컬럼으로 {col} 사용")
                    except Exception as e:
                        logger.warning(f"날짜 컬럼 {col} 변환 중 오류: {e}")
            
            # 날짜 컬럼이 없는 경우 현재 날짜 기준 임의 데이터 생성
            if primary_date_column is None:
                logger.warning("유효한 날짜 컬럼을 찾을 수 없어 현재 날짜 사용")
                df['crawled_at'] = pd.to_datetime('today')
                primary_date_column = 'crawled_at'
            
            # crawled_at 컬럼이 없는 경우 기본 날짜 컬럼으로부터 복제
            if 'crawled_at' not in df.columns:
                logger.info(f"crawled_at 컬럼 생성 ({primary_date_column} 복제)")
                df['crawled_at'] = df[primary_date_column]
            
            # 가격 숫자로 변환
            df['price_numeric'] = df['price'].apply(self.extract_price)
            
            # 상품명에서 키워드 추출
            df['keywords'] = df['name'].apply(self.extract_keywords)
            
            # 결측치 처리
            for col in ['rating', 'review_count']:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
            
            # 가격대 범주화
            price_ranges = [0, 10000, 30000, 50000, 100000, 200000, 500000, float('inf')]
            price_labels = ['~1만원', '1~3만원', '3~5만원', '5~10만원', '10~20만원', '20~50만원', '50만원~']
            df['price_range'] = pd.cut(df['price_numeric'], bins=price_ranges, labels=price_labels, right=False)
            
            # 기간 필터링
            if period != 'all' and 'crawled_at' in df.columns:
                end_date = datetime.now()
                
                if period == '7일' or period == '1주일':
                    start_date = end_date - timedelta(days=7)
                elif period == '2주':
                    start_date = end_date - timedelta(days=14)
                elif period == '1개월':
                    start_date = end_date - timedelta(days=30)
                elif period == '3개월':
                    start_date = end_date - timedelta(days=90)
                elif period == '6개월':
                    start_date = end_date - timedelta(days=180)
                elif period == '1년':
                    start_date = end_date - timedelta(days=365)
                else:
                    logger.warning(f"지원하지 않는 기간: {period}, 전체 데이터 사용")
                    return df
                
                # 날짜 필터링
                try:
                    df = df[(df['crawled_at'] >= start_date) & (df['crawled_at'] <= end_date)]
                    logger.info(f"날짜 필터링 적용: {start_date} ~ {end_date}, 결과 행 수: {len(df)}")
                except Exception as e:
                    logger.warning(f"날짜 필터링 중 오류: {e}")
            
            # 데이터 검증
            if df.empty:
                logger.warning(f"필터링 후 데이터가 없습니다. (기간: {period})")
                return pd.DataFrame({'crawled_at': [pd.to_datetime('today')], 
                                    'category': ['샘플'], 
                                    'price': [0]})
            
            logger.info(f"데이터 로드 완료: {len(df)}행, {len(df.columns)}열")
            return df
        
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {e}", exc_info=True)
            return None
    
    def get_popular_brands(self, data, top_n=20):
        """인기 브랜드 TOP N 추출 with 시각화"""
        try:
            if 'brand' not in data.columns:
                logger.warning("브랜드 컬럼을 찾을 수 없습니다.")
                return []
            
            # 브랜드 카운트 계산
            brand_counts = data['brand'].value_counts()
            
            # 상위 N개 브랜드 추출
            top_brands = brand_counts.head(top_n)
            
            # 시각화용 데이터 생성
            brand_ranking = []
            max_count = top_brands.max()
            
            for brand, count in top_brands.items():
                # 상대적 크기 계산 (최대값 대비)
                relative_size = int((count / max_count) * 10) + 1
                
                brand_ranking.append({
                    'name': brand,
                    'count': int(count),
                    'size': relative_size  # 1-11 사이의 크기
                })
            
            return brand_ranking
        except Exception as e:
            logger.error(f"브랜드 랭킹 추출 중 오류: {e}", exc_info=True)
            return []
    
    def get_top_items(self, data, gender=None, top_n=5):
        """성별 인기 아이템 TOP N 추출"""
        try:
            if 'name' not in data.columns:
                logger.warning("아이템 이름 컬럼을 찾을 수 없습니다.")
                return []
            
            if gender and 'gender' in data.columns:
                filtered_data = data[data['gender'] == gender]
            else:
                filtered_data = data
            
            item_counts = filtered_data['name'].value_counts().reset_index()
            item_counts.columns = ['name', 'count']
            
            # 상위 N개만 반환
            return item_counts.head(top_n).to_dict('records')
        except Exception as e:
            logger.error(f"인기 아이템 추출 중 오류 발생: {e}", exc_info=True)
            return []
    
    def generate_item_trend_chart(self, data, period):
        """아이템별 언급량 추세 차트 생성"""
        try:
            # 저장 경로 설정
            filename = f"item_trend_{period.replace(' ', '').replace('~', '_')}.png"
            save_path = os.path.join(self.output_dir, filename)
            
            # 날짜 컬럼 확인
            date_col = None
            for col in ['date', 'upload_date', 'register_date']:
                if col in data.columns:
                    date_col = col
                    break
            
            if date_col is None or 'name' not in data.columns:
                logger.warning("날짜 또는 아이템 이름 컬럼을 찾을 수 없습니다.")
                return None
            
            # 상위 5개 아이템 추출
            top_items = data['name'].value_counts().head(5).index.tolist()
            
            # 날짜별 아이템 언급량 집계
            plt.figure(figsize=(10, 6))
            
            # 날짜 변환 확인
            try:
                data[date_col] = pd.to_datetime(data[date_col])
            except Exception as e:
                logger.warning(f"날짜 변환 중 오류: {e}")
                # 차트 저장
                plt.title(f'인기 아이템별 언급량 추세 ({period})', fontsize=14)
                plt.xlabel('날짜', fontsize=12)
                plt.ylabel('언급량', fontsize=12)
                plt.text(0.5, 0.5, "날짜 데이터 오류", ha='center', va='center', transform=plt.gca().transAxes)
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                return os.path.join('images/competitor', filename)
            
            # 각 아이템별 시계열 생성
            for i, item in enumerate(top_items):
                item_data = data[data['name'] == item]
                if len(item_data) > 0:
                    try:
                        daily_counts = item_data.groupby(item_data[date_col].dt.date).size()
                        plt.plot(daily_counts.index, daily_counts.values, marker='o', markersize=4, linewidth=2, label=item[:15]+'...' if len(item) > 15 else item)
                    except Exception as inner_e:
                        logger.warning(f"아이템 '{item}' 시계열 생성 중 오류: {inner_e}")
            
            plt.title(f'인기 아이템별 언급량 추세 ({period})', fontsize=14)
            plt.xlabel('날짜', fontsize=12)
            plt.ylabel('언급량', fontsize=12)
            plt.legend(loc='best')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 차트 저장
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # 저장 경로 반환 (상대 경로)
            return os.path.join('images/competitor', filename)
        
        except Exception as e:
            logger.error(f"아이템 트렌드 차트 생성 중 오류 발생: {e}", exc_info=True)
            return None
    
    def generate_category_timeseries_chart(self, data, period):
        """카테고리별 시계열 추이 차트 생성"""
        try:
            # 저장 경로 설정 - 파일명에 한글을 피하기 위해 수정
            period_code = period
            if period == '1개월':
                period_code = '1month'
            elif period == '3개월':
                period_code = '3months'
            elif period == '6개월':
                period_code = '6months'
            elif period == '1년':
                period_code = '1year'
            elif period == '7일':
                period_code = '7days'
            elif period == '2주':
                period_code = '2weeks'
            
            filename = f"category_timeseries_{period_code}.png"
            save_path = os.path.join(self.output_dir, filename)
            
            # 로깅 추가
            logger.info(f"카테고리 시계열 차트 파일 경로: {save_path}")
            
            # 날짜 컬럼 확인 부분 수정
            date_col = 'crawled_at'  # crawled_at 컬럼 직접 사용
            if date_col not in data.columns:
                logger.warning(f"필요한 날짜 컬럼({date_col})을 찾을 수 없습니다.")
                
                # 에러 메시지가 포함된 차트 생성
                plt.figure(figsize=(10, 6))
                plt.title(f'카테고리별 시계열 추이 ({period})', fontsize=14)
                plt.text(0.5, 0.5, f"필요한 날짜 컬럼({date_col})을 찾을 수 없습니다.", ha='center', va='center', transform=plt.gca().transAxes)
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                return os.path.join('images/competitor', filename)
            
            if 'category' not in data.columns:
                logger.warning("카테고리 컬럼을 찾을 수 없습니다.")
                
                # 에러 메시지가 포함된 차트 생성
                plt.figure(figsize=(10, 6))
                plt.title(f'카테고리별 시계열 추이 ({period})', fontsize=14)
                plt.text(0.5, 0.5, "카테고리 컬럼을 찾을 수 없습니다.", ha='center', va='center', transform=plt.gca().transAxes)
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                return os.path.join('images/competitor', filename)
            
            # 날짜 변환 확인
            try:
                data[date_col] = pd.to_datetime(data[date_col])
                logger.info(f"날짜 변환 성공: {date_col}")
            except Exception as e:
                logger.warning(f"날짜 변환 중 오류: {e}")
                # 에러 차트 생성
                plt.figure(figsize=(10, 6))
                plt.title(f'카테고리별 시계열 추이 ({period})', fontsize=14)
                plt.text(0.5, 0.5, f"날짜 데이터 변환 오류: {str(e)}", ha='center', va='center', transform=plt.gca().transAxes)
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                return os.path.join('images/competitor', filename)
            
            # 날짜 범위 설정
            min_date = data[date_col].min().date()
            max_date = data[date_col].max().date()
            logger.info(f"데이터 날짜 범위: {min_date} ~ {max_date}")
            
            # 시각화 - 상단 플롯: 카테고리별 시계열
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
            
            # 카테고리별 시계열 데이터 생성
            try:
                # 상위 5개 카테고리 추출
                top_categories = data['category'].value_counts().head(5).index.tolist()
                logger.info(f"상위 카테고리: {top_categories}")
                
                # 날짜별 데이터 집계를 위해 날짜만 추출
                data['date_only'] = data[date_col].dt.date
                
                # 각 카테고리별 시계열
                for category in top_categories:
                    category_data = data[data['category'] == category]
                    daily_counts = category_data.groupby('date_only').size()
                    
                    # 날짜가 하나밖에 없으면 선 그래프 대신 막대 그래프 사용
                    if len(daily_counts) <= 1:
                        logger.warning(f"카테고리 '{category}'의 날짜 데이터가 부족합니다. 날짜 수: {len(daily_counts)}")
                        # 단일 지점 플롯
                        ax1.bar([category], [daily_counts.values[0] if len(daily_counts) > 0 else 0], label=category)
                    else:
                        ax1.plot(daily_counts.index, daily_counts.values, marker='o', markersize=4, 
                                linewidth=2, label=category)
            except Exception as inner_e:
                logger.warning(f"카테고리 시계열 생성 중 오류: {inner_e}")
                ax1.text(0.5, 0.5, f"카테고리 시계열 생성 오류: {str(inner_e)}", 
                        ha='center', va='center', transform=ax1.transAxes)
            
            ax1.set_title(f'카테고리별 시계열 추이 ({period})', fontsize=14)
            ax1.set_xlabel('날짜', fontsize=12)
            ax1.set_ylabel('언급량', fontsize=12)
            ax1.legend(loc='best')
            ax1.grid(True, alpha=0.3)
            
            # 전월 대비 비중 증가 항목 계산 (하단 플롯)
            try:
                # 현재 날짜를 기준으로 당월/전월 설정
                today = datetime.now().date()
                current_month_start = today.replace(day=1)
                prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
                
                logger.info(f"당월 시작일: {current_month_start}, 전월 시작일: {prev_month_start}")
                
                # 당월/전월 데이터 필터링
                current_month_data = data[data[date_col].dt.date >= current_month_start]
                prev_month_data = data[(data[date_col].dt.date >= prev_month_start) & 
                                      (data[date_col].dt.date < current_month_start)]
                
                logger.info(f"당월 데이터 크기: {len(current_month_data)}, 전월 데이터 크기: {len(prev_month_data)}")
                
                # 데이터가 충분한 경우에만 처리
                if len(current_month_data) > 0 and len(prev_month_data) > 0:
                    # 카테고리별 건수 집계
                    current_counts = current_month_data['category'].value_counts()
                    prev_counts = prev_month_data['category'].value_counts()
                    
                    # 전월 대비 증가율 계산
                    all_categories = set(current_counts.index) | set(prev_counts.index)
                    growth_rates = []
                    
                    for category in all_categories:
                        curr = current_counts.get(category, 0)
                        prev = prev_counts.get(category, 0)
                        
                        if prev > 0:
                            growth_rate = (curr - prev) / prev * 100
                        else:
                            growth_rate = 100 if curr > 0 else 0
                        
                        growth_rates.append((category, growth_rate, curr, prev))
                    
                    # 증가율 기준 정렬
                    growth_rates.sort(key=lambda x: x[1], reverse=True)
                    
                    # 상위 5개 추출
                    top_growth = growth_rates[:5]
                    
                    # 바 차트로 표시
                    categories = [item[0] for item in top_growth]
                    rates = [item[1] for item in top_growth]
                    
                    # 증가율에 따른 색상 설정
                    colors = ['green' if rate > 0 else 'red' for rate in rates]
                    
                    ax2.bar(categories, rates, color=colors)
                    ax2.set_title('전월 대비 비중 증가 항목 TOP 5', fontsize=14)
                    ax2.set_ylabel('증가율 (%)', fontsize=12)
                    ax2.grid(True, axis='y', alpha=0.3)
                    
                    # 증가율 값 표시
                    for i, rate in enumerate(rates):
                        ax2.text(i, rate + (5 if rate > 0 else -15), f'{rate:.1f}%', 
                                ha='center', va='center', fontsize=10)
                else:
                    ax2.text(0.5, 0.5, "당월 또는 전월 데이터가 부족합니다", 
                            ha='center', va='center', transform=ax2.transAxes)
            except Exception as growth_error:
                logger.warning(f"증가율 차트 생성 중 오류: {growth_error}")
                ax2.text(0.5, 0.5, f"증가율 데이터 계산 오류: {str(growth_error)}", 
                        ha='center', va='center', transform=ax2.transAxes)
            
            plt.tight_layout()
            
            # 차트 저장
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # 저장 경로 반환 (상대 경로)
            return os.path.join('images/competitor', filename)
        
        except Exception as e:
            logger.error(f"카테고리 시계열 차트 생성 중 오류 발생: {e}", exc_info=True)
            return None
    
    def generate_price_heatmap(self, data, period):
        """카테고리별 가격대 분포 히트맵 생성"""
        try:
            # 저장 경로 설정
            filename = f"price_heatmap_{period.replace(' ', '').replace('~', '_')}.png"
            save_path = os.path.join(self.output_dir, filename)
            
            # 필요한 컬럼 확인
            if 'category' not in data.columns or 'price_range' not in data.columns:
                logger.warning("카테고리 또는 가격대 컬럼을 찾을 수 없습니다.")
                
                # 에러 메시지가 포함된 차트 생성
                plt.figure(figsize=(12, 8))
                plt.title('카테고리별 가격대 분포 히트맵', fontsize=14)
                plt.text(0.5, 0.5, "카테고리 또는 가격대 데이터 없음", ha='center', va='center', transform=plt.gca().transAxes)
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                return os.path.join('images/competitor', filename)
            
            # 상위 카테고리 추출
            top_categories = data['category'].value_counts().head(8).index.tolist()
            
            # 가격대 순서 정의
            price_order = ['~1만원', '1~3만원', '3~5만원', '5~10만원', '10~20만원', '20~50만원', '50만원~']
            
            # 크로스탭 생성
            try:
                # 카테고리와 가격대로 교차표 생성
                ct = pd.crosstab(
                    data['category'], 
                    data['price_range'],
                    normalize='index'
                )
                
                # 선택한 카테고리 및 가격대 순서로 필터링
                ct = ct.loc[top_categories]
                ct = ct.reindex(columns=price_order)
                
                # NaN 값 0으로 대체
                ct = ct.fillna(0)
                
                # 히트맵 생성
                plt.figure(figsize=(12, 8))
                
                # 커스텀 컬러맵 생성
                colors = ["#f7fbff", "#abd9e9", "#74add1", "#4575b4", "#313695"]
                cmap = LinearSegmentedColormap.from_list("custom_blues", colors)
                
                sns.heatmap(ct, annot=True, fmt='.1%', cmap=cmap, linewidths=0.5, cbar_kws={'label': '비율'})
                
                plt.title('카테고리별 가격대 분포 히트맵', fontsize=16)
                plt.ylabel('카테고리', fontsize=12)
                plt.xlabel('가격대', fontsize=12)
                
                plt.tight_layout()
                
            except Exception as heatmap_error:
                logger.warning(f"히트맵 생성 중 오류: {heatmap_error}")
                plt.figure(figsize=(12, 8))
                plt.title('카테고리별 가격대 분포 히트맵', fontsize=14)
                plt.text(0.5, 0.5, f"히트맵 데이터 생성 오류: {str(heatmap_error)}", 
                        ha='center', va='center', transform=plt.gca().transAxes)
            
            # 차트 저장
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # 저장 경로 반환 (상대 경로)
            return os.path.join('images/competitor', filename)
        
        except Exception as e:
            logger.error(f"가격 히트맵 생성 중 오류 발생: {e}", exc_info=True)
            return None
        
    def generate_category_media_heatmap_data(self, data):
        """카테고리와 미디어 유형에 따른 히트맵 데이터 생성"""
        try:
            # 필요한 컬럼이 있는지 확인
            if 'category' not in data.columns or 'media' not in data.columns:
                return None
            
            # 상위 카테고리 및 미디어 유형 추출
            top_categories = data['category'].value_counts().head(5).index.tolist()
            media_types = data['media'].value_counts().head(5).index.tolist()
            
            # 카테고리와 미디어 유형으로 교차표 생성
            heatmap_data = []
            
            # 행 데이터 구성 (카테고리별)
            for category in top_categories:
                row_data = []
                category_data = data[data['category'] == category]
                
                for media in media_types:
                    count = len(category_data[category_data['media'] == media])
                    
                    # 히트 레벨 계산 (1: 낮음, 2: 중간, 3: 높음)
                    if count == 0:
                        heat_level = 0
                    elif count < 1000:
                        heat_level = 1
                    elif count < 5000:
                        heat_level = 2
                    else:
                        heat_level = 3
                    
                    row_data.append({
                        'count': count,
                        'heat_level': heat_level
                    })
                
                heatmap_data.append({
                    'category': category,
                    'media_data': row_data
                })
            
            # 미디어 타입 목록과 함께 반환
            return {
                'categories': top_categories,
                'media_types': media_types,
                'heatmap_data': heatmap_data
            }
            
        except Exception as e:
            logger.error(f"히트맵 데이터 생성 중 오류 발생: {e}", exc_info=True)
            return None
            
    def generate_category_ratio_charts(self, data, period):
        """카테고리 비율 및 증감률 차트 생성"""
        try:
            # 저장 경로 설정
            ratio_filename = f"category_ratio_{period.replace(' ', '').replace('~', '_')}.png"
            delta_filename = f"category_delta_{period.replace(' ', '').replace('~', '_')}.png"
            ratio_path = os.path.join(self.output_dir, ratio_filename)
            delta_path = os.path.join(self.output_dir, delta_filename)
            
            # 목업 데이터 사용 (실제로는 data에서 추출)
            mock_data_path = os.path.join(self.data_dir, 'mock_category_ratio.csv')
            if os.path.exists(mock_data_path):
                df = pd.read_csv(mock_data_path)
                categories = df["category"]
                ratios = df["ratio"]
                delta_ratios = df["delta_ratio"]
            else:
                # 목업 데이터가 없는 경우 하드코딩된 데이터 사용
                categories = ['드레스', '캐주얼셔츠', '팬츠', '청바지', '니트웨어', '탑', '재킷', '블라우스', '스커트']
                ratios = [19.0, 14.1, 13.6, 10.2, 8.5, 7.3, 6.9, 5.5, 4.1]
                delta_ratios = [52.5, 20.8, 30.9, 9.8, -13.6, -17.1, -9.6, -7.7, -10.5]
            
            # 1. 전체 비중 차트 생성
            plt.figure(figsize=(16, 4), facecolor='#f2f2f2') # 이미지 크기 조정 (a,b) a=너비, b=높이
            ax = plt.axes()
            ax.set_facecolor('#f2f2f2')
            plt.plot(categories, ratios, 'o-', color='#4A90E2', markersize=8, linewidth=2)
            for i, value in enumerate(ratios):
                plt.text(i, value + 1, f"{value}%", ha='center', va='bottom', fontsize=10, fontweight='bold')
            plt.title('전체 비중', fontsize=16, pad=20)
            plt.ylim(0, max(ratios) * 1.2)
            plt.ylabel('%', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.xticks(range(len(categories)), categories, rotation=0)
            for spine in ax.spines.values():
                spine.set_visible(False)
            plt.tight_layout()
            plt.savefig(ratio_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # 2. 전월대비 비중증가율 차트 생성
            plt.figure(figsize=(16, 4), facecolor='#f2f2f2') # 이미지 크기 조정 (a,b) a=너비, b=높이
            ax = plt.axes()
            ax.set_facecolor('#f2f2f2')
            colors = ['#4A90E2' if x >= 0 else '#FF5A5A' for x in delta_ratios]
            bars = plt.bar(categories, delta_ratios, color=colors)
            for i, value in enumerate(delta_ratios):
                offset = 1.5 if value >= 0 else -3
                plt.text(i, value + offset, f"{value:+.1f}%", ha='center', va='center', fontsize=10)
            plt.title('전월대비 비중증가율', fontsize=16, pad=20)
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.ylabel('%', fontsize=10)
            plt.grid(axis='y', alpha=0.3)
            for spine in ax.spines.values():
                spine.set_visible(False)
            plt.tight_layout()
            plt.savefig(delta_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # 저장 경로 반환 (상대 경로)
            return {
                'ratio_chart': os.path.join('images/competitor', ratio_filename),
                'delta_chart': os.path.join('images/competitor', delta_filename)
            }
        
        except Exception as e:
            logger.error(f"카테고리 비율 차트 생성 중 오류 발생: {e}", exc_info=True)
            return None

    def generate_price_range_chart(self, data, period):
        """브랜드별 가격 범위 차트 생성"""
        try:
            # 저장 경로 설정
            filename = f"price_range_{period.replace(' ', '').replace('~', '_')}.png"
            save_path = os.path.join(self.output_dir, filename)
            
            # 가격 데이터 전처리
            if 'price' in data.columns:
                try:
                    # 가격 문자열에서 숫자만 추출
                    data['price_numeric'] = data['price'].astype(str).str.replace('원', '').str.replace(',', '').str.strip()
                    data['price_numeric'] = pd.to_numeric(data['price_numeric'], errors='coerce')
                    
                    # 결측치 제거
                    data_clean = data.dropna(subset=['price_numeric', 'brand', 'category'])
                except Exception as e:
                    logger.warning(f"가격 데이터 전처리 중 오류: {e}")
                    data_clean = data.copy()
            else:
                logger.warning("가격 컬럼이 없습니다.")
                return None
            
            # 브랜드별 가격 범위 계산
            price_range_df = data_clean.groupby(['brand'])['price_numeric'].agg(['min', 'max']).reset_index()
            price_range_df.columns = ['브랜드', '최저가격', '최대가격']
            
            # 브랜드별 평균 가격 계산
            price_range_df['평균가격'] = (price_range_df['최저가격'] + price_range_df['최대가격']) / 2
            
            # 높은 가격순으로 정렬하고 상위 15개 브랜드 선택
            brand_summary = price_range_df.sort_values('평균가격', ascending=True).tail(15)
            
            # 그래프 생성
            try:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # 수평 막대 그래프 생성
                y_pos = np.arange(len(brand_summary))
                
                # 가격 범위 바 그리기
                ax.barh(y_pos, brand_summary['최대가격'] - brand_summary['최저가격'], 
                        left=brand_summary['최저가격'], height=0.6, color='gray', alpha=0.7)
                
                # 최저가격 점 표시
                ax.scatter(brand_summary['최저가격'], y_pos, color='blue', s=50, zorder=3)
                
                # 최대가격 점 표시
                ax.scatter(brand_summary['최대가격'], y_pos, color='red', s=50, zorder=3)
                
                # 가격 표시
                for i, (min_price, max_price) in enumerate(zip(brand_summary['최저가격'], brand_summary['최대가격'])):
                    price_gap = (brand_summary['최대가격'].max() - brand_summary['최저가격'].min()) * 0.03
                    ax.text(min_price - price_gap, i, f"{min_price:,.0f}원", ha='right', va='center', color='blue')
                    ax.text(max_price + price_gap, i, f"{max_price:,.0f}원", ha='left', va='center', color='red')
                
                # Y축 설정
                ax.set_yticks(y_pos)
                ax.set_yticklabels(brand_summary['브랜드'])
                
                # X축 설정
                ax.set_xlabel('가격 (원)')
                ax.grid(axis='x', linestyle='--', alpha=0.7)
                
                # 범례 추가
                ax.legend(['최저가격', '최대가격'], loc='upper right')
                
                # 제목 설정
                ax.set_title('브랜드별 가격 분포', fontsize=16, pad=20)
                
                plt.tight_layout()
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                return os.path.join('images/competitor', filename)
            except Exception as e:
                logger.error(f"가격 범위 차트 생성 중 오류: {e}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"가격 범위 차트 생성 중 오류 발생: {e}", exc_info=True)
            return None

    def render_musinsa(self, period='7일', start_date=None, end_date=None):
        try:
            data = None  # 초기화
            # 데이터 파일 경로
            data_path = os.path.join(self.data_dir, 'musinsa_data.csv')
            display_period = period
            
            # 데이터 파일 존재 여부 확인
            file_exists = os.path.exists(data_path)
            self.logger.info(f"무신사 데이터 파일 경로: {os.path.abspath(data_path)}, 존재 여부: {file_exists}")
            
            if file_exists:
                # 파일에서 데이터 로드
                data = pd.read_csv(data_path)
            else:
                # 데이터베이스에서 데이터 로드
                if period == 'custom' and start_date and end_date:
                    data = self.data_loader.load_data_by_date_range(start_date, end_date)
                else:
                    data = self.data_loader.load_data_by_period(period)
            
            if data is None or data.empty:
                self.logger.warning("데이터가 없습니다.")
                return render_template('musinsa.html', error="데이터가 없습니다.")
            
            # 이후 로직...
            
        except Exception as e:
            self.logger.error(f"데이터 분석 중 오류 발생: {e}", exc_info=True)
            return render_template('musinsa.html', error=f"데이터 분석 중 오류가 발생했습니다: {str(e)}")