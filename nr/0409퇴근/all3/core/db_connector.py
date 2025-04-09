import mysql.connector
from mysql.connector import pooling
import pandas as pd
import os
import logging
from .config import DB_CONFIG

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DBConnector:
    """데이터베이스 연결 및 쿼리 실행을 담당하는 클래스"""
    
    _connection_pool = None

    @classmethod
    def get_connection_pool(cls):
        """연결 풀 반환 (없으면 생성)"""
        if cls._connection_pool is None:
            try:
                cls._connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="fashion_trend_pool",
                    pool_size=5,  # 연결 풀 크기 조정
                    **DB_CONFIG
                )
                logger.info("DB 연결 풀 생성 완료")
            except Exception as e:
                logger.error(f"Connection pool 생성 실패: {e}")
                return None
        return cls._connection_pool
    
    @staticmethod
    def get_connection():
        """MySQL 연결 객체 반환"""
        try:
            pool = DBConnector.get_connection_pool()
            if pool:
                connection = pool.get_connection()
                return connection
            else:
                # 풀 생성 실패 시 직접 연결 시도
                logger.warning("연결 풀 사용 불가, 직접 연결 시도")
                conn = mysql.connector.connect(**DB_CONFIG)
                return conn
        except mysql.connector.Error as err:
            logger.error(f"MySQL 연결 오류: {err}")
            return None
    
    @staticmethod
    def test_connection():
        """데이터베이스 연결 테스트"""
        try:
            conn = DBConnector.get_connection()
            if not conn:
                logger.error("연결 객체를 가져올 수 없습니다.")
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            conn.close()
            
            if result and result[0] == 1:
                logger.info("데이터베이스 연결 테스트 성공")
                return True
            else:
                logger.warning("데이터베이스 연결 테스트 결과가 예상과 다릅니다.")
                return False
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
        cursor = None
        try:
            conn = DBConnector.get_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return None if fetch else False
                
            if fetch:
                try:
                    df = pd.read_sql(query, conn, params=params)
                    return df
                except Exception as e:
                    logger.error(f"pd.read_sql 실행 오류: {e}")
                    
                    # 직접 실행으로 대체 시도
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    if rows:
                        return pd.DataFrame(rows)
                    return pd.DataFrame()
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"쿼리 실행 오류: {e}")
            if not fetch and conn:
                try:
                    conn.rollback()
                except:
                    pass
            return None if fetch else False
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except:
                pass
    
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
        try:
            # 기본 쿼리
            query = "SELECT id, doc_domain, upload_date, tokens, source FROM fashion_trends.magazine_tokenised"
            
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
                conditions.append("DATE(upload_date) >= DATE(%s)")
                params.append(start_date)
            
            if end_date:
                conditions.append("DATE(upload_date) <= DATE(%s)")
                params.append(end_date)
            
            # 조건 적용
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # 정렬 추가
            query += " ORDER BY upload_date DESC"
            
            # 제한 추가
            if limit:
                query += f" LIMIT {limit}"
            else:
                query += " LIMIT 1000"  # 과도한 데이터 로드 방지
            
            logger.info(f"매거진 데이터 로드 쿼리: {query}")
            
            df = DBConnector.execute_query(query, params)
            
            # 데이터 후처리
            if df is not None and not df.empty:
                # 문자열 형태의 토큰 리스트를 실제 리스트로 변환
                try:
                    df['tokens'] = df['tokens'].apply(eval)
                except Exception as e:
                    logger.error(f"토큰 변환 오류: {e}")
                    
                # 날짜 형식 변환
                try:
                    df['upload_date'] = pd.to_datetime(df['upload_date'])
                except Exception as e:
                    logger.error(f"날짜 변환 오류: {e}")
                
                logger.info(f"매거진 데이터 {len(df)}개 로드 완료")
            else:
                logger.warning("매거진 데이터가 없습니다.")
                df = pd.DataFrame(columns=['id', 'doc_domain', 'upload_date', 'tokens', 'source'])
            
            return df
        except Exception as e:
            logger.error(f"매거진 데이터 로드 오류: {e}")
            # 오류 발생 시 빈 데이터프레임 반환
            return pd.DataFrame(columns=['id', 'doc_domain', 'upload_date', 'tokens', 'source'])
    
    @staticmethod
    def get_magazine_sources():
        """매거진 출처 목록 가져오기"""
        query = "SELECT DISTINCT source FROM fashion_trends.magazine_tokenised WHERE doc_domain = '매거진' ORDER BY source"
        
        try:
            df = DBConnector.execute_query(query)
            if df is not None and not df.empty:
                return df['source'].tolist()
            else:
                logger.warning("매거진 출처 데이터가 없습니다.")
                return []
        except Exception as e:
            logger.error(f"매거진 출처 목록 가져오기 오류: {e}")
            return []
    
    @staticmethod
    def get_magazines_in_period(period):
        """특정 기간 내 매거진 목록 가져오기"""
        from datetime import datetime, timedelta
        
        try:
            # 기간에 따른 날짜 범위 계산
            today = datetime.now()
            delta_map = {
                '7일': 7,
                '2주': 14,
                '1개월': 30,
                '3개월': 90,
                '6개월': 180,
                '1년': 365
            }
            
            if period in delta_map:
                delta = delta_map[period]
                start_date = (today - timedelta(days=delta)).strftime('%Y-%m-%d')
                end_date = today.strftime('%Y-%m-%d')
                
                query = """
                SELECT DISTINCT source FROM fashion_trends.magazine_tokenised 
                WHERE doc_domain = '매거진' AND upload_date BETWEEN %s AND %s 
                ORDER BY source
                """
                
                df = DBConnector.execute_query(query, (start_date, end_date))
                if df is not None and not df.empty:
                    return df['source'].tolist()
                else:
                    logger.warning(f"{period} 기간 동안 매거진 출처 데이터가 없습니다.")
                    return []
            else:
                logger.warning(f"지원하지 않는 기간: {period}")
                return DBConnector.get_magazine_sources()
        except Exception as e:
            logger.error(f"기간별 매거진 목록 가져오기 오류: {e}")
            return []
            
    @staticmethod
    def get_news_data(period=None, start_date=None, end_date=None, limit=None):
        """
        뉴스 데이터 로드
        
        Args:
            period (str): 기간 설정 (예: '7일', '1개월')
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
            limit (int): 결과 제한 수
            
        Returns:
            DataFrame: 필터링된 뉴스 데이터
        """
        try:
            from datetime import datetime, timedelta
            
            # 기간에 따른 시작 날짜 설정
            if period and not (start_date and end_date):
                delta_map = {
                    '7일': 7,
                    '2주': 14,
                    '1개월': 30,
                    '3개월': 90,
                    '6개월': 180,
                    '1년': 365
                }
                
                if period in delta_map:
                    days = delta_map[period]
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
            # 데이터 로드
            return DBConnector.load_magazine_data(domain='뉴스', start_date=start_date, end_date=end_date, limit=limit)
        except Exception as e:
            logger.error(f"뉴스 데이터 로드 오류: {e}")
            return pd.DataFrame()
            
    @staticmethod
    def get_musinsa_data(start_date=None, end_date=None, limit=None):
        """
        무신사 데이터 로드
        
        Args:
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
            limit (int): 결과 제한 수
            
        Returns:
            DataFrame: 필터링된 무신사 데이터
        """
        try:
            conn = DBConnector.get_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return pd.DataFrame()
            
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT * FROM fashion_trends.musinsa_data
            WHERE 1=1
            """
            
            params = []
            
            if start_date:
                query += " AND DATE(upload_date) >= DATE(%s)"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(upload_date) <= DATE(%s)"
                params.append(end_date)
                
            query += " ORDER BY upload_date DESC"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            else:
                query += " LIMIT 1000"  # 과도한 데이터 로드 방지
            
            logger.info(f"무신사 데이터 로드 쿼리: {query}, 파라미터: {params}")
            
            cursor.execute(query, params)
            result = cursor.fetchall()
            
            if not result:
                logger.warning("무신사 데이터가 없습니다.")
                return pd.DataFrame()
            
            # 결과를 DataFrame으로 변환
            df = pd.DataFrame(result)
            
            # 날짜 형식 변환
            if 'upload_date' in df.columns:
                df['upload_date'] = pd.to_datetime(df['upload_date'])
            
            logger.info(f"무신사 데이터 {len(df)}개 로드 완료")
            
            return df
            
        except Exception as e:
            logger.error(f"무신사 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame()
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
                if 'conn' in locals() and conn:
                    conn.close()
            except:
                pass