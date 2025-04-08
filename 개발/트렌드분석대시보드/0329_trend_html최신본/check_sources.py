from config import MYSQL_CONFIG
import mysql.connector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_sources():
    try:
        # 데이터베이스 연결
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 소스 목록 조회
        cursor.execute("SELECT DISTINCT source FROM all_trends")
        sources = cursor.fetchall()
        
        logger.info("데이터베이스의 매거진 소스 목록:")
        for source in sources:
            logger.info(f"- {source['source']}")
        
        # 샘플 데이터 확인
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM all_trends 
            GROUP BY source
        """)
        counts = cursor.fetchall()
        
        logger.info("\n매거진별 기사 수:")
        for count in counts:
            logger.info(f"- {count['source']}: {count['count']}개")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"데이터베이스 확인 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_sources() 