import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stopwords 정의
STOPWORDS = set([
    '것', '수', '등', '더', '위해', '또한', '있는', '하는', '에서', '으로',
    '그리고', '이번', '한편', '있다', '했다', '대한', '가장', '이런',
    '한다', '한다면', '바', '때', '다양한', '통해', '기자', '최근',
    '우리', '많은', '중', '때문', '대한', '모든', '하지만', '중인',
    '이후', '그녀', '그는', '에서의', '있는지', '중심', '된다', '있으며',
    '된다', '된다면', '위한','스타일링', '스타일', '아이템', '패션', '브랜드',
    '컬렉션', '코디', '컬러', '트렌드', '디자이너', '쇼핑', '코디', '코디네이터', '코디법', '코디추천', '코디아이템', '박소현', '황기애', '정혜미', '진정',
    '무드', '느낌', '분위기', '매력', '활용', '완성', '연출', '선택', '조합', '포인트', '다양', '모습', '자신', '사람', '마음',
    '제품', '디자인', '에디터', '정윤', '보그', '년대', '등장' '시즌', '스타일링', '스타일', '아이템', '패션', '브랜드', '장진영', '윤다희', '강미', '박은아', 
])

class Analyzer:
    """데이터 분석 기능을 제공하는 클래스"""
    
    @staticmethod
    def remove_stopwords(tokens):
        """불용어 제거"""
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    
    @staticmethod
    def get_top_keywords(df, n=20):
        """
        상위 키워드 추출
        
        Args:
            df (DataFrame): 토큰화된 데이터
            n (int): 반환할 키워드 수
            
        Returns:
            DataFrame: 키워드 및 빈도수
        """
        if df.empty:
            return pd.DataFrame(columns=['token', 'count'])
        
        # 모든 토큰 추출 및 불용어 제거
        all_tokens = []
        for tokens in df['tokens']:
            all_tokens.extend(Analyzer.remove_stopwords(tokens))
        
        # 빈도수 계산
        token_counts = pd.Series(all_tokens).value_counts().head(n).reset_index()
        token_counts.columns = ['token', 'count']
        
        return token_counts
    
    @staticmethod
    def analyze_tfidf(df, article_idx=0, n=20):
        """
        TF-IDF 분석
        
        Args:
            df (DataFrame): 토큰화된 데이터
            article_idx (int): 분석할 기사 인덱스
            n (int): 반환할 키워드 수
            
        Returns:
            list: (키워드, 점수) 튜플 목록
        """
        if df.empty:
            return []
        
        docs = df['tokens'].apply(lambda x: ' '.join(Analyzer.remove_stopwords(x))).tolist()
        
        if not docs or len(docs) <= article_idx:
            return []
        
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(docs)
            feature_names = vectorizer.get_feature_names_out()
            
            scores = tfidf_matrix[article_idx].toarray()[0]
            top_n = scores.argsort()[-n:][::-1]
            
            top_keywords = [(feature_names[i], scores[i]) for i in top_n if scores[i] > 0]
            return top_keywords
        except Exception as e:
            logger.error(f"TF-IDF 분석 오류: {e}")
            return []
    
    @staticmethod
    def generate_network_data(df, max_edges=30):
        """
        키워드 네트워크 데이터 생성
        
        Args:
            df (DataFrame): 토큰화된 데이터
            max_edges (int): 최대 엣지 수
            
        Returns:
            dict: 노드 및 엣지 데이터
        """
        if df.empty:
            return {'nodes': [], 'links': []}
        
        edge_counter = Counter()
        for tokens in df['tokens']:
            cleaned = Analyzer.remove_stopwords(tokens)
            unique_tokens = list(set(cleaned))
            if len(unique_tokens) >= 2:
                edge_counter.update(combinations(unique_tokens, 2))
        
        top_edges = edge_counter.most_common(max_edges)
        
        # 네트워크 그래프 데이터 형식으로 변환
        nodes = set()
        edges = []
        
        for (source, target), weight in top_edges:
            nodes.add(source)
            nodes.add(target)
            edges.append({
                'source': source,
                'target': target,
                'weight': weight
            })
        
        return {
            'nodes': [{'id': node, 'name': node} for node in nodes],
            'links': edges
        }
    
    # 키워드 유형별 사전 정의
    keyword_dict = {
        "아이템": ['드레스', '재킷', '팬츠', '스커트', '코트', '블라우스', '캐주얼상의', '점프수트', '니트웨어', '셔츠', '탑', '청바지', '수영복', '점퍼', '베스트', '패딩'],
        "컬러": ['블랙', '화이트', '베이지', '브라운', '그레이', '블루', '스카이블루', '네이비', '옐로우', '핑크', '레드', '카키', '라벤더', '그린', '퍼플', '민트', '오렌지', '와인', '멀티'],
        "소재": ['합성섬유', '면', '가죽', '시폰', '니트', '데님', '레이스', '시퀸/글리터', '캐시미어/울', '스웨이드', '벨벳', '스판덱스', '퍼', '트위드', '비닐/PVC', '메시', '린넨', '자카드', '저지', '코듀로이', '네오프렌', '플리스', '무스탕', '앙고라', '실크'],
        "프린트": ['무지', '플로럴', '스트라이프', '체크', '그래픽', '도트', '레터링', '페이즐리', '호피', '그라데이션', '타이다이', '카무플라쥬/카모플라쥬', '지그재그', '지브라', '해골', '멀티'],
        "스타일": ['컨트리', '웨딩', '프레피', '히피', '아웃도어', '밀리터리', '복고', '페미닌', '캐주얼', '마린', '에스닉', '오피스룩', '파티', '리조트', '펑크']
    }
    
    # 동의어/유사어 사전 정의
    keyword_aliases = {
        '시퀸/글리터': ['시퀸', '글리터'],
        '캐시미어/울': ['캐시미어', '울'],
        '비닐/PVC': ['비닐', 'pvc', 'PVC'],
        '카무플라쥬/카모플라쥬': ['카무플라쥬', '카모플라쥬']
    }
    
    @staticmethod
    def analyze_item_trends(df, period, keyword_type="아이템"):
        """
        아이템 증감률 분석
        
        Args:
            df (DataFrame): 토큰화된 데이터
            period (str): 기간 설정
            keyword_type (str): 키워드 유형
            
        Returns:
            dict: 분석 결과
        """
        if df.empty:
            return {
                'trend_df': pd.DataFrame(),
                'dates': {
                    'curr_start': None,
                    'curr_end': None,
                    'prev_start': None,
                    'prev_end': None
                }
            }
        
        # 현재 날짜
        today = datetime.now()
        
        # 기간 설정에 따른 날짜 범위 계산
        delta_map = {
            '1주일': 7,
            '2주일': 14,
            '1개월': 30,
            '3개월': 90,
            '6개월': 180,
            '1년': 365,
            '2년': 730,
            # 다른 기간 값도 처리할 수 있도록 추가
            '7일': 7,
            '2주': 14,
            '3주': 21,
            '1달': 30,
            '3달': 90
        }
        
        delta = delta_map.get(period, 30)  # 기본값 30일
        curr_end = today
        curr_start = today - timedelta(days=delta)
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - delta + timedelta(days=1)
        
        # 기간별 데이터 필터링
        df_before = df[
            (df['upload_date'] >= pd.to_datetime(prev_start)) &
            (df['upload_date'] <= pd.to_datetime(prev_end))
        ]
        df_current = df[
            (df['upload_date'] >= pd.to_datetime(curr_start)) &
            (df['upload_date'] <= pd.to_datetime(curr_end))
        ]
        
        # 분석할 키워드 목록
        keywords = Analyzer.keyword_dict.get(keyword_type, [])
        
        # 아이템 카운트 함수
        def count_items(df, keyword_list):
            if df.empty:
                return {k: 0 for k in keyword_list}
            
            all_tokens = [token for tokens in df['tokens'] for token in Analyzer.remove_stopwords(tokens)]
            counts = pd.Series(all_tokens).value_counts()
            
            result = {}
            for item in keyword_list:
                if item in Analyzer.keyword_aliases:
                    result[item] = sum(counts.get(alias, 0) for alias in Analyzer.keyword_aliases[item])
                else:
                    result[item] = counts.get(item, 0)
            
            return result
        
        counts_current = count_items(df_current, keywords)
        counts_before = count_items(df_before, keywords)
        
        # 결과 데이터프레임 생성
        trend_df = pd.DataFrame({
            'item': keywords,
            '현재 언급량': [counts_current[i] for i in keywords],
            '이전 언급량': [counts_before[i] for i in keywords]
        })
        
        # 증감률 계산 (0으로 나누는 오류 방지)
        trend_df['증감률(%)'] = ((trend_df['현재 언급량'] - trend_df['이전 언급량']) /
                             trend_df['이전 언급량'].replace(0, 1)) * 100
        
        return {
            'trend_df': trend_df,
            'dates': {
                'curr_start': curr_start,
                'curr_end': curr_end,
                'prev_start': prev_start,
                'prev_end': prev_end
            }
        }
    
    @staticmethod
    def analyze_magazine_comparison(df, magazines, date_range='전체'):
        """
        매거진별 비교 분석
        
        Args:
            df (DataFrame): 토큰화된 데이터
            magazines (list): 분석할 매거진 목록
            date_range (str): 분석 기간
            
        Returns:
            dict: 분석 결과
        """
        if df.empty or not magazines:
            return {
                'top_tokens_per_mag': {},
                'common_tokens': set(),
                'unique_tokens': {},
                'tfidf_keywords': {}
            }
        
        # 분석 기간 설정
        if date_range != '전체':
            today = datetime.now()
            days_map = {'1개월': 30, '3개월': 90, '6개월': 180, '1년': 365}
            delta = days_map.get(date_range, 30)
            
            start_date = today - timedelta(days=delta)
            df_mag = df[(df['upload_date'] >= start_date)]
        else:
            df_mag = df.copy()
        
        # 선택된 매거진으로 필터링
        df_mag = df_mag[df_mag['source'].isin(magazines)]
        
        if df_mag.empty:
            return {
                'top_tokens_per_mag': {},
                'common_tokens': set(),
                'unique_tokens': {},
                'tfidf_keywords': {}
            }
        
        # 상위 키워드 비교
        top_tokens_per_mag = {}
        for mag in magazines:
            mag_tokens = []
            mag_df = df_mag[df_mag['source'] == mag]
            
            if not mag_df.empty:
                for tokens in mag_df['tokens']:
                    mag_tokens.extend(Analyzer.remove_stopwords(tokens))
                
                top_tokens_per_mag[mag] = pd.Series(mag_tokens).value_counts().head(30)
            else:
                # 해당 매거진 데이터가 없는 경우 빈 시리즈 추가
                top_tokens_per_mag[mag] = pd.Series()
        
        # 공통 vs 고유 키워드 분석
        token_sets = {mag: set(tokens.index) for mag, tokens in top_tokens_per_mag.items() if not tokens.empty}
        
        if len(token_sets) > 1:
            common_tokens = set.intersection(*token_sets.values())
            unique_tokens = {mag: tokens - common_tokens for mag, tokens in token_sets.items()}
        else:
            common_tokens = set()
            unique_tokens = {mag: set(tokens.index) for mag, tokens in top_tokens_per_mag.items() if not tokens.empty}
        
        # TF-IDF 분석
        tfidf_keywords = {}
        
        if not df_mag.empty:
            # 매거진별 그룹화
            mag_groups = df_mag.groupby("source")['tokens']
            
            # 각 매거진별 모든 토큰 합치기
            mag_tokens = {}
            for mag, tokens_group in mag_groups:
                if mag in magazines:
                    all_tokens = []
                    for tokens in tokens_group:
                        all_tokens.extend(Analyzer.remove_stopwords(tokens))
                    mag_tokens[mag] = all_tokens
            
            # 각 매거진별 텍스트 생성
            docs = {}
            for mag, tokens in mag_tokens.items():
                docs[mag] = " ".join(tokens)
            
            # TF-IDF 분석 (2개 이상의 문서가 있을 때만)
            if len(docs) >= 2:
                try:
                    vectorizer = TfidfVectorizer()
                    doc_list = [docs[mag] for mag in magazines if mag in docs]
                    
                    if doc_list:
                        tfidf_matrix = vectorizer.fit_transform(doc_list)
                        feature_names = vectorizer.get_feature_names_out()
                        
                        for i, mag in enumerate([mag for mag in magazines if mag in docs]):
                            if i < tfidf_matrix.shape[0]:  # 인덱스 범위 검사
                                row = tfidf_matrix[i].toarray().flatten()
                                top_n = row.argsort()[-10:][::-1]
                                tfidf_keywords[mag] = [(feature_names[j], round(row[j], 4)) for j in top_n]
                except Exception as e:
                    logger.error(f"TF-IDF 분석 오류: {e}")
        
        return {
            'top_tokens_per_mag': top_tokens_per_mag,
            'common_tokens': common_tokens,
            'unique_tokens': unique_tokens,
            'tfidf_keywords': tfidf_keywords
        }
    
    @staticmethod
    def get_weekly_keyword_trends(df, keywords, period='3개월'):
        """
        주간 키워드 언급량 추세 분석
        
        Args:
            df (DataFrame): 토큰화된 데이터
            keywords (list): 분석할 키워드 목록
            period (str): 분석 기간
            
        Returns:
            DataFrame: 주간 언급량 데이터
        """
        if df.empty or not keywords:
            return pd.DataFrame()
        
        # 분석 기간 설정
        today = datetime.now()
        days_map = {
            '1주일': 7, '2주일': 14, '1개월': 30, '3개월': 90, '6개월': 180, '1년': 365,
            '7일': 7, '2주': 14, '3주': 21, '1달': 30, '3달': 90
        }
        delta = days_map.get(period, 90)  # 기본값 90일 (3개월)
        
        start_date = today - timedelta(days=delta)
        df_filtered = df[(df['upload_date'] >= start_date) & (df['upload_date'] <= today)]
        
        if df_filtered.empty:
            return pd.DataFrame()
        
        # 주간 데이터로 변환
        df_filtered['week'] = df_filtered['upload_date'].dt.to_period('W').apply(lambda r: r.start_time)
        
        # 주간 키워드 언급량 계산
        rows = []
        for week, group in df_filtered.groupby('week'):
            tokens = [token for tokens in group['tokens'] for token in Analyzer.remove_stopwords(tokens)]
            counts = pd.Series(tokens).value_counts()
            
            row = {'week': week}
            for kw in keywords:
                # 키워드에 별칭이 있는 경우 합산
                if kw in Analyzer.keyword_aliases:
                    row[kw] = sum(counts.get(alias, 0) for alias in Analyzer.keyword_aliases[kw])
                else:
                    row[kw] = counts.get(kw, 0)
            
            rows.append(row)
        
        # 주간 데이터 정렬
        result_df = pd.DataFrame(rows).sort_values('week')
        
        return result_df