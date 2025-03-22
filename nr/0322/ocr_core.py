import os
import cv2
import numpy as np
import re
import io
import logging
from typing import List, Dict, Tuple, Optional, Union, Any
from google.cloud import vision
from ultralytics import YOLO
from PIL import Image

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TableDetector:
    """테이블 구조 감지 및 분석 클래스"""
    
    def __init__(self, model_path='best.pt'):
        """YOLO 모델 초기화"""
        try:
            self.model = YOLO(model_path)
            logger.info(f"YOLO 모델 로드 성공: {model_path}")
        except Exception as e:
            logger.error(f"YOLO 모델 로드 실패: {e}")
            self.model = None
        
        # OpenCV 파라미터
        self.min_line_length = 100
        self.max_line_gap = 10
    
    def basic_preprocess(self, image_path: str) -> str:
        """기본적인 이미지 전처리 (그레이스케일, 간단한 대비 조정)"""
        try:
            # 원본 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"이미지를 불러올 수 없습니다: {image_path}")
                return image_path
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 약간의 대비 향상
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 전처리된 이미지 저장
            temp_path = os.path.join(os.path.dirname(image_path), f"basic_prep_{os.path.basename(image_path)}")
            cv2.imwrite(temp_path, enhanced)
            
            return temp_path
        except Exception as e:
            logger.error(f"기본 이미지 전처리 오류: {e}")
            return image_path
    
    def advanced_preprocess(self, image_path: str) -> Dict[str, str]:
        """고급 이미지 전처리 (이진화, 선 강화 등)"""
        try:
            # 원본 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"이미지를 불러올 수 없습니다: {image_path}")
                return {"original": image_path}
            
            # 결과 이미지 경로
            results = {
                "original": image_path
            }
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # 대비 향상
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 적응형 이진화
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            binary_path = os.path.join(os.path.dirname(image_path), f"binary_{os.path.basename(image_path)}")
            cv2.imwrite(binary_path, binary)
            results["binary"] = binary_path
            
            # 테이블 선 강화
            h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            
            h_lines = cv2.morphologyEx(~binary, cv2.MORPH_OPEN, h_kernel, iterations=2)
            v_lines = cv2.morphologyEx(~binary, cv2.MORPH_OPEN, v_kernel, iterations=2)
            
            table_lines = cv2.add(h_lines, v_lines)
            table_enhanced = cv2.add(binary, table_lines)
            
            table_path = os.path.join(os.path.dirname(image_path), f"table_{os.path.basename(image_path)}")
            cv2.imwrite(table_path, ~table_enhanced)  # 테이블 선이 강화된 이미지
            results["table"] = table_path
            
            # 선명화
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            sharp_path = os.path.join(os.path.dirname(image_path), f"sharp_{os.path.basename(image_path)}")
            cv2.imwrite(sharp_path, sharpened)
            results["sharp"] = sharp_path
            
            return results
        
        except Exception as e:
            logger.error(f"고급 이미지 전처리 오류: {e}")
            return {"original": image_path}
    
    def detect_tables(self, image_path: str, use_advanced_preprocess: bool = False) -> List[Dict]:
        """이미지에서 테이블 영역 감지 (하이브리드 접근법)"""
        if self.model is None:
            logger.error("YOLO 모델이 초기화되지 않았습니다.")
            return []
        
        try:
            # 1. 기본 전처리 적용
            basic_prep_path = self.basic_preprocess(image_path)
            
            # 2. 기본 전처리된 이미지로 테이블 감지 시도
            tables = self._detect_with_yolo(basic_prep_path)
            
            # 기본 전처리 이미지 삭제 (임시 파일)
            if basic_prep_path != image_path and os.path.exists(basic_prep_path):
                os.remove(basic_prep_path)
            
            # 3. 테이블 감지 성공 확인
            if tables and len(tables) > 0:
                logger.info("기본 전처리 이미지에서 테이블 감지 성공")
                return tables
            
            # 4. YOLO로 테이블을 감지하지 못한 경우 OpenCV로 시도
            tables = self.detect_tables_with_opencv(image_path)
            if tables:
                logger.info("OpenCV로 테이블 감지 성공")
                return tables
            
            # 5. 고급 전처리 필요 여부 확인
            if use_advanced_preprocess:
                logger.info("테이블 감지 실패, 고급 전처리 시도 중...")
                
                # 고급 전처리 적용
                advanced_images = self.advanced_preprocess(image_path)
                
                # 각 전처리 이미지로 테이블 감지 시도
                for prep_type, prep_path in advanced_images.items():
                    if prep_path == image_path:  # 원본 이미지는 건너뜀
                        continue
                    
                    logger.info(f"[{prep_type}] 이미지로 테이블 감지 시도 중...")
                    prep_tables = self._detect_with_yolo(prep_path)
                    
                    # 전처리 이미지 삭제 (임시 파일)
                    if os.path.exists(prep_path):
                        os.remove(prep_path)
                    
                    # 테이블 감지 성공 시 반환
                    if prep_tables and len(prep_tables) > 0:
                        logger.info(f"[{prep_type}] 전처리 이미지에서 테이블 감지 성공")
                        return prep_tables
                    
                    # OpenCV로 시도
                    prep_tables = self.detect_tables_with_opencv(prep_path)
                    if prep_tables:
                        logger.info(f"[{prep_type}] 전처리 이미지에서 OpenCV로 테이블 감지 성공")
                        return prep_tables
            
            logger.warning("모든 방법으로 테이블 감지 실패")
            return []
        
        except Exception as e:
            logger.error(f"테이블 감지 오류: {e}")
            return []
    
    def _detect_with_yolo(self, image_path: str) -> List[Dict]:
        """YOLO 모델을 사용하여 이미지에서 테이블 영역 감지 (내부 메서드)"""
        try:
            # 이미지 로드
            img = Image.open(image_path)
            
            # YOLO 모델로 예측 실행
            results = self.model(img)
            
            # 결과 정리
            tables = []
            for i, result in enumerate(results):
                boxes = result.boxes
                
                for j, box in enumerate(boxes):
                    # 바운딩 박스 좌표 (x1, y1, x2, y2)
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # 클래스 가져오기
                    class_name = result.names[class_id]
                    
                    # 테이블 정보 저장
                    table_info = {
                        'id': f"{i}_{j}",
                        'x': x1,
                        'y': y1,
                        'width': x2 - x1,
                        'height': y2 - y1,
                        'area': (x2 - x1) * (y2 - y1),
                        'confidence': confidence,
                        'class': class_name
                    }
                    
                    # 테이블 이미지 추출 및 저장
                    table_img = cv2.imread(image_path)[y1:y2, x1:x2]
                    temp_dir = os.path.dirname(image_path)
                    table_path = os.path.join(temp_dir, f"table_{i}_{j}_{os.path.basename(image_path)}")
                    cv2.imwrite(table_path, table_img)
                    table_info['image_path'] = table_path
                    
                    tables.append(table_info)
            
            # 영역 크기로 정렬 (큰 것부터)
            tables.sort(key=lambda t: t['area'], reverse=True)
            
            return tables
        
        except Exception as e:
            logger.error(f"YOLO 테이블 감지 오류: {e}")
            return []
    
    def detect_tables_with_opencv(self, image_path: str) -> List[Dict]:
        """OpenCV를 사용하여 테이블 영역 감지"""
        try:
            # 이미지 로드 및 전처리
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 이진화
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # 노이즈 제거
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 테이블 경계선 감지
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            # 수평선 감지
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            h_lines = cv2.HoughLinesP(
                horizontal_lines, 1, np.pi/180, 100, 
                minLineLength=self.min_line_length, maxLineGap=self.max_line_gap
            )
            
            # 수직선 감지
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            v_lines = cv2.HoughLinesP(
                vertical_lines, 1, np.pi/180, 100, 
                minLineLength=self.min_line_length, maxLineGap=self.max_line_gap
            )
            
            # 수평선, 수직선이 없으면 빈 리스트 반환
            if h_lines is None or v_lines is None:
                return []
            
            # 수평선, 수직선 좌표 추출
            h_coords = []
            for line in h_lines:
                x1, y1, x2, y2 = line[0]
                h_coords.append((min(x1, x2), max(x1, x2), y1))  # (시작x, 끝x, y)
            
            v_coords = []
            for line in v_lines:
                x1, y1, x2, y2 = line[0]
                v_coords.append((x1, min(y1, y2), max(y1, y2)))  # (x, 시작y, 끝y)
            
            # 테이블 영역 감지 (수평선과 수직선이 충분히 교차하는 영역)
            tables = []
            if h_coords and v_coords:
                # 그리드 형태의 테이블 찾기
                h_coords.sort(key=lambda x: x[2])  # y 좌표로 정렬
                v_coords.sort(key=lambda x: x[0])  # x 좌표로 정렬
                
                # 최대 테이블 영역 추정
                min_x = min([v[0] for v in v_coords])
                max_x = max([v[0] for v in v_coords])
                min_y = min([h[2] for h in h_coords])
                max_y = max([h[2] for h in h_coords])
                
                # 여백 추가
                padding = 20
                x1 = max(0, min_x - padding)
                y1 = max(0, min_y - padding)
                x2 = min(image.shape[1], max_x + padding)
                y2 = min(image.shape[0], max_y + padding)
                
                # 테이블 영역이 충분히 큰 경우에만 포함
                area = (x2 - x1) * (y2 - y1)
                if area > 10000:  # 최소 크기 임계값
                    # 테이블 이미지 추출 및 저장
                    table_img = image[y1:y2, x1:x2]
                    temp_dir = os.path.dirname(image_path)
                    table_path = os.path.join(temp_dir, f"table_opencv_{os.path.basename(image_path)}")
                    cv2.imwrite(table_path, table_img)
                    
                    tables.append({
                        'id': f"opencv_0",
                        'x': x1,
                        'y': y1,
                        'width': x2 - x1,
                        'height': y2 - y1,
                        'area': area,
                        'confidence': 0.8,  # 임의의 신뢰도
                        'class': 'table',
                        'image_path': table_path
                    })
            
            return tables
        
        except Exception as e:
            logger.error(f"OpenCV 테이블 감지 오류: {e}")
            return []
    
    def extract_table_structure(self, table_image_path: str) -> Dict:
        """테이블 이미지에서 행, 열, 셀 구조 추출"""
        try:
            # 이미지 로드
            image = cv2.imread(table_image_path)
            if image is None:
                logger.error(f"테이블 이미지를 로드할 수 없습니다: {table_image_path}")
                return {'rows': [], 'columns': [], 'cells': []}
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 이진화 (반전)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # 노이즈 제거
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 수평선 감지
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # 수직선 감지
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # 허프 변환으로 선 감지
            h_lines = cv2.HoughLinesP(
                horizontal_lines, 1, np.pi/180, 100, 
                minLineLength=self.min_line_length, maxLineGap=self.max_line_gap
            )
            
            v_lines = cv2.HoughLinesP(
                vertical_lines, 1, np.pi/180, 100, 
                minLineLength=self.min_line_length, maxLineGap=self.max_line_gap
            )
            
            # 행과 열 좌표 추출
            rows = []
            if h_lines is not None:
                for i, line in enumerate(h_lines):
                    x1, y1, x2, y2 = line[0]
                    rows.append({
                        'id': f"row_{i}",
                        'y1': min(y1, y2),
                        'y2': max(y1, y2),
                        'x1': min(x1, x2),
                        'x2': max(x1, x2)
                    })
            
            columns = []
            if v_lines is not None:
                for i, line in enumerate(v_lines):
                    x1, y1, x2, y2 = line[0]
                    columns.append({
                        'id': f"col_{i}",
                        'x1': min(x1, x2),
                        'x2': max(x1, x2),
                        'y1': min(y1, y2),
                        'y2': max(y1, y2)
                    })
            
            # y 좌표로 행 정렬
            rows.sort(key=lambda r: r['y1'])
            
            # x 좌표로 열 정렬
            columns.sort(key=lambda c: c['x1'])
            
            # 중복 제거 (유사한 y 좌표를 가진 행 병합)
            merged_rows = []
            if rows:
                current_row = rows[0]
                for i in range(1, len(rows)):
                    # y 좌표 차이가 임계값보다 작으면 병합
                    if abs(rows[i]['y1'] - current_row['y1']) < 10:
                        current_row['x1'] = min(current_row['x1'], rows[i]['x1'])
                        current_row['x2'] = max(current_row['x2'], rows[i]['x2'])
                    else:
                        merged_rows.append(current_row)
                        current_row = rows[i]
                merged_rows.append(current_row)
            
            # 중복 제거 (유사한 x 좌표를 가진 열 병합)
            merged_columns = []
            if columns:
                current_col = columns[0]
                for i in range(1, len(columns)):
                    # x 좌표 차이가 임계값보다 작으면 병합
                    if abs(columns[i]['x1'] - current_col['x1']) < 10:
                        current_col['y1'] = min(current_col['y1'], columns[i]['y1'])
                        current_col['y2'] = max(current_col['y2'], columns[i]['y2'])
                    else:
                        merged_columns.append(current_col)
                        current_col = columns[i]
                merged_columns.append(current_col)
            
            # 셀 구조 구성
            cells = []
            for i in range(len(merged_rows) - 1):
                for j in range(len(merged_columns) - 1):
                    # 셀 경계 정의
                    x1 = merged_columns[j]['x1']
                    y1 = merged_rows[i]['y1']
                    x2 = merged_columns[j+1]['x1']
                    y2 = merged_rows[i+1]['y1']
                    
                    cells.append({
                        'id': f"cell_{i}_{j}",
                        'row': i,
                        'col': j,
                        'x1': x1,
                        'y1': y1,
                        'x2': x2,
                        'y2': y2,
                        'width': x2 - x1,
                        'height': y2 - y1
                    })
            
            # 테이블 구조 저장
            table_structure = {
                'rows': merged_rows,
                'columns': merged_columns,
                'cells': cells
            }
            
            return table_structure
        
        except Exception as e:
            logger.error(f"테이블 구조 추출 오류: {e}")
            return {'rows': [], 'columns': [], 'cells': []}


