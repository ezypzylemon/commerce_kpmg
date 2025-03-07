#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from datetime import datetime

# 모듈 경로 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# 내부 모듈 임포트
from config.config_loader import ConfigLoader
from utils.metrics import CrawlMetrics
from utils.rate_limiter import RateLimiter
from src.browser import BrowserManager
from src.auth import InstagramAuth
from src.scraper import InstagramScraper
from src.data_processor import DataProcessor
from src.privacy import PrivacyHandler

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description='인스타그램 데이터 스크래퍼')
    
    parser.add_argument('-c', '--config', type=str, default='config/config.yaml',
                        help='설정 파일 경로 (기본값: config/config.yaml)')
    
    parser.add_argument('-o', '--output', type=str, default='data/instagram_data.csv',
                        help='출력 CSV 파일 경로 (기본값: data/instagram_data.csv)')
    
    parser.add_argument('-p', '--posts', type=int, default=5,
                        help='각 키워드당 수집할 게시물 수 (기본값: 5)')
    
    parser.add_argument('-k', '--keywords', type=str, nargs='+',
                        help='수집할 해시태그 키워드 (설정 파일 대신 사용)')
    
    parser.add_argument('--headless', action='store_true',
                        help='헤드리스 모드로 실행 (화면 표시 없음)')
    
    parser.add_argument('--debug', action='store_true',
                        help='디버그 모드 활성화')
    return parser.parse_args()

