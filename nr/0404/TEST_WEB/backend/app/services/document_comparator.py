# document_comparator.py

import logging
import re
from typing import Dict, List, Any, Tuple, Optional

class DocumentComparator:
    """문서 비교 클래스: 인보이스와 오더 시트 등 서로 다른 문서 간의 비교 기능 제공"""
    
    def __init__(self):
        """비교기 초기화"""
        self.logger = logging.getLogger(__name__)
    
    def compare_documents(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> Dict[str, Any]:
        """두 문서를 비교하여 일치/불일치 정보 반환
        
        Args:
            doc1: 첫 번째 문서 데이터 (파싱된 결과)
            doc2: 두 번째 문서 데이터 (파싱된 결과)
            
        Returns:
            비교 결과: 일치/불일치 항목 및 요약 정보
        """
        # 문서 유형 확인
        doc1_type = doc1.get('document_type', 'unknown')
        doc2_type = doc2.get('document_type', 'unknown')

        self.logger.info(f"문서 비교 시작: {doc1_type} vs {doc2_type}")
        # 문서 유형이 다른 경우에도 비교 계속 진행
        
        # 결과 초기화
        comparison_results = {
            'document_types': {
                'doc1': doc1_type,
                'doc2': doc2_type
            },
            'matches': [],
            'mismatches': [],
            'summary': {
                'total_items': 0,
                'matched_items': 0,
                'mismatched_items': 0,
                'match_percentage': 0
            }
        }
        
        # 문서 기본 정보 비교
        order_info_comparison = self._compare_order_info(doc1.get('order_info', {}), doc2.get('order_info', {}))
        comparison_results['order_info_comparison'] = order_info_comparison
        
        # 제품 항목 비교 - 데이터 타입 표준화 적용
        standardized_doc1 = self._standardize_document_data(doc1.get('products', []))
        standardized_doc2 = self._standardize_document_data(doc2.get('products', []))
        
        # 표준화된 데이터로 비교
        product_comparison = self._compare_products(standardized_doc1, standardized_doc2)
        comparison_results['matches'] = product_comparison['matches']
        comparison_results['mismatches'] = product_comparison['mismatches']
        comparison_results['summary'] = product_comparison['summary']
        
        return comparison_results
    
    def _standardize_document_data(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문서 데이터를 비교를 위해 표준화

        Args:
            products: 제품 데이터 목록

        Returns:
            표준화된 제품 데이터 목록
        """
        standardized_products = []
        
        for product in products:
            # 제품 복사 후 표준화 작업
            std_product = product.copy()
            
            # 사이즈별 수량 정수형으로 변환
            for key in list(std_product.keys()):
                if key.startswith('사이즈_') or key.startswith('size_'):
                    size_key = key if key.startswith('사이즈_') else f"사이즈_{key[5:]}"
                    value = std_product.pop(key, '0')
                    # 문자열을 정수로 변환, 변환할 수 없는 경우 0으로 설정
                    try:
                        std_product[size_key] = int(value)
                    except (ValueError, TypeError):
                        std_product[size_key] = 0
            
            # 총 수량 정수형으로 변환
            total_qty = std_product.get('총_수량', std_product.get('total_quantity', '0'))
            try:
                std_product['총_수량'] = int(total_qty)
            except (ValueError, TypeError):
                std_product['총_수량'] = 0
            
            # 구매가 표준화
            wholesale_price = std_product.get('구매가', std_product.get('wholesale_price', std_product.get('unit_price', '')))
            std_product['구매가'] = self._standardize_price(wholesale_price)
            
            # 총 금액 표준화
            total_price = std_product.get('총_금액', std_product.get('total_price', std_product.get('total_amount', '')))
            std_product['총_금액'] = self._standardize_price(total_price)
            
            # 공통 필드 매핑 - 모델 정보
            std_product['모델코드'] = std_product.get('모델코드', std_product.get('model', std_product.get('product_code', '')))
            std_product['모델명'] = std_product.get('모델명', std_product.get('full_model', std_product.get('model_name', '')))
            
            # 날짜 정보 표준화
            std_product['선적_시작일'] = self._standardize_date(std_product.get('선적_시작일', std_product.get('start_ship', '')))
            std_product['선적_완료일'] = self._standardize_date(std_product.get('선적_완료일', std_product.get('complete_ship', '')))
            
            # 존재하지 않는 필드에 기본값 설정
            if '할인율' not in std_product:
                std_product['할인율'] = '0%'
            
            if '컬러' not in std_product and '모델명' in std_product:
                # 모델명에서 색상 정보 추출 시도
                color_match = re.search(r'(BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE|POLIDO|LEATHER)', std_product['모델명'], re.IGNORECASE)
                std_product['컬러'] = color_match.group(1) if color_match else ''
            
            standardized_products.append(std_product)
        
        return standardized_products
    
    def _standardize_price(self, price_value: Any) -> str:
        """가격 정보를 표준 형식으로 변환

        Args:
            price_value: 원본 가격 데이터

        Returns:
            표준화된 가격 문자열 (EUR 150.00 형식)
        """
        if not price_value:
            return 'EUR 0.00'
        
        # 문자열 변환
        price_str = str(price_value).strip()
        
        # 통화 추출 (기본값 EUR)
        currency = 'EUR'
        if 'EUR' in price_str:
            currency = 'EUR'
        elif '$' in price_str:
            currency = '$'
        
        # 숫자 추출
        number_match = re.search(r'[-+]?\d+(?:\.\d+)?', price_str.replace(',', ''))
        if number_match:
            try:
                price_num = float(number_match.group(0))
                return f"{currency} {price_num:.2f}"
            except (ValueError, TypeError):
                pass
        
        # 숫자 추출 실패 시 기본값 반환
        return 'EUR 0.00'
    
    def _standardize_date(self, date_value: Any) -> str:
        """날짜를 표준 형식으로 변환 (MM/DD/YYYY)

        Args:
            date_value: 원본 날짜 데이터

        Returns:
            표준화된 날짜 문자열
        """
        if not date_value:
            return ''
        
        date_str = str(date_value).strip()
        
        # 다양한 날짜 형식 처리
        # MM/DD/YYYY 형식인지 확인
        if re.match(r'\d{2}/\d{2}/\d{4}', date_str):
            return date_str
        
        # DD-MM-YYYY 형식인지 확인 및 변환
        date_match = re.match(r'(\d{2})-(\d{2})-(\d{4})', date_str)
        if date_match:
            day, month, year = date_match.groups()
            return f"{month}/{day}/{year}"
        
        # YYYY-MM-DD 형식인지 확인 및 변환
        date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if date_match:
            year, month, day = date_match.groups()
            return f"{month}/{day}/{year}"
        
        # 기타 형식은 그대로 반환
        return date_str
    
    def _compare_order_info(self, order_info1: Dict[str, str], order_info2: Dict[str, str]) -> Dict[str, Any]:
        """주문 기본 정보 비교
        
        Args:
            order_info1: 첫 번째 문서의 주문 정보
            order_info2: 두 번째 문서의 주문 정보
            
        Returns:
            기본 정보 비교 결과
        """
        comparison = {
            'matches': [],
            'mismatches': []
        }
        
        # 비교할 필드 쌍 정의 (필드명1, 필드명2, 표시명)
        fields_to_compare = [
            # 발주서/오더컨펌 간 필드명 매핑
            ('po_number', 'order_id', '주문번호'),
            ('created_date', 'date', '작성일자'),
            ('start_ship', 'shipping_window', '선적시작일'),
            ('complete_ship', 'shipping_window', '선적완료일'),
            ('terms', 'payment_terms', '결제조건'),
            ('brand', 'brand', '브랜드'),
            ('season', 'season', '시즌'),
            ('total_amount', 'total_amount', '총액'),
            ('total_quantity', 'total_quantity', '총수량'),
            ('company', 'company', '거래처')
        ]
        
        for field1, field2, display_name in fields_to_compare:
            value1 = order_info1.get(field1)
            value2 = order_info2.get(field2)
            
            # 값이 모두 존재하는 경우만 비교
            if value1 is not None and value2 is not None:
                # 데이터 타입 및 값 정규화
                if display_name == '총액':
                    value1 = self._standardize_price(value1)
                    value2 = self._standardize_price(value2)
                elif display_name == '총수량':
                    try:
                        value1 = int(value1)
                        value2 = int(value2)
                    except (ValueError, TypeError):
                        pass
                elif display_name in ['선적시작일', '선적완료일', '작성일자']:
                    value1 = self._standardize_date(value1)
                    value2 = self._standardize_date(value2)
                else:
                    # 일반 텍스트 정규화
                    value1 = self._normalize_value(value1)
                    value2 = self._normalize_value(value2)
                
                if value1 == value2:
                    comparison['matches'].append({
                        'field': display_name,
                        'value': value1
                    })
                else:
                    comparison['mismatches'].append({
                        'field': display_name,
                        'value1': value1,
                        'value2': value2
                    })
        
        return comparison
    
    def _compare_products(self, products1: List[Dict[str, Any]], products2: List[Dict[str, Any]]) -> Dict[str, Any]:
        """제품 항목 비교
        
        Args:
            products1: 첫 번째 문서의 제품 목록 (표준화됨)
            products2: 두 번째 문서의 제품 목록 (표준화됨)
            
        Returns:
            제품 비교 결과
        """
        comparison = {
            'matches': [],
            'mismatches': [],
            'summary': {
                'total_items': 0,
                'matched_items': 0,
                'mismatched_items': 0,
                'match_percentage': 0
            }
        }
        
        # 제품 식별 키 생성
        products1_by_key = {}
        for product in products1:
            key = self._generate_product_key(product)
            products1_by_key[key] = product
        
        products2_by_key = {}
        for product in products2:
            key = self._generate_product_key(product)
            products2_by_key[key] = product
        
        # 모든 제품 키 합집합
        all_product_keys = set(products1_by_key.keys()) | set(products2_by_key.keys())
        comparison['summary']['total_items'] = len(all_product_keys)
        
        # 각 제품 비교
        for key in all_product_keys:
            product1 = products1_by_key.get(key)
            product2 = products2_by_key.get(key)
            
            if not product1 or not product2:
                # 한쪽에만 존재하는 항목
                comparison['mismatches'].append({
                    'product_key': key,
                    'doc1_exists': bool(product1),
                    'doc2_exists': bool(product2),
                    'reason': '한쪽 문서에만 존재',
                    'product_name': (product1 or product2).get('모델명', key)
                })
                comparison['summary']['mismatched_items'] += 1
                continue
            
            # 제품 세부 필드 비교
            field_comparison = self._compare_product_fields(product1, product2)
            
            if field_comparison['mismatched_fields']:
                comparison['mismatches'].append({
                    'product_key': key,
                    'product_name': product1.get('모델명', key),
                    'doc1_exists': True,
                    'doc2_exists': True,
                    'mismatched_fields': field_comparison['mismatched_fields']
                })
                comparison['summary']['mismatched_items'] += 1
            else:
                comparison['matches'].append({
                    'product_key': key,
                    'product_name': product1.get('모델명', key),
                    'size': self._get_size_summary(product1),
                    'quantity': product1.get('총_수량', 0),
                    'price': product1.get('구매가', '')
                })
                comparison['summary']['matched_items'] += 1
        
        # 일치율 계산
        if comparison['summary']['total_items'] > 0:
            comparison['summary']['match_percentage'] = round(
                comparison['summary']['matched_items'] / 
                comparison['summary']['total_items'] * 100,
                2
            )
        
        return comparison
    
    def _get_size_summary(self, product: Dict[str, Any]) -> str:
        """제품의 사이즈 요약 문자열 생성

        Args:
            product: 제품 정보

        Returns:
            사이즈 요약 문자열 (예: "39(1), 40(2), 41(1)")
        """
        size_info = []
        for size in range(39, 47):
            size_key = f'사이즈_{size}'
            if size_key in product and product[size_key] > 0:
                size_info.append(f"{size}({product[size_key]})")
        
        return ", ".join(size_info) if size_info else "-"
    
    def _compare_product_fields(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> Dict[str, List]:
        """제품 세부 필드 비교
        
        Args:
            product1: 첫 번째 문서의 제품 정보 (표준화됨)
            product2: 두 번째 문서의 제품 정보 (표준화됨)
            
        Returns:
            필드 비교 결과
        """
        result = {
            'matched_fields': [],
            'mismatched_fields': []
        }
        
        # 비교할 필드 목록
        fields_to_compare = [
            ('총_수량', '총 수량'),
            ('구매가', '단가'),
            ('컬러', '색상'),
            ('총_금액', '총 금액')
        ]
        
        # 사이즈별 수량도 비교
        for size in range(39, 47):
            size_key = f'사이즈_{size}'
            fields_to_compare.append((size_key, f'사이즈 {size}'))
        
        # 각 필드 비교
        for field, display_name in fields_to_compare:
            value1 = product1.get(field)
            value2 = product2.get(field)
            
            # 두 값 모두 존재하는 경우만 비교
            if value1 is not None and value2 is not None:
                # 수량과 금액 필드는 타입 변환 없이 직접 비교 (이미 표준화됨)
                if field == '총_수량' or field.startswith('사이즈_'):
                    equal = value1 == value2
                elif field == '구매가' or field == '총_금액':
                    equal = value1 == value2
                else:
                    # 텍스트 필드는 일반 정규화 후 비교
                    equal = self._normalize_value(value1) == self._normalize_value(value2)
                
                if equal:
                    result['matched_fields'].append(display_name)
                else:
                    result['mismatched_fields'].append({
                        'field': display_name,
                        'value1': value1,
                        'value2': value2
                    })
        
        return result
    
    def _generate_product_key(self, product: Dict[str, Any]) -> str:
        """제품 식별을 위한 키 생성
        
        Args:
            product: 제품 정보
            
        Returns:
            고유 식별 키
        """
        # 제품 코드 가져오기
        product_code = product.get('모델코드', '')
        
        # 제품 코드가 없는 경우 대체 식별자 사용
        if not product_code:
            # 모델명에서 코드 추출 시도
            model_name = product.get('모델명', '')
            code_match = re.search(r'(AJ\d+|A[JRCSL]\d+)', model_name)
            if code_match:
                product_code = code_match.group(1)
            else:
                # 스타일 코드 사용 시도
                product_code = product.get('스타일코드', 'unknown')
        
        # 키 생성 시 컬러 정보 포함
        color = product.get('컬러', '')
        
        # 키 생성 (모델 코드 + 컬러를 기본으로 사용)
        key_parts = [product_code]
        if color:
            key_parts.append(color)
        
        return '_'.join(key_parts).lower()
    
    def _normalize_value(self, value: Any) -> str:
        """비교를 위한 값 정규화
        
        Args:
            value: 정규화할 값
            
        Returns:
            정규화된 문자열
        """
        # 문자열로 변환
        str_value = str(value)
        
        # 공백 제거
        str_value = str_value.strip()
        
        # 숫자 정규화 (123.00 -> 123, 123.45 -> 123.45)
        if str_value.replace('.', '', 1).isdigit():
            try:
                num_value = float(str_value)
                # 소수점 이하가 0인 경우 정수로 변환
                if num_value.is_integer():
                    str_value = str(int(num_value))
            except ValueError:
                pass
        
        # 대소문자 일치 문제 해결
        str_value = str_value.lower()
        
        # 통화 기호 및 쉼표 제거
        str_value = str_value.replace('$', '').replace('€', '').replace('₩', '').replace(',', '')
        
        return str_value