class DocumentProcessor:
    """문서 처리 및 인식 클래스"""
    
    def __init__(self, vision_client):
        """문서 처리기 초기화"""
        self.vision_client = vision_client
    
    def extract_text_with_vision(self, image_path: str) -> Dict:
        """Google Vision API로 텍스트 추출 (위치 정보 포함)"""
        if not self.vision_client:
            logger.error("Google Cloud Vision API 클라이언트가 초기화되지 않았습니다.")
            return {"full_text": "", "blocks": []}
        
        try:
            # 이미지 파일 읽기
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # 언어 힌트 추가 (영어 우선)
            image_context = vision.ImageContext(
                language_hints=['en']
            )
            
            # 문서 텍스트 감지
            response = self.vision_client.document_text_detection(
                image=image,
                image_context=image_context
            )
            
            if response.error.message:
                logger.error(f"Google Vision API 오류: {response.error.message}")
                return {"full_text": "", "blocks": []}
            
            # 전체 텍스트 추출
            full_text = response.full_text_annotation.text
            
            # 텍스트 정리
            full_text = self.clean_ocr_text(full_text)
            
            # 텍스트 블록 및 위치 정보 추출
            blocks = []
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    block_text = ""
                    for paragraph in block.paragraphs:
                        para_text = ""
                        for word in paragraph.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            para_text += word_text + " "
                        block_text += para_text.strip() + " "
                    
                    # 텍스트 블록 좌표 추출
                    vertices = block.bounding_box.vertices
                    x = vertices[0].x
                    y = vertices[0].y
                    width = vertices[2].x - vertices[0].x
                    height = vertices[2].y - vertices[0].y
                    
                    blocks.append({
                        'text': block_text.strip(),
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'area': width * height
                    })
            
            logger.info(f"OCR로 추출한 텍스트 길이: {len(full_text)} 문자, 블록 수: {len(blocks)}")
            return {"full_text": full_text, "blocks": blocks}
        
        except Exception as e:
            logger.error(f"텍스트 추출 오류: {e}")
            return {"full_text": "", "blocks": []}
    
    def clean_ocr_text(self, text: str) -> str:
        """OCR 텍스트 정리"""
        if not text:
            return ""
        
        # 특수 문자 처리 및 문자열 정리
        cleaned = re.sub(r'[«»•‣◦□■●]', '', text)
        
        # 불필요한 줄바꿈 제거 (빈 줄은 유지)
        cleaned = re.sub(r'([^\n])\n([^\n])', r'\1 \2', cleaned)
        
        # 공백 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def detect_document_type(self, text: str) -> str:
        """문서 유형 감지 (주문서, 인보이스 등)"""
        # 주문서 패턴
        po_patterns = [
            r'PO#:\s*\d+',
            r'Purchase Order',
            r'Order Information',
            r'Grand Total:'
        ]
        
        # 인보이스 패턴
        invoice_patterns = [
            r'ORDER CONFIRMATION ID:',
            r'Invoice',
            r'Doc\.\s*Total:',
            r'Payment Terms:'
        ]
        
        # 패턴 일치 점수 계산
        po_score = sum(1 for pattern in po_patterns if re.search(pattern, text, re.IGNORECASE))
        invoice_score = sum(1 for pattern in invoice_patterns if re.search(pattern, text, re.IGNORECASE))
        
        # 가장 높은 점수의 문서 유형 반환
        if po_score > invoice_score:
            return "purchase_order"
        elif invoice_score > po_score:
            return "order_confirmation"
        else:
            return "unknown"
    
    def extract_document_metadata(self, text: str, doc_type: str) -> Dict[str, str]:
        """문서 메타데이터 추출 (주문번호, 날짜 등)"""
        metadata = {
            'document_type': doc_type
        }
        
        # 공통 패턴 추출
        # 브랜드
        brand_match = re.search(r'(TOGA\s+VIRILIS)', text, re.IGNORECASE)
        if brand_match:
            metadata['brand'] = brand_match.group(1).strip()
        
        # 시즌
        season_match = re.search(r'(\d{4}(?:SS|FW)[A-Z]*)', text)
        if season_match:
            metadata['season'] = season_match.group(1)
        
        # 주문서 특정 패턴
        if doc_type == "purchase_order":
            # PO 번호
            po_match = re.search(r'PO#:\s*(\d+)', text, re.IGNORECASE)
            if po_match:
                metadata['po_number'] = po_match.group(1)
            
            # 생성 날짜
            date_match = re.search(r'Created:\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if date_match:
                metadata['created_date'] = date_match.group(1)
            
            # 선적 날짜
            ship_start_match = re.search(r'Start\s+Ship:\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if ship_start_match:
                metadata['start_ship'] = ship_start_match.group(1)
            
            ship_end_match = re.search(r'Complete\s+Ship:\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if ship_end_match:
                if ship_end_match:
                    metadata['complete_ship'] = ship_end_match.group(1)
           
           # 결제 조건
            terms_match = re.search(r'Terms:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
            if terms_match:
               metadata['terms'] = terms_match.group(1).strip()
           
           # 총액
            total_match = re.search(r'Grand\s+Total:\s*(\w+)\s*([\d,.]+)', text, re.IGNORECASE)
            if total_match:
               currency = total_match.group(1)
               metadata['currency'] = currency
               metadata['total_amount'] = total_match.group(2).replace(',', '')
           
           # 총 수량
            qty_match = re.search(r'Total\s+Quantity:\s*(\d+)', text, re.IGNORECASE)
            if qty_match:
               metadata['total_quantity'] = qty_match.group(1)
       
       # 인보이스 특정 패턴
        elif doc_type == "order_confirmation":
           # 인보이스 ID
           invoice_match = re.search(r'ORDER CONFIRMATION ID:\s*(\d+)', text, re.IGNORECASE)
           if invoice_match:
               metadata['invoice_id'] = invoice_match.group(1)
           
           # 날짜
           date_match = re.search(r'Date:\s*(\d{2}-\d{2}-\d{4})', text, re.IGNORECASE)
           if date_match:
               metadata['date'] = date_match.group(1)
           
           # 결제 조건
           payment_match = re.search(r'Payment Terms:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
           if payment_match:
               metadata['payment_terms'] = payment_match.group(1).strip()
           
           # 결제 방법
           method_match = re.search(r'Payment Method:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
           if method_match:
               metadata['payment_method'] = method_match.group(1).strip()
           
           # 인코텀즈
           incoterms_match = re.search(r'Incoterms:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
           if incoterms_match:
               metadata['incoterms'] = incoterms_match.group(1).strip()
           
           # 총액
           total_match = re.search(r'Doc\.\s*Total:\s*([\d,.]+)\s*(\w+)', text, re.IGNORECASE)
           if total_match:
               metadata['total_amount'] = total_match.group(1).replace(',', '')
               metadata['currency'] = total_match.group(2)
           elif total_match := re.search(r'Total Before Discount:\s*([\d,.]+)\s*(\w+)', text, re.IGNORECASE):
               metadata['total_amount'] = total_match.group(1).replace(',', '')
               metadata['currency'] = total_match.group(2)
           
           # 배송 기간
           shipping_match = re.search(r'SHIPPING\s+WINDOW\s+(\d{1,2}\s+\w{3}\s+\d{2})\s+(\d{1,2}\s+\w{3}\s+\d{2})', text, re.IGNORECASE)
           if shipping_match:
               metadata['shipping_start'] = shipping_match.group(1)
               metadata['shipping_end'] = shipping_match.group(2)
       
        logger.info(f"추출된 문서 메타데이터: {metadata}")
        return metadata


class TableContentExtractor:
   """테이블 내용 추출 클래스"""
   
   def __init__(self, vision_client):
       """테이블 내용 추출기 초기화"""
       self.vision_client = vision_client
       # 기본 사이즈 배열 (유럽 사이즈)
       self.default_sizes = ['39', '40', '41', '42', '43', '44', '45', '46']
   
   def extract_table_content(self, table_image_path: str, table_structure: Dict) -> Dict:
       """테이블 이미지에서 구조화된 콘텐츠 추출"""
       try:
           # OCR 적용
           with io.open(table_image_path, 'rb') as image_file:
               content = image_file.read()
           
           vision_image = vision.Image(content=content)
           response = self.vision_client.document_text_detection(image=vision_image)
           
           if response.error.message:
               logger.error(f"테이블 OCR 오류: {response.error.message}")
               return {"grid": [], "raw_text": ""}
           
           # 전체 텍스트 추출
           raw_text = response.full_text_annotation.text
           
           # 디버깅: 테이블 내 텍스트 출력
           logger.debug(f"테이블 내 텍스트: {raw_text}")
           
           # 테이블 유형 추측 (사이즈-수량 테이블 또는 기타 정보 테이블)
           # 2자리와 3자리 사이즈 모두 고려
           is_size_table = bool(re.search(r'\b(?:39|40|41|42|43|44|45|46)\b|\b(?:390|400|410|420|430|440|450|460)\b', raw_text))
           is_product_table = bool(re.search(r'\b(AJ\d+|FTVRM|MODEL|ITEM CODE|UNIT PRICE)\b', raw_text, re.IGNORECASE))
           
           table_type = ""
           if is_size_table:
               table_type = "size_table"
           elif is_product_table:
               table_type = "product_table"
           
           # 텍스트 블록 및 위치 정보 추출
           text_blocks = []
           for page in response.full_text_annotation.pages:
               for block in page.blocks:
                   for paragraph in block.paragraphs:
                       para_text = ""
                       for word in paragraph.words:
                           word_text = ''.join([symbol.text for symbol in word.symbols])
                           para_text += word_text + " "
                       
                       # 텍스트 블록 좌표 (왼쪽 상단)
                       vertices = paragraph.bounding_box.vertices
                       x = vertices[0].x
                       y = vertices[0].y
                       width = vertices[2].x - vertices[0].x
                       height = vertices[2].y - vertices[0].y
                       
                       text_blocks.append({
                           'text': para_text.strip(),
                           'x': x,
                           'y': y,
                           'width': width,
                           'height': height,
                           'center_x': x + width/2,
                           'center_y': y + height/2
                       })
           
           # 셀별 텍스트 매핑
           cells = table_structure.get('cells', [])
           
           grid = []
           for cell in cells:
               cell_content = ""
               
               # 셀 영역 정의
               cell_x1, cell_y1 = cell['x1'], cell['y1']
               cell_x2, cell_y2 = cell['x2'], cell['y2']
               
               # 셀에 포함된 텍스트 블록 찾기
               for block in text_blocks:
                   block_center_x = block['center_x']
                   block_center_y = block['center_y']
                   
                   # 텍스트 블록의 중심이 셀 내에 있는지 확인
                   if (cell_x1 <= block_center_x <= cell_x2 and
                       cell_y1 <= block_center_y <= cell_y2):
                       if cell_content:
                           cell_content += " "
                       cell_content += block['text']
               
               grid.append({
                   'row': cell['row'],
                   'col': cell['col'],
                   'text': cell_content.strip(),
                   'x1': cell_x1,
                   'y1': cell_y1,
                   'x2': cell_x2,
                   'y2': cell_y2
               })
           
           # 행별로 그리드 정렬
           grid.sort(key=lambda cell: (cell['row'], cell['col']))
           
           return {
               "grid": grid,
               "raw_text": raw_text,
               "table_type": table_type
           }
       
       except Exception as e:
           logger.error(f"테이블 내용 추출 오류: {e}")
           return {"grid": [], "raw_text": "", "table_type": ""}
   
   def analyze_table_headers(self, grid: List[Dict], raw_text: str = "") -> Dict:
       """테이블 헤더 분석 및 역할 식별 (개선된 버전)"""
       if not grid:
           return {"headers": [], "data_start_row": 0}
       
       # 행과 열 개수 파악
       max_row = max(cell['row'] for cell in grid) if grid else 0
       max_col = max(cell['col'] for cell in grid) if grid else 0
       
       # 행별 데이터 구성
       rows = [[] for _ in range(max_row + 1)]
       for cell in grid:
           row_idx = cell['row']
           if 0 <= row_idx <= max_row:
               rows[row_idx].append(cell)
       
       # 헤더 행 식별 (첫 번째 행부터 검사)
       headers = []
       data_start_row = 0
       
       # 다양한 사이즈 패턴 확인 (2자리, 3자리 모두 확인)
       size_patterns = [
           # 2자리 유럽 사이즈
           r'\b(?:39|40|41|42|43|44|45|46)\b',
           # 3자리 유럽 사이즈
           r'\b(?:390|400|410|420|430|440|450|460)\b',
           # 연속된 숫자 패턴 (사이즈로 간주)
           r'\b(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})\b'
       ]
       
       # 헤더 키워드 패턴
       header_patterns = [
           r'\b(MODEL|ITEM\s*CODE|UNIT\s*PRICE|STYLE|COLOR|QTY|TOTAL)\b',
           r'\b(FTVRM\w+|AJ\d+|BLACK\s+LEATHER|POLIDO)\b'
       ]
       
       # 사이즈 행 또는 헤더 행 찾기
       for row_idx, row in enumerate(rows):
           # 행의 셀 텍스트 조사
           row_text = ' '.join([cell['text'] for cell in row if cell['text']])
           logger.debug(f"행 {row_idx} 텍스트: {row_text}")
           
           # 사이즈 행 확인 (다양한 패턴 확인)
           is_size_row = False
           for pattern in size_patterns:
               if re.search(pattern, row_text, re.IGNORECASE):
                   is_size_row = True
                   logger.info(f"사이즈 행 발견 (행 {row_idx}): {row_text}")
                   break
           
           # 헤더 패턴 확인
           is_header_row = False
           for pattern in header_patterns:
               if re.search(pattern, row_text, re.IGNORECASE):
                   is_header_row = True
                   logger.info(f"헤더 행 발견 (행 {row_idx}): {row_text}")
                   break
           
           # 테이블 전체 텍스트에서 사이즈 찾기 (행 분석으로 찾지 못한 경우)
           if not is_size_row and raw_text:
               for pattern in size_patterns:
                   if re.search(pattern, raw_text, re.IGNORECASE):
                       # 행이 사이즈 행에 가까운지 확인 (행 내용이 거의 숫자로만 구성됨)
                       digits_ratio = sum(1 for c in row_text if c.isdigit()) / len(row_text) if row_text else 0
                       if digits_ratio > 0.5:  # 50% 이상이 숫자인 경우
                           is_size_row = True
                           logger.info(f"사이즈 행으로 추정 (행 {row_idx}, 숫자 비율: {digits_ratio:.2f}): {row_text}")
                           break
           
           if is_size_row or is_header_row:
               # 헤더 역할 추론
               header_role = None
               if is_size_row:
                   header_role = "size"
               elif re.search(r'\b(MODEL|STYLE|ITEM\s*CODE|FTVRM)\b', row_text, re.IGNORECASE):
                   header_role = "product_info"
               elif re.search(r'\b(UNIT\s*PRICE|PRICE|EUR)\b', row_text, re.IGNORECASE):
                   header_role = "price"
               elif re.search(r'\b(TOTAL|QTY|QUANTITY)\b', row_text, re.IGNORECASE):
                   header_role = "total"
               
               # 헤더 정보 저장
               headers.append({
                   'row_idx': row_idx,
                   'cells': row,
                   'text': row_text,
                   'role': header_role
               })
               
               # 데이터 시작 행 갱신
               data_start_row = row_idx + 1
           
           # 사이즈 헤더 행을 발견한 경우 데이터 시작 행 갱신
           if is_size_row:
               data_start_row = row_idx + 1
               # 사이즈 행 발견 시 추가 로깅
               sizes = []
               for pattern in size_patterns:
                   found_sizes = re.findall(pattern, row_text)
                   if isinstance(found_sizes[0], tuple) if found_sizes else False:
                       # 튜플 형태의 결과 처리 (연속 숫자 패턴)
                       sizes.extend(list(found_sizes[0]))
                   else:
                       sizes.extend(found_sizes)
               logger.info(f"사이즈 행에서 추출한 사이즈: {sizes}")
       
       # 테이블 전체 텍스트에서 사이즈 인식 시도 (마지막 시도)
       if not headers and raw_text:
           for pattern in size_patterns:
               sizes = re.findall(pattern, raw_text)
               if sizes:
                   if isinstance(sizes[0], tuple) if sizes else False:
                       # 튜플 형태의 결과 처리
                       flat_sizes = [item for sublist in sizes for item in sublist]
                       logger.info(f"테이블 텍스트에서 사이즈 추출: {flat_sizes}")
                   else:
                       logger.info(f"테이블 텍스트에서 사이즈 추출: {sizes}")
                   # 가상 헤더 생성
                   headers.append({
                       'row_idx': -1,  # 가상 행 인덱스
                       'cells': [],
                       'text': ' '.join(sizes if not isinstance(sizes[0], tuple) else flat_sizes),
                       'role': "size"
                   })
                   break
       
       return {
           "headers": headers,
           "data_start_row": data_start_row
       }
   
   def extract_text_blocks_from_grid(self, grid: List[Dict]) -> List[Dict]:
       """그리드 데이터에서 텍스트 블록 정보 추출"""
       text_blocks = []
       for cell in grid:
           if cell['text'].strip():
               text_blocks.append({
                   'text': cell['text'].strip(),
                   'x': cell['x1'],
                   'y': cell['y1'],
                   'width': cell['x2'] - cell['x1'],
                   'height': cell['y2'] - cell['y1'],
                   'center_x': cell['x1'] + (cell['x2'] - cell['x1'])/2,
                   'center_y': cell['y1'] + (cell['y2'] - cell['y1'])/2,
                   'row': cell['row'],
                   'col': cell['col']
               })
       return text_blocks

   def extract_size_quantity_vertical(self, grid: List[Dict], headers_info: Dict, raw_text: str) -> Dict[str, Dict]:
       """수직 정렬 기반 사이즈-수량 매핑 추출"""
       size_qty_maps = {}
       
       # 사이즈 헤더 행 찾기
       size_row = None
       for header in headers_info.get('headers', []):
           if header.get('role') == 'size':
               size_row = header
               break
       
       if not size_row:
           logger.warning("사이즈 행을 찾을 수 없습니다.")
           return {}
       
       logger.info(f"사이즈 행 발견: row_idx={size_row['row_idx']}, text={size_row['text']}")
       
       # 사이즈 셀 위치 찾기
       size_cells = {}
       for cell in size_row['cells']:
           size_text = cell['text'].strip()
           size_match = re.search(r'\b(\d{2,3})\b', size_text)
           if size_match:
               size = size_match.group(1)
               # 3자리 사이즈(390)를 2자리(39)로 정규화
               normalized_size = size[:2] if len(size) > 2 else size
               size_cells[normalized_size] = {
                   'col': cell['col'], 
                   'x1': cell['x1'], 
                   'x2': cell['x2'],
                   'center_x': (cell['x1'] + cell['x2'])/2
               }
       
       logger.info(f"추출된 사이즈 셀: {list(size_cells.keys())}")
       
       # 데이터 행에서 제품 코드 찾기
       product_rows = []
       for cell in grid:
           if cell['row'] >= headers_info['data_start_row']:
               code_match = re.search(r'\b(AJ\d+)\b', cell['text'])
               if code_match:
                   product_code = code_match.group(1)
                   row = cell['row']
                   product_rows.append({'row': row, 'product_code': product_code, 'cell': cell})
       
       logger.info(f"제품 행 발견: {[p['product_code'] for p in product_rows]}")
       
       # 각 제품 행에 대해 수직으로 일치하는 수량 찾기
       for product_info in product_rows:
           row = product_info['row']
           product_code = product_info['product_code']
           
           # 두 가지 접근법 시도:
           # 1. 같은 행에서 각 사이즈 열의 값 찾기
           # 2. 다음 행(수량 행일 가능성 높음)에서 사이즈 열과 수직 정렬된 값 찾기
           
           # 1. 같은 행에서 시도
           same_row_cells = [c for c in grid if c['row'] == row]
           size_qty_map = {}
           
           for size, size_info in size_cells.items():
               # 같은 열 찾기
               qty_cell = next((c for c in same_row_cells if c['col'] == size_info['col']), None)
               
               # 열 인덱스로 찾지 못하면 x좌표 범위로 찾기
               if not qty_cell:
                   qty_cell = next((c for c in same_row_cells 
                                   if size_info['x1'] <= c['x1'] + (c['x2']-c['x1'])/2 <= size_info['x2']), None)
               
               # 셀에서 수량 추출
               if qty_cell and qty_cell['text'].strip():
                   qty_match = re.search(r'\b(\d+)\b', qty_cell['text'])
                   if qty_match:
                       qty = int(qty_match.group(1))
                       size_qty_map[size] = qty
           
           # 첫 번째 방법으로 충분한 데이터를 얻지 못했다면 두 번째 방법 시도
           if len(size_qty_map) < len(size_cells) * 0.5:  # 50% 미만의 사이즈에 대한 수량을 찾은 경우
               logger.info(f"제품 {product_code}: 같은 행에서 충분한 수량을 찾지 못했습니다. 다음 행 확인...")
               
               # 2. 다음 행 시도
               next_row = row + 1
               next_row_cells = [c for c in grid if c['row'] == next_row]
               
               if next_row_cells:
                   for size, size_info in size_cells.items():
                       # x좌표 범위로 매칭
                       qty_cell = next((c for c in next_row_cells 
                                      if size_info['x1'] <= c['x1'] + (c['x2']-c['x1'])/2 <= size_info['x2']), None)
                       
                       # 수직 정렬 확인 - 중심점 기준으로 최소 거리 사용
                       if not qty_cell:
                           min_dist = float('inf')
                           closest_cell = None
                           for cell in next_row_cells:
                               dist = abs(cell['x1'] + (cell['x2']-cell['x1'])/2 - size_info['center_x'])
                               if dist < min_dist:
                                   min_dist = dist
                                   closest_cell = cell
                           
                           # 거리가 너무 멀면 무시
                           if min_dist <= 50:  # 픽셀 단위, 필요에 따라 조정
                               qty_cell = closest_cell
                       
                       # 셀에서 수량 추출
                       if qty_cell and qty_cell['text'].strip():
                           qty_match = re.search(r'\b(\d+)\b', qty_cell['text'])
                           if qty_match:
                               qty = int(qty_match.group(1))
                               size_qty_map[size] = qty
           
           # 결과 로깅
           if size_qty_map:
               logger.info(f"제품 {product_code} 사이즈-수량 매핑 성공: {size_qty_map}")
               size_qty_maps[product_code] = {
                   'row': row,
                   'size_qty': size_qty_map
               }
           else:
               logger.warning(f"제품 {product_code} 사이즈-수량 매핑 실패")
       
       return size_qty_maps

   def map_sizes_to_quantities_by_proximity(self, text_blocks: List[Dict], sizes: List[str], raw_text: str) -> Dict[str, Dict]:
       """공간적 근접성 기반 사이즈-수량 매핑"""
       # 제품 코드 추출
       product_codes = re.findall(r'\b(AJ\d+)\b', raw_text)
       if not product_codes:
           return {}
       
       # 중복 제거
       product_codes = list(set(product_codes))
       
       # 결과 저장용
       size_qty_maps = {}
       
       # 각 제품에 대해 제품 코드 근처의 사이즈-수량 쌍 찾기
       for product_code in product_codes:
           # 제품 코드 위치 찾기
           product_blocks = [block for block in text_blocks if re.search(r'\b' + product_code + r'\b', block['text'])]
           
           if not product_blocks:
               continue
           
           # 첫 번째 제품 블록 사용
           product_block = product_blocks[0]
           
           # 제품 코드 주변 텍스트 영역 정의 (y 좌표 기준)
           product_y = product_block['center_y']
           context_range = 100  # 상하 100픽셀 범위 내의 텍스트 블록 고려
           
           # 사이즈 텍스트 블록 찾기
           size_blocks = []
           for block in text_blocks:
               # 근접한 y 좌표 내에 있는지 확인
               if abs(block['center_y'] - product_y) <= context_range:
                   for size in sizes:
                       if re.search(r'\b' + size + r'\b', block['text']):
                           size_blocks.append({
                               'size': size,
                               'x': block['x'],
                               'y': block['y'],
                               'center_x': block['center_x'],
                               'center_y': block['center_y']
                           })
           
           # 수량 텍스트 블록 찾기 (1~20 사이의 숫자만 포함된 블록)
           qty_blocks = []
           for block in text_blocks:
               # 근접한 y 좌표 내에 있는지 확인
               if abs(block['center_y'] - product_y) <= context_range:
                   # 숫자만 있는지 확인
                   qty_match = re.match(r'^(\d+)$', block['text'].strip())
                   if qty_match and 1 <= int(qty_match.group(1)) <= 20:  # 합리적인 수량 범위
                       qty_blocks.append({
                           'qty': int(qty_match.group(1)),
                           'x': block['x'],
                           'y': block['y'],
                           'center_x': block['center_x'],
                           'center_y': block['center_y']
                       })
           
           # 각 사이즈에 대해 가장 가까운 수량 찾기
           size_qty_map = {}
           for size_block in size_blocks:
               closest_qty = None
               min_distance = float('inf')
               
               for qty_block in qty_blocks:
                   # 거리 계산 (x, y 좌표 모두 고려)
                   distance = ((size_block['center_x'] - qty_block['center_x']) ** 2 + 
                              (size_block['center_y'] - qty_block['center_y']) ** 2) ** 0.5
                   
                   # x 좌표가 비슷하면 가중치 추가 (같은 열에 있을 가능성)
                   if abs(size_block['center_x'] - qty_block['center_x']) < 30:  # x좌표 차이가 작으면 같은 열
                       distance *= 0.5
                   
                   if distance < min_distance:
                       min_distance = distance
                       closest_qty = qty_block
               
               # 가까운 수량을 찾은 경우에만 매핑
               if closest_qty and min_distance < 200:  # 최대 거리 제한
                   size_qty_map[size_block['size']] = closest_qty['qty']
           
           # 결과가 있으면 저장
           if size_qty_map:
               logger.info(f"공간적 근접성 기반 제품 {product_code} 사이즈-수량 매핑 성공: {size_qty_map}")
               size_qty_maps[product_code] = {
                   'row': -1,  # 행 정보 없음
                   'size_qty': size_qty_map
               }
           else:
               logger.warning(f"공간적 근접성 기반 제품 {product_code} 사이즈-수량 매핑 실패")
       
       return size_qty_maps
   
   def extract_size_quantity_mapping(self, grid: List[Dict], headers_info: Dict, raw_text: str = "") -> Dict[str, Dict]:
       """사이즈-수량 매핑 추출 (구조적 접근법)"""
       try:
           # 1. 구조적 매핑 시도 (수직 정렬 기반)
           size_qty_maps = self.extract_size_quantity_vertical(grid, headers_info, raw_text)
           
           # 성공적으로 매핑이 추출되었는지 확인
           if size_qty_maps and any(len(m.get('size_qty', {})) > 0 for m in size_qty_maps.values()):
               logger.info("수직 정렬 기반 사이즈-수량 매핑 성공")
               return size_qty_maps
           
           # 2. 공간적 근접성 기반 매핑 시도
           ocr_text_blocks = self.extract_text_blocks_from_grid(grid)
           size_qty_maps = self.map_sizes_to_quantities_by_proximity(ocr_text_blocks, self.default_sizes, raw_text)
           
           if size_qty_maps and any(len(m.get('size_qty', {})) > 0 for m in size_qty_maps.values()):
               logger.info("공간적 근접성 기반 사이즈-수량 매핑 성공")
               return size_qty_maps
           
           logger.warning("구조적 매핑 실패, 텍스트 기반 규칙으로 시도...")
           
           # 3. 텍스트 기반 규칙 시도 (하드코딩 매핑 없이)
           size_map = {}
           
           # 제품 코드 추출
           product_codes = re.findall(r'\b(AJ\d+)\b', raw_text)
           if not product_codes:
               logger.warning("텍스트에서 제품 코드를 찾을 수 없습니다.")
               return {}
           
           # 중복 제거 및 정렬
           product_codes = sorted(list(set(product_codes)))
           logger.info(f"추출된 제품 코드: {product_codes}")
           
           # 각 제품별 코드 주변 문맥 추출
           for product_code in product_codes:
               # 제품 코드 주변 텍스트 추출
               product_pattern = fr'{product_code}.*?(?=AJ\d+|$)'
               product_section_match = re.search(product_pattern, raw_text, re.DOTALL)
               
               if not product_section_match:
                   logger.warning(f"제품 {product_code}의 주변 텍스트를 찾을 수 없습니다.")
                   continue
               
               product_section = product_section_match.group(0)
               
               # 제품 섹션에서 사이즈-수량 패턴 찾기
               size_qty_map = {}
               
               # 패턴 1: 사이즈:수량 형식 (예: 39:1 40:2 41:3)
               size_qty_pattern1 = r'(\d{2}):(\d+)'
               size_qty_matches1 = re.findall(size_qty_pattern1, product_section)
               
               if size_qty_matches1:
                   for size, qty in size_qty_matches1:
                       size_qty_map[size] = int(qty)
                   logger.info(f"패턴1(사이즈:수량)로 제품 {product_code} 사이즈-수량 매핑 성공")
               
               # 패턴 2: 숫자 나열 (마지막은 합계) - 인보이스에 흔한 패턴
               # 예: 1 1 2 2 1 7 (39 40 41 42 43 합계)
               if not size_qty_map:
                   # 숫자 나열 찾기
                   number_sequence = re.findall(r'(\d+(?:\s+\d+){3,})', product_section)
                   if number_sequence:
                       # 가장 긴 숫자 나열 사용
                       longest_sequence = max(number_sequence, key=len)
                       numbers = [int(n) for n in re.findall(r'\d+', longest_sequence)]
                       
                       # 마지막 숫자는 합계일 가능성이 높음
                       if len(numbers) >= 2 and sum(numbers[:-1]) == numbers[-1]:
                           # 기본 사이즈 매핑
                           qty_list = numbers[:-1]  # 마지막은 합계이므로 제외
                           sizes_to_use = self.default_sizes[:len(qty_list)]
                           
                           for i, size in enumerate(sizes_to_use):
                               if i < len(qty_list):
                                   size_qty_map[size] = qty_list[i]
                           
                           logger.info(f"패턴2(숫자 나열)로 제품 {product_code} 사이즈-수량 매핑 성공")
               
               # 패턴 3: 총 수량만 있는 경우, 균등 분배
               if not size_qty_map:
                   total_qty_match = re.search(r'(?:TOTAL|Total|QTY|Qty).*?(\d+)', product_section, re.IGNORECASE)
                   if total_qty_match:
                       total_qty = int(total_qty_match.group(1))
                       logger.info(f"제품 {product_code}의 총 수량 발견: {total_qty}")
                       
                       # 기본 사이즈 배열
                       sizes_to_use = self.default_sizes[:6]  # 가장 일반적인 6개 사이즈
                       
                       # 균등 분배 로직
                       base_qty = total_qty // len(sizes_to_use)
                       remainder = total_qty % len(sizes_to_use)
                       
                       # 중간 사이즈에 더 많은 수량 배분
                       if remainder > 0:
                           # 중간 인덱스부터 시작해서 나머지 수량 배분
                           middle_index = len(sizes_to_use) // 2 - remainder // 2
                           
                           for i, size in enumerate(sizes_to_use):
                               if middle_index <= i < middle_index + remainder:
                                   size_qty_map[size] = base_qty + 1
                               else:
                                   size_qty_map[size] = base_qty
                       else:
                           # 균등 분배
                           for size in sizes_to_use:
                               size_qty_map[size] = base_qty
                       
                       logger.info(f"패턴3(총 수량 기반 균등 분배)로 제품 {product_code} 사이즈-수량 매핑 성공")
               
               # 제품별 사이즈-수량 매핑 저장
               if size_qty_map:
                   size_map[product_code] = {
                       'row': -1,  # 행 정보 없음
                       'size_qty': size_qty_map,
                       'method': 'text_pattern'
                   }
           
           return size_map
           
       except Exception as e:
           logger.error(f"사이즈-수량 매핑 오류: {e}")
           import traceback
           logger.error(traceback.format_exc())
           
           # 실패 시 빈 맵 반환
           return {}
   
   def extract_product_information(self, grid: List[Dict], raw_text: str, metadata: Dict) -> List[Dict]:
       """제품 정보 추출 (사이즈별 칼럼 형식)"""
       products = []
       
       # 제품 코드 패턴으로 제품 추출
       product_codes = re.findall(r'\b(AJ\d+)\b', raw_text)
       
       if not product_codes:
           return products
       
       # 중복 제거
       product_codes = list(set(product_codes))
       logger.info(f"추출된 제품 코드: {', '.join(product_codes)}")
       
       for product_code in product_codes:
           # 제품 코드 주변 텍스트 추출 (정규식으로 제품 섹션 찾기)
           product_section_regex = fr'{product_code}.*?(?=AJ\d+|$)'
           product_section_match = re.search(product_section_regex, raw_text, re.DOTALL)
           
           if not product_section_match:
               continue
           
           product_section = product_section_match.group(0)
           
           # 색상 추출
           color_match = re.search(r'(BLACK\s+(?:LEATHER|POLIDO)|WHITE\s+LEATHER|BROWN\s+LEATHER)', product_section)
           color = color_match.group(1) if color_match else "BLACK LEATHER"
           
           # 스타일 코드 추출
           style_match = re.search(r'Style\s+[#]?(FTVRM\w+)|#?(FTVRM\w+)|(FTVRM\w+)', product_section, re.IGNORECASE)
           style_code = ""
           if style_match:
               # 여러 그룹 중 매칭된 첫 번째 그룹 선택
               for i in range(1, 4):
                   if style_match.group(i):
                       style_code = style_match.group(i)
                       break
           
           # 가격 정보 추출
           wholesale_match = re.search(r'Wholesale:?\s*(?:EUR)?\s*(\d+\.\d+)', product_section)
           if wholesale_match:
               wholesale_price = wholesale_match.group(1)
           else:
               # UNIT PRICE 패턴 (ORDER CONFIRMATION)
               unit_price_match = re.search(r'(\d+\.\d+)(?:\s+0\.00%|\s+EUR)', product_section)
               wholesale_price = unit_price_match.group(1) if unit_price_match else ""
           
           retail_match = re.search(r'(?:Sugg\.|Suggested)\s+Retail:?\s*(?:EUR)?\s*(\d+\.\d+)', product_section)
           retail_price = retail_match.group(1) if retail_match else ""
           
           # 총 수량 추출
           total_qty_match = re.search(r'(?:TOTAL|Total).*?(\d+)$', product_section, re.MULTILINE)
           total_qty = total_qty_match.group(1) if total_qty_match else ""
           
           # 총 금액 추출
           total_price_match = re.search(r'(\d+\.\d+)(?:\s+EUR|\s*$)', product_section)
           total_price = total_price_match.group(1) if total_price_match else ""
           
           # 기본 제품 정보 구성
           product_info = {
               'Product_Code': product_code,
               'Style': style_code,
               'Color': color,
               'Wholesale_Price': wholesale_price,
               'Retail_Price': retail_price,
               'Total_Qty': total_qty,
               'Total_Price': total_price,
               'Brand': metadata.get('brand', 'TOGA VIRILIS'),
               'Season': metadata.get('season', ''),
               'Document_Type': metadata.get('document_type', '')
           }
           
           # 문서 유형별 추가 정보
           if metadata.get('document_type') == 'purchase_order':
               product_info.update({
                   'PO_Number': metadata.get('po_number', ''),
                   'Created_Date': metadata.get('created_date', ''),
                   'Currency': metadata.get('currency', 'EUR')
               })
           elif metadata.get('document_type') == 'order_confirmation':
               product_info.update({
                   'Invoice_ID': metadata.get('invoice_id', ''),
                   'Date': metadata.get('date', ''),
                   'Payment_Terms': metadata.get('payment_terms', ''),
                   'Currency': metadata.get('currency', 'EUR')
               })
           
           # 각 사이즈별 수량 칼럼 추가 (나중에 채움)
           for size in self.default_sizes:
               product_info[f'Size_{size}'] = 0
           
           products.append(product_info)
       
       # 특별 케이스: ORDER CONFIRMATION 형식 처리
       if not products and metadata.get('document_type') == 'order_confirmation':
           # ORDER CONFIRMATION 특화 패턴
           order_conf_pattern = r'(FTVRM\w+)\s+\w+\s+(AJ\d+)\s*-\s*([A-Z\s]+(?:LEATHER|POLIDO))\s+(\d+\.\d+)\s+0\.00%.*?\s+((?:\d+\s+)+\d+)'
           order_conf_matches = re.findall(order_conf_pattern, raw_text)
           
           for match in order_conf_matches:
               ftvrm_code, product_code, color, price, quantity_text = match
               
               # 수량 및 합계 추출
               quantities = re.findall(r'\d+', quantity_text)
               if len(quantities) >= 2:
                   total_qty = quantities[-1]  # 마지막 숫자는 합계
                   size_quantities = quantities[:-1]  # 마지막 이전은 사이즈별 수량
               else:
                   total_qty = ""
                   size_quantities = quantities
               
               # 기본 제품 정보 구성
               product_info = {
                   'Product_Code': product_code,
                   'Style': ftvrm_code,
                   'Color': color.strip(),
                   'Wholesale_Price': price,
                   'Total_Qty': total_qty,
                   'Brand': metadata.get('brand', 'TOGA VIRILIS'),
                   'Season': metadata.get('season', ''),
                   'Document_Type': 'order_confirmation',
                   'Invoice_ID': metadata.get('invoice_id', ''),
                   'Date': metadata.get('date', ''),
                   'Payment_Terms': metadata.get('payment_terms', ''),
                   'Currency': metadata.get('currency', 'EUR')
               }
               
               # 각 사이즈별 수량 칼럼 추가
               for size in self.default_sizes:
                   product_info[f'Size_{size}'] = 0
               
               products.append(product_info)
       
       return products
   
   def generate_custom_code(self, product_info: Dict, size: str) -> str:
       """품번코드 자동 생성"""
       try:
           # 시즌 정보에서 연도 추출
           year = "00"
           season = product_info.get('Season', '')
           if season and len(season) >= 6:
               try:
                   year = season[2:4]  # 2024SS에서 '24' 추출
               except:
                   year = "00"
           
           # 시즌 코드 추출 (SS -> S, FW -> F)
           season_code = "X"
           if "SS" in season:
               season_code = "S"
           elif "FW" in season:
               season_code = "F"
           
           # 색상 코드 추출
           color = product_info.get('Color', '')
           color_code = "X"
           if color:
               if 'BLACK' in color:
                   if 'POLIDO' in color:
                       color_code = "P"
                   else:
                       color_code = "B"
               elif 'WHITE' in color:
                   color_code = "W"
               elif 'BROWN' in color:
                   color_code = "N"  # Brown = 브라운
           
           # 제품 카테고리 결정 (신발 = SH)
           category = "SH"  # Shoes
           
           # 브랜드 코드 (TOGA VIRILIS = TV)
           brand = "TV"
           
           # 판매 유형 및 라인
           sale_type = "ON"  # Online
           line = "M"        # Mens
           sub_category = "FL"  # Footwear
           
           # 배치 번호 (기본값)
           batch = "01"
           vendor = "AF"
           
           # 제품 코드에서 번호 부분 추출 (AJ1323 -> 1323)
           product_code = product_info.get('Product_Code', '')
           item_code = "000"
           if product_code:
               code_match = re.search(r'AJ(\d+)', product_code)
               if code_match:
                   item_code = code_match.group(1).zfill(3)  # 최소 3자리로 채움
           
           # 기본 품번코드 형식 생성
           custom_code = f"{year}{season_code}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{size}"
           
           return custom_code
       
       except Exception as e:
           logger.error(f"품번코드 생성 오류: {e}")
           return f"ERROR-{product_info.get('Product_Code', 'UNKNOWN')}-{size}"
   
   def create_size_quantity_dataframe(self, products: List[Dict], size_qty_maps: Dict[str, Dict]) -> List[Dict]:
       """사이즈-수량 매핑을 적용하여 제품 정보를 데이터프레임 형식으로 변환"""
       updated_products = []
       
       for product in products:
           product_code = product.get('Product_Code', '')
           
           # 제품의 사이즈-수량 매핑 가져오기
           size_qty_map = size_qty_maps.get(product_code, {}).get('size_qty', {})
           
           # 기존 제품 정보 복사
           updated_product = product.copy()
           
           # 각 사이즈별 수량 필드 업데이트
           for size in self.default_sizes:
               updated_product[f'Size_{size}'] = size_qty_map.get(size, 0)
           
           # 총 수량 계산 (만약 없다면)
           if not updated_product.get('Total_Qty'):
               total_qty = sum(size_qty_map.values())
               updated_product['Total_Qty'] = str(total_qty) if total_qty > 0 else ""
           
           updated_products.append(updated_product)
       
       return updated_products