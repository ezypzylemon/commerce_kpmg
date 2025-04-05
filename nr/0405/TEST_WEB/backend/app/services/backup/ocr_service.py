import os
import tempfile
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
from datetime import datetime, timedelta
import re
import logging
from typing import List, Dict, Tuple, Optional, Union

class OCRProcessor:
    def __init__(self):
        """OCR 프로세서 초기화"""
        self.temp_dir = tempfile.mkdtemp()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """PDF 파일을 고해상도 이미지로 변환"""
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, image in enumerate(images):
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_path = os.path.join(self.temp_dir, f"temp_page_{i}_{timestamp}.jpg")
                image.save(image_path, "JPEG", quality=95)
                image_paths.append(image_path)
            
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
            
            # 이미지 크기 조정
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
            enhanced_path = os.path.join(self.temp_dir, f"enhanced_{os.path.basename(image_path)}")
            cv2.imwrite(enhanced_path, sharpened)
            
            return enhanced_path
        except Exception as e:
            self.logger.error(f"이미지 처리 오류: {e}")
            return image_path

    def extract_text_with_improved_ocr(self, image_path: str) -> Tuple[str, Dict]:
        """OCR을 적용하여 이미지에서 텍스트 추출"""
        try:
            # 이미지 전처리
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
            self.logger.error(f"OCR 처리 오류: {e}")
            return "", {}
        
        # ocr_service.py 수정 (기존 파일에 추가)

