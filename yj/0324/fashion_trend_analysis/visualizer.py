# visualizer.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from collections import Counter
from wordcloud import WordCloud
import matplotlib.font_manager as fm
import platform

class TrendVisualizer:
    def __init__(self, data, output_dir):
        """시각화 모듈 초기화"""
        self.data = data
        self.output_dir = output_dir
        
        # 출력 디렉토리 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 한글 폰트 설정
        self.font_path = self.get_korean_font()
        if self.font_path:
            font_name = fm.FontProperties(fname=self.font_path).get_name()
            plt.rcParams['font.family'] = font_name
            plt.rcParams['axes.unicode_minus'] = False
    
    def get_korean_font(self):
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
                    print("한글 폰트를 찾을 수 없습니다. 워드클라우드에 한글이 깨질 수 있습니다.")
                    font_path = None
        
        return font_path
    
    def generate_category_counts(self):
        """카테고리별 상품 수 시각화"""
        plt.figure(figsize=(12, 6))
        sns.countplot(data=self.data, y='category', order=self.data['category'].value_counts().index)
        plt.title('카테고리별 상품 수', fontsize=15)
        plt.xlabel('상품 수', fontsize=12)
        plt.ylabel('카테고리', fontsize=12)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'category_counts.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_category_prices(self):
        """카테고리별 평균 가격 시각화"""
        plt.figure(figsize=(12, 6))
        category_price = self.data.groupby('category')['price_numeric'].mean().sort_values(ascending=False)
        sns.barplot(x=category_price.values, y=category_price.index)
        plt.title('카테고리별 평균 가격', fontsize=15)
        plt.xlabel('평균 가격 (원)', fontsize=12)
        plt.ylabel('카테고리', fontsize=12)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'category_prices.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_top_brands(self, top_n=20):
        """인기 브랜드 TOP N 시각화"""
        plt.figure(figsize=(12, 8))
        top_brands = self.data['brand'].value_counts().head(top_n)
        sns.barplot(x=top_brands.values, y=top_brands.index)
        plt.title(f'인기 브랜드 TOP {top_n}', fontsize=15)
        plt.xlabel('상품 수', fontsize=12)
        plt.ylabel('브랜드', fontsize=12)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'top_brands.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_price_distribution(self):
        """가격대별 상품 수 분포 시각화"""
        plt.figure(figsize=(12, 6))
        price_range_counts = self.data['price_range'].value_counts().sort_index()
        sns.barplot(x=price_range_counts.index, y=price_range_counts.values)
        plt.title('가격대별 상품 수', fontsize=15)
        plt.xlabel('가격대', fontsize=12)
        plt.ylabel('상품 수', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'price_distribution.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_keyword_wordcloud(self):
        """워드클라우드 생성"""
        # 모든 키워드 추출
        all_keywords = []
        for keywords in self.data['keywords']:
            all_keywords.extend(keywords)
        
        # 키워드 빈도 계산
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(100)
        
        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path=self.font_path,
            width=800, height=400,
            background_color='white',
            max_words=100,
            colormap='viridis'
        )
        wordcloud.generate_from_frequencies(dict(top_keywords))
        
        plt.figure(figsize=(12, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('인기 키워드 워드클라우드', fontsize=15)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'keyword_wordcloud.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_top_keywords(self):
        """인기 키워드 TOP 20 막대 그래프"""
        # 모든 키워드 추출
        all_keywords = []
        for keywords in self.data['keywords']:
            all_keywords.extend(keywords)
        
        # 키워드 빈도 계산
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(20)
        keywords_df = pd.DataFrame(top_keywords, columns=['keyword', 'count'])
        
        plt.figure(figsize=(12, 8))
        sns.barplot(data=keywords_df, y='keyword', x='count', order=keywords_df.sort_values('count', ascending=False)['keyword'])
        plt.title('인기 키워드 TOP 20', fontsize=15)
        plt.xlabel('빈도', fontsize=12)
        plt.ylabel('키워드', fontsize=12)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'top_keywords.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_category_price_heatmap(self):
        """카테고리별 가격대 분포 히트맵"""
        # 크로스탭 생성
        price_category_crosstab = pd.crosstab(
            self.data['category'], 
            self.data['price_range'],
            normalize='index'
        )
        
        # 가격대 순서 정렬
        price_order = ['~1만원', '1~3만원', '3~5만원', '5~10만원', '10~20만원', '20~50만원', '50만원~']
        price_category_crosstab = price_category_crosstab.reindex(columns=[col for col in price_order if col in price_category_crosstab.columns])
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(price_category_crosstab, annot=True, cmap='Blues', fmt='.1%')
        plt.title('카테고리별 가격대 분포', fontsize=15)
        plt.xlabel('가격대', fontsize=12)
        plt.ylabel('카테고리', fontsize=12)
        plt.tight_layout()
        
        # 이미지 저장
        filepath = os.path.join(self.output_dir, 'category_price_heatmap.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_all_visualizations(self):
        """모든 시각화 생성"""
        result_files = {}
        
        # 카테고리 분석
        result_files['category_counts'] = self.generate_category_counts()
        result_files['category_prices'] = self.generate_category_prices()
        
        # 브랜드 분석
        result_files['top_brands'] = self.generate_top_brands()
        
        # 가격 분석
        result_files['price_distribution'] = self.generate_price_distribution()
        result_files['category_price_heatmap'] = self.generate_category_price_heatmap()
        
        # 키워드 분석
        result_files['keyword_wordcloud'] = self.generate_keyword_wordcloud()
        result_files['top_keywords'] = self.generate_top_keywords()
        
        return result_files