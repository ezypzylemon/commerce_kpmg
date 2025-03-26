# preprocessor.py
import pandas as pd
import numpy as np
import re

class DataPreprocessor:
    def __init__(self, csv_path):
        """데이터 전처리기 초기화"""
        self.csv_path = csv_path
        self.data = None
        
    def load_data(self):
        """CSV 파일 로드"""
        try:
            self.data = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            print(f"데이터 로드 완료: {len(self.data)}개 행")
            return True
        except Exception as e:
            print(f"데이터 로드 중 오류: {e}")
            return False
    
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
    
    def process(self):
        """전체 전처리 과정 수행"""
        if self.data is None:
            if not self.load_data():
                return None
        
        # 가격 숫자로 변환
        self.data['price_numeric'] = self.data['price'].apply(self.extract_price)
        
        # 상품명에서 키워드 추출
        self.data['keywords'] = self.data['name'].apply(self.extract_keywords)
        
        # 결측치 처리
        for col in ['rating', 'review_count']:
            if col in self.data.columns:
                self.data[col] = self.data[col].fillna(0)
        
        # 가격대 범주화
        price_ranges = [0, 10000, 30000, 50000, 100000, 200000, 500000, float('inf')]
        price_labels = ['~1만원', '1~3만원', '3~5만원', '5~10만원', '10~20만원', '20~50만원', '50만원~']
        self.data['price_range'] = pd.cut(self.data['price_numeric'], bins=price_ranges, labels=price_labels, right=False)
        
        print("데이터 전처리 완료")
        return self.data