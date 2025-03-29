import time
import json
import random
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from datetime import datetime

class MusinsaCrawler:
    def __init__(self, headless=True, output_dir="/Users/jiyeonjoo/Desktop/최종 플젝"):
        """무신사 크롤러 초기화"""
        self.setup_browser(headless)
        self.products = []
        self.output_dir = output_dir
        
        # 디렉토리 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 카테고리 정의
        self.categories = {
            '001': '상의',
            '002': '아우터',
            '003': '바지',
            '020': '원피스',
            '022': '스커트',
            '004': '가방',
            '005': '신발',
            '006': '액세서리',
            '017': '스포츠/용품'
        }
        
        # 수집된 제품 ID 추적
        self.collected_ids = set()
        
    def setup_browser(self, headless):
        """브라우저 설정"""
        options = Options()
        if headless:
            options.add_argument('--headless=new')
        
        # 기본 설정
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        
        # 창 크기 설정
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        self.driver.set_page_load_timeout(30)
        
        # 1. clean_gender_text 메서드 수정
    def clean_gender_text(self, text):
        """성별 정보 정제 - 남/여만 깔끔하게 추출"""
        if not text or text == 'N/A':
            return 'N/A'
            
        # 간결하게 남/여 정보만 반환
        if '남' in text and '여' in text:
            return '남/여'
        elif '남' in text:
            return '남'
        elif '여' in text:
            return '여'
        else:
            return 'N/A'

    # 2. clean_season_text 메서드 수정  
    def clean_season_text(self, text):
        """시즌 정보 정제 - 연도와 SS/FW 형식만 추출"""
        if not text or text == 'N/A':
            return 'N/A'
            
        # 연도와 시즌 패턴 추출 (2023 SS, 2024 FW 등)
        season_pattern = re.search(r'(20\d{2})\s*(SS|FW)', text)
        if season_pattern:
            return f"{season_pattern.group(1)} {season_pattern.group(2)}"
            
        # SS나 FW만 있는 경우는 제외하고 N/A 반환
        return 'N/A'

            
    def get_product_info(self, link, category_code):
        """상품 상세 정보 수집 (단일 상품)"""
        try:
            # 상품 페이지 접속
            self.driver.get(link)
            time.sleep(2)
            
            # 상품 ID 추출
            product_id = link.split('/products/')[-1].split('?')[0].split('#')[0]
            
            # 카테고리 정보 설정
            category_name = self.categories.get(category_code, '기타')
            
            # 기본 정보 초기화
            product = {
                'product_id': int(product_id),
                'link': link,
                'brand': 'N/A',
                'name': 'N/A',
                'price': 'N/A',
                'category': category_name,
                'category_code': category_code,
                'rating': 0,
                'review_count': 0,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'gender': 'N/A',
                'season': 'N/A',
                'views': 0
            }
            
            # 1. 상세 페이지에서 카테고리 경로 직접 추출
            try:
                breadcrumb_selectors = [
                    ".location_category_path", ".item_categories", ".location", 
                    ".breadcrumb", ".navi_path", "ul.location_list"
                ]
                
                for selector in breadcrumb_selectors:
                    try:
                        breadcrumb = self.driver.find_element(By.CSS_SELECTOR, selector)
                        breadcrumb_text = breadcrumb.text
                        
                        # 경로에서 카테고리 추출
                        if '>' in breadcrumb_text:
                            categories = breadcrumb_text.split('>')
                            if len(categories) > 1:
                                main_category = categories[1].strip()
                                product['category'] = main_category
                                break
                    except:
                        continue
            except:
                pass
            
            # 2. 상품명 추출
            try:
                name_selectors = [
                    'h2.product_title, h1.product_title', 
                    '.product_title, .item-title', 
                    'title',
                    'meta[property="og:title"]'
                ]
                
                for selector in name_selectors:
                    try:
                        if 'meta' in selector:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            name_value = element.get_attribute('content')
                        elif selector == 'title':
                            name_value = self.driver.title
                            if '|' in name_value:
                                name_value = name_value.split('|')[0].strip()
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            name_value = element.text.strip()
                        
                        if name_value and name_value != 'N/A':
                            product['name'] = name_value
                            break
                    except:
                        continue
            except:
                pass
            
            # 3. 브랜드명 추출
            try:
                brand_selectors = [
                    'div.brand_name a', 'p.product_article_contents a', 
                    '.brand_title a', 'a.product_article_info', 
                    '.product-brand', '.brand-name',
                    'span.product_article_info'
                ]
                
                for selector in brand_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        brand_value = element.text.strip()
                        
                        if brand_value and brand_value != 'N/A':
                            product['brand'] = brand_value
                            break
                    except:
                        continue
            except:
                pass
            
            # 4. 가격 정보 추출
            try:
                price_selectors = [
                    '.price', '.product-price', '.sale_price', 
                    '.discountPrice', '.item_price', 'span.num', 
                    'p.price'
                ]
                
                for selector in price_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        price_value = element.text.strip()
                        
                        # 숫자만 추출
                        nums = re.findall(r'\d+', price_value.replace(',', ''))
                        if nums:
                            price_num = int(''.join(nums))
                            product['price'] = f"{price_num:,}원"
                            break
                    except:
                        continue
            except:
                pass
            
            # 5. JSON-LD 데이터에서 추가 정보 추출 (찾지 못한 정보 보완)
            try:
                json_ld_elements = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                
                for element in json_ld_elements:
                    try:
                        json_content = element.get_attribute('textContent')
                        json_data = json.loads(json_content)
                        
                        # 브랜드 추출 (아직 찾지 못했다면)
                        if product['brand'] == 'N/A' and 'brand' in json_data:
                            if isinstance(json_data['brand'], dict) and 'name' in json_data['brand']:
                                product['brand'] = json_data['brand']['name']
                        
                        # 상품명 추출 (아직 찾지 못했다면)
                        if product['name'] == 'N/A' and 'name' in json_data:
                            product['name'] = json_data['name']
                        
                        # 가격 정보 추출 (아직 찾지 못했다면)
                        if product['price'] == 'N/A':
                            if 'offers' in json_data:
                                offers_data = json_data['offers']
                                if isinstance(offers_data, dict) and 'price' in offers_data:
                                    price = offers_data['price']
                                    if isinstance(price, (int, float)):
                                        product['price'] = f"{int(price):,}원"
                                    else:
                                        product['price'] = f"{price}원"
                            elif 'goodsPrice' in json_data:
                                goods_price = json_data['goodsPrice']
                                if isinstance(goods_price, dict):
                                    if 'originPrice' in goods_price:
                                        product['price'] = f"{goods_price['originPrice']:,}원"
                        
                        # 리뷰 및 평점 추출
                        if 'aggregateRating' in json_data:
                            rating_data = json_data['aggregateRating']
                            if 'ratingValue' in rating_data:
                                product['rating'] = float(rating_data['ratingValue'])
                            if 'reviewCount' in rating_data:
                                product['review_count'] = int(rating_data['reviewCount'])
                    except:
                        continue
            except:
                pass

            # 6. 성별 및 시즌 정보 개선된 추출 방식
            try:
                # 방법 1: 상세 정보 테이블에서 찾기
                detail_rows = self.driver.find_elements(By.CSS_SELECTOR, "dl.sc-1fwcs34-0, .product_article, .product-table tr, .article-detail-spec dl")
                
                for element in detail_rows:
                    try:
                        text = element.text
                        
                        # 성별 정보 추출
                        # 4. get_product_info 메서드 내 성별/시즌 추출 로직 수정
                        # 이 부분을 get_product_info 메서드 내에서 찾아 수정:

                        # 성별 정보 추출
                        if "성별" in text:
                            gender_text = text.split("성별")[-1].strip()
                            product['gender'] = self.clean_gender_text(gender_text)
                            
                        # 시즌 정보 추출
                        if "시즌" in text:
                            season_text = text.split("시즌")[-1].strip()
                            product['season'] = self.clean_season_text(season_text)
                            
                        # 조회수 정보
                        if "조회수" in text:
                            view_text = text.split("조회수")[-1].strip()
                            match = re.search(r'([\d\.]+)천', view_text)
                            if match:
                                product['views'] = int(float(match.group(1)) * 1000)
                            else:
                                nums = re.findall(r'\d+', view_text)
                                if nums:
                                    product['views'] = int(''.join(nums))
                    except:
                        continue
                
                # 방법 2: 직접적인 성별/시즌 정보 요소 찾기
                if product['gender'] == 'N/A':
                    gender_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product-info-gender, .gender, .item-gender")
                    for el in gender_elements:
                        try:
                            gender_text = el.text.strip()
                            if gender_text:
                                product['gender'] = self.clean_gender_text(gender_text)
                                break
                        except:
                            continue
                
                if product['season'] == 'N/A':
                    season_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product-info-season, .season, .item-season")
                    for el in season_elements:
                        try:
                            season_text = el.text.strip()
                            if season_text:
                                product['season'] = self.clean_season_text(season_text)
                                break
                        except:
                            continue
            except:
                pass

            return product
            
        except Exception as e:
            print(f"상품 정보 수집 중 오류: {e}")
            
            # 최소한의 정보만 반환
            return {
                'product_id': int(product_id) if 'product_id' in locals() else 0,
                'link': link,
                'brand': 'N/A',
                'name': 'N/A',
                'price': 'N/A',
                'category': self.categories.get(category_code, '기타'),
                'category_code': category_code,
                'rating': 0,
                'review_count': 0,
                'error': str(e),
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_category_products(self, category_code, max_items=20):
        """특정 카테고리에서 상품 수집 (순차 처리)"""
        category_name = self.categories.get(category_code, '카테고리')
        print(f"{category_name}({category_code}) 카테고리 수집 시작...")
        
        products_info = []
        
        try:
            # 카테고리 페이지 접속
            url = f"https://www.musinsa.com/category/{category_code}?gf=A"
            print(f"URL 접속: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # 쿠키 동의 버튼 클릭 (있는 경우)
            try:
                cookie_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-cookie-accept")))
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # 스크롤 5번 수행 (더 많은 상품 로드)
            for i in range(5):
                print(f"스크롤 {i+1}/5 수행 중...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 더보기 버튼 클릭 시도
                try:
                    load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".more-btn, .btn-more, [data-more], .btn-goods-more")
                    if load_more_buttons:
                        for btn in load_more_buttons:
                            if btn.is_displayed():
                                btn.click()
                                print("더보기 버튼 클릭")
                                time.sleep(2)
                                break
                except:
                    pass
            
            # 상품 링크 수집
            all_links = []
            
            # 모든 링크 검색
            all_a_tags = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in all_a_tags:
                try:
                    href = link.get_attribute('href')
                    if href and '/products/' in href:
                        product_id = href.split('/products/')[-1].split('?')[0].split('#')[0]
                        if product_id.isdigit() and product_id not in self.collected_ids:
                            all_links.append(href)
                except:
                    continue
            
            # 중복 제거 및 최대 개수 제한
            unique_links = list(set(all_links))[:max_items]
            print(f"총 {len(unique_links)}개 상품 링크 수집 완료")
            
            # 각 상품 정보 순차적으로 수집
            for i, link in enumerate(unique_links):
                print(f"상품 {i+1}/{len(unique_links)} 정보 수집 중...")
                product_info = self.get_product_info(link, category_code)
                
                # 제품 ID 추출
                product_id = link.split('/products/')[-1].split('?')[0].split('#')[0]
                
                if product_info:
                    products_info.append(product_info)
                    self.collected_ids.add(product_id)
                
                # 요청 간격 조절 (랜덤)
                time.sleep(random.uniform(0.5, 1.5))
            
            print(f"{category_name} 카테고리에서 총 {len(products_info)}개 상품 정보 수집 완료")
            return products_info
            
        except Exception as e:
            print(f"카테고리 {category_code} 처리 중 오류: {e}")
            return products_info
    
    def crawl_all_categories(self, items_per_category=20, total_target=100):
        """모든 카테고리에서 균등하게 상품 수집"""
        start_time = datetime.now()
        print(f"크롤링 시작: {start_time}")
        
        # 전체 카테고리 목록
        all_categories = list(self.categories.keys())
        random.shuffle(all_categories)  # 카테고리 순서를 랜덤하게 섞어서 다양한 카테고리 수집
        
        # 카테고리당 수집할 상품 수 계산
        num_categories = len(all_categories)
        items_per_cat = max(1, min(items_per_category, total_target // num_categories))
        
        print(f"총 {num_categories}개 카테고리에서 카테고리당 약 {items_per_cat}개씩, 총 {total_target}개 목표로 수집합니다.")
        
        total_collected = 0
        
        # 모든 카테고리를 순회하며 수집
        for code in all_categories:
            try:
                category_name = self.categories.get(code)
                print(f"\n===== {category_name} 카테고리 크롤링 시작 =====")
                
                # 남은 목표 수량 계산
                remaining_target = total_target - total_collected
                if remaining_target <= 0:
                    print(f"목표 수량 {total_target}개를 달성했습니다. 크롤링을 종료합니다.")
                    break
                
                # 현재 카테고리에서 수집할 상품 수 결정
                current_target = min(items_per_cat, remaining_target)
                category_products = self.get_category_products(code, current_target)
                
                # 수집된 상품 추가
                self.products.extend(category_products)
                total_collected += len(category_products)
                
                print(f"{category_name} 카테고리 완료 (현재까지 총 {total_collected}/{total_target}개 상품)")
                
                # 크롤링 결과 중간 저장
                self.save_to_csv(f"musinsa_progress_{code}.csv")
                
                # 카테고리 간 전환 시 대기
                time.sleep(random.uniform(2, 4))
                
                # 목표 달성 시 종료
                if total_collected >= total_target:
                    print(f"목표 수량 {total_target}개를 달성했습니다. 크롤링을 종료합니다.")
                    break
                
            except Exception as e:
                print(f"{self.categories.get(code)} 카테고리 처리 중 오류: {e}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n전체 크롤링 완료: {end_time} (소요시간: {duration})")
        print(f"총 {len(self.products)}개 상품 수집됨")
        
        # 최종 결과 저장
        final_path = self.save_to_csv()
        
        return final_path
    
    
    def save_to_csv(self, filename=None):
        """수집한 데이터를 CSV로 저장"""
        if not self.products:
            print("저장할 데이터가 없습니다.")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"musinsa_products_{timestamp}.csv"
        
        # 전체 경로 생성
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 데이터프레임 생성
            df = pd.DataFrame(self.products)
            
            # 컬럼 순서 정리
            columns = ['product_id', 'brand', 'name', 'price', 'category', 'category_code', 
        'rating', 'review_count', 'views', 'link', 'crawled_at', 'gender', 'season']
            
            # 존재하는 컬럼만 선택
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            # 최종 정리: 성별과 시즌 정보 최종 정제
            if 'gender' in df.columns:
                df['gender'] = df['gender'].apply(lambda x: self.clean_gender_text(x) if isinstance(x, str) else x)
                
            if 'season' in df.columns:
                df['season'] = df['season'].apply(lambda x: self.clean_season_text(x) if isinstance(x, str) else x)
            
            # CSV 저장
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"데이터가 {filepath} 파일로 저장되었습니다. (총 {len(df)}개 행)")
            
            # 카테고리별 통계
            if 'category' in df.columns:
                category_stats = df['category'].value_counts()
                print("\n===== 카테고리별 상품 수 =====")
                for category, count in category_stats.items():
                    print(f"{category}: {count}개")
                
            return filepath
        except Exception as e:
            print(f"CSV 저장 중 오류: {e}")
            return None


    def close(self):
        """브라우저 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("브라우저 세션 종료")


# 실행 코드
if __name__ == "__main__":
    try:
        # 결과 저장 경로 설정
        output_directory = "/Users/jiyeonjoo/Desktop/lastproject"
        
        # 크롤러 초기화
        crawler = MusinsaCrawler(headless=False, output_dir=output_directory)
        
        # 모든 카테고리에서 총 100개 이상의 상품 수집
        # - 카테고리당 최대 15개씩
        # - 총 목표 120개 (여유있게 설정)
        crawler.crawl_all_categories(items_per_category=150, total_target=1000)
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
    finally:
        # 브라우저 종료
        if 'crawler' in locals():
            crawler.close()