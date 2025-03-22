import os
import sys
import glob
import cv2
import numpy as np
import pandas as pd
from google.cloud import vision
import io
import re
from datetime import datetime
import tempfile
from pdf2image import convert_from_path
from typing import List, Dict, Tuple, Optional, Union, Any
import logging
from collections import defaultdict

# 내부 모듈 임포트
from ocr_core import TableDetector, DocumentProcessor, TableContentExtractor

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedOCRProcessor:
    """개선된 OCR 처리기"""
    
    def __init__(self, yolo_model_path='best.pt'):
        """OCR 프로세서 초기화"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Google Cloud Vision API 클라이언트 초기화
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision API 클라이언트가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logger.error(f"Google Cloud Vision API 클라이언트 초기화 실패: {e}")
            self.vision_client = None
        
        # 테이블 감지 및 분석기 초기화
        self.table_detector = TableDetector(model_path=yolo_model_path)
        
        # 문서 처리기 초기화
        self.document_processor = DocumentProcessor(self.vision_client)
        
        # 테이블 내용 추출기 초기화
        self.table_extractor = TableContentExtractor(self.vision_client)
        
        # 기본 사이즈 배열 (유럽 사이즈)
        self.default_sizes = ['39', '40', '41', '42', '43', '44', '45', '46']
    
    def process_pdf(self, pdf_path: str, output_dir: Optional[str] = None) -> pd.DataFrame:
        """PDF 파일 처리 및 데이터 추출 메인 함수"""
        logger.info(f"PDF 파일 처리 시작: {pdf_path}")
        
        # 1. PDF를 이미지로 변환
        image_paths = self.pdf_to_images(pdf_path)
        
        if not image_paths:
            logger.error("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
            return pd.DataFrame()
        
        try:
            all_products = []
            all_size_qty_maps = {}
            
            # 각 페이지별 처리
            for i, image_path in enumerate(image_paths):
                logger.info(f"페이지 {i+1} 처리 중...")
                
                # 2. 전체 문서 OCR 텍스트 추출
                ocr_result = self.document_processor.extract_text_with_vision(image_path)
                full_text = ocr_result['full_text']
                
                # 3. 문서 유형 감지
                doc_type = self.document_processor.detect_document_type(full_text)
                logger.info(f"문서 유형 감지 결과: {doc_type}")
                
                # 4. 문서 메타데이터 추출
                metadata = self.document_processor.extract_document_metadata(full_text, doc_type)
                
                # 5. 테이블 영역 감지 (하이브리드 접근법)
                # - 먼저 기본 전처리 후 테이블 감지 시도
                # - 실패 시 고급 전처리 적용 후 재시도
                tables = self.table_detector.detect_tables(image_path)
                
                # 테이블 감지 실패 시 고급 전처리 적용
                if not tables:
                    logger.info("기본 테이블 감지 실패, 고급 전처리 적용 후 재시도...")
                    tables = self.table_detector.detect_tables(image_path, use_advanced_preprocess=True)
                
                products = []
                size_qty_maps = {}
                
                if tables:
                    logger.info(f"{len(tables)}개의 테이블 영역 감지됨")
                    
                    # 각 테이블 처리
                    for table_info in tables:
                        # 테이블 구조 추출
                        table_structure = self.table_detector.extract_table_structure(table_info['image_path'])
                        
                        # 테이블 내용 추출
                        table_content = self.table_extractor.extract_table_content(table_info['image_path'], table_structure)
                        
                        # 테이블 헤더 분석
                        headers_info = self.table_extractor.analyze_table_headers(
                            table_content['grid'], 
                            table_content['raw_text']
                        )
                        
                        # 사이즈-수량 매핑 추출
                        table_size_qty_maps = self.table_extractor.extract_size_quantity_mapping(
                            table_content['grid'], 
                            headers_info,
                            table_content['raw_text']
                        )
                        
                        # 통합 사이즈-수량 맵에 추가
                        size_qty_maps.update(table_size_qty_maps)
                        
                        # 제품 정보 추출
                        table_products = self.table_extractor.extract_product_information(
                            table_content['grid'], 
                            table_content['raw_text'], 
                            metadata
                        )
                        
                        # 제품 목록에 추가
                        products.extend(table_products)
                
                # 테이블 인식 실패 시 텍스트 기반 백업 방법 사용
                if not products:
                    logger.info("테이블 인식 실패 또는 테이블에서 제품 정보 추출 실패, 텍스트 기반 추출 시도...")
                    
                    # 텍스트 기반 제품 정보 추출
                    text_products = self.extract_product_info_from_text(full_text, metadata)
                    products.extend(text_products)
                    
                    # 텍스트 기반 사이즈-수량 매핑 추출
                    text_size_qty_maps = self.extract_size_quantity_from_text(full_text, doc_type)
                    size_qty_maps.update(text_size_qty_maps)
                
                # 사이즈-수량 매핑 적용하여 제품 정보 업데이트
                updated_products = self.table_extractor.create_size_quantity_dataframe(products, size_qty_maps)
                
                # 현재 페이지의 결과 추가
                all_products.extend(updated_products)
                all_size_qty_maps.update(size_qty_maps)
                
                # 임시 파일 삭제
                if os.path.exists(image_path):
                    os.remove(image_path)
                
                # 테이블 이미지 파일 삭제
                for table in tables:
                    table_path = table.get('image_path', '')
                    if os.path.exists(table_path):
                        os.remove(table_path)
            
            # 결과 데이터프레임 생성
            if all_products:
                df = pd.DataFrame(all_products)
                
                # 데이터 후처리
                df = self.post_process_dataframe(df)
                
                # 엑셀 파일 저장 (선택적)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_file = os.path.join(output_dir, f"extracted_data_{timestamp}.xlsx")
                    df.to_excel(output_file, index=False)
                    logger.info(f"데이터를 엑셀로 저장했습니다: {output_file}")
                
                return df
            else:
                logger.warning("추출된 제품 정보가 없습니다.")
                return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())  # 상세 오류 로그 추가
            return pd.DataFrame()
        
        finally:
            # 남은 임시 파일 정리
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """PDF 파일을 고해상도 이미지로 변환"""
        try:
            # PDF의 모든 페이지 변환
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, image in enumerate(images):
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_path = os.path.join(self.temp_dir, f"page_{i}_{timestamp}.jpg")
                image.save(image_path, "JPEG", quality=100)  # 최대 품질로 저장
                image_paths.append(image_path)
            
            logger.info(f"PDF를 {len(images)}개의 이미지로 변환했습니다.")
            return image_paths
        except Exception as e:
            logger.error(f"PDF 변환 오류: {e}")
            return []
    
    def extract_product_info_from_text(self, text: str, metadata: Dict) -> List[Dict]:
        """텍스트 기반 제품 정보 추출 (테이블 인식 실패 시 대체 방법)"""
        products = []
        
        # 제품 섹션 패턴 (AJ 코드부터 다음 AJ 코드 전까지)
        product_pattern = r'(AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN).*?)(?=AJ\d+|$)'
        product_sections = re.findall(product_pattern, text, re.DOTALL)
        
        for section in product_sections:
            # 제품 코드 추출
            product_code_match = re.search(r'(AJ\d+)', section)
            if not product_code_match:
                continue
            
            product_code = product_code_match.group(1)
            
            # 색상 추출
            color_match = re.search(r'(BLACK\s+(?:LEATHER|POLIDO)|WHITE\s+LEATHER|BROWN\s+LEATHER)', section)
            color = color_match.group(1) if color_match else "BLACK LEATHER"
            
            # 스타일 추출
            style_match = re.search(r'Style\s+[#]?(\w+)|#?(\w+)|(FTVRM\w+)', section, re.IGNORECASE)
            style = ""
            if style_match:
                for i in range(1, 4):
                    if style_match.group(i):
                        style = style_match.group(i)
                        break
            
            # 가격 추출
            wholesale_match = re.search(r'Wholesale:?\s*(?:EUR)?\s*(\d+\.\d+)', section)
            wholesale_price = wholesale_match.group(1) if wholesale_match else ""
            
            # 다른 가격 패턴 검색
            if not wholesale_price:
                price_match = re.search(r'(\d+\.\d+)\s*EUR', section)
                wholesale_price = price_match.group(1) if price_match else ""
            
            retail_match = re.search(r'(?:Sugg\.|Suggested)\s+Retail:?\s*(?:EUR)?\s*(\d+\.\d+)', section)
            retail_price = retail_match.group(1) if retail_match else ""
            
            # 총수량 추출
            total_qty = ""
            qty_match = re.search(r'(?:TOTAL|Total|Qty).*?(\d+)$', section, re.MULTILINE)
            if qty_match:
                total_qty = qty_match.group(1)
            
            # 제품 정보 저장
            product_data = {
                'Product_Code': product_code,
                'Style': style,
                'Color': color,
                'Wholesale_Price': wholesale_price,
                'Retail_Price': retail_price,
                'Total_Qty': total_qty,
                'Brand': metadata.get('brand', 'TOGA VIRILIS'),
                'Season': metadata.get('season', '2024SS'),
                'Document_Type': metadata.get('document_type', 'unknown')
            }
            
            # 문서 유형별 추가 필드
            if metadata.get('document_type') == 'purchase_order':
                product_data.update({
                    'PO_Number': metadata.get('po_number', ''),
                    'Created_Date': metadata.get('created_date', ''),
                    'Total_Amount': metadata.get('total_amount', ''),
                    'Currency': metadata.get('currency', 'EUR')
                })
            elif metadata.get('document_type') == 'order_confirmation':
                product_data.update({
                    'Invoice_ID': metadata.get('invoice_id', ''),
                    'Date': metadata.get('date', ''),
                    'Payment_Terms': metadata.get('payment_terms', ''),
                    'Total_Amount': metadata.get('total_amount', ''),
                    'Currency': metadata.get('currency', 'EUR')
                })
            
            # 각 사이즈별 수량 칼럼 추가 (나중에 채움)
            for size in self.default_sizes:
                product_data[f'Size_{size}'] = 0
            
            products.append(product_data)
        
        # ORDER CONFIRMATION 특화 패턴
        if not products and "ORDER CONFIRMATION" in text.upper():
            # 패턴: [FTVRM 코드] [AJ 코드] - [설명] [가격] [0.00%] [날짜] [총액] [수량들]
            pattern = r'(FTVRM\w+).*?(AJ\d+).*?(BLACK\s+(?:LEATHER|POLIDO)|WHITE\s+LEATHER).*?(\d+\.\d+).*?(\d+\.\d+)'
            matches = re.findall(pattern, text)
            
            for match in matches:
                ftvrm_code, product_code, color, price, total = match
                
                # 제품 정보 저장
                product_data = {
                    'Product_Code': product_code,
                    'Style': ftvrm_code,
                    'Color': color.strip(),
                    'Wholesale_Price': price,
                    'Total_Amount': total,
                    'Brand': metadata.get('brand', 'TOGA VIRILIS'),
                    'Season': metadata.get('season', '2024SS'),
                    'Document_Type': 'order_confirmation',
                    'Invoice_ID': metadata.get('invoice_id', ''),
                    'Date': metadata.get('date', ''),
                    'Payment_Terms': metadata.get('payment_terms', ''),
                    'Currency': metadata.get('currency', 'EUR')
                }
                
                # 각 사이즈별 수량 칼럼 추가 (나중에 채움)
                for size in self.default_sizes:
                    product_data[f'Size_{size}'] = 0
                
                products.append(product_data)
        
        logger.info(f"텍스트에서 추출한 제품 수: {len(products)}")
        return products
    
    def extract_size_quantity_from_text(self, text: str, doc_type: str) -> Dict[str, Dict]:
        """텍스트에서 사이즈-수량 패턴 추출"""
        size_qty_maps = {}
        
        # 제품 코드 추출
        product_codes = re.findall(r'\b(AJ\d+)\b', text)
        if not product_codes:
            return size_qty_maps
        
        # 중복 제거
        product_codes = list(set(product_codes))
        
        # 문서 타입에 따른 처리
        if doc_type == 'order_confirmation':
            # ORDER CONFIRMATION 특화 패턴: 테이블 행 패턴 확인
            # 예: FTVRM1323 09009 AJ1323 - BLACK LEATHER 220.00 0.00% 30 Nov 23 31 Jan 24 1540.00 1 1 2 2 1 7
            order_conf_pattern = r'(FTVRM\w+).*?(AJ\d+).*?(BLACK|WHITE).*?(\d+\.\d+).*?((?:\d+\s+)+\d+)'
            order_conf_matches = re.findall(order_conf_pattern, text)
            
            for match in order_conf_matches:
                _, product_code, _, _, quantity_text = match
                
                # 수량 배열 추출 (마지막은 합계)
                quantities = re.findall(r'\d+', quantity_text)
                if len(quantities) <= 1:
                    continue
                
                # 마지막 수량은 합계, 앞의 수치는 사이즈별 수량
                size_quantities = quantities[:-1]
                
                # 기본 사이즈 배열
                used_sizes = self.default_sizes[:len(size_quantities)]
                
                # 사이즈-수량 매핑
                size_qty_map = {}
                for i, size in enumerate(used_sizes):
                    if i < len(size_quantities):
                        qty = int(size_quantities[i])
                        size_qty_map[size] = qty
                
                # 제품별 사이즈-수량 매핑 저장
                if size_qty_map:
                    size_qty_maps[product_code] = {
                        'row': -1,  # 행 정보 없음
                        'size_qty': size_qty_map
                    }
        
        elif doc_type == 'purchase_order':
            # 구매주문서 패턴: 각 사이즈 및 수량 영역 찾기
            for product_code in product_codes:
                # 제품 코드 주변 텍스트 추출 (정규식으로 제품 섹션 찾기)
                product_section_regex = fr'{product_code}.*?(?=AJ\d+|$)'
                product_section_match = re.search(product_section_regex, text, re.DOTALL)
                
                if not product_section_match:
                    continue
                
                product_section = product_section_match.group(0)
                
                # 사이즈 행 찾기
                size_row_match = re.search(r'Size\s+((?:(?:\d{2})(?:\s+|\n+))+)', product_section, re.IGNORECASE)
                
                # 사이즈별 수량 매핑
                size_qty_map = {}
                
                if size_row_match:
                    # 사이즈 추출
                    size_row = size_row_match.group(1)
                    sizes = re.findall(r'\b(\d{2})\b', size_row)
                    
                    # 수량 행 찾기 (사이즈 행 다음에 나오는 숫자들)
                    qty_match = re.search(r'Qty\s+((?:\d+(?:\s+|\n+))+)', product_section, re.IGNORECASE)
                    
                    if qty_match:
                        qty_row = qty_match.group(1)
                        quantities = re.findall(r'\b(\d+)\b', qty_row)
                        
                        # 사이즈와 수량 매핑
                        for i, size in enumerate(sizes):
                            if i < len(quantities):
                                qty = int(quantities[i])
                                size_qty_map[size] = qty
                else:
                    # 대체 패턴 - 다른 형식의 사이즈-수량 표기
                    alt_pattern = r'Size.*?(\d{2}):(\d+)'
                    alt_matches = re.findall(alt_pattern, product_section)
                    
                    for size, qty in alt_matches:
                        size_qty_map[size] = int(qty)
                
                # 제품별 사이즈-수량 매핑 저장
                if size_qty_map:
                    size_qty_maps[product_code] = {
                        'row': -1,  # 행 정보 없음
                        'size_qty': size_qty_map
                    }
                else:
                    # 패턴 실패 시 총 수량을 기반으로 추정
                    total_qty_match = re.search(r'Total.*?(\d+)', product_section, re.IGNORECASE)
                    if total_qty_match:
                        total_qty = int(total_qty_match.group(1))
                        
                        # 기본 사이즈 배열
                        used_sizes = self.default_sizes[:6]  # 주로 사용되는 6개 사이즈
                        
                        # 수량 균등 분배
                        base_qty = total_qty // len(used_sizes)
                        remainder = total_qty % len(used_sizes)
                        
                        # 사이즈-수량 매핑
                        size_qty_map = {}
                        for i, size in enumerate(used_sizes):
                            qty = base_qty + (1 if i < remainder else 0)
                            size_qty_map[size] = qty
                        
                        # 제품별 사이즈-수량 매핑 저장
                        size_qty_maps[product_code] = {
                            'row': -1,  # 행 정보 없음
                            'size_qty': size_qty_map,
                            'estimated': True  # 추정된 데이터임을 표시
                        }
        
        return size_qty_maps
    
    def post_process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임 후처리"""
        if df.empty:
            return df
        
        # 칼럼명 표준화 (첫 글자 대문자)
        std_columns = {}
        for col in df.columns:
            if '_' in col:
                # Product_Code와 같은 형식은 그대로 유지
                std_columns[col] = col
            else:
                # 첫 글자만 대문자로 변경
                std_columns[col] = col.title()
        
        df = df.rename(columns=std_columns)
        
        # 사이즈 표기 정규화
        if 'Size' in df.columns:
            # 문서 유형에 따라 사이즈 형식 조정
            if 'Document_Type' in df.columns:
                doc_types = df['Document_Type'].unique()
                if 'purchase_order' in doc_types:
                    # 2자리 형식 (39, 40, 41...)
                    df['Size'] = df['Size'].astype(str).str.replace(r'(\d{2})0', r'\1', regex=True)
                elif 'order_confirmation' in doc_types:
                    # 3자리 형식 (390, 400, 410...)
                    df['Size'] = df['Size'].astype(str).apply(lambda x: x + '0' if len(x) == 2 else x)
        
        # 누락된 필드 채우기
        default_values = {
            'Brand': 'TOGA VIRILIS',
            'Season': '2024SS',
            'Currency': 'EUR'
        }
        
        for field, default_value in default_values.items():
            if field in df.columns:
                df[field] = df[field].fillna(default_value)
        
        # 수량을 정수로 변환
        if 'Quantity' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0).astype(int)
        
        # 가격 데이터 정리 (숫자 형식으로)
        price_columns = ['Wholesale_Price', 'Retail_Price', 'Total_Amount', 'Total_Price']
        for col in price_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 열 순서 정리
        ordered_columns = [
            'Custom_Code', 'Product_Code', 'Style', 'Color', 'Size', 'Quantity', 
            'Wholesale_Price', 'Retail_Price', 'Document_Type', 'PO_Number', 
            'Invoice_ID', 'Created_Date', 'Date', 'Brand', 'Season', 
            'Total_Amount', 'Currency', 'Total_Qty'
        ]
        
        # 데이터프레임에 존재하는 열만 유지
        available_columns = [col for col in ordered_columns if col in df.columns]
        
        # 나머지 열 추가
        remaining_columns = [col for col in df.columns if col not in ordered_columns]
        final_columns = available_columns + remaining_columns
        
        return df[final_columns]


