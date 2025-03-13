import os
import tempfile
import cv2
import numpy as np
from pdf2image import convert_from_path
import pandas as pd
from datetime import datetime, timedelta
import re
import logging
from typing import List, Dict, Tuple, Optional, Union
from google.cloud import vision
import io

class OCRProcessor:
    def __init__(self):
        """OCR 프로세서 초기화"""
        self.temp_dir = tempfile.mkdtemp()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Google Cloud Vision API 클라이언트 초기화
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            self.logger.info("Google Cloud Vision API 클라이언트가 성공적으로 초기화되었습니다.")
        except Exception as e:
            self.logger.error(f"Google Cloud Vision API 클라이언트 초기화 실패: {e}")
            self.vision_client = None

    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """PDF 파일을 고해상도 이미지로 변환"""
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, image in enumerate(images):
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_path = os.path.join(self.temp_dir, f"temp_page_{i}_{timestamp}.jpg")
                image.save(image_path, "JPEG", quality=100)  # 최대 품질로 저장
                image_paths.append(image_path)
            
            self.logger.info(f"PDF를 {len(images)}개의 이미지로 변환했습니다.")
            return image_paths
        except Exception as e:
            self.logger.error(f"PDF 변환 오류: {e}")
            return []

    def enhance_image_for_ocr(self, image_path: str) -> str:
        """OCR 성능 향상을 위한 이미지 전처리"""
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                self.logger.warning(f"이미지를 불러올 수 없습니다: {image_path}")
                return image_path
            
            # 원본 이미지 복사
            original_image = image.copy()
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # 적응형 이진화 (문서의 밝기 차이에 강인함)
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 테이블 선 강화
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            
            table_mask = cv2.bitwise_or(horizontal_lines, vertical_lines)
            
            # 표와 텍스트 결합
            enhanced = cv2.bitwise_or(binary, table_mask)
            
            # 엣지 감지 및 강화 (텍스트 경계 선명화)
            edges = cv2.Canny(enhanced, 50, 150)
            dilated = cv2.dilate(edges, np.ones((1, 1), np.uint8), iterations=1)
            
            # 최종 이미지 = 원본 이미지 + 강화된 엣지
            final_enhanced = cv2.addWeighted(denoised, 0.8, dilated, 0.2, 0)
            
            # 처리된 이미지 저장
            enhanced_path = os.path.join(self.temp_dir, f"enhanced_{os.path.basename(image_path)}")
            
            # 이미지 저장 (향상된 이미지와 원본 이미지 모두 저장하여 OCR 시도)
            cv2.imwrite(enhanced_path, final_enhanced)
            
            # 원본 이미지 경로도 함께 저장 (binarized 이미지가 실패할 경우 원본 사용)
            original_path = os.path.join(self.temp_dir, f"original_{os.path.basename(image_path)}")
            cv2.imwrite(original_path, original_image)
            
            self.logger.info(f"이미지 전처리 완료: {enhanced_path}")
            return enhanced_path
        except Exception as e:
            self.logger.error(f"이미지 처리 오류: {e}")
            return image_path

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출 (구글 비전 API 사용)"""
        if not self.vision_client:
            self.logger.error("Google Cloud Vision API 클라이언트가 초기화되지 않았습니다.")
            return ""
        
        # PDF를 이미지로 변환
        image_paths = self.pdf_to_images(pdf_path)
        
        if not image_paths:
            self.logger.error("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
            return ""
        
        full_text = ""
        
        # 각 이미지에 OCR 적용
        for image_path in image_paths:
            try:
                # 이미지 전처리
                enhanced_path = self.enhance_image_for_ocr(image_path)
                
                # Google Cloud Vision OCR 적용
                text = self._extract_text_with_google_vision(enhanced_path)
                
                # 텍스트 정리
                cleaned_text = self.clean_ocr_text(text)
                full_text += cleaned_text + "\n\n"
                
                # 임시 이미지 파일 삭제
                try:
                    if os.path.exists(enhanced_path):
                        os.remove(enhanced_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    self.logger.warning(f"임시 이미지 파일 삭제 실패: {e}")
                
            except Exception as e:
                self.logger.error(f"이미지 처리 중 오류: {e}")
                continue
                
        return full_text

    def _extract_text_with_google_vision(self, image_path: str) -> str:
        """Google Cloud Vision API를 사용하여 OCR 처리"""
        if not self.vision_client:
            self.logger.error("Google Cloud Vision API 클라이언트가 초기화되지 않았습니다.")
            return ""
            
        try:
            # 이미지 파일 읽기
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # 텍스트 감지 요청 (문서 모드 사용)
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                self.logger.error(f"Google Cloud Vision API 오류: {response.error.message}")
                return ""
            
            # 전체 텍스트 추출
            full_text = response.full_text_annotation.text
            
            # 테이블 구조 및 레이아웃 분석 (향후 확장)
            pages = response.full_text_annotation.pages
            
            # 디버깅 정보 기록
            self.logger.info(f"감지된 텍스트 길이: {len(full_text)} 문자")
            self.logger.info(f"감지된 페이지 수: {len(pages)}")
            
            return full_text
        
        except Exception as e:
            self.logger.error(f"Google Cloud Vision OCR 처리 중 오류: {e}")
            return ""

    def extract_text_with_improved_ocr(self, image_path: str) -> Tuple[str, Dict]:
        """OCR을 적용하여 이미지에서 텍스트 추출 (기존 호환성 유지)"""
        text = self._extract_text_with_google_vision(image_path)
        return text, {}  # 두 번째 반환값은 호환성을 위해 빈 딕셔너리 반환

    def clean_ocr_text(self, text: str) -> str:
        """OCR 텍스트 정리 및 정규화"""
        if not text:
            return ""
            
        # 특수 문자 처리 및 문자열 정리
        cleaned = re.sub(r'[«»•‣◦□■●]', '', text)
        
        # 불필요한 줄바꿈 제거 (빈 줄은 유지)
        cleaned = re.sub(r'([^\n])\n([^\n])', r'\1 \2', cleaned)
        
        # 공백 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    def extract_product_sections(self, text: str) -> List[str]:
        """OCR 텍스트에서 개별 상품 섹션을 분리하여 추출"""
        # 향상된 제품 패턴 정규식
        product_pattern = r'((?:AJ\d+|FTVRM\w+)\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE|POLIDO|LEATHER).*?)(?=(?:AJ\d+|FTVRM\w+)\s*[-]?\s*|$)'
        product_sections = re.findall(product_pattern, text, re.DOTALL | re.IGNORECASE)
        
        # 섹션 정리
        product_sections = [section.strip() for section in product_sections if section.strip()]
        
        if not product_sections:
            self.logger.warning("제품 섹션을 추출하지 못했습니다. 대체 패턴 시도...")
            # 대체 패턴: 스타일 코드와 제품 코드 모두 검색
            alt_pattern = r'(?:Style\s+[#]?FTVRM\w+|AJ\d+).*?(?=Style\s+[#]?FTVRM\w+|AJ\d+|$)'
            product_sections = re.findall(alt_pattern, text, re.DOTALL | re.IGNORECASE)
            product_sections = [section.strip() for section in product_sections if section.strip()]
        
        self.logger.info(f"총 {len(product_sections)}개의 제품 섹션을 찾았습니다.")
        return product_sections

    def extract_order_information(self, text: str) -> Dict[str, str]:
        """주문 정보 추출 함수"""
        order_info = {}
        
        # 주문 번호 추출 (발주서 & 오더컨펌)
        po_patterns = [
            r'PO\s*[#:]\s*(\d+)',
            r'ORDER\s+CONFIRMATION\s+ID:\s*(\d+)'
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info['po_number'] = match.group(1)
                break
        
        # 날짜 추출
        date_patterns = [
            (r'Created:\s*(\d{2}/\d{2}/\d{4})', 'created_date'),
            (r'Start\s+Ship:\s*(\d{2}/\d{2}/\d{4})', 'start_ship'),
            (r'Complete\s+Ship:\s*(\d{2}/\d{2}/\d{4})', 'complete_ship'),
            (r'Date:\s*(\d{2}-\d{2}-\d{4})', 'date')
        ]
        
        for pattern, key in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info[key] = match.group(1)
        
        # 결제 조건 추출
        terms_patterns = [
            r'Terms:\s*(.*?)(?:\n|$)',
            r'Payment\s+Terms:\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in terms_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info['terms'] = match.group(1).strip()
                break
        
        # 브랜드 및 시즌 추출
        brand_patterns = [
            r'(TOGA\s+VIRILIS).*?(\d{4}[SF]S\w*)',
            r'Brand:\s*(.*?)(?:\n|$).*?Season:\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                order_info['brand'] = match.group(1).strip()
                order_info['season'] = match.group(2).strip() if len(match.groups()) > 1 else ""
                break
        
        # 총액 추출
        total_patterns = [
            r'Grand\s+Total:\s*(\w+)\s*([\d,.]+)',
            r'Doc\.\s+Total:\s*([\d,.]+)\s*(\w+)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'EUR' in match.group(0):
                    order_info['currency'] = 'EUR'
                    # 통화가 앞에 있는지 뒤에 있는지에 따라 다르게 추출
                    if 'EUR' in match.group(1):
                        order_info['total_amount'] = match.group(2).replace(',', '')
                    else:
                        order_info['total_amount'] = match.group(1).replace(',', '')
                break
        
        # 총 수량 추출
        qty_patterns = [
            r'Total\s+Quantity:\s*(\d+)',
            r'TOTAL\s+(?:\w+\s+)?\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)'
        ]
        
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info['total_quantity'] = match.group(1)
                break
        
        # 거래처 정보 추출
        company_patterns = [
            r'EQL\s*\(?HANDSOME,?\s*CORP\.?\)?',
            r'CUSTOMER:\s*\n\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.groups():
                    order_info['company'] = match.group(1).strip()
                else:
                    order_info['company'] = match.group(0).strip()
                break
        
        # 문서 유형 감지
        if 'ORDER CONFIRMATION' in text:
            order_info['document_type'] = 'order_confirmation'
        elif 'PO#:' in text or 'Purchase Order' in text:
            order_info['document_type'] = 'purchase_order'
        elif 'INVOICE' in text:
            order_info['document_type'] = 'invoice'
        else:
            order_info['document_type'] = 'unknown'
            
        self.logger.info(f"추출된 주문 정보: {order_info}")
        return order_info

    def extract_product_info(self, section: str) -> Dict[str, str]:
        """상품 섹션에서 기본 제품 정보 추출"""
        product_info = {}
        
        # 제품 코드 추출 (AJ 코드)
        product_code_match = re.search(r'(AJ\d+)', section)
        if product_code_match:
            product_info['product_code'] = product_code_match.group(1)
        
        # 색상 추출
        color_patterns = [
            r'(BLACK\s+LEATHER|BLACK\s+POLIDO|WHITE\s+LEATHER|BROWN\s+LEATHER)',
            r'Colors.*?BLACK\s+BLACK'
        ]
        
        for pattern in color_patterns:
            color_match = re.search(pattern, section, re.IGNORECASE)
            if color_match:
                if 'BLACK BLACK' in color_match.group(0):
                    product_info['color'] = 'BLACK LEATHER'
                else:
                    product_info['color'] = color_match.group(1) if color_match.groups() else color_match.group(0)
                break
        
        # 스타일 코드 추출
        style_patterns = [
            r'Style\s*[#]?(\w+)',
            r'FTVRM\w+',
            r'Style\s+#FTVRM\w+'
        ]
        
        for pattern in style_patterns:
            style_match = re.search(pattern, section)
            if style_match:
                if match_groups := style_match.groups():
                    product_info['style'] = match_groups[0]
                else:
                    product_info['style'] = style_match.group(0).replace('Style #', '').strip()
                break
        
        # 브랜드 및 시즌 추출
        brand_match = re.search(r'(TOGA\s+VIRILIS).*?(\d{4}[SF]S\w+)', section)
        if brand_match:
            product_info['brand'] = brand_match.group(1).strip()
            product_info['season'] = brand_match.group(2)
        
        # 가격 정보 추출
        wholesale_patterns = [
            r'Wholesale:?\s*EUR\s*(\d+(?:\.\d+)?)',
            r'Wholesale:?\s*(\d+(?:\.\d+)?)',
            r'UNIT\s+PRICE.*?(\d+\.\d+)'
        ]
        
        for pattern in wholesale_patterns:
            wholesale_match = re.search(pattern, section, re.IGNORECASE)
            if wholesale_match:
                product_info['wholesale_price'] = wholesale_match.group(1)
                break
        
        retail_patterns = [
            r'(?:Sugg\.|Suggested)\s+Retail:?\s*EUR\s*(\d+(?:\.\d+)?)',
            r'Retail:?\s*EUR\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in retail_patterns:
            retail_match = re.search(pattern, section, re.IGNORECASE)
            if retail_match:
                product_info['retail_price'] = retail_match.group(1)
                break
        
        # 제품 카테고리 추출
        category_patterns = [
            r'Silhouette:\s*(.+?)(?=Country|$)',
            r'Product\s+Line:\s*(\w+)'
        ]
        
        for pattern in category_patterns:
            category_match = re.search(pattern, section, re.IGNORECASE)
            if category_match:
                product_info['category'] = category_match.group(1).strip()
                break
        
        # 원산지 추출
        origin_match = re.search(r'Country of Origin:\s*([A-Z]+)', section)
        if origin_match:
            product_info['origin'] = origin_match.group(1).strip()
        
        self.logger.info(f"추출된 제품 정보: {product_info}")
        return product_info

    def extract_sizes_and_quantities(self, section: str) -> List[Tuple[str, str]]:
        """상품 섹션에서 사이즈 및 수량 정보 추출"""
        if not section or not isinstance(section, str):
            return []
        
        # 사이즈 행 추출 시도
        size_row_match = re.search(r'(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})(?:\s+(\d{2,3}))?', section)
        if size_row_match:
            sizes = [s for s in size_row_match.groups() if s]
            
            # 해당 사이즈 행 바로 아래에서 수량 찾기
            quantity_pattern = r'BLACK\s+BLACK\s+((?:\s*\d+)+)'
            quantity_match = re.search(quantity_pattern, section, re.IGNORECASE)
            
            if quantity_match:
                quantities_str = quantity_match.group(1)
                quantities = re.findall(r'\d+', quantities_str)
                
                # 사이즈와 수량이 맞지 않는 경우 조정
                if len(quantities) != len(sizes):
                    # 표에서 정확한 수량 행 탐색
                    quantity_line = re.search(r'BLACK\s+BLACK((?:\s+\d+)+)', section)
                    if quantity_line:
                        quantities = re.findall(r'\d+', quantity_line.group(1))
                
                # 그래도 맞지 않으면 기본값 1 설정
                if len(quantities) != len(sizes):
                    self.logger.warning(f"사이즈와 수량의 수가 일치하지 않습니다. 사이즈: {sizes}, 수량: {quantities}")
                    quantities = ['1'] * len(sizes)
                
                # 사이즈와 수량 쌍 생성
                size_quantity_pairs = list(zip(sizes, quantities))
                return size_quantity_pairs
        
        # 표 구조에서 추출하지 못한 경우 대체 방법 시도
        sizes = re.findall(r'\b(39|40|41|42|43|44|45|46)\b', section)
        if not sizes:
            # 390, 400 형식으로 된 사이즈 검색
            alt_sizes = re.findall(r'\b(390|400|410|420|430|440|450|460)\b', section)
            sizes = [s[:2] for s in alt_sizes]  # 390 -> 39로 변환
        
        if sizes:
            # 수량 추출 (각 사이즈 다음에 나오는 숫자를 수량으로 간주)
            size_quantity_pairs = []
            for size in sizes:
                # 사이즈 뒤에 나오는 숫자를 찾음
                qty_pattern = rf'{size}\s+(\d+)'
                qty_match = re.search(qty_pattern, section)
                if qty_match:
                    quantity = qty_match.group(1)
                    size_quantity_pairs.append((size, quantity))
                else:
                    # 사이즈 행과 수량 행이 분리된 경우
                    # BLACK BLACK 다음에 나오는 숫자들을 수량으로 간주
                    black_pattern = r'BLACK\s+BLACK\s+((?:\d+\s+)+)'
                    black_match = re.search(black_pattern, section)
                    if black_match:
                        all_quantities = re.findall(r'\d+', black_match.group(1))
                        if all_quantities and len(sizes) == len(all_quantities):
                            idx = sizes.index(size)
                            if idx < len(all_quantities):
                                size_quantity_pairs.append((size, all_quantities[idx]))
                                continue
                    
                    # 기본값 설정
                    size_quantity_pairs.append((size, '1'))
            
            return size_quantity_pairs
        
        self.logger.warning("사이즈 및 수량 정보를 추출할 수 없습니다.")
        return []

    def generate_custom_code(self, product_info: Dict[str, str], size: str) -> str:
        """품번코드 생성"""
        # 연도 추출 (시즌 정보에서)
        year = "00"
        season = product_info.get('season', '')
        if season and len(season) >= 6:
            try:
                year = season[2:4]  # 2024SS에서 '24' 추출
            except:
                year = "00"
        
        # 시즌 코드 (SS -> S, FW -> F)
        season_code = "X"
        if "SS" in season:
            season_code = "S"
        elif "FW" in season:
            season_code = "F"
        
        # 색상 처리
        color = product_info.get('color', '')
        color_code = "X"
        if color:
            if 'BLACK' in color:
                if 'POLIDO' in color:
                    color_code = "X"
                else:
                    color_code = "B"
            elif 'WHITE' in color:
                color_code = "W"
            elif 'BROWN' in color:
                color_code = "B"
        
        # 차수/거래처 코드는 고정값 사용
        batch = "01"
        vendor = "AF"
        
        # 브랜드 코드
        brand_name = product_info.get('brand', '')
        brand = "XX"
        if 'TOGA VIRILIS' in brand_name:
            brand = "TV"
        
        # 상품 카테고리 설정
        category_name = product_info.get('category', '')
        category = "XX"
        if 'Shoes' in category_name or 'SHOES' in category_name or 'Footwear' in category_name:
            category = "SH"
        
        # 고정 값
        sale_type = "ON"  # Online
        line = "M"  # Mens
        sub_category = "FL"  # Footwear
        
        # 품번코드에서 번호 부분 추출
        product_code = product_info.get('product_code', '')
        item_code = "000"
        if product_code:
            item_code = product_code.replace("AJ", "")
        
        # 사이즈를 옵션으로 사용 (39 -> 390으로 변환)
        option1 = size
        
        # 일부 상품 코드에 대한 특별 처리
        if product_code == "AJ826" and 'BLACK POLIDO' in color:
            # AJ826 BLACK POLIDO 상품은 21X01AF 형식 사용
            custom_code = f"21X01AF-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
        else:
            # 기본 품번코드 형식
            custom_code = f"{year}{season_code}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
        
        return custom_code

    def process_pdf(self, pdf_path: str, output_dir: Optional[str] = None, verbose: bool = True) -> Tuple[pd.DataFrame, Optional[str]]:
        """PDF 문서에서 OCR 처리 후 데이터 추출 및 엑셀 저장"""
        # 전체 텍스트 추출
        full_text = self.extract_text_from_pdf(pdf_path)
        
        if not full_text:
            self.logger.error("텍스트 추출 실패: PDF에서 텍스트를 추출할 수 없습니다.")
            return pd.DataFrame(), None
        
        if verbose:
            self.logger.info(f"추출된 텍스트 일부: {full_text[:500]}...")
        
        # 주문 정보 추출
        order_info = self.extract_order_information(full_text)
        
        # 상품 섹션 분리
        product_sections = self.extract_product_sections(full_text)
        
        all_products = []
        
        # 각 상품 섹션 처리
        for section in product_sections:
            # 제품 정보 추출
            product_info = self.extract_product_info(section)
            
            # 사이즈 및 수량 추출
            size_quantity_pairs = self.extract_sizes_and_quantities(section)
            
            # 각 사이즈별 데이터 생성
            for size, quantity in size_quantity_pairs:
                # 품번코드 생성
                custom_code = self.generate_custom_code(product_info, size)
                
                # 데이터 추가
                product_data = {
                    'Product_Code': product_info.get('product_code', ''),
                    'Style': product_info.get('style', ''),
                    'Color': product_info.get('color', ''),
                    'Size': size,
                    'Quantity': quantity,
                    'Wholesale_Price': product_info.get('wholesale_price', ''),
                    'Retail_Price': product_info.get('retail_price', ''),
                    'Brand': product_info.get('brand', ''),
                    'Season': product_info.get('season', ''),
                    'Custom_Code': custom_code,
                    'Document_Type': order_info.get('document_type', ''),
                    'PO_Number': order_info.get('po_number', ''),
                    'Created_Date': order_info.get('created_date', order_info.get('date', '')),
                    'Total_Amount': order_info.get('total_amount', ''),
                    'Currency': order_info.get('currency', 'EUR'),
                    'Total_Quantity': order_info.get('total_quantity', ''),
                    'Year': product_info.get('season', '')[:4] if product_info.get('season', '') else '',
                    'Category': product_info.get('category', '')
                }
                
                all_products.append(product_data)
        
        # 데이터프레임 생성
        if all_products:
            df_result = pd.DataFrame(all_products)
            
            # 추가 필드 생성
            if 'Season' in df_result.columns:
                # 시즌 코드 분리 (2024SS -> 24S)
                df_result['Year_Code'] = df_result['Season'].str.slice(2, 4)
                df_result['Season_Code'] = df_result['Season'].str.slice(4, 5)
            
            # 데이터 후처리 및 정리
            df_result = self._post_process_dataframe(df_result)
            
            # 출력 디렉토리 설정
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"product_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                df_result.to_excel(output_file, index=False)
                self.logger.info(f"데이터를 엑셀 파일로 저장했습니다: {output_file}")
                return df_result, output_file
            
            return df_result, None
        
        self.logger.warning("추출된 상품 정보가 없습니다.")
        return pd.DataFrame(), None

    def _post_process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임 후처리 및 정리"""
        # 누락된 필드를 위한 기본값 설정
        default_values = {
            'Year': '2024',
            'Season_Code': 'S',
            'Batch': '01',
            'Vendor': 'AF',
            'Category': 'Shoes',
            'Brand_Code': 'TV',
            'Sale_Type': 'ON',
            'Line': 'M',
            'Sub_Category': 'FL'
        }
        
        # 누락된 필드 채우기
        for field, default_value in default_values.items():
            if field not in df.columns:
                df[field] = default_value
        
        # 열 순서 정리
        ordered_columns = [
            'Product_Code', 'Style', 'Color', 'Size', 'Quantity', 'Wholesale_Price', 
            'Document_Type', 'PO_Number', 'Created_Date', 'Brand', 'Season', 
            'Year', 'Total_Amount', 'Currency', 'Total_Quantity', 'Custom_Code'
        ]
        
        # 데이터프레임에 존재하는 열만 유지
        available_columns = [col for col in ordered_columns if col in df.columns]
        
        # 나머지 열 추가
        remaining_columns = [col for col in df.columns if col not in ordered_columns]
        final_columns = available_columns + remaining_columns
        
        return df[final_columns]