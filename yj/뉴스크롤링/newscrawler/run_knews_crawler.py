# run_knews_crawler.py (한국섬유신문 1년치 기사 수집)
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import logging
import random
from utils import save_to_db
from config import KEYWORDS, MAX_RETRIES, RETRY_DELAY

# 상수 정의
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

# 날짜 범위 설정 - 1년치 데이터
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365)

def parse_knews_date(date_text):
    """한국섬유신문 발행일 파싱 - '승인 2025.03.27 18:32' 형식 지원"""
    try:
        # '승인' 텍스트가 포함된 날짜 형식 처리
        patterns = [
            r'승인\s+(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})',  # 승인 2025.03.26 15:33
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})',         # 2025.03.26 15:33
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})'            # 2025-03-26 15:33
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                year, month, day, hour, minute = map(int, match.groups())
                return datetime(year, month, day, hour, minute)
        
        # 로깅용: 날짜 텍스트 출력
        logging.debug(f"날짜 텍스트: '{date_text}'")
        logging.warning(f"날짜 형식 불일치: {date_text}")
    except ValueError as e:
        logging.error(f"날짜 파싱 오류: {date_text} - {e}")
    except Exception as e:
        logging.error(f"예상치 못한 오류: {date_text} - {e}")
    return None

def extract_knews_content(url, max_retries=3):
    """본문과 발행일 추출 (재시도 로직 포함)"""
    # User-Agent 다양화
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    headers = {"User-Agent": random.choice(user_agents)}
    
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "html.parser")

            # 본문 추출 개선 - 다양한 선택자 시도
            content_elem = soup.select_one("#article-view-content-div")
            if not content_elem:
                # 대체 선택자 시도
                content_elem = soup.select_one(".article-view-content") or \
                               soup.select_one(".article-body") or \
                               soup.select_one(".news-content")
                
            if not content_elem:
                logging.warning(f"본문 요소를 찾을 수 없음: {url}")
                return None, None

            # 광고 및 불필요한 요소 제거
            for tag in content_elem.select(".article-ad, .reporter, script, iframe, .article-copyright"):
                tag.decompose()

            # 전체 본문 내용 저장 - HTML 태그 제거하고 텍스트만 추출
            content = content_elem.get_text(strip=True, separator="\n").strip()
            
            # 충분한 본문 내용이 있는지 확인
            if not content or len(content) < 10:
                logging.warning(f"짧은 본문 내용: {url}")
            
            # 발행일 추출 개선 - 다양한 선택자 시도
            date_elem = soup.select_one(".sv-info .sv-date") or \
                        soup.select_one(".article_info .write_info") or \
                        soup.select_one(".info-text") or \
                        soup.select_one(".article-info") or \
                        soup.select_one(".view-info") or \
                        soup.select_one("[itemprop='datePublished']")

            date_text = ""
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # 날짜 텍스트 디버깅 출력
                logging.debug(f"추출된 날짜 텍스트: '{date_text}'")
            
            published = parse_knews_date(date_text)
            
            # 발행일을 파싱하지 못한 경우 로그 남기기
            if not published and date_text:
                logging.warning(f"발행일 파싱 실패: {date_text}")
            
            return content, published
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logging.warning(f"재시도 중 ({attempt+1}/{max_retries}): {url} - {e}")
                time.sleep(3 * (attempt + 1))  # 백오프 시간 증가
            else:
                logging.error(f"최대 재시도 횟수 초과: {url} - {e}")
        except Exception as e:
            logging.error(f"본문 추출 실패: {url} - {e}")
            break
            
    return None, None

def assign_keywords(title, content):
    """제목과 내용을 분석하여 적절한 키워드 할당"""
    from config import KEYWORDS
    
    # 소문자로 변환하여 비교
    title_lower = title.lower()
    content_lower = content.lower() if content else ""
    
    matched_keywords = []
    
    # 설정된 키워드 중에서 제목이나 내용에 포함된 키워드 찾기
    for keyword in KEYWORDS:
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower or keyword_lower in content_lower:
            matched_keywords.append(keyword)
    
    # 매칭된 키워드가 없으면 기본 키워드 "패션" 사용
    if not matched_keywords:
        return KEYWORDS[0]
    
    # 매칭된 키워드 중 첫 번째 키워드 반환 (또는 쉼표로 구분된 문자열로 반환)
    return matched_keywords[0]  # 또는 ", ".join(matched_keywords)

def is_within_date_range(published_date):
    """주어진 날짜가 설정된 범위 내에 있는지 확인"""
    if not published_date:
        return False
    return START_DATE <= published_date <= END_DATE

