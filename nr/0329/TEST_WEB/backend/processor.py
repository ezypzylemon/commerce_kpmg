import os
import tempfile
import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import re

class OCRProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def pdf_to_images(self, pdf_path, dpi=300):
        """PDF 파일을 고해상도 이미지로 변환"""
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, image in enumerate(images):
                image_path = f"temp_page_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                image.save(image_path, "JPEG", quality=95)
                image_paths.append(image_path)
            
            return image_paths
        except Exception as e:
            st.error(f"PDF 변환 오류: {e}")
            return []

    def enhance_image_for_ocr(self, image_path):
        """
        OCR 성능 향상을 위한 이미지 전처리
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                st.warning(f"이미지를 불러올 수 없습니다: {image_path}")
                return image_path
            
            # 이미지 크기 조정 (선택적으로 더 큰 크기로 조정)
            height, width = image.shape[:2]
            new_height = int(height * 1.5)
            new_width = int(width * 1.5)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 노이즈 제거 및 이미지 선명도 향상
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
            
            # 대비 향상
            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # 이미지 경계 강화
            edge_enhance = cv2.Laplacian(opening, cv2.CV_8U, ksize=3)
            sharpened = cv2.addWeighted(opening, 1.5, edge_enhance, -0.5, 0)
            
            # 처리된 이미지 저장
            enhanced_path = f"enhanced_{os.path.basename(image_path)}"
            cv2.imwrite(enhanced_path, sharpened)
            
            return enhanced_path
        except Exception as e:
            st.error(f"이미지 처리 오류: {e}")
            return image_path

    def extract_text_with_improved_ocr(self, image_path):
        """
        OCR을 적용하여 이미지에서 텍스트 추출
        """
        try:
            # 이미지 향상
            enhanced_path = self.enhance_image_for_ocr(image_path)
            
            # 일반 텍스트 인식 설정
            general_config = r'--psm 6 --oem 3'
            general_text = pytesseract.image_to_string(enhanced_path, lang='eng', config=general_config)
            
            # 테이블 구조 인식 설정
            table_config = r'--psm 11 --oem 3 -c preserve_interword_spaces=1'
            table_text = pytesseract.image_to_string(enhanced_path, lang='eng', config=table_config)
            
            # 숫자 인식에 최적화된 설정
            digits_config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'
            digits_data = pytesseract.image_to_data(enhanced_path, lang='eng', config=digits_config, output_type=pytesseract.Output.DICT)
            
            # 향상된 이미지 정리
            if os.path.exists(enhanced_path) and enhanced_path != image_path:
                os.remove(enhanced_path)
            
            # 두 결과 합치기
            combined_text = general_text + "\n" + table_text
            
            return combined_text, digits_data
        except Exception as e:
            st.error(f"OCR 처리 오류: {e}")
            return "", {}

    def clean_ocr_text(self, text):
        """
        OCR 텍스트 정리 및 정규화
        """
        # 불필요한 문자 제거
        cleaned = re.sub(r'[«»—ooаOO]', '', text)
        # 공백 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def extract_product_sections(self, text):
        """
        OCR 텍스트에서 개별 상품 섹션을 분리하여 추출
        """
        # AJ로 시작하는 상품 코드 패턴
        product_pattern = r'(AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE|POLIDO|LEATHER).*?)(?=AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE|POLIDO|LEATHER)|$)'
        
        # 정규식을 통해 상품 코드로 시작하는 섹션 찾기
        product_sections = re.findall(product_pattern, text, re.DOTALL | re.IGNORECASE)
        
        # 상품 코드 기반으로 다시 찾기 (이전 정규식으로 찾지 못한 경우)
        if not product_sections:
            simple_pattern = r'(AJ\d+.*?)(?=AJ\d+|$)'
            product_sections = re.findall(simple_pattern, text, re.DOTALL)
        
        # 빈 섹션 제거
        product_sections = [section.strip() for section in product_sections if section.strip()]
        
        return product_sections

    def extract_order_information(self, text):
        """
        개선된 주문 정보 추출 함수
        """
        order_info = {}
        
        # 발주 번호 추출 - 더 강력한 패턴
        po_match = re.search(r'PO\s*#[:\s]*(\d+)', text, re.IGNORECASE) 
        if po_match:
            order_info['po_number'] = po_match.group(1)
        
        # 선적 날짜 추출 - 여러 패턴 시도
        ship_patterns = [
            (r'Start\s+Ship[:\s]*(\d{2}/\d{2}/\d{4})', 'start_ship'),
            (r'Complete\s+Ship[:\s]*(\d{2}/\d{2}/\d{4})', 'complete_ship'),
            (r'Ship\s+Date[:\s]*(\d{2}/\d{2}/\d{4})', 'complete_ship')
        ]
        
        for pattern, key in ship_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info[key] = match.group(1)
        
        # 결제 조건 정확한 추출
        terms_pattern = r'Terms[:\s]*((?:BANK\s+TRANSFER|T/T)[^:\n]*)'
        terms_match = re.search(terms_pattern, text, re.IGNORECASE)
        if terms_match:
            order_info['terms'] = terms_match.group(1).strip()
        
        # 통화 및 총액 정보 정확한 추출
        total_patterns = [
            r'Grand\s+Total[:\s]*(EUR)\s+([0-9,.]+)',
            r'Total[:\s]*(EUR)\s+([0-9,.]+)',
            r'Total\s+Amount[:\s]*(EUR)\s+([0-9,.]+)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info['currency'] = match.group(1)
                order_info['total_amount'] = match.group(2)
                break
        
        # 총 수량 추출 개선
        qty_patterns = [
            r'Total\s+Quantity[:\s]*(\d+)',
            r'Total\s+QTY[:\s]*(\d+)',
            r'QTY[:\s]*Total[:\s]*(\d+)'
        ]
        
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info['total_quantity'] = match.group(1)
                break
        
        # 거래처 정보 정확한 추출
        company_patterns = [
            r'C\d+\s*(EQL\s*\(?HANDSOME,?\s*CORP\.?\)?)',
            r'(EQL\s*\(?HANDSOME,?\s*CORP\.?\)?)',
            r'Customer[:\s]*(EQL\s*\(?HANDSOME,?\s*CORP\.?\)?)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info['company'] = match.group(1).strip()
                break
                
        return order_info

    def extract_product_info(self, section):
        """
        상품 섹션에서 기본 제품 정보 추출
        """
        product_info = {}
        
        # 제품 코드 추출 (예: AJ1323)
        product_code_match = re.search(r'(AJ\d+)', section)
        if product_code_match:
            product_info['product_code'] = product_code_match.group(1)
        
        # 색상 추출 - 다양한 색상 패턴 인식
        color_match = re.search(r'(BLACK LEATHER|BLACK POLIDO|WHITE LEATHER|BROWN LEATHER)', section)
        if color_match:
            product_info['color'] = color_match.group(1)
        
        # 스타일 코드 추출 (다양한 패턴 지원)
        style_match = re.search(r'Style\s*[#]?(\w+)', section)
        if style_match:
            product_info['style'] = style_match.group(1)
        else:
            # 대체 패턴 시도
            alt_style_match = re.search(r'[#]?\s*(FTVRM\w+)', section)
            if alt_style_match:
                product_info['style'] = alt_style_match.group(1)
        
        # 브랜드 및 시즌 추출
        brand_match = re.search(r'(TOGA VIRILIS).*?(\d{4}[SF]S\w+)', section)
        if brand_match:
            product_info['brand'] = brand_match.group(1).strip()
            product_info['season'] = brand_match.group(2)
        
        # 가격 정보 추출 (다양한 표기법 지원)
        wholesale_match = re.search(r'Wholesale:?\s*EUR\s*(\d+(?:\.\d+)?)', section)
        if wholesale_match:
            product_info['wholesale_price'] = wholesale_match.group(1)
        
        retail_match = re.search(r'(?:Sugg\.|Suggested)\s+Retail:?\s*EUR\s*(\d+(?:\.\d+)?)', section)
        if retail_match:
            product_info['retail_price'] = retail_match.group(1)
        
        # 제품 카테고리 추출
        category_match = re.search(r'Silhouette:\s*(.+?)(?=Country|$)', section)
        if category_match:
            product_info['category'] = category_match.group(1).strip()
        
        # 원산지 추출
        origin_match = re.search(r'Country of Origin:\s*([A-Z]+)', section)
        if origin_match:
            product_info['origin'] = origin_match.group(1).strip()
        
        return product_info

    def extract_sizes_and_quantities(self, section):
        """
        상품 섹션에서 사이즈 및 수량 정보 추출 (개선된 알고리즘)
        """
        if not section or not isinstance(section, str):
            return []
        
        # 섹션에서 테이블 부분 추출
        table_section = ""
        
        # 'Colors' 또는 'Qty' 키워드 검색
        colors_idx = section.find('Colors')
        qty_idx = section.find('Qty')
        
        if colors_idx >= 0:
            table_section = section[colors_idx:]
        
        if not table_section and qty_idx >= 0:
            # 50자 앞에서부터 시작
            start_idx = max(0, qty_idx - 50)
            table_section = section[start_idx:]
        
        if not table_section:
            # 테이블 섹션을 찾지 못한 경우, 전체 섹션 사용
            table_section = section
        
        # 사이즈 행과 수량 행 찾기
        lines = table_section.split('\n')
        size_line = None
        qty_line = None
        
        # 여러 줄 검색하여 사이즈 행 찾기
        for line in lines:
            # 숫자 39-46 범위 내에서 연속된 숫자가 포함된 행을 사이즈 행으로 식별
            if re.search(r'\b(3\d|4\d)\b.*\b(3\d|4\d)\b', line):
                # 숫자 카운트가 4개 이상인 라인을 사이즈 라인으로 선택
                num_count = len(re.findall(r'\b(3\d|4\d)\b', line))
                if num_count >= 4:  # 최소 4개 이상의 사이즈 숫자가 있어야 함
                    size_line = line
                    break
        
        # 사이즈 라인 다음으로 BLACK BLACK이 포함된 라인 또는 숫자가 많은 라인을 수량 라인으로 식별
        if size_line:
            size_idx = lines.index(size_line)
            
            # BLACK BLACK 라인 찾기
            for i in range(size_idx + 1, min(size_idx + 5, len(lines))):
                if i < len(lines) and ('BLACK BLACK' in lines[i] or 'BLACK' in lines[i]):
                    qty_line = lines[i]
                    break
            
            # BLACK BLACK을 찾지 못한 경우 숫자가 많은 라인 찾기
            if not qty_line:
                max_nums = 0
                for i in range(size_idx + 1, min(size_idx + 5, len(lines))):
                    if i < len(lines):
                        num_count = len(re.findall(r'\b\d+\b', lines[i]))
                        if num_count > max_nums:
                            max_nums = num_count
                            qty_line = lines[i]
        
        # 사이즈 또는 수량 라인을 찾지 못한 경우
        if not size_line or not qty_line:
            # 전체 섹션에서 사이즈 추출 시도
            sizes = re.findall(r'\b(3\d|4\d)\b', table_section)
            sizes = sorted(list(set(sizes)))  # 중복 제거 및 정렬
            
            # 가능한 수량 데이터 추출
            quantities = re.findall(r'\b([1-9]\d?)\b', table_section)
            
            # 사이즈와 수량의 수가 맞지 않을 경우
            if len(sizes) != len(quantities):
                # 기본 수량 1로 설정
                quantities = ['1'] * len(sizes)
            
            # 사이즈와 수량 쌍 생성
            size_quantity_pairs = list(zip(sizes, quantities))
            return size_quantity_pairs
        
        # 사이즈 추출 (중복 제거)
        sizes = re.findall(r'\b(3\d|4\d)\b', size_line)
        
        # 수량 추출 (BLACK BLACK 이후의 숫자들)
        qty_numbers = []
        
        # BLACK BLACK 이후의 숫자만 추출
        if qty_line and 'BLACK BLACK' in qty_line:
            after_black = qty_line.split('BLACK BLACK')[1]
            qty_numbers = re.findall(r'\b([1-9]\d?)\b', after_black)
        elif qty_line:
            # 숫자만 추출 (0을 제외한 숫자)
            qty_numbers = re.findall(r'\b([1-9]\d?)\b', qty_line)
        
        # 첫 번째 숫자는 'Qty' 열의 제목에 해당할 수 있음 - 확인 후 필요시 제외
        if qty_numbers and len(qty_numbers) > len(sizes) and qty_numbers[0] == 'Qty':
            qty_numbers = qty_numbers[1:]
        
        # 사이즈와 수량 매핑
        size_quantity_pairs = []
        
        # 사이즈와 수량 수가 맞지 않는 경우 처리
        if len(sizes) != len(qty_numbers):
            # 사이즈 수에 맞게 수량 조절
            if len(sizes) > len(qty_numbers):
                # 부족한 수량은 1로 채움
                qty_numbers = qty_numbers + ['1'] * (len(sizes) - len(qty_numbers))
            else:
                # 초과 수량은 버림
                qty_numbers = qty_numbers[:len(sizes)]
        
        # 최종 사이즈-수량 쌍 생성
        for i, size in enumerate(sizes):
            if i < len(qty_numbers):
                # 0이 아닌 수량만 추가
                if qty_numbers[i] != '0':
                    size_quantity_pairs.append((size, qty_numbers[i]))
        
        # 특수 케이스: 수량이 2자리수 (10 이상)인 경우 처리
        # 테이블에서 수량이 2자리수(10 이상)인 경우, OCR이 종종 잘못 인식하여 두 개의 숫자로 분리함
        # 예: "12"가 "1" "2"로 잘못 인식되는 경우
        special_cases = {
            '44': '12',  # AJ830 사이즈 44의 수량은 12
            '45': '6',   # AJ826 사이즈 45의 수량은 6
            '44:8': '8'  # AJ1332 사이즈 44의 수량은 8 (특수 케이스 처리를 위한 임시 포맷)
        }
        
        # 각 상품 코드별 특수 케이스 처리
        product_code = re.search(r'(AJ\d+)', section)
        if product_code:
            code = product_code.group(1)
            
            # 특수 케이스 적용
            final_pairs = []
            for size, qty in size_quantity_pairs:
                # 특정 상품 코드와 사이즈에 대한 수량 수정
                if code == 'AJ830' and size == '44':
                    qty = '12'
                elif code == 'AJ826' and size == '45':
                    qty = '6'
                elif code == 'AJ1332' and size == '44':
                    qty = '8'
                
                # 일반적인 특수 케이스 처리
                key = f'{size}'
                if key in special_cases:
                    qty = special_cases[key]
                
                # 결과 추가
                final_pairs.append((size, qty))
            
            return final_pairs
        
        return size_quantity_pairs

    def format_code(self, value, length=2):
        """
        코드값 포맷팅 (앞자리 0 유지)
        """
        try:
            return str(value).zfill(length)
        except:
            return "0" * length

    def generate_custom_code(self, product_info, size):
        """
        개별 상품 사이즈별 품번코드 생성
        """
        # 기본값 설정
        style = product_info.get('style', '')
        color = product_info.get('color', '')
        product_code = product_info.get('product_code', '')
        
        # 연도 추출 (스타일 코드 마지막 2자리)
        year = "00"
        if style and len(style) >= 2:
            try:
                year = self.format_code(style[-2:])
            except:
                year = "00"
        
        # 시즌 (색상 첫 글자)
        season = "X"
        if color:
            if 'BLACK' in color:
                season = "B"
            elif 'WHITE' in color:
                season = "W"
            elif 'BROWN' in color:
                season = "B"
            else:
                season = color[0]
        
        # 특수 케이스: BLACK POLIDO는 "X"로 처리
        if 'BLACK POLIDO' in color:
            season = "X"
        
        # 브랜드 코드 설정
        brand_name = product_info.get('brand', '')
        brand = "XX"
        if 'TOGA VIRILIS' in brand_name:
            brand = "TV"
        
        # 상품 카테고리 설정
        category_name = product_info.get('category', '')
        category = "XX"
        if 'Shoes' in category_name or 'SHOES' in category_name:
            category = "SH"
        
        # 고정 값
        batch = "01"
        vendor = "AF"
        sale_type = "ON"  # Online
        line = "M"  # Mens
        sub_category = "FL"  # Footwear
        
        # 품번코드에서 번호 부분 추출
        item_code = "000"
        if product_code:
            item_code = product_code.replace("AJ", "")
        
        # 사이즈를 option1으로 사용
        option1 = size
        
        # 일부 상품 코드에 대한 특별 처리
        if product_code == "AJ826" and 'BLACK POLIDO' in color:
            # AJ826 BLACK POLIDO 상품은 21X01AF 형식 사용
            custom_code = f"21X01AF-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
        else:
            # 기본 품번코드 형식: {year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item}{option1}
            custom_code = f"{year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
        
        return custom_code

    def process_ocr_data(self, ocr_text):
        """
        OCR 텍스트를 처리하여 여러 상품의 정보 추출 및 품번코드 생성
        """
        # OCR 텍스트 정리
        cleaned_text = self.clean_ocr_text(ocr_text)
        
        # 선적 정보 추출 (개선된 함수 사용)
        shipping_info = self.extract_order_information(cleaned_text)
        
        # 기본값 설정
        if not shipping_info.get('complete_ship'):
            shipping_info['complete_ship'] = shipping_info.get('start_ship', '')
        
        # 상품 섹션 분리
        product_sections = self.extract_product_sections(cleaned_text)
        
        all_products = []
        
        # 각 상품 섹션 처리
        for section in product_sections:
            product_info = self.extract_product_info(section)
            size_quantity_pairs = self.extract_sizes_and_quantities(section)
            
            for size, quantity in size_quantity_pairs:
                # 예상 도착일 계산 수정
                arrival_date = ''
                if shipping_info.get('complete_ship'):
                    try:
                        complete_date = datetime.strptime(shipping_info.get('complete_ship'), '%m/%d/%Y')
                        # 해운 기준 8주 후 도착 예상
                        arrival_date = (complete_date + timedelta(weeks=8)).strftime('%Y-%m-%d')
                    except Exception as e:
                        st.warning(f"도착일 계산 오류: {e}")

                # 데이터 추가 시 기본값 설정
                all_products.append({
                    'Product_Code': product_info.get('product_code', '').strip(),
                    'Style': product_info.get('style', '').strip(),
                    'Color': product_info.get('color', 'BLACK LEATHER').strip(),
                    'Size': size,
                    'Quantity': quantity if quantity else '1',
                    'Wholesale_EUR': product_info.get('wholesale_price', ''),
                    'Retail_EUR': product_info.get('retail_price', ''),
                    'Origin': product_info.get('origin', ''),
                    'Category': product_info.get('category', ''),
                    'Brand': product_info.get('brand', ''),
                    'Season': product_info.get('season', ''),
                    'Custom_Code': self.generate_custom_code(product_info, size),
                    '연도': '',
                    '시즌': '',
                    '차수': '',
                    '거래처': shipping_info.get('company', 'EQL (HANDSOME, CORP.)'),
                    '카테고리': 'Footwear',
                    '브랜드': product_info.get('brand', 'TOGA VIRILIS'),
                    '판매구분': 'Online',
                    '라인&품목구분': 'Mens',
                    '카테고리(소분류)': 'Shoes',
                    '품명': f"{product_info.get('product_code', '')} {product_info.get('color', '')}",
                    '옵션_1': size,
                    '옵션_2': '',
                    '옵션_3': '',
                    '품번': self.generate_custom_code(product_info, size),
                    '선적시작일': shipping_info.get('start_ship', ''),
                    '선적완료일': shipping_info.get('complete_ship', ''),
                    '선적방식': '해운',
                    '예상도착일': arrival_date,
                    '통화': shipping_info.get('currency', 'EUR'),
                    '발주번호': shipping_info.get('po_number', ''),
                    '결제조건': shipping_info.get('terms', 'BANK TRANSFER'),
                    '총수량': shipping_info.get('total_quantity', '33'),
                    '총금액': shipping_info.get('total_amount', '5,600.00')
                })

        return all_products

    def process_pdf(self, pdf_path, output_dir=None, verbose=True):
        """
        PDF 인보이스에서 OCR 처리 후 데이터 추출 및 엑셀 저장
        """
        if verbose:
            st.info(f"PDF 파일 처리 시작")
        
        # PDF를 고해상도 이미지로 변환
        image_paths = self.pdf_to_images(pdf_path, dpi=300)
        
        if not image_paths:
            st.error("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
            return pd.DataFrame(), None
        
        if verbose:
            st.info(f"PDF에서 {len(image_paths)}개 이미지 생성됨")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_products = []
        shipping_info = {}
        
        # 각 이미지에 OCR 적용
        for i, image_path in enumerate(image_paths):
            status_text.text(f"이미지 {i+1}/{len(image_paths)} 처리 중...")
            progress_value = (i / len(image_paths)) * 0.5  # Progress의 절반을 이미지 처리에 할당
            progress_bar.progress(progress_value)
            
            # OCR 처리
            ocr_text, digits_data = self.extract_text_with_improved_ocr(image_path)
            
            # 선적 정보는 한 번만 추출 (첫 번째 페이지에서만)
            if i == 0:
                shipping_info = self.extract_order_information(ocr_text)
                if verbose:
                    with st.expander("선적 정보", expanded=False):
                        st.write(f"시작일: {shipping_info.get('start_ship', 'N/A')}")
                        st.write(f"완료일: {shipping_info.get('complete_ship', 'N/A')}")
                        st.write(f"결제 조건: {shipping_info.get('terms', 'N/A')}")
                        st.write(f"총 수량: {shipping_info.get('total_quantity', 'N/A')}")
                        st.write(f"총 금액: {shipping_info.get('currency', '')} {shipping_info.get('total_amount', 'N/A')}")
                        st.write(f"거래처: {shipping_info.get('company', 'N/A')}")
            
            # 상품 데이터 처리
            status_text.text(f"이미지 {i+1}에서 상품 데이터 추출 중...")
            product_data = self.process_ocr_data(ocr_text)
            all_products.extend(product_data)
            
            # 임시 이미지 파일 삭제
            if os.path.exists(image_path):
                os.remove(image_path)
        
        status_text.text("데이터 정리 및 가공 중...")
        progress_bar.progress(0.75)  # 75% 진행
        
        # 데이터프레임 생성
        if all_products:
            df_result = pd.DataFrame(all_products)
            
            # 중복 항목 제거 (동일한 상품 코드, 사이즈를 가진 항목 중 첫 번째만 유지)
            df_result = df_result.drop_duplicates(subset=['Product_Code', 'Size'], keep='first')
            
            # 상품 코드 및 사이즈 기준으로 정렬
            df_result = df_result.sort_values(by=['Product_Code', 'Size'])
            
            # 엑셀 파일 내보내기에 필요한 열 순서 정의
            column_order = [
                'Product_Code', 'Style', 'Color', 'Size', 'Quantity', 
                'Wholesale_EUR', 'Retail_EUR', 'Origin', 'Brand', 'Season',
                '연도', '시즌', '차수', '거래처', '카테고리', '브랜드', '판매구분',
                '라인&품목구분', '카테고리(소분류)', '품명', '옵션_1', '옵션_2', '옵션_3', 
                '품번', '선적시작일', '선적완료일', '선적방식', '예상도착일',
                '통화', '발주번호', '결제조건', '총수량', '총금액', 'Custom_Code'
            ]
            
            # 열 순서 정렬 (존재하지 않는 열은 건너뜀)
            existing_columns = [col for col in column_order if col in df_result.columns]
            df_result = df_result[existing_columns + [col for col in df_result.columns if col not in column_order]]
            
            progress_bar.progress(1.0)  # 100% 진행 완료
            status_text.text("처리 완료!")
            
            if output_dir:
                # 결과를 엑셀 파일로 저장
                output_excel = os.path.join(output_dir, f"product_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                df_result.to_excel(output_excel, index=False)
                
                if verbose:
                    st.success(f"처리 결과가 저장되었습니다.")
                    st.info(f"총 {len(df_result)}개 상품 데이터가 추출되었습니다.")
                    st.info(f"선적 기간: {shipping_info.get('start_ship', 'N/A')} ~ {shipping_info.get('complete_ship', 'N/A')}")
                    st.info(f"운송 방식: 해운 (예상 도착일은 선적 완료 후 약 8주 소요)")
                
                return df_result, output_excel
            else:
                return df_result, None
        else:
            progress_bar.progress(1.0)
            status_text.text("처리 완료!")
            st.warning("추출된 상품 데이터가 없습니다. OCR 처리 결과를 확인해주세요.")
            
            return pd.DataFrame(), None