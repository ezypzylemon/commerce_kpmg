# main.py
import os
import logging
from datetime import datetime
import sys

# 자체 모듈 임포트
from crawler import MusinsaCrawler
from preprocessor import DataPreprocessor
from visualizer import TrendVisualizer
from report_generator import ReportGenerator
#from notification import NotificationSender

# 로깅 설정
logging.basicConfig(
    filename='fashion_trend_analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # 날짜 폴더 생성
        today = datetime.now().strftime('%Y-%m-%d')
        base_dir = f"/Users/jiyeonjoo/Documents/GitHub/commerce_kpmg/yj/0324/fashion_trend_analysis/reports/{today}"
        os.makedirs(base_dir, exist_ok=True)
        
        logging.info(f"===== 패션 트렌드 분석 시작: {today} =====")


        # 1. 크롤링 실행
        logging.info("크롤링 시작...")
        crawler = MusinsaCrawler(headless=True, output_dir=base_dir)
        csv_path = crawler.crawl_all_categories(items_per_category=20, total_target=120)
        crawler.close()
        logging.info(f"크롤링 완료: {csv_path}")
        
        # 2. 데이터 전처리
        logging.info("데이터 전처리 시작...")
        preprocessor = DataPreprocessor(csv_path)
        processed_data = preprocessor.process()
        logging.info("데이터 전처리 완료")
        
        # 3. 시각화
        logging.info("시각화 시작...")
        viz_dir = os.path.join(base_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        
        visualizer = TrendVisualizer(processed_data, output_dir=viz_dir)
        viz_results = visualizer.generate_all_visualizations()
        logging.info(f"시각화 완료: {len(viz_results)} 이미지 생성됨")
        
        # 4. 보고서 생성
        logging.info("보고서 생성 시작...")
        report_path = os.path.join(base_dir, f"fashion_trend_report_{today}.html")
        report_gen = ReportGenerator(
            processed_data, 
            viz_results, 
            output_path=report_path
        )
        report_gen.generate()
        logging.info(f"보고서 생성 완료: {report_path}")

        logging.info(f"===== 패션 트렌드 분석 완료: {today} =====")
        return True
 
    
    #     # 5. 알림 발송 (선택사항)
    #     try:
    #         logging.info("알림 발송 시작...")
    #         notifier = NotificationSender()
    #         notifier.send_email(
    #             subject=f"[자동] 패션 트렌드 분석 보고서 ({today})",
    #             message=f"""
    #             안녕하세요,
                
    #             {today} 기준 패션 트렌드 분석 보고서가 생성되었습니다.
    #             첨부 파일을 확인해 주세요.
                
    #             * 총 수집 상품 수: {len(processed_data)}개
    #             * 카테고리 수: {processed_data['category'].nunique()}개
    #             * 브랜드 수: {processed_data['brand'].nunique()}개
                
    #             이 메일은 자동으로 발송되었습니다.
    #             """,
    #             attachments=[report_path]
    #         )
    #         logging.info("알림 발송 완료")
    #     except Exception as e:
    #         logging.warning(f"알림 발송 실패: {e}")
        
    #     logging.info(f"===== 패션 트렌드 분석 완료: {today} =====")
    #     return True
        
    # except Exception as e:
    #     logging.error(f"프로세스 실행 중 오류 발생: {e}", exc_info=True)
    #     # 오류 알림 발송
    #     try:
    #         notifier = NotificationSender()
    #         notifier.send_email(
    #             subject=f"[오류] 패션 트렌드 분석 실패 ({today})",
    #             message=f"오류 내용: {str(e)}"
    #         )
    #     except:
    #         pass
    #     return False
    except Exception as e:
        logging.error(f"프로세스 실행 중 오류 발생: {e}", exc_info=True)
        return False




if __name__ == "__main__":
    # 커맨드 라인 인자 처리 (선택사항)
    headless_mode = True
    output_dir = "/Users/jiyeonjoo/Documents/GitHub/commerce_kpmg/yj/0324/fashion_trend_analysis"
    
    if len(sys.argv) > 1:
        # 첫 번째 인자: 헤드리스 모드 (True/False)
        if sys.argv[1].lower() == 'false':
            headless_mode = False
    
    if len(sys.argv) > 2:
        # 두 번째 인자: 출력 디렉토리
        output_dir = sys.argv[2]
    
    # 메인 함수 실행
    success = main()
    
    # 종료 코드 설정 (자동화 스크립트에서 사용)
    sys.exit(0 if success else 1)