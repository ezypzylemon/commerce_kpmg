import os
import tempfile
import cv2
import numpy as np
from pdf2image import convert_from_path
import pandas as pd
from datetime import datetime
import re
import logging
import json
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

    def pdf_to_images(self, pdf_path: str, dpi: int = 300, first_page: int = 1, last_page: int = 1) -> List[str]:
        """PDF 파일을 고해상도 이미지로 변환 (특정 페이지만 처리)"""
        try:
            images = convert_from_path(pdf_path, dpi=dpi, first_page=first_page, last_page=last_page)
            image_paths = []
            
            for i, image in enumerate(images):
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_path = os.path.join(self.temp_dir, f"temp_page_{i}_{timestamp}.jpg")
                image.save(image_path, "JPEG", quality=100)  # 최대 품질로 저장
                image_paths.append(image_path)
            
            self.logger.info(f"PDF의 {first_page}~{last_page} 페이지를 {len(images)}개의 이미지로 변환했습니다.")
            return image_paths
        except Exception as e:
            self.logger.error(f"PDF 변환 오류: {e}")
            
            return []

    def extract_text_from_region(self, image, region, retry_ocr=True):
        """이미지의 특정 영역에서 텍스트를 추출"""
        try:
            # 영역 좌표 가져오기
            x = region["x"]
            y = region["y"]
            width = region["width"]
            height = region["height"]
            
            # 이미지 경계 확인
            img_height, img_width = image.shape[:2]
            
            # 좌표가 이미지 경계를 벗어나는 경우 조정
            if x >= img_width or y >= img_height:
                if retry_ocr:
                    # 첫 번째 시도가 실패했다면 원점에서 가깝게 조정
                    x = min(x, img_width - 1)
                    y = min(y, img_height - 1)
                else:
                    return ""
            
            # 경계를 넘어가지 않도록 조정
            x = max(0, min(x, img_width-1))
            y = max(0, min(y, img_height-1))
            width = min(width, img_width - x)
            height = min(height, img_height - y)
            
            # 영역이 너무 작으면 확장
            min_width, min_height = 10, 10
            if width < min_width:
                width = min(min_width, img_width - x)
            if height < min_height:
                height = min(min_height, img_height - y)
            
            # 영역 잘라내기
            region_img = image[y:y+height, x:x+width]
            
            # 영역이 비어있는지 확인
            if region_img.size == 0:
                return ""
            
            # OCR 수행
            _, buffer = cv2.imencode('.jpg', region_img)
            byte_img = buffer.tobytes()
            vision_image = vision.Image(content=byte_img)
            
            response = self.vision_client.text_detection(image=vision_image)
            
            # 오류 처리
            if response.error.message:
                if retry_ocr:
                    # 첫 번째 시도가 실패했다면 영역을 확장하여 재시도
                    expanded_region = {
                        "x": max(0, x - 5),
                        "y": max(0, y - 5),
                        "width": width + 10,
                        "height": height + 10
                    }
                    return self.extract_text_from_region(image, expanded_region, retry_ocr=False)
                return ""
            
            # 텍스트 추출
            if response.text_annotations:
                return response.text_annotations[0].description.strip()
            
            # 텍스트가 없는 경우 재시도
            if retry_ocr:
                # 영역을 확장하여 재시도
                expanded_region = {
                    "x": max(0, x - 5),
                    "y": max(0, y - 5),
                    "width": width + 10,
                    "height": height + 10
                }
                return self.extract_text_from_region(image, expanded_region, retry_ocr=False)
            
            return ""
                
        except Exception as e:
            if retry_ocr:
                try:
                    # 오류 발생 시 영역을 확장하여 재시도
                    expanded_region = {
                        "x": max(0, region.get("x", 0) - 5),
                        "y": max(0, region.get("y", 0) - 5),
                        "width": region.get("width", 20) + 10,
                        "height": region.get("height", 20) + 10
                    }
                    return self.extract_text_from_region(image, expanded_region, retry_ocr=False)
                except:
                    return ""
            return ""

    def normalize_price(self, price_text, item_quantity=None, unit_price=None):
        """
        금액 형식을 정규화하여 'EUR 1540.00' 형식으로 반환
        쉼표를 제거하고 소수점 두 자리까지 표현
        """
        if not price_text:
            return price_text

        # 통화 기호 추출 (기본값은 EUR)
        currency = "EUR"
        if "EUR" in price_text:
            currency = "EUR"
        elif "$" in price_text:
            currency = "$"

        # 모든 쉼표 제거 및 숫자 추출
        price_text_no_comma = price_text.replace(',', '')
        number_match = re.search(r'(\d+(?:\.\d+)?)', price_text_no_comma)

        if not number_match:
            return price_text

        extracted_number = number_match.group(1)

        try:
            # 문자열을 부동소수점으로 변환
            number = float(extracted_number)

            # 항상 소수점 두 자리까지 표현
            return f"{currency} {number:.2f}"

        except ValueError:
            return price_text

    def standardize_model_info(self, model_text):
        """
        모델 텍스트에서 모델 코드와 설명을 추출하고 표준화합니다.
        
        Args:
            model_text (str): 원본 모델 텍스트
            
        Returns:
            tuple: (model_code, model_description, full_model)
        """
        # 줄바꿈 문자와 연속된 공백 제거
        model_text = ' '.join(model_text.replace('\n', ' ').split())
        
        # 다양한 모델 코드 패턴 시도 (A로 시작하고 J, R, C, S, L 등이 뒤따르는 패턴)
        model_code_match = re.search(r'(A[JRCSLK]\d+)', model_text)
        
        if not model_code_match:
            # 모델 코드를 찾지 못한 경우
            return model_text, '', model_text
        
        # 모델 코드 추출
        model_code = model_code_match.group(1)
        
        # 모델 코드 이후 텍스트를 설명으로 처리
        # 코드가 여러 번 나타날 수 있으므로 첫 번째 발견 위치에서 잘라냄
        code_pos = model_text.find(model_code)
        desc_start = code_pos + len(model_code)
        model_description = model_text[desc_start:].strip()
        
        # 설명 시작 부분의 하이픈과 공백 정리
        model_description = re.sub(r'^[-\s]+|[-\s]+$', '', model_description)
        
        # 모델명 조합 (코드와 설명 사이에 하이픈 추가)
        if model_description:
            full_model = f"{model_code}-{model_description}"
        else:
            full_model = model_code
        
        return model_code, model_description, full_model

    def extract_and_clean_model_name(self, model_text):
        """
        모델명을 추출하고 정리하는 강력한 함수
        
        1. 개행 문자 제거
        2. 연속된 공백 제거
        3. 모델 코드 추출
        4. 모델 설명 정리
        """
        # 개행 문자를 공백으로 대체하고 여러 공백을 단일 공백으로 줄임
        cleaned_text = ' '.join(model_text.split())
        
        # 모델 코드 추출
        model_code_match = re.search(r'(AJ\d+)', cleaned_text)
        if not model_code_match:
            return cleaned_text
        
        model_code = model_code_match.group(1)
        
        # 모델 코드 제거 후 남은 텍스트
        model_description = cleaned_text.replace(model_code, '').strip()
        
        # 하이픈으로 시작하는 특수 문자 제거
        model_description = model_description.lstrip('-').strip()
        
        # 최종 모델명 구성
        return f"{model_code}-{model_description}"

    def adjust_size_quantities(self, sizes_list):
        """수량 리스트를 39-46 형식으로 변환"""
        converted_sizes = {}
        for size, quantity in zip(range(39, 45), sizes_list):
            converted_sizes[size] = int(quantity)
        
        # 45, 46 사이즈는 0으로 고정
        converted_sizes[45] = 0
        converted_sizes[46] = 0
        
        return converted_sizes

    def _get_config_path(self, config_name: str) -> str:
        """설정 파일 경로 반환"""
        # 현재 모듈 디렉토리 기준으로 설정 파일 경로 찾기
        module_dir = os.path.dirname(__file__)
        config_dir = os.path.join(module_dir, 'config')
        
        # 설정 디렉토리가 없으면 생성
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, config_name)
        
        if not os.path.exists(config_path):
            self.logger.warning(f"설정 파일이 없습니다: {config_path}")
            
        return config_path

    def process_pdf(self, pdf_path: str, output_dir: Optional[str] = None, 
                    processing_method: str = "standard", verbose: bool = True) -> Tuple[pd.DataFrame, Optional[str]]:
        """PDF 문서 처리 (처리 방식 선택 가능)"""
        
        # 처리 방식에 따라 다른 메소드 호출
        if processing_method == "invoice_json":
            # 인보이스 특화 처리 (invojson.py 코드 사용)
            json_path = self._get_config_path("invoice_data.json")
            return self._process_invoice_with_json(pdf_path, json_path, output_dir)
        
        elif processing_method == "order_json":
            # 오더시트 특화 처리 (newreorder.py 코드 사용)
            json_path = self._get_config_path("order_data.json")
            return self._process_order_sheet_with_json(pdf_path, json_path, output_dir)
        
        else:
            # 기본 처리 방식 - 텍스트 기반 파싱
            return self._process_pdf_standard(pdf_path, output_dir, verbose)

    def _process_pdf_standard(self, pdf_path: str, output_dir: Optional[str] = None, verbose: bool = True) -> Tuple[pd.DataFrame, Optional[str]]:
        """기본 텍스트 기반 PDF 처리 방식"""
        # 전체 텍스트 추출 (첫 페이지만)
        image_paths = self.pdf_to_images(pdf_path, first_page=1, last_page=1)
        if not image_paths:
            self.logger.error("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
            return pd.DataFrame(), None
            
        # 이미지에서 OCR 텍스트 추출
        image_path = image_paths[0]
        
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"이미지를 로드할 수 없습니다: {image_path}")
                return pd.DataFrame(), None
                
            # OCR 텍스트 추출
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
                
            vision_image = vision.Image(content=content)
            response = self.vision_client.document_text_detection(image=vision_image)
            
            if response.error.message:
                self.logger.error(f"Google Vision API 오류: {response.error.message}")
                return pd.DataFrame(), None
                
            full_text = response.full_text_annotation.text
            
            # 주문 정보 추출
            order_info = self._extract_order_info(full_text)
            
            # 품목 정보 추출 (정규식 기반)
            products = self._extract_products(full_text)
            
            # 데이터프레임 생성
            if products:
                df_result = pd.DataFrame(products)
                
                # 출력 디렉토리 설정
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    output_file = os.path.join(output_dir, f"standard_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                    df_result.to_excel(output_file, index=False)
                    self.logger.info(f"데이터를 엑셀 파일로 저장했습니다: {output_file}")
                    return df_result, output_file
                
                return df_result, None
            
            self.logger.warning("추출된 상품 정보가 없습니다.")
            return pd.DataFrame(), None
            
        except Exception as e:
            self.logger.error(f"표준 처리 중 오류: {e}")
            return pd.DataFrame(), None
        finally:
            # 임시 파일 정리
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)

    def _extract_order_info(self, text: str) -> Dict[str, str]:
        """OCR 텍스트에서 주문 정보 추출"""
        order_info = {}
        
        # 주문 번호 추출
        po_match = re.search(r'PO#:\s*(\d+)', text, re.IGNORECASE)
        if po_match:
            order_info['po_number'] = po_match.group(1)
        
        # 날짜 추출
        date_match = re.search(r'Created:\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if date_match:
            order_info['created_date'] = date_match.group(1)
        
        # 브랜드 및 시즌 추출
        brand_match = re.search(r'(TOGA\s+VIRILIS).*?(\d{4}[SF]S\w*)', text, re.DOTALL | re.IGNORECASE)
        if brand_match:
            order_info['brand'] = brand_match.group(1)
            order_info['season'] = brand_match.group(2)
        
        return order_info

    def _extract_products(self, text: str) -> List[Dict[str, str]]:
        """OCR 텍스트에서 상품 정보 추출"""
        products = []
        
        # AJ 코드로 시작하는 상품 코드 패턴
        product_pattern = r'(AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE|POLIDO|LEATHER).*?)(?=AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE|POLIDO|LEATHER)|$)'
        
        # 상품 섹션 찾기
        product_sections = re.findall(product_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for section in product_sections:
            # 제품 코드 추출
            product_code_match = re.search(r'(AJ\d+|A\d)', section)
            if not product_code_match:
                continue
                
            product_code = product_code_match.group(1)
            
            # 색상 추출
            color_match = re.search(r'(BLACK LEATHER|BLACK POLIDO|WHITE LEATHER|BROWN LEATHER)', section)
            color = color_match.group(1) if color_match else "Unknown"
            
            # 사이즈별 수량 추출 (간단한 버전)
            size_qty_matches = re.findall(r'(39|40|41|42|43|44|45|46)\s+(\d+)', section)
            
            # 제품 데이터 생성
            if size_qty_matches:
                for size, qty in size_qty_matches:
                    product = {
                        'product_code': product_code,
                        'color': color,
                        'size': size,
                        'quantity': qty
                    }
                    products.append(product)
            else:
                # 매칭되는 사이즈-수량이 없는 경우 기본 항목 추가
                product = {
                    'product_code': product_code,
                    'color': color,
                    'size': '',
                    'quantity': '0'
                }
                products.append(product)
        
        return products

    def _process_invoice_with_json(self, pdf_path: str, json_path: str, output_dir: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[str]]:
        """인보이스 특화 처리 (invojson.py 기반)"""
        try:
            # 출력 폴더 생성
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            else:
                output_dir = self.temp_dir
            
            # JSON 파일 로드
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # PDF를 이미지로 변환
            image_paths = self.pdf_to_images(pdf_path, dpi=300)
            
            if not image_paths:
                self.logger.error(f"PDF 변환 실패: {pdf_path}")
                return pd.DataFrame(), None
            
            # 첫 번째 페이지만 처리
            image_path = image_paths[0]
            image = cv2.imread(image_path)
            
            if image is None:
                self.logger.error(f"이미지를 로드할 수 없습니다: {image_path}")
                return pd.DataFrame(), None
            
            # 이미지 크기 확인 및 비율 계산
            img_height, img_width = image.shape[:2]
            
            # JSON 문서 크기와 실제 이미지 크기 비교 및 비율 계산
            json_width = json_data.get('document_bounds', {}).get('end_x', img_width)
            json_height = json_data.get('document_bounds', {}).get('end_y', img_height)
            
            # 비율 계산 (기본값 = 1.0, 좌표 변경 없음)
            scale_x = img_width / json_width if json_width > 0 else 1.0
            scale_y = img_height / json_height if json_height > 0 else 1.0
            
            # JSON 좌표 스케일링 함수 정의
            def scale_region(region):
                """JSON 좌표를 실제 이미지 크기에 맞게 스케일링"""
                scaled = {
                    "x": int(region.get("x", 0) * scale_x),
                    "y": int(region.get("y", 0) * scale_y),
                    "width": max(1, int(region.get("width", 10) * scale_x)),
                    "height": max(1, int(region.get("height", 10) * scale_y))
                }
                return scaled
            
            # 좌표 정보에 스케일링 적용
            scaled_json = json_data.copy()
            
            # shipping_dates 스케일링
            if "shipping_dates" in scaled_json:
                shipping_dates = scaled_json["shipping_dates"]
                if isinstance(shipping_dates, dict):
                    if "start_date" in shipping_dates and isinstance(shipping_dates["start_date"], dict):
                        scaled_json["shipping_dates"]["start_date"] = scale_region(shipping_dates["start_date"])
                    if "end_date" in shipping_dates and isinstance(shipping_dates["end_date"], dict):
                        scaled_json["shipping_dates"]["end_date"] = scale_region(shipping_dates["end_date"])
            
# products 스케일링
            if "products" in scaled_json and isinstance(scaled_json["products"], list):
                for i, product in enumerate(scaled_json["products"]):
                    if not isinstance(product, dict):
                        continue
                        
                    for key in product:
                        if key == "sizes" and isinstance(product[key], dict):
                            for size in product[key]:
                                if isinstance(product[key][size], dict):
                                    product[key][size] = scale_region(product[key][size])
                        elif isinstance(product[key], dict) and all(k in product[key] for k in ["x", "y", "width", "height"]):
                            product[key] = scale_region(product[key])
            
            # summary 스케일링
            if "summary" in scaled_json and isinstance(scaled_json["summary"], dict):
                for key in scaled_json["summary"]:
                    if isinstance(scaled_json["summary"][key], dict):
                        scaled_json["summary"][key] = scale_region(scaled_json["summary"][key])
            
            # 메타데이터 추출
            metadata = self._extract_metadata_from_json(image, scaled_json, image_path)
            
            # 제품 데이터 추출 (스케일 조정된 JSON 사용)
            products_data = self._extract_product_data_from_json(image, scaled_json)
            
            # 구조화된 데이터 생성
            structured_data = self._clean_extracted_data(products_data, metadata)
            
            # 데이터프레임 생성
            if structured_data:
                # 모든 가능한 사이즈 열 찾기
                all_sizes = set()
                for item in structured_data:
                    for key in item.keys():
                        if key.startswith('사이즈_'):
                            all_sizes.add(key)
                
                # 정렬된 사이즈 열 리스트
                sorted_sizes = sorted(list(all_sizes), key=lambda x: int(x.split('_')[1]))
                
                # 모든 아이템에 모든 사이즈 열 추가 (값이 없으면 0)
                for item in structured_data:
                    for size in sorted_sizes:
                        if size not in item:
                            item[size] = '0'
                
                # 기본 열 순서 정의
                columns = ['주문_ID', '브랜드', '시즌', '선적_시작일', '선적_완료일', 
                        '모델코드', '모델명', '모델설명', '스타일코드', '컬러', '구매가', '판매가'] + sorted_sizes + ['총_수량', '총_금액']
                
                # 데이터프레임 생성
                df = pd.DataFrame(structured_data)
                
                # 누락된 열 처리
                for col in columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # 조정된 컬럼 리스트 생성 (실제 존재하는 컬럼만 포함)
                adjusted_columns = [col for col in columns if col in df.columns]
                
                # 열 순서 조정
                df = df[adjusted_columns]
                
                # 엑셀 파일로 저장
                output_file = os.path.join(output_dir, f"invoice_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                df.to_excel(output_file, index=False)
                self.logger.info(f"인보이스 데이터를 엑셀 파일로 저장했습니다: {output_file}")
                
                return df, output_file
            
            self.logger.warning("추출된 구조화된 데이터가 없습니다.")
            return pd.DataFrame(), None
            
        except Exception as e:
            self.logger.error(f"인보이스 처리 중 오류: {e}")
            return pd.DataFrame(), None
        finally:
            # 임시 파일 정리
            for path in image_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass

    def _extract_metadata_from_json(self, image, json_data, image_path):
        """JSON 파일과 이미지를 사용하여 메타데이터 추출"""
        metadata = {
            'brand': '',
            'season': '',
            'start_ship': '',
            'complete_ship': '',
            'order_id': ''  # 빈 값으로 유지하고 추출 시도하지 않음
        }

        if json_data.get("products") and len(json_data["products"]) > 0:
            first_product = json_data["products"][0]

            if "brand" in first_product:
                metadata['brand'] = self.extract_text_from_region(image, first_product["brand"])

            if "season" in first_product:
                metadata['season'] = self.extract_text_from_region(image, first_product["season"])

        if "shipping_dates" in json_data:
            shipping_dates = json_data["shipping_dates"]

            if "start_date" in shipping_dates:
                metadata['start_ship'] = self.extract_text_from_region(image, shipping_dates["start_date"])

            if "end_date" in shipping_dates:
                metadata['complete_ship'] = self.extract_text_from_region(image, shipping_dates["end_date"])

        # 주문 ID 추출 코드 제거
        # 기존에 있던 try-except 블록 전체 삭제

        return metadata

    def _extract_product_data_from_json(self, image, json_data):
        """JSON 파일과 이미지를 사용하여 제품 데이터 추출"""
        products_data = []
        
        for product_idx, product_json in enumerate(json_data.get("products", [])):
            product = {}
            
            # 모델명/코드 추출
            if "name" in product_json:
                # 원본 텍스트 추출
                model_text = self.extract_text_from_region(image, product_json["name"])
                
                # 모델 정보 표준화
                model_code, model_description, full_model = self.standardize_model_info(model_text)
                
                product['model'] = model_code
                product['model_description'] = model_description
                product['full_model'] = full_model
            
            # 스타일 코드 추출
            if "style_code" in product_json:
                product['style_code'] = self.extract_text_from_region(image, product_json["style_code"])
            
            # 브랜드 추출
            if "brand" in product_json:
                product['brand'] = self.extract_text_from_region(image, product_json["brand"])
            
            # 시즌 추출
            if "season" in product_json:
                product['season'] = self.extract_text_from_region(image, product_json["season"])
            
            # 컬러 추출
            if "color" in product_json:
                product['color'] = self.extract_text_from_region(image, product_json["color"])
            
            # 구매가 추출
            if "wholesale_price" in product_json:
                wholesale_price = self.extract_text_from_region(image, product_json["wholesale_price"])
                product['wholesale_price'] = self.normalize_price(wholesale_price)
            
            # 판매가 추출
            if "retail_price" in product_json:
                retail_price = self.extract_text_from_region(image, product_json["retail_price"])
                product['retail_price'] = self.normalize_price(retail_price)
            
            # 총 금액 추출
            if "total_price" in product_json:
                total_price = self.extract_text_from_region(image, product_json["total_price"])
                product['total_price'] = self.normalize_price(total_price, 
                                                          product.get('total_quantity'), 
                                                          product.get('wholesale_price'))
            
            # 사이즈별 수량 추출
            sizes = {}
            total_quantity = 0
            
            if "sizes" in product_json:
                for size, region in product_json["sizes"].items():
                    if size != "qty":
                        size_qty = self.extract_text_from_region(image, region)
                        
                        if not size_qty or size_qty.isspace() or not re.search(r'\d+', size_qty):
                            size_qty = "0"
                        else:
                            size_qty_match = re.search(r'\d+', size_qty)
                            if size_qty_match:
                                size_qty = size_qty_match.group(0)
                        
                        sizes[f'size_{size}'] = size_qty
                        
                        try:
                            total_quantity += int(size_qty)
                        except ValueError:
                            pass
                
                # 총 수량 추출
                if "qty" in product_json["sizes"]:
                    qty_text = self.extract_text_from_region(image, product_json["sizes"]["qty"])
                    qty_match = re.search(r'\d+', qty_text)
                    
                    if qty_match and not qty_text.isspace():
                        product['total_quantity'] = qty_match.group(0)
                    else:
                        product['total_quantity'] = str(total_quantity)
                else:
                    product['total_quantity'] = str(total_quantity)
            
            # 사이즈별 수량 추가
            product.update(sizes)
            
            # 빈 필드 확인 및 채우기
            required_fields = ['model', 'color', 'wholesale_price', 'retail_price', 'total_price', 'total_quantity']
            for field in required_fields:
                if field not in product or not product[field]:
                    if field in ['total_quantity', 'total_price']:
                        product[field] = '0'
                    elif field == 'model' and product_idx < len(json_data.get("products", [])):
                        product[field] = f"Product_{product_idx+1}"
                    else:
                        product[field] = ''
            
            products_data.append(product)
        
        return products_data

    def _clean_extracted_data(self, products_data, metadata):
        """추출된 데이터를 정리하고 구조화"""
        if not products_data:
            return None
        
        structured_data = []
        
        for product in products_data:
            # 필요 정보 구조화
            item = {
                '모델코드': product.get('model', ''),
                '모델명': product.get('full_model', ''),
                '모델설명': product.get('model_description', ''),
                '스타일코드': product.get('style_code', ''),
                '컬러': product.get('color', ''),
                '총_수량': product.get('total_quantity', '0'),
                '총_금액': product.get('total_price', '0'),
                '브랜드': product.get('brand', metadata.get('brand', '')),
                '시즌': product.get('season', metadata.get('season', '')),
                '선적_시작일': metadata.get('start_ship', ''),
                '선적_완료일': metadata.get('complete_ship', ''),
                '주문_ID': metadata.get('order_id', ''),
                '구매가': product.get('wholesale_price', ''),
                '판매가': product.get('retail_price', '')
            }
            
            # 사이즈별 수량 추가
            for key, value in product.items():
                if key.startswith('size_'):
                    size_num = key.split('_')[1]
                    item[f'사이즈_{size_num}'] = value
            
            structured_data.append(item)
        
        return structured_data

    def _process_order_sheet_with_json(self, pdf_path: str, json_path: str, output_dir: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[str]]:
            """오더시트 특화 처리 (newreorder.py 기반)"""
            try:
                # 출력 폴더 생성
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                else:
                    output_dir = self.temp_dir

                # JSON 파일 로드
                with open(json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # PDF를 이미지로 변환
                image_paths = self.pdf_to_images(pdf_path, dpi=300)

                if not image_paths:
                    self.logger.error(f"PDF 변환 실패: {pdf_path}")
                    return pd.DataFrame(), None

                # 첫 번째 페이지만 처리
                image_path = image_paths[0]
                img = cv2.imread(image_path)

                if img is None:
                    self.logger.error(f"이미지를 로드할 수 없습니다: {image_path}")
                    return pd.DataFrame(), None

                # 이미지 크기 확인
                img_height, img_width = img.shape[:2]
                self.logger.info(f"이미지 크기: {img_width}x{img_height}")

                # 디버깅용 이미지 생성 (좌표 시각화)
                debug_img = img.copy()

                # 스케일링 팩터 계산 (JSON의 document_bounds 기준으로)
                if 'document_bounds' in config:
                    # JSON에서 document_bounds 정보 추출
                    json_base_width = config['document_bounds']['end_x'] - config['document_bounds']['start_x']
                    json_base_height = config['document_bounds']['end_y'] - config['document_bounds']['start_y']
                    json_start_x = config['document_bounds']['start_x']
                    json_start_y = config['document_bounds']['start_y']

                    # 스케일링 팩터 계산
                    scale_x = img_width / json_base_width
                    scale_y = img_height / json_base_height
                
                    self.logger.info(f"문서 경계: 너비={json_base_width}, 높이={json_base_height}")
                    self.logger.info(f"스케일링 팩터: x={scale_x}, y={scale_y}")
                else:
                    # 기본값 설정 (문서 경계가 없는 경우)
                    self.logger.warning("document_bounds 정보가 없습니다. 기본값을 사용합니다.")
                    json_base_width = 1700
                    json_base_height = 2200
                    json_start_x = 0
                    json_start_y = 0
                    scale_x = img_width / json_base_width
                    scale_y = img_height / json_base_height

                # 좌표 스케일링 함수
                def scale_region(region):
                    """JSON 좌표를 실제 이미지 크기에 맞게 스케일링"""
                    # 원본 좌표
                    orig_x = region.get('x', 0)
                    orig_y = region.get('y', 0)
                    orig_width = region.get('width', 100)
                    orig_height = region.get('height', 30)

                    # 문서 경계 기준 조정된 좌표 계산
                    adjusted_x = orig_x - json_start_x
                    adjusted_y = orig_y - json_start_y

                    # 스케일링 적용
                    x = int(adjusted_x * scale_x)
                    y = int(adjusted_y * scale_y)
                    width = max(1, int(orig_width * scale_x))
                    height = max(1, int(orig_height * scale_y))

                    # 이미지 경계 확인
                    x = max(0, min(x, img_width - 1))
                    y = max(0, min(y, img_height - 1))
                    width = min(width, img_width - x)
                    height = min(height, img_height - y)

                    return {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height
                    }

                # 데이터 추출
                extracted_data = []

                # 헤더 필드 추출 (브랜드, 시즌, 날짜)
                if 'header_fields' in config:
                    header_fields = config['header_fields']

                    # 브랜드 추출
                    brand_text = ""
                    if 'brand' in header_fields:
                        brand_region = scale_region(header_fields['brand'])
                        brand_text = self.extract_text_from_region(img, brand_region)
                        # 디버깅 이미지에 영역 표시
                        cv2.rectangle(debug_img, (brand_region['x'], brand_region['y']), 
                                    (brand_region['x'] + brand_region['width'], brand_region['y'] + brand_region['height']), 
                                    (0, 0, 255), 2)
                        cv2.putText(debug_img, "Brand", (brand_region['x'], brand_region['y']-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                    # 시즌 추출
                    season_text = ""
                    if 'season' in header_fields:
                        season_region = scale_region(header_fields['season'])
                        season_text = self.extract_text_from_region(img, season_region)
                        cv2.rectangle(debug_img, (season_region['x'], season_region['y']), 
                                    (season_region['x'] + season_region['width'], season_region['y'] + season_region['height']), 
                                    (255, 0, 0), 2)
                        cv2.putText(debug_img, "Season", (season_region['x'], season_region['y']-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

                    # 날짜 추출
                    date_text = ""
                    if 'date' in header_fields:
                        date_region = scale_region(header_fields['date'])
                        date_text = self.extract_text_from_region(img, date_region)
                        cv2.rectangle(debug_img, (date_region['x'], date_region['y']), 
                                    (date_region['x'] + date_region['width'], date_region['y'] + date_region['height']), 
                                    (0, 255, 0), 2)
                        cv2.putText(debug_img, "Date", (date_region['x'], date_region['y']-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # 각 제품 행 처리
                for i, row_config in enumerate(config['product_rows']):
                    self.logger.info(f"\n제품 {i+1} 추출 시작 ---")

                    # 아이템 코드 추출
                    item_code = ""
                    if 'item_code' in row_config:
                        item_region = scale_region(row_config['item_code'])
                        item_code = self.extract_text_from_region(img, item_region)

                    # 모델명 추출
                    model_text = ""
                    if 'model' in row_config:
                        model_region = scale_region(row_config['model'])
                        model_text = self.extract_text_from_region(img, model_region)

                    # 모델명 정리
                    model_name = self.extract_and_clean_model_name(model_text)

                    # 모델 코드 추출
                    model_code_match = re.search(r'(AJ\d+|AC\d+|AR\d+|AL\d+)', model_name)
                    model_code = model_code_match.group(1) if model_code_match else ''

                    # 단가 추출
                    unit_price = ""
                    if 'unit_price' in row_config:
                        price_region = scale_region(row_config['unit_price'])
                        unit_price = self.extract_text_from_region(img, price_region)

                    # 할인율 추출
                    discount = ""
                    if 'disc_prcnt' in row_config:
                        discount_region = scale_region(row_config['disc_prcnt'])
                        discount = self.extract_text_from_region(img, discount_region)

                    # 선적 시작일 추출
                    shipping_start = ""
                    if 'shipping_start' in row_config:
                        start_region = scale_region(row_config['shipping_start'])
                        shipping_start = self.extract_text_from_region(img, start_region)

                    # 선적 완료일 추출
                    shipping_end = ""
                    if 'shipping_end' in row_config:
                        end_region = scale_region(row_config['shipping_end'])
                        shipping_end = self.extract_text_from_region(img, end_region)

                        # 수량 추출
                    sizes_quantities = []
                    for size_key in ['390', '400', '410', '420', '430', '440']:
                        if size_key in row_config['sizes']:
                            size_region = scale_region(row_config['sizes'][size_key])
                            size_quantity = self.extract_text_from_region(img, size_region)
                            # 빈 문자열이거나 숫자가 아닌 경우 0으로 처리
                            qty = 0
                            if size_quantity and size_quantity.strip() and re.search(r'\d+', size_quantity):
                                qty_match = re.search(r'\d+', size_quantity)
                                if qty_match:
                                    qty = int(qty_match.group(0))
                            sizes_quantities.append(qty)
                        else:
                            sizes_quantities.append(0)

                    # 합계 수량 추출
                    total_qty = 0
                    if 'total' in row_config['sizes']:
                        total_region = scale_region(row_config['sizes']['total'])
                        total_qty_text = self.extract_text_from_region(img, total_region)
                        if total_qty_text and total_qty_text.strip() and re.search(r'\d+', total_qty_text):
                            qty_match = re.search(r'\d+', total_qty_text)
                            if qty_match:
                                total_qty = int(qty_match.group(0))
                    else:
                        total_qty = sum(sizes_quantities)  # 직접 계산

                    # 단가 정규화
                    normalized_unit_price = self.normalize_price(unit_price)

                    # 총 금액 추출 또는 계산
                    total_price = ""
                    if 'total_price' in row_config:
                        price_region = scale_region(row_config['total_price'])
                        total_price = self.extract_text_from_region(img, price_region)
                        total_price = self.normalize_price(total_price)
                    else:
                        # 총 금액 계산
                        try:
                            # 단가에서 숫자만 추출
                            unit_price_text = normalized_unit_price.replace('EUR ', '').replace(',', '')
                            unit_price_value = float(re.search(r'\d+\.?\d*', unit_price_text).group(0))

                            # 총 금액 = 단가 x 수량
                            total_amount = unit_price_value * total_qty
                            total_price = f"EUR {total_amount:.2f}"
                        except (ValueError, TypeError, AttributeError):
                            total_price = 'EUR 0.00'

                    # 사이즈 변환 (390->39, 400->40, ...)
                    converted_sizes = self.adjust_size_quantities(sizes_quantities)

                    # 제품 정보 딕셔너리 생성
                    product = {
                        '브랜드': brand_text,
                        '시즌': season_text,
                        '날짜': date_text,
                        '스타일코드': item_code,
                        '모델코드': model_code,
                        '모델명': model_name,
                        '구매가': normalized_unit_price,
                        '할인율': discount,
                        '선적_시작일': shipping_start,
                        '선적_완료일': shipping_end,
                        '총_수량': total_qty,
                        '총_금액': total_price
                    }

                    # 사이즈별 수량을 개별 컬럼으로 추가
                    for size in range(39, 47):
                        product[f'사이즈_{size}'] = converted_sizes.get(size, 0)

                    extracted_data.append(product)

                # 디버깅 이미지 저장
                debug_image_path = os.path.join(output_dir, "debug_regions.jpg")
                cv2.imwrite(debug_image_path, debug_img)
                self.logger.info(f"디버깅 이미지를 저장했습니다: {debug_image_path}")

                # 엑셀로 저장
                if extracted_data:
                    # 데이터프레임 생성
                    df = pd.DataFrame(extracted_data)

                    # 컬럼 순서 지정
                    columns_order = [
                        '브랜드', '시즌', '날짜', '스타일코드', '모델코드', '모델명', 
                        '구매가', '할인율', '선적_시작일', '선적_완료일', '총_수량', '총_금액'
                    ] + [f'사이즈_{size}' for size in range(39, 47)]

                    # 누락된 컬럼 확인
                    for col in columns_order:
                        if col not in df.columns:
                            df[col] = ''

                    # 존재하는 컬럼만 사용
                    valid_columns = [col for col in columns_order if col in df.columns]
                    df = df[valid_columns]

                    # 엑셀 파일 경로 생성
                    output_file = os.path.join(output_dir, f"order_sheet_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

                    # 엑셀로 저장
                    df.to_excel(output_file, index=False)
                    self.logger.info(f"오더시트 데이터를 엑셀 파일로 저장했습니다: {output_file}")
                
                    return df, output_file

                self.logger.warning("추출된 오더시트 데이터가 없습니다.")
                return pd.DataFrame(), None

            except Exception as e:
                self.logger.error(f"오더시트 처리 중 오류: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                return pd.DataFrame(), None
            finally:
                # 임시 파일 정리
                for path in image_paths:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except:
                            pass