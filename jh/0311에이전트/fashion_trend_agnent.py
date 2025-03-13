import schedule
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import mysql.connector
import logging
import sys
import re
from config import DB_PATH, CRAWL_TIME, URLS, HEADERS, LOG_CONFIG, MYSQL_CONFIG

# 로깅 설정 수정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 파일 핸들러
file_handler = logging.FileHandler(LOG_CONFIG['filename'])
file_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
logger.addHandler(file_handler)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(console_handler)

class DatabaseConnection:
    def __init__(self):
        self.config = MYSQL_CONFIG

    def __enter__(self):
        self.conn = mysql.connector.connect(**self.config)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

class FashionTrendCrawler:
    def __init__(self):
        self.headers = HEADERS
        self.setup_database()

    def setup_database(self):
        """데이터베이스 및 테이블 설정"""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                tables = ['vogue', 'wkorea', 'jentestore', 'wwdkorea', 'marieclaire']
                
                for table in tables:
                    cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table}_trends (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        scraping_date VARCHAR(10),
                        upload_date VARCHAR(10),
                        editor VARCHAR(100),
                        title TEXT,
                        content TEXT,
                        article_url VARCHAR(255) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    ''')
                conn.commit()
                logging.info("데이터베이스 설정 완료")
        except Exception as e:
            logging.error(f"데이터베이스 설정 오류: {str(e)}")

    def save_to_db(self, data_df, table_name):
        """데이터프레임을 DB에 저장"""
        try:
            with DatabaseConnection() as conn:
                data_df = data_df.rename(columns={
                    '스크래핑 날짜': 'scraping_date',
                    '업로드 날짜': 'upload_date',
                    '에디터': 'editor',
                    '제목': 'title',
                    '본문': 'content',
                    '기사 URL': 'article_url'
                })

                # MySQL용 INSERT 구문으로 변환
                for _, row in data_df.iterrows():
                    sql = f'''
                    INSERT IGNORE INTO {table_name}_trends 
                    (scraping_date, upload_date, editor, title, content, article_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    '''
                    values = (
                        row['scraping_date'],
                        row['upload_date'],
                        row['editor'],
                        row['title'],
                        row['content'],
                        row['article_url']
                    )
                    cursor = conn.cursor()
                    cursor.execute(sql, values)
                
                conn.commit()
                logging.info(f"{table_name} 데이터 저장 완료")
        except Exception as e:
            logging.error(f"{table_name} 데이터 저장 오류: {str(e)}")

    def crawl_vogue(self):
        """보그 크롤링"""
        try:
            main_url = URLS['vogue']
            article_links = []
            
            response = requests.get(main_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "lxml")
            
            for a_tag in soup.select("a[href^='/2025']"):
                article_url = "https://www.vogue.co.kr" + a_tag["href"]
                if article_url not in article_links:
                    article_links.append(article_url)
            
            data = []
            scrape_date = datetime.today().strftime("%Y.%m.%d")
            
            for url in article_links:
                try:
                    response = requests.get(url, headers=self.headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "제목 없음"
                        
                        paragraphs = soup.find_all("p")
                        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                        
                        lines = content.split("\n")
                        if len(lines) > 1:
                            upload_date = lines[1].strip()
                            content = "\n".join(lines[2:]).strip()
                        else:
                            upload_date = "날짜 없음"
                            content = ""
                        
                        pattern = r"(패션 뉴스|패션 트렌드|패션 아이템|여행|셀러브리티 스타일|웰니스|뷰 포인트)\n\d{4}\.\d{2}\.\d{2}by\s*[가-힣]+.*"
                        content = re.sub(pattern, "", content, flags=re.DOTALL).strip()
                        
                        data.append({
                            "스크래핑 날짜": scrape_date,
                            "업로드 날짜": upload_date,
                            "에디터": "Vogue",
                            "제목": title,
                            "본문": content,
                            "기사 URL": url
                        })
                        
                except Exception as e:
                    logging.error(f"보그 기사 크롤링 오류 ({url}): {str(e)}")
            
            df = pd.DataFrame(data)
            self.save_to_db(df, 'vogue')
            logging.info("보그 크롤링 완료")
            
        except Exception as e:
            logging.error(f"보그 크롤링 오류: {str(e)}")

    def crawl_wkorea(self):
        """더블유 코리아 크롤링"""
        try:
            main_url = URLS['wkorea']
            article_data = []
            
            response = requests.get(main_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "lxml")
            
            for article in soup.select("li"):
                a_tag = article.select_one("a[href^='https://www.wkorea.com/2025']")
                if not a_tag:
                    continue
                
                article_url = a_tag["href"]
                title_tag = article.select_one("h3.s_tit")
                title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
                article_data.append({"제목": title, "기사 URL": article_url})
            
            data = []
            scrape_date = datetime.today().strftime("%Y.%m.%d")
            
            for article in article_data:
                try:
                    response = requests.get(article["기사 URL"], headers=self.headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        paragraphs = soup.find_all("p")
                        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                        
                        lines = content.split("\n")
                        if len(lines) > 1:
                            upload_date_match = re.match(r"W Fashion\s*(\d{4}\.\d{2}\.\d{2})", lines[0])
                            upload_date = upload_date_match.group(1) if upload_date_match else "날짜 없음"
                            editor = lines[1].strip()
                        else:
                            upload_date = "날짜 없음"
                            editor = "미상"
                        
                        content = "\n".join(lines[2:]).strip() if len(lines) > 2 else ""
                        
                        data.append({
                            "스크래핑 날짜": scrape_date,
                            "업로드 날짜": upload_date,
                            "에디터": editor,
                            "제목": article["제목"],
                            "본문": content,
                            "기사 URL": article["기사 URL"]
                        })
                        
                except Exception as e:
                    logging.error(f"더블유 코리아 기사 크롤링 오류 ({article['기사 URL']}): {str(e)}")
            
            df = pd.DataFrame(data)
            self.save_to_db(df, 'wkorea')
            logging.info("더블유 코리아 크롤링 완료")
            
        except Exception as e:
            logging.error(f"더블유 코리아 크롤링 오류: {str(e)}")

    def crawl_jentestore(self):
        """젠테 스토어 크롤링"""
        try:
            main_url = URLS['jentestore']
            article_links = []
            
            response = requests.get(main_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "lxml")
            
            for a_tag in soup.select("a[href^='/promotion/event_view?no=']"):
                article_url = "https://jentestore.com" + a_tag["href"]
                if article_url not in article_links:
                    article_links.append(article_url)
                if len(article_links) >= 30:
                    break
            
            data = []
            scrape_date = datetime.today().strftime("%Y.%m.%d")
            
            for url in article_links:
                try:
                    response = requests.get(url, headers=self.headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        paragraphs = soup.find_all("p")
                        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                        
                        lines = content.split("\n")
                        if len(lines) > 1:
                            title = f"{lines[0]}: {lines[1]}"
                        else:
                            title = "제목 없음"
                        
                        content = "\n".join(lines[3:]).strip() if len(lines) > 3 else ""
                        
                        editor_match = re.search(r"에디터:\s*([가-힣]+)", content)
                        editor = editor_match.group(1) if editor_match else "Jente Store"
                        
                        content = re.split(r"에디터:\s*[가-힣]+", content, maxsplit=1)[0].strip()
                        
                        data.append({
                            "스크래핑 날짜": scrape_date,
                            "업로드 날짜": datetime.today().strftime("%Y.%m.%d"),
                            "에디터": editor,
                            "제목": title,
                            "본문": content,
                            "기사 URL": url
                        })
                        
                except Exception as e:
                    logging.error(f"젠테 스토어 기사 크롤링 오류 ({url}): {str(e)}")
            
            df = pd.DataFrame(data)
            self.save_to_db(df, 'jentestore')
            logging.info("젠테 스토어 크롤링 완료")
            
        except Exception as e:
            logging.error(f"젠테 스토어 크롤링 오류: {str(e)}")

    def crawl_wwdkorea(self):
        """WWD 코리아 크롤링"""
        try:
            main_url = URLS['wwdkorea']
            article_data = []
            
            response = requests.get(main_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "lxml")
            
            for article in soup.select("li div.views"):
                a_tag = article.select_one("h4.titles a[href^='/news/articleView.html?idxno=']")
                if not a_tag:
                    continue
                
                article_url = "https://www.wwdkorea.com" + a_tag["href"]
                title = a_tag.get_text(strip=True)
                
                date_tag = article.select_one("em.info.dated")
                upload_date = date_tag.get_text(strip=True) if date_tag else "날짜 없음"
                
                editor_tag = article.select_one("em.info.name")
                editor = editor_tag.get_text(strip=True).replace(" 에디터", "") if editor_tag else "미상"
                
                article_data.append({
                    "제목": title,
                    "기사 URL": article_url,
                    "업로드 날짜": upload_date,
                    "에디터": editor
                })
                
                if len(article_data) >= 30:
                    break
            
            data = []
            scrape_date = datetime.today().strftime("%Y.%m.%d")
            
            for article in article_data:
                try:
                    response = requests.get(article["기사 URL"], headers=self.headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        paragraphs = soup.find_all("p")
                        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                        
                        content = re.split(r"<더블유더블유디코리아>(가|의)", content, maxsplit=1)[0].strip()
                        
                        data.append({
                            "스크래핑 날짜": scrape_date,
                            "업로드 날짜": article["업로드 날짜"],
                            "에디터": article["에디터"],
                            "제목": article["제목"],
                            "본문": content,
                            "기사 URL": article["기사 URL"]
                        })
                        
                except Exception as e:
                    logging.error(f"WWD 코리아 기사 크롤링 오류 ({article['기사 URL']}): {str(e)}")
            
            df = pd.DataFrame(data)
            self.save_to_db(df, 'wwdkorea')
            logging.info("WWD 코리아 크롤링 완료")
            
        except Exception as e:
            logging.error(f"WWD 코리아 크롤링 오류: {str(e)}")

    def crawl_marieclaire(self):
        """마리끌레르 크롤링"""
        try:
            main_url = URLS['marieclaire']
            article_data = []
            
            response = requests.get(main_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "lxml")
            
            for article in soup.select("h2.entry-title a"):
                article_url = article["href"]
                title = article.get_text(strip=True)
                
                article_data.append({
                    "제목": title,
                    "기사 URL": article_url
                })
                
                if len(article_data) >= 30:
                    break
            
            data = []
            scrape_date = datetime.today().strftime("%Y.%m.%d")
            
            for article in article_data:
                try:
                    response = requests.get(article["기사 URL"], headers=self.headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        
                        date_tag = soup.select_one("span.updated.rich-snippet-hidden")
                        upload_date = date_tag.get_text(strip=True)[:10].replace("-", ".") if date_tag else "날짜 없음"
                        
                        editor_tag = soup.select_one("span.fn a")
                        editor = editor_tag.get_text(strip=True) if editor_tag else "미상"
                        
                        excerpt_tag = soup.select_one("div.mck_post_excerpt")
                        excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ""
                        
                        paragraphs = soup.select("div.post-content p")
                        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                        
                        full_content = f"{excerpt}\n{content}".strip()
                        
                        data.append({
                            "스크래핑 날짜": scrape_date,
                            "업로드 날짜": upload_date,
                            "에디터": editor,
                            "제목": article["제목"],
                            "본문": full_content,
                            "기사 URL": article["기사 URL"]
                        })
                        
                except Exception as e:
                    logging.error(f"마리끌레르 기사 크롤링 오류 ({article['기사 URL']}): {str(e)}")
            
            df = pd.DataFrame(data)
            self.save_to_db(df, 'marieclaire')
            logging.info("마리끌레르 크롤링 완료")
            
        except Exception as e:
            logging.error(f"마리끌레르 크롤링 오류: {str(e)}")

    def run_all_crawlers(self):
        """모든 크롤러 실행"""
        print("\n=== 크롤링 작업 시작 ===")
        logging.info("크롤링 작업 시작")
        
        for crawler in ['vogue', 'wkorea', 'jentestore', 'wwdkorea', 'marieclaire']:
            print(f"\n>>> {crawler} 크롤링 시작...")
            getattr(self, f'crawl_{crawler}')()
            
        print("\n=== 크롤링 작업 완료 ===")
        logging.info("크롤링 작업 완료")

def main():
    crawler = FashionTrendCrawler()
    
    print(f"\n스케줄러 시작 - 매일 {CRAWL_TIME}에 실행됩니다.")
    schedule.every().day.at(CRAWL_TIME).do(crawler.run_all_crawlers)
    
    # 즉시 첫 실행
    crawler.run_all_crawlers()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()