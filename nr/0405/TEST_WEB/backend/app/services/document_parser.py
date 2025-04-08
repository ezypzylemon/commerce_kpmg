import re
import logging
from typing import Dict, List, Any, Optional

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
            감지된 문서 유형 ("purchase_order", "order_confirmation", "invoice", "unknown")
        """
        # 오더 컨펌 문서 감지
        if re.search(r'ORDER\s+CONFIRMATION\s+ID', text, re.IGNORECASE) or \
        re.search(r'THANK YOU FOR YOUR ORDER', text, re.IGNORECASE):
            return "order_confirmation"

        # 발주서(PO) 문서 감지
        if re.search(r'PO\s*[#:]\s*\d+', text, re.IGNORECASE) or \
        re.search(r'Purchase\s+Order', text, re.IGNORECASE) or \
        re.search(r'Start\s+Ship.*?Complete\s+Ship', text, re.DOTALL | re.IGNORECASE):
            return "purchase_order"

        # 인보이스 감지
        if re.search(r'INVOICE', text, re.IGNORECASE) or \
           re.search(r'BILL\s+TO', text, re.IGNORECASE):
            return "invoice"

        # 기본값
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
        
        # 문서 유형에 따라 적절한 구조 반환
        if doc_type == "purchase_order":
            return {"document_type": "purchase_order", "raw_text": text}
        elif doc_type == "order_confirmation":
            return {"document_type": "order_confirmation", "raw_text": text}
        elif doc_type == "invoice":
            return {"document_type": "invoice", "raw_text": text}
        else:
            self.logger.warning(f"지원되지 않는 문서 유형: {doc_type}")
            return {"document_type": "unknown", "raw_text": text}