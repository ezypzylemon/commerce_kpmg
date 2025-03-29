# database.py
import mysql.connector
from mysql.connector import Error
import logging
from config import MYSQL_CONFIG, NEWS_TABLE

def create_database():
    """데이터베이스가 없는 경우 생성"""
    # 데이터베이스 이름 백업
    db_name = MYSQL_CONFIG['database']
    
    # 데이터베이스 이름 제거한 설정으로 접속
    config = MYSQL_CONFIG.copy()
    del config['database']
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 데이터베이스 생성
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} "
                      f"CHARACTER SET {MYSQL_CONFIG['charset']} "
                      f"COLLATE {MYSQL_CONFIG['collation']}")
        
        logging.info(f"데이터베이스 '{db_name}' 생성/확인 완료")
        
    except Error as e:
        logging.error(f"데이터베이스 생성 오류: {e}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_tables():
    """필요한 테이블 생성"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # 뉴스 기사 테이블
        create_news_table_query = f"""
        CREATE TABLE IF NOT EXISTS {NEWS_TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword VARCHAR(100) NOT NULL,
            title VARCHAR(500) NOT NULL,
            link VARCHAR(500) NOT NULL,
            published DATETIME,
            source VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_link (link)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_news_table_query)
        logging.info(f"테이블 '{NEWS_TABLE}' 생성/확인 완료")
        
        # 필요시 추가 테이블 생성 코드
        
        conn.commit()
        
    except Error as e:
        logging.error(f"테이블 생성 오류: {e}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def init_database():
    """데이터베이스 및 테이블 초기화"""
    try:
        create_database()
        create_tables()
        logging.info("데이터베이스 초기화 완료")
        return True
    except Exception as e:
        logging.error(f"데이터베이스 초기화 실패: {e}")
        return False

if __name__ == "__main__":
    # 로깅 설정
    import logging.config
    from config import LOGGING_CONFIG
    
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 데이터베이스 초기화 실행
    success = init_database()
    if success:
        print("데이터베이스 및 테이블 초기화 완료")
    else:
        print("데이터베이스 초기화 실패. 로그를 확인하세요.")