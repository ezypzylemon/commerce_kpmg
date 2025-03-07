import time
import random
from datetime import datetime, timedelta

class RateLimiter:
    """요청 속도를 제한하는 클래스"""
    
    def __init__(self, min_delay=2, max_delay=7, requests_per_hour=30):
        """
        속도 제한 초기화
        
        Args:
            min_delay (float): 최소 지연 시간(초)
            max_delay (float): 최대 지연 시간(초)
            requests_per_hour (int): 시간당 최대 요청 수
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.requests_per_hour = requests_per_hour
        self.request_timestamps = []
    
    def wait(self):
        """인간과 유사한 랜덤 지연을 적용하고 시간당 요청 수를 제한합니다."""
        # 랜덤 지연 적용
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        
        # 시간당 요청 수 제한
        now = datetime.now()
        self.request_timestamps.append(now)
        
        # 1시간 이상 지난 타임스탬프 제거
        hour_ago = now.timestamp() - 3600
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if ts.timestamp() > hour_ago]
        
        # 시간당 요청 수를 초과했는지 확인
        if len(self.request_timestamps) > self.requests_per_hour:
            wait_time = 3600 - (now.timestamp() - self.request_timestamps[0].timestamp())
            if wait_time > 0:
                print(f"시간당 요청 제한에 도달했습니다. {wait_time:.2f}초 대기...")
                time.sleep(wait_time)
    
    def set_limits(self, min_delay=None, max_delay=None, requests_per_hour=None):
        """속도 제한 설정을 업데이트합니다."""
        if min_delay is not None:
            self.min_delay = min_delay
        if max_delay is not None:
            self.max_delay = max_delay
        if requests_per_hour is not None:
            self.requests_per_hour = requests_per_hour