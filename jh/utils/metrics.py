import logging
import json
from datetime import datetime

class CrawlMetrics:
    """크롤링 지표를 수집하고 기록하는 클래스"""
    
    def __init__(self, log_file='logs/crawl.log', stats_file='logs/stats.json'):
        """
        크롤링 지표 초기화
        
        Args:
            log_file (str): 로그 파일 경로
            stats_file (str): 통계 파일 경로
        """
        self.start_time = datetime.now()
        self.log_file = log_file
        self.stats_file = stats_file
        
        # 로거 설정
        self.setup_logger()
        
        # 통계 초기화
        self.init_stats()
        
        self.post_start_time = None
        self.post_times = []
    
    def setup_logger(self):
        """로거를 설정합니다."""
        # 로그 디렉토리 생성
        import os
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 로거 설정
        self.logger = logging.getLogger('instagram_crawler')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 추가
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
    
    def init_stats(self):
        """통계를 초기화합니다."""
        self.stats = {
            'start_time': self.start_time.isoformat(),
            'keywords_processed': 0,
            'posts_attempted': 0,
            'posts_successful': 0,
            'errors': {
                'login': 0,
                'navigation': 0,
                'data_extraction': 0,
                'other': 0
            },
            'data_quality': {
                'posts_with_text': 0,
                'posts_with_hashtags': 0,
                'posts_with_likes': 0,
                'posts_with_comments': 0,
                'posts_with_date': 0,
                'posts_with_image': 0
            },
            'performance': {
                'avg_time_per_post': 0,
                'total_runtime': 0
            }
        }
    
    def start_post(self):
        """게시물 크롤링 시작 시간을 기록합니다."""
        self.post_start_time = datetime.now()
        self.stats['posts_attempted'] += 1
        self.logger.info(f"게시물 크롤링 시작 ({self.stats['posts_attempted']}번째)")
    
    def end_post(self, success=True, data=None):
        """게시물 크롤링 완료를 기록합니다."""
        if self.post_start_time:
            post_time = (datetime.now() - self.post_start_time).total_seconds()
            self.post_times.append(post_time)
            
            if success:
                self.stats['posts_successful'] += 1
                
                # 데이터 품질 측정
                if data:
                    for key, field in [
                        ('text', 'posts_with_text'),
                        ('hashtags', 'posts_with_hashtags'),
                        ('likes', 'posts_with_likes'),
                        ('comments', 'posts_with_comments'),
                        ('date', 'posts_with_date'),
                        ('image_url', 'posts_with_image')
                    ]:
                        value = data.get(key)
                        if value and (not isinstance(value, list) or len(value) > 0):
                            self.stats['data_quality'][field] += 1
            
            result = "성공" if success else "실패"
            self.logger.info(f"게시물 처리 완료: {result}, 소요시간={post_time:.2f}초")
            self.post_start_time = None
    
    def log_error(self, error_type, message):
        """오류를 로깅합니다."""
        self.logger.error(f"{error_type}: {message}")
        if error_type in self.stats['errors']:
            self.stats['errors'][error_type] += 1
        else:
            self.stats['errors']['other'] += 1
    
    def keyword_complete(self, keyword):
        """키워드 처리 완료를 기록합니다."""
        self.stats['keywords_processed'] += 1
        self.logger.info(f"키워드 '{keyword}' 처리 완료")
    
    def save_stats(self):
        """현재 통계를 파일에 저장합니다."""
        # 최종 통계 계산
        self.stats['end_time'] = datetime.now().isoformat()
        total_runtime = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        self.stats['performance']['total_runtime'] = total_runtime
        
        if self.post_times:
            self.stats['performance']['avg_time_per_post'] = sum(self.post_times) / len(self.post_times)
        
        # 통계 파일 디렉토리 생성
        import os
        stats_dir = os.path.dirname(self.stats_file)
        if stats_dir and not os.path.exists(stats_dir):
            os.makedirs(stats_dir)
        
        # 통계 파일에 저장
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        success_rate = 0
        if self.stats['posts_attempted'] > 0:
            success_rate = (self.stats['posts_successful'] / self.stats['posts_attempted']) * 100
        
        self.logger.info(f"크롤링 완료: {self.stats['posts_successful']}/{self.stats['posts_attempted']} 성공 ({success_rate:.1f}%)")
        self.logger.info(f"총 실행 시간: {total_runtime:.2f}초")