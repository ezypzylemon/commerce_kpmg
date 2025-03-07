from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import random
import os

class InstagramScraper:
    """인스타그램 게시물 스크래핑을 담당하는 클래스"""
    
    def __init__(self, driver, selectors, rate_limiter=None, metrics=None):
        """
        스크래퍼 초기화
        
        Args:
            driver: Selenium 웹드라이버
            selectors (dict): 스크래핑 관련 선택자
            rate_limiter: 요청 속도 제한 객체
            metrics: 지표 수집 객체
        """
        self.driver = driver
        self.selectors = selectors
        self.rate_limiter = rate_limiter
        self.metrics = metrics
    
    def log(self, message, level='info'):
        """로깅 헬퍼 함수"""
        if self.metrics:
            if level == 'info':
                self.metrics.logger.info(message)
            elif level == 'error':
                self.metrics.logger.error(message)
            elif level == 'debug':
                self.metrics.logger.debug(message)
    
    def extract_text_and_hashtags(self):
        """게시물 텍스트와 해시태그를 추출합니다."""
        text = ""
        hashtags = []
        
        # 본문 콘텐츠가 있는 다양한 선택자 시도
        text_selectors = [
            'h1[dir="auto"]',
            'div[dir="auto"]',
            'h1._ap3a, h1._aaco, h1._aacu, h1._aacx, h1._aad7, h1._aade',
            'div._ap3a, div._aaco, div._aacu, div._aacx, div._aad7, div._aade',
            'span[dir="auto"]',
            'div[role="dialog"] span',
            'div[role="dialog"] div[dir="auto"]',
        ]
        
        # 먼저 본문 전체를 포함할 가능성이 높은 요소를 찾음
        found_main_content = False
        for selector in text_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        elem_text = elem.text
                        # 본문으로 판단되는 충분히 긴 텍스트를 찾았다면
                        if elem_text and len(elem_text) > 30:  # 의미 있는 길이의 텍스트
                            text = elem_text
                            found_main_content = True
                            self.log(f"본문 내용 발견 (길이: {len(text)})")
                            
                            # 해시태그 추출
                            hashtag_matches = re.findall(r'#\w+', elem_text)
                            if hashtag_matches:
                                hashtags.extend(hashtag_matches)
                            
                            break
                    except Exception as e:
                        self.log(f"텍스트 추출 중 오류: {str(e)}", 'debug')
                        continue
                
                if found_main_content:
                    break
            except Exception as e:
                self.log(f"선택자 '{selector}' 처리 중 오류: {str(e)}", 'debug')
                continue
        
        # 본문을 못 찾았으면 기존 방식으로 시도
        if not found_main_content:
            self.log("주요 본문을 찾지 못해 대체 방법 시도", 'debug')
            for selector in self.selectors.get('text_selectors', [
                'div[role="dialog"] span',
                'div[role="dialog"] div[dir="auto"] span',
                'div[role="dialog"] h1 ~ div span',
                'span[dir="auto"]'
            ]):
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            elem_text = elem.text
                            if elem_text and len(elem_text) > 3:  # 의미 있는 텍스트만
                                text += elem_text + " "
                                # 해시태그 추출
                                hashtag_matches = re.findall(r'#\w+', elem_text)
                                if hashtag_matches:
                                    hashtags.extend(hashtag_matches)
                        except Exception:
                            continue
                except Exception:
                    continue
        
        # 추가로 a 태그로 된 해시태그 찾기
        try:
            hashtag_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/explore/tags/"]')
            for link in hashtag_links:
                try:
                    tag_text = link.text
                    if tag_text and tag_text.startswith('#'):
                        hashtags.append(tag_text)
                except Exception:
                    continue
        except Exception as e:
            self.log(f"해시태그 링크 추출 중 오류: {str(e)}", 'debug')
        
        return text.strip(), list(set(hashtags))  # 중복 해시태그 제거
    
    def extract_numeric_value(self, text_pattern, all_spans):
        """특정 패턴을 포함하는 텍스트에서 숫자 값을 추출합니다."""
        value = ""
        
        for span in all_spans:
            try:
                text = span.text
                if text and any(pattern in text.lower() for pattern in text_pattern):
                    # 숫자 추출
                    numbers = re.findall(r'\d+[,\.]?\d*[KkMm]?', text)
                    if numbers:
                        value = numbers[0]
                        break
            except Exception:
                continue
        
        # K, M 단위 변환
        if value:
            try:
                if 'k' in value.lower():
                    value = float(value.lower().replace('k', '').replace(',', '')) * 1000
                elif 'm' in value.lower():
                    value = float(value.lower().replace('m', '').replace(',', '')) * 1000000
                elif ',' in value:
                    value = float(value.replace(',', ''))
            except Exception:
                pass  # 변환 실패시 원래 문자열 유지
        
        return value
    
    def extract_date(self):
        """게시물 날짜를 추출합니다."""
        try:
            # 모든 time 태그 찾기
            time_elements = self.driver.find_elements(By.TAG_NAME, 'time')
            
            for time_elem in time_elements:
                try:
                    date_attr = time_elem.get_attribute('datetime')
                    if date_attr:
                        return date_attr
                except Exception:
                    continue
            
            # 대체 방법: 'title' 속성에서 찾기
            time_elements = self.driver.find_elements(By.CSS_SELECTOR, '[title]')
            for elem in time_elements:
                try:
                    title_text = elem.get_attribute('title')
                    if title_text and len(title_text) > 5:
                        return title_text
                except Exception:
                    continue
        except Exception as e:
            self.log(f"날짜 추출 실패: {str(e)}", 'error')
        
        return ""
    
    def extract_image_url(self):
        """게시물 이미지 URL을 추출합니다."""
        try:
            # 모든 img 태그 찾기
            img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
            
            for img in img_elements:
                try:
                    src = img.get_attribute('src')
                    if src and ('scontent' in src or 'cdninstagram' in src):
                        return src
                except Exception:
                    continue
        except Exception as e:
            self.log(f"이미지 URL 추출 실패: {str(e)}", 'error')
        
        return ""
    
    def navigate_to_next_post(self):
        """다음 게시물로 이동합니다."""
        try:
            self.log("다음 게시물로 이동 시도...")
            
            # 모든 버튼 요소 찾기
            all_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            button_clicked = False
            
            # 다음 버튼 찾기
            for button in all_buttons:
                try:
                    text = button.text.lower()
                    aria_label = button.get_attribute('aria-label')
                    if (text and ('다음' in text or 'next' in text)) or \
                       (aria_label and ('다음' in aria_label or 'next' in aria_label.lower())):
                        button.click()
                        button_clicked = True
                        self.log("다음 버튼 찾아서 클릭함")
                        break
                except Exception:
                    continue
            
            # SVG 요소에서 찾기
            if not button_clicked:
                svg_elements = self.driver.find_elements(By.TAG_NAME, 'svg')
                for svg in svg_elements:
                    try:
                        aria_label = svg.get_attribute('aria-label')
                        if aria_label and ('다음' in aria_label or 'next' in aria_label.lower()):
                            # 부모 버튼 찾기
                            parent = svg
                            for _ in range(3):  # 최대 3단계 상위로 탐색
                                parent = parent.find_element(By.XPATH, '..')
                                if parent.tag_name == 'button':
                                    parent.click()
                                    button_clicked = True
                                    self.log("SVG 부모 버튼 찾아서 클릭함")
                                    break
                        if button_clicked:
                            break
                    except Exception:
                        continue
            
            # 오른쪽 영역 클릭 시도
            if not button_clicked:
                try:
                    dialog = self.driver.find_element(By.CSS_SELECTOR, 'div[role="dialog"]')
                    action = ActionChains(self.driver)
                    size = dialog.size
                    action.move_to_element_with_offset(dialog, size['width'] - 50, size['height'] // 2)
                    action.click()
                    action.perform()
                    button_clicked = True
                    self.log("오른쪽 영역 클릭 시도")
                except Exception as e:
                    self.log(f"오른쪽 영역 클릭 실패: {str(e)}", 'error')
            
            if not button_clicked:
                self.log("다음 버튼을 찾을 수 없습니다.", 'error')
                return False
            
            # 다음 게시물 로드 대기
            if self.rate_limiter:
                self.rate_limiter.wait()
            else:
                time.sleep(random.uniform(2, 4))
            
            return True
            
        except Exception as e:
            self.log(f"다음 게시물 이동 실패: {str(e)}", 'error')
            return False
    
    def close_post_dialog(self):
        """게시물 대화상자를 닫습니다."""
        try:
            self.log("게시물 대화상자 닫기 시도...")
            
            # 닫기 버튼 찾기
            close_buttons = []
            
            # SVG 요소에서 찾기
            svg_elements = self.driver.find_elements(By.TAG_NAME, 'svg')
            for svg in svg_elements:
                try:
                    aria_label = svg.get_attribute('aria-label')
                    if aria_label and ('닫기' in aria_label or 'close' in aria_label.lower()):
                        close_buttons.append(svg)
                except Exception:
                    continue
            
            # 모든 버튼에서 찾기
            all_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for button in all_buttons:
                try:
                    aria_label = button.get_attribute('aria-label')
                    if aria_label and ('닫기' in aria_label or 'close' in aria_label.lower()):
                        close_buttons.append(button)
                except Exception:
                    continue
            
            close_success = False
            for x_elem in close_buttons:
                try:
                    # 직접 클릭 또는 부모 버튼 클릭
                    try:
                        x_elem.click()
                        close_success = True
                        self.log("X 버튼 직접 클릭 성공")
                        break
                    except Exception:
                        # 부모 버튼 찾기
                        parent = x_elem
                        for _ in range(3):
                            try:
                                parent = parent.find_element(By.XPATH, '..')
                                if parent.tag_name == 'button':
                                    parent.click()
                                    close_success = True
                                    self.log("X 버튼 부모 클릭 성공")
                                    break
                            except Exception:
                                continue
                        if close_success:
                            break
                except Exception:
                    continue
            
            if not close_success:
                self.log("팝업 닫기 버튼을 찾을 수 없습니다. ESC 키 시도...", 'error')
                # ESC 키 시도
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log(f"팝업 닫기 실패: {str(e)}", 'error')
            return False
    
    def scrape_post(self):
        """현재 게시물의 데이터를 스크래핑합니다."""
        post_data = {
            'text': '',
            'hashtags': [],
            'likes': '',
            'comments': '',
            'date': '',
            'image_url': '',
            'video_views': ''
        }
        
        # 현재 팝업 창 캡처 (디버깅용)
        try:
            from datetime import datetime
            screenshot_path = f"debug/post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            self.log(f"게시물 팝업 스크린샷 저장: {screenshot_path}", 'debug')
            
            # 페이지 소스도 저장 (디버깅용)
            debug_html_path = f"debug/post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.log(f"페이지 소스 저장: {debug_html_path}", 'debug')
        except Exception as e:
            self.log(f"디버그 파일 저장 실패: {str(e)}", 'debug')
        
        # 팝업 내 모든 텍스트 요소 찾기
        try:
            all_spans = self.driver.find_elements(By.TAG_NAME, 'span')
            all_divs = self.driver.find_elements(By.TAG_NAME, 'div')
            all_sections = self.driver.find_elements(By.TAG_NAME, 'section')
            self.log(f"팝업 내 요소 수: span={len(all_spans)}, div={len(all_divs)}, section={len(all_sections)}", 'debug')
        except Exception:
            all_spans = []
            all_divs = []
            all_sections = []
        
        # 텍스트 및 해시태그 추출
        try:
            text, hashtags = self.extract_text_and_hashtags()
            post_data['text'] = text
            post_data['hashtags'] = hashtags
            self.log(f"텍스트 길이: {len(text)}, 해시태그: {len(hashtags)}개")
            if text:
                self.log(f"텍스트 샘플: {text[:100]}...")
        except Exception as e:
            self.log(f"텍스트/해시태그 추출 실패: {str(e)}", 'error')
        
        # 좋아요 수 추출 (개선된 방법)
        try:
            # 먼저 좋아요 섹션 찾기
            like_sections = self.driver.find_elements(By.CSS_SELECTOR, 'section')
            for section in like_sections:
                try:
                    section_text = section.text
                    if '좋아요' in section_text or 'like' in section_text.lower():
                        numbers = re.findall(r'\d+[,\.]?\d*[KkMm]?', section_text)
                        if numbers:
                            post_data['likes'] = self.convert_metric(numbers[0])
                            self.log(f"좋아요 수 찾음 (섹션): {post_data['likes']}")
                            break
                except Exception:
                    continue
            
            # 섹션에서 못 찾았으면 다른 방법 시도
            if not post_data['likes']:
                like_patterns = ['좋아요', '회', 'like']
                post_data['likes'] = self.extract_numeric_value(like_patterns, all_spans)
                if post_data['likes']:
                    self.log(f"좋아요 수 찾음 (span): {post_data['likes']}")
        except Exception as e:
            self.log(f"좋아요 수 추출 실패: {str(e)}", 'error')
        
        # 댓글 수 추출
        try:
            comment_patterns = ['댓글', 'comment']
            post_data['comments'] = self.extract_numeric_value(comment_patterns, all_spans)
            self.log(f"댓글: {post_data['comments']}")
        except Exception as e:
            self.log(f"댓글 수 추출 실패: {str(e)}", 'error')
        
        # 날짜 추출
        try:
            post_data['date'] = self.extract_date()
            self.log(f"날짜: {post_data['date']}")
        except Exception as e:
            self.log(f"날짜 추출 실패: {str(e)}", 'error')
        
        # 이미지 URL 추출
        try:
            post_data['image_url'] = self.extract_image_url()
            url_preview = post_data['image_url'][:30] + "..." if post_data['image_url'] else "없음"
            self.log(f"이미지 URL: {url_preview}")
        except Exception as e:
            self.log(f"이미지 URL 추출 실패: {str(e)}", 'error')
        
        # 동영상 조회수 추출
        try:
            view_patterns = ['조회', 'view']
            post_data['video_views'] = self.extract_numeric_value(view_patterns, all_spans)
            self.log(f"조회수: {post_data['video_views']}")
        except Exception as e:
            self.log(f"조회수 추출 실패: {str(e)}", 'error')
        
        return post_data

    def convert_metric(self, value_str):
        """K, M 등의 단위를 숫자로 변환합니다."""
        if not value_str:
            return ""
        
        try:
            value_str = value_str.strip()
            if 'k' in value_str.lower():
                return float(value_str.lower().replace('k', '').replace(',', '')) * 1000
            elif 'm' in value_str.lower():
                return float(value_str.lower().replace('m', '').replace(',', '')) * 1000000
            elif ',' in value_str:
                return float(value_str.replace(',', ''))
            elif value_str.isdigit():
                return float(value_str)
            return value_str
        except Exception:
            return value_str

    def search_hashtag(self, hashtag):
        """해시태그를 검색합니다."""
        try:
            self.log(f"해시태그 '{hashtag}' 검색 시작...")
            
            # 해시태그 URL로 직접 접근
            hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            self.log(f"URL로 접근: {hashtag_url}")
            self.driver.get(hashtag_url)
            
            # 페이지 로드 대기
            if self.rate_limiter:
                self.rate_limiter.wait()
            else:
                time.sleep(7)
            
            return True
        except Exception as e:
            self.log(f"해시태그 검색 실패: {str(e)}", 'error')
            return False
    
    def find_and_click_first_post(self):
        """첫 번째 게시물을 찾아 클릭합니다."""
        try:
            self.log("첫 번째 게시물 찾기...")
            
            # 여러 선택자 시도
            post_selectors = self.selectors.get('post_selectors', [
                'article div a', 
                'article a', 
                'div[role="presentation"] a',
                'a[href*="/p/"]'
            ])
            
            for selector in post_selectors:
                try:
                    posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if posts and len(posts) > 0:
                        self.log(f"게시물 링크 찾음: {selector} ({len(posts)}개)")
                        
                        # 첫 번째 게시물 클릭
                        posts[0].click()
                        self.log("첫 번째 게시물 클릭됨")
                        
                        # 게시물 로드 대기
                        if self.rate_limiter:
                            self.rate_limiter.wait()
                        else:
                            time.sleep(3)
                        
                        return True
                except Exception as e:
                    self.log(f"선택자 '{selector}'로 게시물 찾기 실패: {str(e)}", 'debug')
                    continue
            
            self.log("게시물을 찾을 수 없습니다.", 'error')
            return False
            
        except Exception as e:
            self.log(f"첫 번째 게시물 클릭 실패: {str(e)}", 'error')
            return False
    
    def scrape_hashtag_posts(self, hashtag, max_posts=5):
        """해시태그 검색 결과에서 게시물을 스크래핑합니다."""
        # 여기서 posts_data 변수를 초기화합니다
        posts_data = []
        
        if not self.search_hashtag(hashtag):
            return posts_data
        
        if not self.find_and_click_first_post():
            return posts_data
        
        # 게시물 데이터 수집
        for i in range(max_posts):
            if self.metrics:
                self.metrics.start_post()
            
            self.log(f"게시물 {i+1}/{max_posts} 스크래핑 중...")
            post_data = self.scrape_post()
            
            # 데이터 추가
            if post_data:
                posts_data.append(post_data)
                if self.metrics:
                    self.metrics.end_post(success=True, data=post_data)
            else:
                if self.metrics:
                    self.metrics.end_post(success=False)
            
            # 다음 게시물로 이동 (마지막 게시물이 아닌 경우)
            if i < max_posts - 1:
                if not self.navigate_to_next_post():
                    self.log(f"다음 게시물로 이동 실패. 현재까지 {len(posts_data)}개 수집됨", 'error')
                    break
        
        # 팝업 닫기
        self.close_post_dialog()
        
        return posts_data