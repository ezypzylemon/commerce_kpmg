# document_parser.py

import re
import logging
from typing import Dict, List, Tuple, Any, Optional

class DocumentParser:
    """다양한 문서 유형 파싱을 위한 기본 클래스"""
    
    def __init__(self):
        """파서 초기화"""
        self.logger = logging.getLogger(__name__)
    
    def detect_document_type(self, text: str) -> str:
        """문서 유형 자동 감지
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            감지된 문서 유형 ("purchase_order", "order_confirmation", "unknown")
        """
        # 오더 컨펌 문서 감지
        if re.search(r'ORDER CONFIRMATION', text, re.IGNORECASE):
            return "order_confirmation"
        
        # 발주서(PO) 문서 감지
        if re.search(r'PO#:', text, re.IGNORECASE) or re.search(r'Purchase Order', text, re.IGNORECASE):
            return "purchase_order"
        
        # 인보이스 감지
        if re.search(r'INVOICE', text, re.IGNORECASE):
            return "invoice"
        
        # 기타 문서 감지 로직 추가 가능
        
        return "unknown"
    
    def parse_document(self, text: str, doc_type: Optional[str] = None) -> Dict[str, Any]:
        """문서 유형에 따라 적절한 파싱 함수 호출
        
        Args:
            text: OCR로 추출된 텍스트
            doc_type: 문서 유형 (None인 경우 자동 감지)
            
        Returns:
            파싱된 문서 데이터
        """
        # 문서 유형이 지정되지 않은 경우 자동 감지
        if doc_type is None:
            doc_type = self.detect_document_type(text)
        
        self.logger.info(f"파싱 중인 문서 유형: {doc_type}")
        
        # 문서 유형에 따라 적절한 파싱 함수 호출
        if doc_type == "purchase_order":
            return self.parse_purchase_order(text)
        elif doc_type == "order_confirmation":
            return self.parse_order_confirmation(text)
        elif doc_type == "invoice":
            return self.parse_invoice(text)
        else:
            self.logger.warning(f"지원되지 않는 문서 유형: {doc_type}")
            return {"document_type": "unknown", "raw_text": text}
    
    def parse_purchase_order(self, text: str) -> Dict[str, Any]:
        """발주서(PO) 문서 파싱
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            파싱된 발주서 데이터
        """
        order_data = {
            "document_type": "purchase_order",
            "order_info": self._extract_po_order_info(text),
            "products": self._extract_po_products(text)
        }
        
        return order_data
    
    def parse_order_confirmation(self, text: str) -> Dict[str, Any]:
        """오더 컨펌 문서 파싱
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            파싱된 오더 컨펌 데이터
        """
        order_data = {
            "document_type": "order_confirmation",
            "order_info": self._extract_oc_order_info(text),
            "products": self._extract_oc_products(text)
        }
        
        return order_data
    
    def parse_invoice(self, text: str) -> Dict[str, Any]:
        """인보이스 문서 파싱
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            파싱된 인보이스 데이터
        """
        # 현재는 발주서와 동일한 파싱 로직 사용 (필요시 확장)
        return self.parse_purchase_order(text)
    
    def _extract_po_order_info(self, text: str) -> Dict[str, str]:
        """발주서에서 주문 정보 추출
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            주문 기본 정보
        """
        order_info = {}
        
        # 발주 번호 추출
        po_match = re.search(r'PO#:\s*(\d+)', text, re.IGNORECASE) 
        if po_match:
            order_info['po_number'] = po_match.group(1)
        
        # 날짜 추출
        date_match = re.search(r'Created:\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if date_match:
            order_info['created_date'] = date_match.group(1)
        
        # 선적 날짜 추출
        ship_patterns = [
            (r'Start\s+Ship:\s*(\d{2}/\d{2}/\d{4})', 'start_ship'),
            (r'Complete\s+Ship:\s*(\d{2}/\d{2}/\d{4})', 'complete_ship')
        ]
        
        for pattern, key in ship_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_info[key] = match.group(1)
        
        # 결제 조건 추출
        terms_match = re.search(r'Terms:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
        if terms_match:
            order_info['terms'] = terms_match.group(1).strip()
        
        # 브랜드 정보 추출
        brand_match = re.search(r'TOGA VIRILIS\s*-\s*(20\d{2}[SF]S\w*)', text, re.IGNORECASE)
        if brand_match:
            order_info['brand'] = 'TOGA VIRILIS'
            order_info['season'] = brand_match.group(1)
        
        # 총액 추출
        total_match = re.search(r'Grand Total:\s*EUR\s*([\d,\.]+)', text, re.IGNORECASE)
        if total_match:
            order_info['total_amount'] = total_match.group(1).replace(',', '')
            order_info['currency'] = 'EUR'
        
        # 총 수량 추출
        qty_match = re.search(r'Total Quantity:\s*(\d+)', text, re.IGNORECASE)
        if qty_match:
            order_info['total_quantity'] = qty_match.group(1)
        
        # 거래처 정보 추출
        company_match = re.search(r'EQL\s*\(?HANDSOME,?\s*CORP\.?\)?', text, re.IGNORECASE)
        if company_match:
            order_info['company'] = company_match.group(0)
        
        return order_info
    
    def _extract_po_products(self, text: str) -> List[Dict[str, Any]]:
        """발주서에서 상품 정보 추출
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            상품 정보 리스트
        """
        products = []
        
        # 상품 섹션 추출
        product_sections = self._extract_product_sections(text)
        
        for section in product_sections:
            product_info = self._extract_product_info(section)
            size_quantity_pairs = self._extract_sizes_and_quantities(section)
            
            if product_info and size_quantity_pairs:
                # 각 사이즈별 데이터 생성
                for size, quantity in size_quantity_pairs:
                    # 품번코드 생성
                    custom_code = self._generate_custom_code(product_info, size)
                    
                    # 데이터 추가
                    product_data = {
                        'product_code': product_info.get('product_code', ''),
                        'style': product_info.get('style', ''),
                        'color': product_info.get('color', ''),
                        'size': size,
                        'quantity': quantity,
                        'wholesale_price': product_info.get('wholesale_price', ''),
                        'retail_price': product_info.get('retail_price', ''),
                        'brand': product_info.get('brand', ''),
                        'season': product_info.get('season', ''),
                        'custom_code': custom_code
                    }
                    
                    products.append(product_data)
        
        return products
    
    def _extract_product_sections(self, text: str) -> List[str]:
        """OCR 텍스트에서 개별 상품 섹션을 분리하여 추출
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            상품 섹션 리스트
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
    
    def _extract_product_info(self, section: str) -> Dict[str, str]:
        """상품 섹션에서 기본 제품 정보 추출
        
        Args:
            section: 상품 섹션 텍스트
            
        Returns:
            제품 기본 정보
        """
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
    
    def _extract_sizes_and_quantities(self, section: str) -> List[Tuple[str, str]]:
        """상품 섹션에서 사이즈 및 수량 정보 추출
        
        Args:
            section: 상품 섹션 텍스트
            
        Returns:
            (사이즈, 수량) 튜플 리스트
        """
        if not section or not isinstance(section, str):
            return []
        
        # 사이즈 추출
        sizes = re.findall(r'\b(39|40|41|42|43|44|45|46)\b', section)
        
        # 수량 추출 - 사이즈 뒤에 나오는 숫자를 수량으로 간주
        quantities = []
        for size in sizes:
            # 사이즈 뒤에 나오는 숫자를 찾음
            qty_pattern = rf'{size}\s+(\d+)'
            qty_match = re.search(qty_pattern, section)
            if qty_match:
                quantities.append(qty_match.group(1))
            else:
                # 수량을 찾지 못한 경우 기본값 1 설정
                quantities.append('1')
        
        # 사이즈와 수량의 수가 맞지 않을 경우
        if len(sizes) != len(quantities):
            self.logger.warning(f"사이즈와 수량의 수가 일치하지 않습니다. 사이즈: {sizes}, 수량: {quantities}")
            # 기본 수량 1로 설정
            quantities = ['1'] * len(sizes)
        
        # 사이즈와 수량 쌍 생성
        size_quantity_pairs = list(zip(sizes, quantities))
        
        return size_quantity_pairs
    
    def _generate_custom_code(self, product_info: Dict[str, str], size: str) -> str:
        """품번코드 생성
        
        Args:
            product_info: 제품 정보
            size: 사이즈
            
        Returns:
            생성된 품번코드
        """
        # 기본값 설정
        style = product_info.get('style', '')
        color = product_info.get('color', '')
        product_code = product_info.get('product_code', '')
        
        # 연도 추출
        year = "00"
        if style and len(style) >= 2:
            try:
                year = style[-2:] if style[-2:].isdigit() else "00"
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
    
    def _extract_oc_order_info(self, text: str) -> Dict[str, str]:
        """오더 컨펌에서 주문 정보 추출
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            주문 기본 정보
        """
        order_info = {}
        
        # 오더 ID 추출
        order_id_match = re.search(r'ORDER CONFIRMATION ID:\s*(\d+)', text, re.IGNORECASE)
        if order_id_match:
            order_info['order_id'] = order_id_match.group(1)
        
        # 날짜 추출
        date_match = re.search(r'Date:\s*(\d{2}-\d{2}-\d{4})', text, re.IGNORECASE)
        if date_match:
            order_info['date'] = date_match.group(1)
        
        # 시즌 추출
        season_match = re.search(r'Season:\s*(20\d{2}[SF]S)', text, re.IGNORECASE)
        if season_match:
            order_info['season'] = season_match.group(1)
        
        # 브랜드 추출
        brand_match = re.search(r'Brand:\s*(\w+\s*\w*)', text, re.IGNORECASE)
        if brand_match:
            order_info['brand'] = brand_match.group(1)
        
        # 결제 조건 추출
        payment_match = re.search(r'Payment Terms:\s*([^\n]+)', text, re.IGNORECASE)
        if payment_match:
            order_info['payment_terms'] = payment_match.group(1).strip()
        
        # 결제 방법 추출
        method_match = re.search(r'Payment Method:\s*([^\n]+)', text, re.IGNORECASE)
        if method_match:
            order_info['payment_method'] = method_match.group(1).strip()
        
        # 총액 추출
        total_match = re.search(r'Doc\. Total:\s*(\d+\.\d{2})\s*EUR', text, re.IGNORECASE)
        if total_match:
            order_info['total_amount'] = total_match.group(1)
            order_info['currency'] = 'EUR'
        
        # 거래처 정보 추출
        company_match = re.search(r'CUSTOMER:\s*\n\s*(.+?)\n', text, re.IGNORECASE)
        if company_match:
            order_info['company'] = company_match.group(1).strip()
        
        return order_info
    
    def _extract_oc_products(self, text: str) -> List[Dict[str, Any]]:
        """오더 컨펌에서 상품 정보 추출
        
        Args:
            text: OCR로 추출된 텍스트
            
        Returns:
            상품 정보 리스트
        """
        products = []
        
        # 오더 컨펌의 상품 테이블 추출 시도
        # ITEM CODE 열이 있는 표를 찾기
        table_pattern = r'ITEM CODE\s+MODEL.*?TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        table_match = re.search(table_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if not table_match:
            self.logger.warning("오더 컨펌에서 상품 테이블을 찾을 수 없습니다.")
            return products
        
        # 상품 행 패턴
        product_pattern = r'(FTVRM\w+)\s+(AJ\d+\s*-\s*[A-Z\s]+(?:LEATHER|POLIDO))\s+(\d+\.\d{2})\s+(\d+\.\d{2}%)\s+(\d+\s*\w+\s*\d+)\s+(\d+\s*\w+\s*\d+)\s+(\d+\.\d{2})'
        product_matches = re.finditer(product_pattern, text, re.DOTALL)
        
        for match in product_matches:
            item_code = match.group(1)
            product_name = match.group(2)
            unit_price = match.group(3)
            discount = match.group(4)
            shipping_window_start = match.group(5)
            shipping_window_end = match.group(6)
            total_price = match.group(7)
            
            # 제품 코드 추출
            product_code_match = re.search(r'(AJ\d+)', product_name)
            product_code = product_code_match.group(1) if product_code_match else ""
            
            # 색상 추출
            color_match = re.search(r'BLACK LEATHER|BLACK POLIDO|WHITE LEATHER|BROWN LEATHER', product_name)
            color = color_match.group(0) if color_match else ""
            
            # 사이즈별 수량 추출
            size_quantities = []
            
            # 표의 각 열이 사이즈를 나타냄
            sizes = ['390', '400', '410', '420', '430', '440']
            
            # 특정 품목 행 전체를 찾아 사이즈 수량 추출
            item_line_pattern = rf'{re.escape(item_code)}.*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
            item_line_match = re.search(item_line_pattern, text, re.DOTALL)
            
            if item_line_match:
                for i, size in enumerate(sizes):
                    # 수량이 0이 아닌 경우만 추가
                    quantity = item_line_match.group(i+1)
                    if quantity and int(quantity) > 0:
                        size_quantities.append((size, quantity))
            
            # 기본 상품 정보 생성
            for size, quantity in size_quantities:
                # 품번코드 생성에 필요한 정보 모으기
                product_info = {
                    'product_code': product_code,
                    'style': item_code,
                    'color': color,
                    'brand': 'TOGA VIRILIS',  # 파일에서 추출 또는 기본값
                    'season': '2024SS',  # 파일에서 추출 또는 기본값
                    'category': 'Shoes'  # 파일에서 추출 또는 기본값
                }
                
                # 품번코드 생성
                custom_code = self._generate_custom_code(product_info, size)
                
                # 최종 제품 데이터
                product_data = {
                    'item_code': item_code,
                    'product_code': product_code,
                    'product_name': product_name,
                    'color': color,
                    'size': size,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount': discount,
                    'total_price': total_price,
                    'custom_code': custom_code
                }
                
                products.append(product_data)
        
        return products