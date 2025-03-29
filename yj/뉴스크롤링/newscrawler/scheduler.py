# scheduler.py
import time
import logging
import logging.config
import schedule
import os
import sys
from datetime import datetime
from config import LOGGING_CONFIG

# 로깅 설정
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def run_crawler():
    """크롤러 실행 함수"""
    logger.info(f"정기 크롤링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 현재 디렉토리 기준으로 main.py 실행
        result = os.system('python main.py')
        
        if result == 0:
            logger.info("크롤링 작업 성공")
        else:
            logger.error(f"크롤링 작업 실패 (코드: {result})")
    
    except Exception as e:
        logger.error(f"스케줄러 오류: {e}")

def setup_schedule():
    """스케줄 설정"""
    # 매일 특정 시간(오전 6시, 오후 2시, 오후 10시)에 크롤링 실행
    schedule.every().day.at("06:00").do(run_crawler)
    schedule.every().day.at("14:00").do(run_crawler)
    schedule.every().day.at("22:00").do(run_crawler)
    
    # 또는 매 시간마다 실행하려면:
    # schedule.every(1).hours.do(run_crawler)
    
    logger.info("스케줄러 설정 완료")
    logger.info("다음 실행 시간:")
    for job in schedule.jobs:
        logger.info(f" - {job}")

def main():
    """스케줄러 메인 함수"""
    logger.info("=" * 50)
    logger.info("한국섬유신문 크롤링 스케줄러 시작")
    logger.info("=" * 50)
    
    # 시작 즉시 한 번 실행
    run_crawler()
    
    # 스케줄 설정
    setup_schedule()
    
    # 스케줄러 무한 루프
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        logger.info("스케줄러 중지 (Ctrl+C)")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
    finally:
        logger.info("스케줄러 종료")

if __name__ == "__main__":
    main()