def main():
    """인스타그램 크롤러 메인 함수"""
    # 인수 파싱
    args = parse_arguments()
    
    # 프로그램 시작 시간
    start_time = datetime.now()
    run_id = start_time.strftime("%Y%m%d_%H%M%S")
    
    # 로그 및 데이터 디렉토리 생성
    log_dir = os.path.join("logs", run_id)
    data_dir = os.path.join("data", run_id)
    for directory in [log_dir, data_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # 파일 경로 설정
    log_file = os.path.join(log_dir, "crawler.log")
    stats_file = os.path.join(log_dir, "stats.json")
    output_file = args.output if args.output else os.path.join(data_dir, "instagram_data.csv")
    
    # 지표 수집 초기화
    metrics = CrawlMetrics(log_file=log_file, stats_file=stats_file)
    metrics.logger.info("인스타그램 크롤러 시작")
    metrics.logger.info(f"실행 ID: {run_id}")
    
    try:
        # 설정 로드
        config_loader = ConfigLoader(config_path=args.config)
        config = config_loader.get_config()
        
        # 명령줄 인수로 설정 덮어쓰기
        if args.headless:
            config['browser']['headless'] = True
        
        if args.posts:
            config['limits']['posts_per_keyword'] = args.posts
        
        # 키워드 설정
        keywords = []
        if args.keywords:
            keywords = [{"ko": kw, "en": kw} for kw in args.keywords]
        else:
            keywords = config_loader.get_keywords()
        
        if not keywords:
            metrics.logger.error("수집할 키워드가 지정되지 않았습니다.")
            return
        
        # 속도 제한 설정
        limits = config_loader.get_limits()
        rate_limiter = RateLimiter(
            min_delay=limits.get('min_delay', 2),
            max_delay=limits.get('max_delay', 7),
            requests_per_hour=limits.get('requests_per_hour', 30)
        )
        
        # 브라우저 설정
        browser_manager = BrowserManager(config_loader.get_browser_config())
        driver = browser_manager.setup_driver()
        
        # 인스타그램 로그인
        auth = InstagramAuth(
            driver, 
            config_loader.get_selectors('login'),
            logger=metrics.logger
        )
        
        if not auth.login():
            metrics.logger.error("로그인에 실패했습니다. 프로그램을 종료합니다.")
            browser_manager.close()
            return
        
        # 스크래퍼 초기화
        scraper = InstagramScraper(
            driver,
            config_loader.get_selectors('post'),
            rate_limiter=rate_limiter,
            metrics=metrics
        )
        
        # 데이터 처리기 초기화
        data_processor = DataProcessor(logger=metrics.logger)
        
        # 수집 데이터 저장 구조
        all_data = {
            'keyword': [],
            'text': [],
            'hashtags': [],
            'likes': [],
            'comments': [],
            'date': [],
            'image_url': [],
            'video_views': []
        }
        
        # 각 키워드에 대해 게시물 수집
        for keyword_dict in keywords:
            ko_keyword = keyword_dict.get('ko', '')
            en_keyword = keyword_dict.get('en', '')
            
            # 영어 키워드가 없으면 한글 키워드 사용
            if not en_keyword:
                en_keyword = ko_keyword
            
            metrics.logger.info(f"키워드 '{ko_keyword}' 데이터 수집 시작")
            
            # 게시물 스크래핑
            posts_data = scraper.scrape_hashtag_posts(
                en_keyword,
                max_posts=config['limits']['posts_per_keyword']
            )
            
            # 수집된 데이터가 있으면 전체 데이터에 추가
            if posts_data:
                posts_count = len(posts_data)
                
                # 키워드 필드 추가
                keyword_name = ko_keyword or en_keyword
                
                # 결과 데이터에 통합
                for post in posts_data:
                    all_data['keyword'].append(keyword_name)
                    for key in post:
                        all_data[key].append(post[key])
                
                metrics.logger.info(f"키워드 '{keyword_name}'에서 {posts_count}개 게시물 수집 완료")
            else:
                metrics.logger.warning(f"키워드 '{ko_keyword or en_keyword}'에서 수집된 게시물이 없습니다.")
            
            # 키워드 처리 완료 기록
            metrics.keyword_complete(ko_keyword or en_keyword)
        
        # 수집된 데이터 처리 및 저장
        if all_data['text']:
            # 데이터 처리
            processed_data = data_processor.process_data(all_data)
            
            # 개인정보 처리
            privacy_handler = PrivacyHandler(
                retention_days=config.get('privacy', {}).get('retention_days', 30),
                logger=metrics.logger
            )
            
            # 원본 데이터 저장 (암호화)
            original_file = os.path.join(data_dir, "instagram_data_original.csv")
            data_processor.save_to_csv(all_data, original_file)
            
            # 데이터 익명화
            anonymized_data = privacy_handler.anonymize_data(processed_data)
            anonymized_file = os.path.join(data_dir, "instagram_data_anonymized.csv")
            data_processor.save_to_csv(anonymized_data, anonymized_file)
            
            # 암호화된 데이터 저장
            encrypted_data = privacy_handler.encrypt_data(processed_data)
            encrypted_file = os.path.join(data_dir, "instagram_data_encrypted.csv")
            data_processor.save_to_csv(encrypted_data, encrypted_file)
            
            # 삭제 일정 예약
            for file_path in [original_file, encrypted_file]:
                privacy_handler.schedule_deletion(file_path)
            
            # 데이터 수집 영수증 생성
            receipt_file = os.path.join(data_dir, "data_receipt.txt")
            privacy_handler.generate_data_receipt(processed_data, receipt_file)
            
            # 데이터 요약 출력
            summary = data_processor.get_data_summary(processed_data)
            metrics.logger.info(summary)
            
            # 기본 출력 파일에도 저장
            if output_file != anonymized_file:
                data_processor.save_to_csv(anonymized_data, output_file)
        else:
            metrics.logger.warning("수집된 데이터가 없습니다.")
        
    except Exception as e:
        metrics.logger.error(f"프로그램 실행 중 오류 발생: {str(e)}", exc_info=True)
    
    finally:
        # 브라우저 종료
        try:
            browser_manager.close()
        except:
            pass
        
        # 최종 통계 저장
        try:
            metrics.save_stats()
        except:
            pass
        
        # 실행 시간 계산
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        metrics.logger.info(f"프로그램 종료. 총 실행 시간: {elapsed_time:.2f}초")

if __name__ == "__main__":
    main()