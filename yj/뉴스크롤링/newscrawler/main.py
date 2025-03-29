# main.py
import argparse
import logging
import logging.config
from datetime import datetime
from database import init_database
from run_knews_crawler import crawl_knews
from utils import get_article_count
from config import LOGGING_CONFIG, NEWS_TABLE

def setup_logging():
    """로깅 설정"""
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.info(f"크롤링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="한국섬유신문 기사 크롤러")
    parser.add_argument("--init", action="store_true", help="데이터베이스 초기화")
    parser.add_argument("--pages", type=int, default=20, help="크롤링할 최대 페이지 수")
    parser.add_argument("--start-page", type=int, default=1, help="크롤링 시작 페이지 번호")
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    
    # 데이터베이스 초기화
    if args.init:
        logging.info("데이터베이스 초기화 중...")
        if not init_database():
            logging.error("데이터베이스 초기화 실패. 프로그램을 종료합니다.")
            return
    
    # 크롤링 전 기사 수 확인
    before_count = get_article_count(NEWS_TABLE)
    logging.info(f"크롤링 전 기사 수: {before_count}")
    
    # 크롤링 실행
    try:
        total_collected, total_saved = crawl_knews(
            start_page=args.start_page,
            max_pages=args.pages
        )
        
        # 크롤링 후 기사 수 확인
        after_count = get_article_count(NEWS_TABLE)
        
        # 결과 출력
        logging.info("=" * 50)
        logging.info("크롤링 결과")
        logging.info(f"수집 시도 기사: {total_collected}")
        logging.info(f"저장 성공 기사: {total_saved}")
        logging.info(f"이전 기사 수: {before_count}")
        logging.info(f"현재 기사 수: {after_count}")
        logging.info(f"새로 추가된 기사: {after_count - before_count}")
        logging.info("=" * 50)
        
    except Exception as e:
        logging.error(f"크롤링 중 오류 발생: {e}")
    
    logging.info(f"크롤링 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()