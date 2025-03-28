# document_comparator.py

import logging
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
        
        # 제품 항목 비교
        product_comparison = self._compare_products(doc1.get('products', []), doc2.get('products', []))
        comparison_results['matches'] = product_comparison['matches']
        comparison_results['mismatches'] = product_comparison['mismatches']
        comparison_results['summary'] = product_comparison['summary']
        
        return comparison_results
    
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
                # 값 정규화 (데이터 타입, 형식 차이 등 고려)
                value1_norm = self._normalize_value(value1)
                value2_norm = self._normalize_value(value2)
                
                if value1_norm == value2_norm:
                    comparison['matches'].append({
                        'field': display_name,
                        'value': value1_norm
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
            products1: 첫 번째 문서의 제품 목록
            products2: 두 번째 문서의 제품 목록
            
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
        # 두 문서 간 매핑을 위해 제품 코드+사이즈 조합 사용
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
                    'reason': '한쪽 문서에만 존재'
                })
                comparison['summary']['mismatched_items'] += 1
                continue
            
            # 제품 세부 필드 비교
            field_comparison = self._compare_product_fields(product1, product2)
            
            if field_comparison['mismatched_fields']:
                comparison['mismatches'].append({
                    'product_key': key,
                    'product_name': product1.get('product_code', '') + ' ' + product1.get('color', ''),
                    'doc1_exists': True,
                    'doc2_exists': True,
                    'mismatched_fields': field_comparison['mismatched_fields']
                })
                comparison['summary']['mismatched_items'] += 1
            else:
                comparison['matches'].append({
                    'product_key': key,
                    'product_name': product1.get('product_code', '') + ' ' + product1.get('color', ''),
                    'size': product1.get('size', ''),
                    'quantity': product1.get('quantity', ''),
                    'price': product1.get('wholesale_price', '') or product1.get('unit_price', '')
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
    
    def _compare_product_fields(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> Dict[str, List]:
        """제품 세부 필드 비교
        
        Args:
            product1: 첫 번째 문서의 제품 정보
            product2: 두 번째 문서의 제품 정보
            
        Returns:
            필드 비교 결과
        """
        result = {
            'matched_fields': [],
            'mismatched_fields': []
        }
        
        # 비교할 필드 쌍 정의 (필드명1, 필드명2, 표시명)
        fields_to_compare = [
            # 발주서/오더컨펌 간 필드명 매핑
            ('quantity', 'quantity', '수량'),
            ('wholesale_price', 'unit_price', '단가'),
            ('size', 'size', '사이즈'),
            ('color', 'color', '색상')
        ]
        
        for field1, field2, display_name in fields_to_compare:
            value1 = product1.get(field1)
            value2 = product2.get(field2)
            
            # 값이 모두 존재하는 경우만 비교
            if value1 is not None and value2 is not None:
                # 값 정규화
                value1_norm = self._normalize_value(value1)
                value2_norm = self._normalize_value(value2)
                
                if value1_norm == value2_norm:
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
        # 제품 코드 + 사이즈 조합으로 키 생성
        product_code = product.get('product_code') or product.get('item_code', '')
        
        # 제품 코드가 없는 경우 대체 식별자 사용
        if not product_code:
            # 스타일 코드 사용 시도
            product_code = product.get('style', '')
        
        size = product.get('size', '')
        
        return f"{product_code}_{size}"
    
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
        if str_value.replace('.', '').isdigit():
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
        str_value = str_value.replace('$', '').replace('€', '').replace(',', '')
        
        return str_value