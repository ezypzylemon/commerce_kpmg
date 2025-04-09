# core/musinsa_data_loader.py
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from .db_connector import DBConnector
from .config import PERIOD_DAYS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MusinsaDataLoader:
    """무신사 데이터 로드 및 처리를 담당하는 클래스"""
    
    def __init__(self):
        self.data = None
        self.last_update = None
        self.last_period = None
        self.cache_enabled = True
        self.cache_timeout = 3600  # 캐시 유효 시간 (초)
    
    def load_data_by_period(self, period='7일'):
        """기간별 무신사 데이터 로드"""
        try:
            # 캐시된 데이터 확인
            if self.cache_enabled and self.data is not None and self.last_period == period:
                # 마지막 업데이트 후 cache_timeout 이내인 경우 캐시된 데이터 반환
                if self.last_update and (datetime.now() - self.last_update).total_seconds() < self.cache_timeout:
                    logger.info(f"캐시된 무신사 데이터 사용 (기간: {period})")
                    return self.data
            
            # 데이터베이스에서 데이터 로드
            days = PERIOD_DAYS.get(period, 7)
            if not days:
                logger.warning(f"지원하지 않는 기간: {period}, 기본값 7일로 설정")
                days = 7
                
            start_date = datetime.now() - timedelta(days=days)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            logger.info(f"무신사 데이터 로드 시작 (기간: {period}, 시작일: {start_date_str})")
            
            # DBConnector를 통해 데이터 가져오기
            data = DBConnector.get_musinsa_data(start_date=start_date_str)
            
            if data is None or data.empty:
                logger.warning(f"{period} 기간 동안 무신사 데이터가 없습니다.")
                # 기본 데이터 생성 및 반환
                return self.get_default_data()
            
            # 데이터 전처리
            self._preprocess_data(data)
            
            # 캐시 업데이트
            self.data = data
            self.last_update = datetime.now()
            self.last_period = period
            
            logger.info(f"무신사 데이터 {len(data)}개 로드 완료 (기간: {period})")
            return self.data
        
        except Exception as e:
            logger.error(f"무신사 데이터 로드 중 오류 발생: {e}")
            # 오류 발생 시 기본 데이터 반환
            return self.get_default_data()
    
    def load_data_by_date_range(self, start_date, end_date):
        """날짜 범위로 무신사 데이터 로드"""
        try:
            # 날짜 형식 확인 및 변환
            try:
                start_date_obj = pd.to_datetime(start_date)
                end_date_obj = pd.to_datetime(end_date)
                
                # 날짜 문자열 형식으로 변환
                start_date_str = start_date_obj.strftime('%Y-%m-%d')
                end_date_str = end_date_obj.strftime('%Y-%m-%d')
                
                logger.info(f"무신사 데이터 로드 시작 (기간: {start_date_str} ~ {end_date_str})")
            except Exception as e:
                logger.error(f"날짜 형식 변환 오류: {e}")
                return self.get_default_data()
            
            # DBConnector를 통해 데이터 가져오기
            data = DBConnector.get_musinsa_data(
                start_date=start_date_str, 
                end_date=end_date_str
            )
            
            if data is None or data.empty:
                logger.warning(f"{start_date_str}부터 {end_date_str}까지 무신사 데이터가 없습니다.")
                # 기본 데이터 생성 및 반환
                return self.get_default_data()
            
            # 데이터 전처리
            self._preprocess_data(data)
            
            logger.info(f"무신사 데이터 {len(data)}개 로드 완료 (기간: {start_date_str} ~ {end_date_str})")
            return data
        
        except Exception as e:
            logger.error(f"무신사 데이터 로드 중 오류 발생: {e}")
            # 오류 발생 시 기본 데이터 반환
            return self.get_default_data()
    
    def _preprocess_data(self, data):
        """데이터 전처리"""
        try:
            # 컬럼명 확인 및 표준화
            if data is None or data.empty:
                return data
            
            # 날짜 형식 변환
            if 'upload_date' in data.columns:
                data['upload_date'] = pd.to_datetime(data['upload_date'])
                if 'date' not in data.columns:
                    data['date'] = data['upload_date']
            
            # 가격 데이터 정제
            if 'price' in data.columns:
                try:
                    data['price'] = data['price'].apply(lambda x: 
                        float(str(x).replace(',', '').replace('원', '').strip()) 
                        if isinstance(x, str) 
                        else float(x) if not pd.isna(x) else 0.0
                    )
                except Exception as e:
                    logger.warning(f"가격 데이터 변환 중 오류 발생: {e}")
                    data['price'] = data['price'].fillna(0)
            
            # 필수 컬럼 확인 및 추가
            required_columns = ['brand', 'category', 'price', 'date']
            for col in required_columns:
                if col not in data.columns:
                    if col == 'date' and 'upload_date' in data.columns:
                        data['date'] = data['upload_date']
                    else:
                        data[col] = None
            
            return data
            
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류 발생: {e}")
            return data
    
    def get_default_data(self):
        """기본 데이터 생성"""
        try:
            # 예시 브랜드 및 카테고리
            brands = ['A브랜드', 'B브랜드', 'C브랜드', 'D브랜드', 'E브랜드']
            categories = ['상의', '하의', '아우터', '신발', '액세서리']
            
            # 현재 날짜 기준 최근 10일의 날짜 생성
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(10)]
            
            # 기본 데이터 생성
            data = []
            for i in range(50):  # 50개의 더미 데이터 생성
                data.append({
                    'brand': np.random.choice(brands),
                    'category': np.random.choice(categories),
                    'price': np.random.randint(10000, 100000),
                    'date': pd.to_datetime(np.random.choice(dates)),
                    'item_name': f'샘플 상품 {i+1}',
                    'upload_date': pd.to_datetime(np.random.choice(dates))
                })
            
            df = pd.DataFrame(data)
            logger.info(f"기본 무신사 데이터 {len(df)}개 생성")
            return df
            
        except Exception as e:
            logger.error(f"기본 데이터 생성 중 오류 발생: {e}")
            # 빈 데이터프레임 반환
            return pd.DataFrame(columns=['brand', 'category', 'price', 'date', 'item_name', 'upload_date'])
    
    def generate_visualizations(self, data=None):
        """무신사 데이터 시각화"""
        try:
            if data is None:
                data = self.data
            
            if data is None or data.empty:
                logger.warning("시각화를 위한 데이터가 없습니다.")
                return None
            
            # 시각화 결과 저장
            visualizations = {}
            
            # 여기에 시각화 로직 추가 가능 (예: 브랜드별 분포, 가격대별 분포 등)
            
            return visualizations
        except Exception as e:
            logger.error(f"시각화 생성 중 오류 발생: {e}")
            return None
    
    def get_top_brands(self, data=None, limit=10):
        """상위 브랜드 가져오기"""
        try:
            if data is None:
                data = self.data
            
            if data is None or data.empty:
                logger.warning("상위 브랜드 분석을 위한 데이터가 없습니다.")
                return {}
            
            if 'brand' not in data.columns:
                logger.warning("브랜드 정보가 없습니다.")
                return {}
            
            return data['brand'].value_counts().head(limit).to_dict()
        except Exception as e:
            logger.error(f"상위 브랜드 분석 중 오류 발생: {e}")
            return {} 