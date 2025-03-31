import mysql.connector
import pandas as pd
import os
import logging
from config import DB_CONFIG

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DBConnector:
    """데이터베이스 연결 및 쿼리 실행을 담당하는 클래스"""
    
    @staticmethod
    def get_connection():
        """MySQL 연결 객체 반환"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except mysql.connector.Error as err:
            logger.error(f"MySQL 연결 오류: {err}")
            raise
    
    @staticmethod
    def test_connection():
        """데이터베이스 연결 테스트"""
        try:
            conn = DBConnector.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            conn.close()
            return result[0] == 1
        except Exception as e:
            logger.error(f"연결 테스트 실패: {e}")
            return False
    
    @staticmethod
    def execute_query(query, params=None, fetch=True):
        """
        쿼리 실행 및 결과 반환
        
        Args:
            query (str): SQL 쿼리문
            params (tuple, list, dict): 쿼리 파라미터
            fetch (bool): 결과를 가져올지 여부
            
        Returns:
            DataFrame 또는 None: 쿼리 결과 (fetch=True인 경우)
        """
        conn = None
        try:
            conn = DBConnector.get_connection()
            if fetch:
                df = pd.read_sql(query, conn, params=params)
                return df
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return None
        except Exception as e:
            logger.error(f"쿼리 실행 오류: {e}")
            if not fetch and conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def load_magazine_data(domain=None, source=None, start_date=None, end_date=None, limit=None):
        """
        매거진 토큰화 데이터 로드
        
        Args:
            domain (str): 문서 도메인 필터 (예: '매거진', '뉴스' 등)
            source (str): 출처 필터 (예: 'Vogue', 'W', 'Harper's' 등)
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
            limit (int): 결과 제한 수
            
        Returns:
            DataFrame: 필터링된 매거진 데이터
        """
        # 기본 쿼리
        query = "SELECT id, doc_domain, upload_date, tokens, source FROM magazine_tokenised"
        
        # 필터 조건 추가
        conditions = []
        params = []
        
        if domain:
            conditions.append("doc_domain = %s")
            params.append(domain)
        
        if source:
            conditions.append("source = %s")
            params.append(source)
        
        if start_date:
            conditions.append("upload_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("upload_date <= %s")
            params.append(end_date)
        
        # 조건 적용
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 정렬 추가
        query += " ORDER BY upload_date DESC"
        
        # 제한 추가
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            df = DBConnector.execute_query(query, params)
            
            # 데이터 후처리
            if not df.empty:
                # 문자열 형태의 토큰 리스트를 실제 리스트로 변환
                df['tokens'] = df['tokens'].apply(eval)
                # 날짜 형식 변환
                df['upload_date'] = pd.to_datetime(df['upload_date'])
            
            return df
        except Exception as e:
            logger.error(f"매거진 데이터 로드 오류: {e}")
            # 오류 발생 시 빈 데이터프레임 반환
            return pd.DataFrame(columns=['id', 'doc_domain', 'upload_date', 'tokens', 'source'])
    
    @staticmethod
    def get_magazine_sources():
        """매거진 출처 목록 가져오기"""
        query = "SELECT DISTINCT source FROM magazine_tokenised WHERE doc_domain = '매거진' ORDER BY source"
        
        try:
            df = DBConnector.execute_query(query)
            return df['source'].tolist() if not df.empty else []
        except Exception as e:
            logger.error(f"매거진 출처 목록 가져오기 오류: {e}")
            return []
    
    @staticmethod
    def get_magazines_in_period(period):
        """특정 기간 내 매거진 목록 가져오기"""
        from datetime import datetime, timedelta
        
        # 기간에 따른 날짜 범위 계산
        today = datetime.now()
        delta_map = {
            '7일': 7,
            '2주': 14,
            '3주': 21,
            '1달': 30,
            '3달': 90,
            '6개월': 180,
            '1년': 365
        }
        
        if period in delta_map:
            delta = delta_map[period]
            start_date = (today - timedelta(days=delta)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
            
            query = """
            SELECT DISTINCT source FROM magazine_tokenised 
            WHERE doc_domain = '매거진' AND upload_date BETWEEN %s AND %s 
            ORDER BY source
            """
            
            try:
                df = DBConnector.execute_query(query, (start_date, end_date))
                return df['source'].tolist() if not df.empty else []
            except Exception as e:
                logger.error(f"기간별 매거진 목록 가져오기 오류: {e}")
                return []
        else:
            return DBConnector.get_magazine_sources()
            
    @staticmethod
    def get_news_data(period=None, start_date=None, end_date=None, limit=None):
        """
        뉴스 데이터 로드
        
        Args:
            period (str): 기간 설정 (예: '7일', '1달')
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
            limit (int): 결과 제한 수
            
        Returns:
            DataFrame: 필터링된 뉴스 데이터
        """
        return DBConnector.load_magazine_data(domain='뉴스', start_date=start_date, end_date=end_date, limit=limit)
            
    @staticmethod
    def get_musinsa_data(period=None, start_date=None, end_date=None, limit=None):
        """
        무신사 데이터 로드
        
        Args:
            period (str): 기간 설정 (예: '7일', '1달')
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
            limit (int): 결과 제한 수
            
        Returns:
            DataFrame: 필터링된 무신사 데이터
        """
        return DBConnector.load_magazine_data(domain='무신사', start_date=start_date, end_date=end_date, limit=limit)