from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random

class BrowserManager:
    """브라우저 생성 및 제어를 담당하는 클래스"""
    
    def __init__(self, config):
        """
        브라우저 관리자 초기화
        
        Args:
            config (dict): 브라우저 설정
        """
        self.config = config
        self.driver = None
    
    def setup_driver(self):
        """웹드라이버를 설정하고 반환합니다."""
        options = Options()
        
        # 사용자 에이전트 설정
        user_agent = self.config.get('user_agent')
        if user_agent:
            options.add_argument(f'User-Agent={user_agent}')
        
        # 자동화 감지 방지 설정
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 추가 브라우저 설정
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--start-maximized')
        
        # 헤드리스 모드 설정 (선택적)
        if self.config.get('headless', False):
            options.add_argument('--headless')
        
        # 웹드라이버 생성
        self.driver = webdriver.Chrome(options=options)
        
        # 자동화 감지 우회 스크립트 실행
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', 
                                   {"userAgent": user_agent or 'Mozilla/5.0'})
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 창 크기 설정
        window_size = self.config.get('window_size', {'width': 1920, 'height': 1080})
        self.driver.set_window_size(window_size['width'], window_size['height'])
        
        return self.driver
    
    def add_human_behavior(self):
        """인간과 유사한 행동 패턴을 추가합니다."""
        if not self.driver:
            return
        
        # 랜덤 마우스 이동
        try:
            action = webdriver.ActionChains(self.driver)
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            random_x = random.randint(100, viewport_width - 200)
            random_y = random.randint(100, viewport_height - 200)
            
            action.move_by_offset(random_x, random_y)
            action.perform()
        except Exception:
            pass
        
        # 랜덤 스크롤
        if random.random() < 0.3:  # 30% 확률로 스크롤
            try:
                scroll_amount = random.randint(100, 300)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
                time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                pass
    
    def close(self):
        """브라우저를 종료합니다."""
        if self.driver:
            self.driver.quit()
            self.driver = None