def compare_documents(po_df: pd.DataFrame, invoice_df: pd.DataFrame) -> Dict:
    """구매주문서와 인보이스 비교"""
    if po_df.empty or invoice_df.empty:
        return {"status": "error", "message": "비교할 데이터가 부족합니다."}
    
    # 비교 결과 저장
    comparison = {
        "status": "success",
        "matching_items": [],
        "mismatched_items": [],
        "missing_items": [],
        "summary": {
            "total_items_po": len(po_df),
            "total_items_invoice": len(invoice_df),
            "matched_count": 0,
            "mismatched_count": 0,
            "missing_count": 0
        }
    }
    
    # 공통 키 필드 설정
    key_fields = ['Product_Code', 'Size']
    
    # PO 데이터를 딕셔너리로 변환 (키: 제품코드_사이즈)
    po_dict = {}
    for _, row in po_df.iterrows():
        key = f"{row['Product_Code']}_{row['Size']}"
        po_dict[key] = row.to_dict()
    
    # 인보이스 데이터와 비교
    for _, inv_row in invoice_df.iterrows():
        key = f"{inv_row['Product_Code']}_{inv_row['Size']}"
        inv_item = inv_row.to_dict()
        
        if key in po_dict:
            po_item = po_dict[key]
            
            # 수량 비교
            if po_item['Quantity'] == inv_item['Quantity']:
                comparison["matching_items"].append({
                    "product_code": inv_item['Product_Code'],
                    "size": inv_item['Size'],
                    "po_qty": po_item['Quantity'],
                    "invoice_qty": inv_item['Quantity']
                })
                comparison["summary"]["matched_count"] += 1
            else:
                comparison["mismatched_items"].append({
                    "product_code": inv_item['Product_Code'],
                    "size": inv_item['Size'],
                    "po_qty": po_item['Quantity'],
                    "invoice_qty": inv_item['Quantity'],
                    "difference": inv_item['Quantity'] - po_item['Quantity']
                })
                comparison["summary"]["mismatched_count"] += 1
            
            # 처리된 항목 표시
            po_dict[key]["processed"] = True
        else:
            # 구매주문서에 없는 항목
            comparison["missing_items"].append({
                "product_code": inv_item['Product_Code'],
                "size": inv_item['Size'],
                "invoice_qty": inv_item['Quantity'],
                "type": "extra_in_invoice"
            })
            comparison["summary"]["missing_count"] += 1
    
    # 인보이스에 없는 PO 항목 확인
    for key, item in po_dict.items():
        if item.get("processed") is not True:
            comparison["missing_items"].append({
                "product_code": item['Product_Code'],
                "size": item['Size'],
                "po_qty": item['Quantity'],
                "type": "missing_in_invoice"
            })
            comparison["summary"]["missing_count"] += 1
    
    return comparison