def crawl_knews(start_page=1, max_pages=500):
    """한국섬유신문 1년치 기사 크롤링"""
    source_name = "한국섬유신문"
    total_collected = 0
    total_saved = 0
    empty_pages = 0  # 연속 빈 페이지 카운터
    old_articles_count = 0  # 1년 이상 오래된 기사 카운터

    for page in range(start_page, start_page + max_pages):
        url = f"https://www.ktnews.com/news/articleList.html?page={page}"
        try:
            logging.info(f"페이지 수집 중: {page}")
            
            # 너무 많은 연속 요청 방지를 위한 임의 지연
            time.sleep(2 + random.random() * 2)  # 2-4초 랜덤 지연
            
            res = requests.get(url, headers=HEADERS)
            
            # 요청 상태 확인
            if res.status_code != 200:
                logging.error(f"페이지 요청 실패: 상태 코드 {res.status_code}")
                if res.status_code == 403:  # 접근 금지
                    logging.critical("접근이 차단되었을 수 있습니다. 30분 대기 후 재시도합니다.")
                    time.sleep(1800)  # 30분 대기
                    continue
                elif res.status_code == 429:  # Too Many Requests
                    logging.warning("요청이 너무 많습니다. 5분 대기 후 재시도합니다.")
                    time.sleep(300)  # 5분 대기
                    continue
                else:
                    # 기타 오류는 다음 페이지로 넘어감
                    continue

            soup = BeautifulSoup(res.text, "html.parser")
            
            # 다양한 선택자 시도
            articles = soup.select(".article-list a.article-title") or \
                    soup.select(".news-list a.article-title") or \
                    soup.select(".news-list-box a") or \
                    soup.select("a[href*='articleView']")
            
            if not articles:
                empty_pages += 1
                logging.warning(f"빈 페이지 감지: {page}")
                if empty_pages >= 3:  # 연속 3페이지가 비어있으면 종료
                    logging.info("연속 빈 페이지 감지로 크롤링 종료")
                    break
                continue
            else:
                empty_pages = 0  # 기사가 있으면 카운터 초기화
            
            # 오래된 기사 카운터 (페이지당)
            page_old_articles = 0
            
            for a in articles:
                link = a.get("href")
                # 링크가 상대 경로인 경우 처리
                if link and not link.startswith('http'):
                    link = "https://www.ktnews.com" + link
                
                title = a.get_text(strip=True)
                
                if not title or len(title) < 5:
                    logging.warning(f"유효하지 않은 제목: {link}")
                    continue
                    
                # 너무 많은 연속 요청 방지
                time.sleep(1 + random.random() * 2)  # 1-3초 랜덤 지연
                
                content, published = extract_knews_content(link)

                # 날짜 범위 확인
                if published and not is_within_date_range(published):
                    logging.info(f"범위 밖 기사 (너무 오래됨): {title} - {published}")
                    page_old_articles += 1
                    old_articles_count += 1
                    # 페이지의 50% 이상이 오래된 기사이면서 총 5개 이상 발견되면 크롤링 종료
                    if page_old_articles > len(articles) * 0.5 and old_articles_count >= 5:
                        logging.info("오래된 기사가 많아 크롤링을 종료합니다.")
                        return total_collected, total_saved
                    continue

                if content:
                    # 제목과 내용 기반으로 적절한 키워드 할당
                    keyword = assign_keywords(title, content)
                    
                    # 발행일이 없으면 현재 시간으로 대체
                    if published is None:
                        published = datetime.now()
                        logging.warning(f"발행일 없음, 현재 시간으로 대체: {link}")
                    
                    data = (keyword, title, link, published, source_name, content)
                    
                    if save_to_db(data, table_name="knews_articles"):
                        total_saved += 1
                        logging.info(f"저장 성공: {title}")
                    else:
                        logging.warning(f"저장 실패: {title}")
                        
                    total_collected += 1
                else:
                    logging.warning(f"본문 추출 실패: {title} ({link})")

            # 페이지 간 간격
            logging.info(f"페이지 {page} 완료 - 수집: {total_collected}, 저장: {total_saved}")
            time.sleep(3 + random.random() * 2)  # 페이지 간 3-5초 랜덤 지연

        except Exception as e:
            logging.error(f"페이지 {page} 처리 중 오류: {e}")
            time.sleep(10)  # 오류 발생 시 10초 대기
            continue

    logging.info(f"크롤링 완료 - 총 수집: {total_collected}, 총 저장: {total_saved}")
    return total_collected, total_saved


if __name__ == "__main__":
    import logging.config
    from config import LOGGING_CONFIG
    
    # 로깅 설정
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 시작 메시지
    logging.info(f"=== 한국섬유신문 1년치 기사 크롤링 시작 ({START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}) ===")
    
    # 크롤링 실행
    collected, saved = crawl_knews()
    
    # 종료 메시지
    logging.info(f"=== 크롤링 완료 - 총 수집 기사: {collected}, 저장된 기사: {saved} ===")
    print(f"총 수집 기사: {collected}, 저장된 기사: {saved}")