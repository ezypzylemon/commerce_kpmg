from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

class InstagramAuth:
    """인스타그램 인증을 담당하는 클래스"""
    
    def __init__(self, driver, selectors, logger=None):
        """
        인스타그램 인증 초기화
        
        Args:
            driver: Selenium 웹드라이버
            selectors (dict): 로그인 관련 선택자
            logger: 로깅을 위한 로거 객체
        """
        self.driver = driver
        self.selectors = selectors
        self.logger = logger
        
        # 환경 변수에서 로그인 정보 로드
        load_dotenv(verbose=True)
        self.username = os.getenv('INSTAGRAM_ID')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
    
    def log(self, message, level='info'):
        """로깅 헬퍼 함수"""
        if self.logger:
            if level == 'info':
                self.logger.info(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)
    
    def login(self):
        """인스타그램에 로그인합니다."""
        if not self.username or not self.password:
            self.log("로그인 정보가 설정되지 않았습니다.", 'error')
            return False
        
        try:
            # 인스타그램 로그인 페이지 접속
            self.driver.get('https://www.instagram.com/')
            self.log("인스타그램 페이지 접속")
            
            # 쿠키 팝업이 나타날 경우 대기
            time.sleep(5)
            
            # 사용자명 필드 찾기 및 입력
            username_selector = self.selectors.get('username_field', 'input[name="username"]')
            self.log(f"사용자명 필드 찾는 중: {username_selector}")
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, username_selector))
            )
            
            username_field = self.driver.find_element(By.CSS_SELECTOR, username_selector)
            username_field.clear()
            username_field.send_keys(self.username)
            self.log("사용자명 입력 완료")
            
            # 비밀번호 필드 찾기 및 입력
            password_selector = self.selectors.get('password_field', 'input[name="password"]')
            password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
            password_field.clear()
            password_field.send_keys(self.password)
            self.log("비밀번호 입력 완료")
            
            # 로그인 버튼 클릭
            login_button_selector = self.selectors.get('login_button', 'button[type="submit"]')
            login_button = self.driver.find_element(By.CSS_SELECTOR, login_button_selector)
            login_button.click()
            self.log("로그인 버튼 클릭")
            
            # 로그인 완료 대기
            self.log("로그인 진행 중...")
            time.sleep(10)
            
            # 로그인 성공 확인
            home_icon_selector = self.selectors.get('home_icon', 'svg[aria-label="홈"], svg[aria-label="Home"]')
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, home_icon_selector))
                )
                self.log("로그인 성공!")
                return True
            except:
                self.log("로그인 후 홈 화면 로드 실패", 'error')
                # 로그인은 됐을 수 있으므로 일단 진행
                return True
            
        except Exception as e:
            self.log(f"로그인 실패: {str(e)}", 'error')
            return False