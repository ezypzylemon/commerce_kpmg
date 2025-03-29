# utils.py
import mysql.connector
from mysql.connector import Error
import logging
from contextlib import contextmanager
from config import MYSQL_CONFIG

@contextmanager
def get_db_connection():
    """데이터베이스 연결을 컨텍스트 매니저로 관리"""
    conn = None
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        yield conn
    except Error as e:
        logging.error(f"데이터베이스 연결 오류: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()
            logging.debug("데이터베이스 연결 종료")

@contextmanager
def get_db_cursor(conn, dictionary=False):
    """커서를 컨텍스트 매니저로 관리"""
    cursor = None
    try:
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
    finally:
        if cursor:
            cursor.close()
            logging.debug("커서 종료")
            

def check_article_exists(conn, link, table_name="knews_articles"):
    """링크로 기사 중복 체크"""
    normalized_link = normalize_url(link)
    query = f"SELECT COUNT(*) FROM {table_name} WHERE link LIKE %s"
    
    try:
        with get_db_cursor(conn) as cursor:
            # URL을 부분 일치로 검색
            cursor.execute(query, (f"%{normalized_link.split('/')[-1]}%",))
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        logging.error(f"중복 체크 오류: {e}")
        return False
    
def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS knews_articles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        keyword VARCHAR(100) NOT NULL,
        title VARCHAR(500) NOT NULL,
        link VARCHAR(500) UNIQUE NOT NULL,
        published DATETIME,
        source VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(create_table_query)
                conn.commit()
                logging.info("테이블 생성/확인 완료")
    except Error as e:
        logging.error(f"테이블 생성 오류: {e}")

def save_to_db(data, table_name="knews_articles"):
    """데이터베이스에 기사 저장 (중복 체크 확인을 위한 로깅 추가)"""
    keyword, title, link, published, source, content = data
    
    try:
        with get_db_connection() as conn:
            # 중복 체크 디버깅
            with get_db_cursor(conn) as cursor:
                check_query = f"SELECT COUNT(*) FROM {table_name} WHERE link = %s"
                cursor.execute(check_query, (link,))
                count = cursor.fetchone()[0]
                logging.debug(f"링크 '{link}'의 중복 체크 결과: {count}개 발견")
                
                if count > 0:
                    logging.info(f"중복 기사 발견: {title}")
                    return False
            
            # 데이터 삽입
            query = f"""
                INSERT INTO {table_name} 
                (keyword, title, link, published, source, content)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            with get_db_cursor(conn) as cursor:
                cursor.execute(query, data)
                conn.commit()
                logging.info(f"기사 저장 성공: {title}")
                return True
                
    except Error as e:
        logging.error(f"DB 저장 실패: {e} - {title}")
        # 에러 상세 정보 출력
        logging.error(f"에러 상세: {str(e)}")
        return False
  
def normalize_url(url):
    """URL을 정규화하여 중복 체크 정확도 향상"""
    # URL에서 쿼리 스트링 제거
    import re
    normalized = re.sub(r'\?.*$', '', url)
    # 슬래시로 끝나는 경우 제거
    normalized = re.sub(r'/$', '', normalized)
    return normalized

def get_latest_articles(limit=10, table_name="knews_articles"):
    """최근 저장된 기사 조회"""
    query = f"""
        SELECT id, keyword, title, link, published, source
        FROM {table_name}
        ORDER BY published DESC
        LIMIT %s
    """
    
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn, dictionary=True) as cursor:
                cursor.execute(query, (limit,))
                return cursor.fetchall()
    except Error as e:
        logging.error(f"기사 조회 실패: {e}")
        return []

def get_article_count(table_name="knews_articles"):
    """저장된 총 기사 수 조회"""
    query = f"SELECT COUNT(*) FROM {table_name}"
    
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    except Error as e:
        logging.error(f"기사 수 조회 실패: {e}")
        return 0