def main():
    """메인 함수"""
    import argparse
    
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='개선된 OCR로 PDF 문서 처리')
    parser.add_argument('--pdf_path', help='처리할 PDF 파일 경로')
    parser.add_argument('--output', '-o', help='결과를 저장할 디렉토리 경로')
    parser.add_argument('--model', '-m', default='best.pt', help='사용할 YOLO 모델 경로')
    parser.add_argument('--compare', '-c', action='store_true', help='문서 비교 모드 활성화')
    parser.add_argument('--po', help='구매주문서 PDF 파일 경로')
    parser.add_argument('--invoice', help='인보이스 PDF 파일 경로')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 출력')
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 출력 디렉토리 설정
    output_dir = args.output or 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # OCR 프로세서 초기화
    try:
        processor = ImprovedOCRProcessor(yolo_model_path=args.model)
        
        # 문서 비교 모드
        if args.compare and args.po and args.invoice:
            logger.info("문서 비교 모드 시작...")
            
            # 구매주문서 처리
            logger.info(f"구매주문서 처리 중: {args.po}")
            po_df = processor.process_pdf(args.po, output_dir)
            
            # 인보이스 처리
            logger.info(f"인보이스 처리 중: {args.invoice}")
            invoice_df = processor.process_pdf(args.invoice, output_dir)
            
            # 두 문서 비교
            if not po_df.empty and not invoice_df.empty:
                comparison_result = compare_documents(po_df, invoice_df)
                
                # 비교 결과 저장
                comparison_file = os.path.join(output_dir, f"comparison_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(comparison_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(comparison_result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"문서 비교 결과: {comparison_file}")
                
                # 요약 결과 출력
                print("\n문서 비교 결과 요약:")
                print(f"- 총 항목 수 (PO): {comparison_result['summary']['total_items_po']}")
                print(f"- 총 항목 수 (Invoice): {comparison_result['summary']['total_items_invoice']}")
                print(f"- 일치 항목: {comparison_result['summary']['matched_count']}")
                print(f"- 불일치 항목: {comparison_result['summary']['mismatched_count']}")
                print(f"- 누락 항목: {comparison_result['summary']['missing_count']}")
            else:
                logger.error("문서 비교 실패: 하나 이상의 문서에서 데이터 추출 실패")
        
        # 단일 문서 처리 모드
        elif args.pdf_path:
            df = processor.process_pdf(args.pdf_path, output_dir)
            
            if not df.empty:
                logger.info(f"처리 완료: {len(df)} 개의 제품 정보가 추출되었습니다.")
                print("\n데이터 미리보기:")
                print(df.head())
            else:
                logger.warning("제품 정보 추출 실패")
        
        # PDF 경로가 제공되지 않은 경우 input 폴더 확인
        else:
            # input 폴더의 모든 PDF 파일 찾기
            pdf_files = sorted(glob.glob('input/*.pdf'))
            if not pdf_files:
                logger.error("input 폴더에 PDF 파일이 없습니다.")
                return
            
            logger.info(f"input 폴더에서 {len(pdf_files)}개의 PDF 파일을 발견했습니다.")
            
            for pdf_file in pdf_files:
                logger.info(f"처리 중: {pdf_file}")
                df = processor.process_pdf(pdf_file, output_dir)
                
                if not df.empty:
                    logger.info(f"처리 완료: {len(df)} 개의 제품 정보가 추출되었습니다.")
                else:
                    logger.warning(f"{pdf_file}에서 제품 정보 추출 실패")
    
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())  # 상세 오류 로그 추가
        print(f"처리 중 오류 발생: {e}")


if __name__ == "__main__":
    main()