# 기존 OCR 프로세서 클래스에 메서드 추가
    def extract_text_from_pdf(self, pdf_path):
        """PDF에서 텍스트 추출 (OCR 처리)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            추출된 전체 텍스트
        """
        # 이미지로 변환
        image_paths = self.pdf_to_images(pdf_path)

        if not image_paths:
            self.logger.error("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
            return ""

        full_text = ""

        # 각 이미지에 OCR 적용
        for image_path in image_paths:
            # OCR 엔진 선택 (환경 변수 등으로 설정 가능)
            use_google_vision = os.environ.get('USE_GOOGLE_VISION', 'false').lower() == 'true'

            if use_google_vision:
                # Google Cloud Vision OCR 사용
                text, _ = self._extract_text_with_google_vision(image_path)
            else:
                # Tesseract OCR 사용
                text, _ = self.extract_text_with_improved_ocr(image_path)

            # 텍스트 정리
            cleaned_text = self.clean_ocr_text(text)
            full_text += cleaned_text + "\n\n"

            # 임시 이미지 파일 삭제
            try:
                os.remove(image_path)
            except Exception as e:
                self.logger.warning(f"임시 이미지 파일 삭제 실패: {e}")

        return full_text

    def _extract_text_with_google_vision(self, image_path):
        """Google Cloud Vision API를 사용하여 OCR 처리

        Args:
            image_path: 이미지 파일 경로

        Returns:
            (추출된 텍스트, 상세 데이터)
        """
        try:
            from google.cloud import vision

            # Google Cloud Vision 클라이언트 초기화
            client = vision.ImageAnnotatorClient()

            # 이미지 파일 읽기
            with open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # OCR 요청
            response = client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                # 전체 텍스트는 첫 번째 항목에 있음
                full_text = texts[0].description

                # 개별 텍스트 블록은 나머지 항목에 있음
                text_blocks = []
                for text in texts[1:]:
                    vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
                    text_blocks.append({
                        'text': text.description,
                        'vertices': vertices
                    })

                return full_text, {'text_blocks': text_blocks}

            return "", {}

        except ImportError:
            self.logger.error("Google Cloud Vision 라이브러리가 설치되지 않았습니다.")
            return "", {}

        except Exception as e:
            self.logger.error(f"Google Cloud Vision OCR 처리 중 오류: {e}")
            return "", {}

    def clean_ocr_text(self, text: str) -> str:
        """OCR 텍스트 정리 및 정규화"""
        # 불필요한 문자 제거
        cleaned = re.sub(r'[«»—ooаOO]', '', text)
        # 공백 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def extract_product_sections(self, text: str) -> List[str]:
        """OCR 텍스트에서 개별 상품 섹션을 분리하여 추출"""
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

    def extract_order_information(self, text: str) -> Dict[str, str]:
        """개선된 주문 정보 추출 함수"""
        order_info = {}
        
        # 발주 번호 추출
        po_match = re.search(r'PO\s*#[:\s]*(\d+)', text, re.IGNORECASE) 
        if po_match:
            order_info['po_number'] = po_match.group(1)
        
        # 선적 날짜 추출
        ship_patterns = [
            (r'Start\s+Ship[:\s]*(\d{2}/\d{2}/\d{4})', 'start_ship'),
            (r'Complete\s+Ship[:\s]*(\d{2}/\d{2}/\d{4})', 'complete_ship'),
            (r'Ship\s+Date[:\s]*(\d{2}/\d{2}/\d{4})', 'complete_ship')
        ]
        
        for pattern, key in ship_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info[key] = match.group(1)
        
        # 결제 조건 추출
        terms_pattern = r'Terms[:\s]*((?:BANK\s+TRANSFER|T/T)[^:\n]*)'
        terms_match = re.search(terms_pattern, text, re.IGNORECASE)
        if terms_match:
            order_info['terms'] = terms_match.group(1).strip()
        
        # 통화 및 총액 정보 추출
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
        
        # 총 수량 추출
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
        
        # 거래처 정보 추출
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

    def extract_product_info(self, section: str) -> Dict[str, str]:
        """상품 섹션에서 기본 제품 정보 추출"""
        product_info = {}
        
        # 제품 코드 추출
        product_code_match = re.search(r'(AJ\d+)', section)
        if product_code_match:
            product_info['product_code'] = product_code_match.group(1)
        
        # 색상 추출
        color_match = re.search(r'(BLACK LEATHER|BLACK POLIDO|WHITE LEATHER|BROWN LEATHER)', section)
        if color_match:
            product_info['color'] = color_match.group(1)
        
        # 스타일 코드 추출
        style_match = re.search(r'Style\s*[#]?(\w+)', section)
        if style_match:
            product_info['style'] = style_match.group(1)
        else:
            alt_style_match = re.search(r'[#]?\s*(FTVRM\w+)', section)
            if alt_style_match:
                product_info['style'] = alt_style_match.group(1)
        
        # 브랜드 및 시즌 추출
        brand_match = re.search(r'(TOGA VIRILIS).*?(\d{4}[SF]S\w+)', section)
        if brand_match:
            product_info['brand'] = brand_match.group(1).strip()
            product_info['season'] = brand_match.group(2)
        
        # 가격 정보 추출
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

    def extract_sizes_and_quantities(self, section: str) -> List[Tuple[str, str]]:
        """상품 섹션에서 사이즈 및 수량 정보 추출"""
        if not section or not isinstance(section, str):
            return []
        
        # 사이즈 추출
        sizes = re.findall(r'\b(39|40|41|42|43|44|45|46)\b', section)
        
        # 수량 추출
        quantities = re.findall(r'\b([1-9]\d?)\b', section)
        
        # 사이즈와 수량의 수가 맞지 않을 경우
        if len(sizes) != len(quantities):
            # 기본 수량 1로 설정
            quantities = ['1'] * len(sizes)
        
        # 사이즈와 수량 쌍 생성
        size_quantity_pairs = list(zip(sizes, quantities))
        
        return size_quantity_pairs

    def generate_custom_code(self, product_info: Dict[str, str], size: str) -> str:
        """품번코드 생성"""
        # 기본값 설정
        style = product_info.get('style', '')
        color = product_info.get('color', '')
        product_code = product_info.get('product_code', '')
        
        # 연도 추출
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
            # 기본 품번코드 형식
            custom_code = f"{year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
        
        return custom_code

    def process_pdf(self, pdf_path: str, output_dir: Optional[str] = None, verbose: bool = True) -> Tuple[pd.DataFrame, Optional[str]]:
        """PDF 인보이스에서 OCR 처리 후 데이터 추출 및 엑셀 저장"""
        # 이미지로 변환
        image_paths = self.pdf_to_images(pdf_path)
        
        if not image_paths:
            self.logger.error("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
            return pd.DataFrame(), None
        
        all_products = []
        
        # 각 이미지에 OCR 적용
        for image_path in image_paths:
            # OCR 텍스트 추출
            ocr_text, _ = self.extract_text_with_improved_ocr(image_path)
            
            # 텍스트 정리
            cleaned_text = self.clean_ocr_text(ocr_text)
            
            # 선적 정보 추출
            shipping_info = self.extract_order_information(cleaned_text)
            
            # 상품 섹션 분리
            product_sections = self.extract_product_sections(cleaned_text)
            
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
                        'Total_Amount': shipping_info.get('total_amount', ''),
                        'PO_Number': shipping_info.get('po_number', ''),
                        'Shipping_Terms': shipping_info.get('terms', '')
                    }
                    
                    all_products.append(product_data)
        
        # 데이터프레임 생성
        if all_products:
            df_result = pd.DataFrame(all_products)
            
            # 출력 디렉토리 설정
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"product_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                df_result.to_excel(output_file, index=False)
                return df_result, output_file
            
            return df_result, None
        
        return pd.DataFrame(), None