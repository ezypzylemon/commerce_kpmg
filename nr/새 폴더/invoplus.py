import cv2
import numpy as np
import os
import pandas as pd
import re
import traceback
from pdf2image import convert_from_path
from google.cloud import vision
from datetime import datetime

# Vision 클라이언트 초기화 - 환경 변수에 이미 설정되어 있다고 가정
vision_client = vision.ImageAnnotatorClient()
print("[INFO] Google Cloud Vision API 클라이언트가 초기화되었습니다.")

def pdf_to_image(pdf_path, output_folder="temp_images", dpi=400):
    """PDF를 이미지로 변환합니다."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
    image_paths = []
    
    for i, image in enumerate(images):
        output_path = f"{output_folder}/page_{i+1}.jpg"
        image.save(output_path, 'JPEG')
        image_paths.append(output_path)
    
    return image_paths

def extract_text_with_reading_order(image_path):
    """
    Google Cloud Vision API의 document_text_detection을 사용하여
    읽기 순서를 보존한 텍스트를 추출하는 함수
    """
    try:
        # 이미지 파일 읽기
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        vision_image = vision.Image(content=content)
        
        # 문서 텍스트 감지 요청 (위치 정보 포함)
        response = vision_client.document_text_detection(image=vision_image)
        
        # 오류 처리
        if response.error.message:
            print(f"Error: {response.error.message}")
            return ""
        
        # 단어들을 읽기 순서대로 정렬하기 위한 리스트
        ordered_text = []
        
        # 페이지별 처리
        for page in response.full_text_annotation.pages:
            # 각 블록마다
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    # 단락 내의 모든 단어 추적
                    para_words = []
                    
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        # 단어의 상단 좌측 좌표
                        y_coord = word.bounding_box.vertices[0].y
                        x_coord = word.bounding_box.vertices[0].x
                        para_words.append((y_coord, x_coord, word_text))
                    
                    # 단락 내에서 단어를 위치에 따라 정렬
                    para_words.sort(key=lambda x: (x[0], x[1]))
                    ordered_text.extend(para_words)
        
        # y좌표로 먼저 정렬 (행), 그다음 x좌표로 정렬 (열)
        ordered_text.sort(key=lambda x: (x[0], x[1]))
        
        # 같은 행에 있는 단어들을 그룹화
        current_line = []
        result_lines = []
        current_y = ordered_text[0][0] if ordered_text else 0
        y_threshold = 10  # 같은 행으로 간주할 y좌표 차이 임계값
        
        for y, x, text in ordered_text:
            if abs(y - current_y) > y_threshold:
                # 새 행 시작, 현재 행 저장하고 초기화
                if current_line:
                    # x좌표로 정렬하여 한 행 내에서 왼쪽에서 오른쪽으로 단어 순서 유지
                    result_lines.append(' '.join([word for _, _, word in sorted(current_line, key=lambda item: item[1])]))
                current_line = [(y, x, text)]
                current_y = y
            else:
                current_line.append((y, x, text))
        
        # 마지막 행 처리
        if current_line:
            result_lines.append(' '.join([word for _, _, word in sorted(current_line, key=lambda item: item[1])]))
        
        # 연속된 빈 줄을 제거하고 줄 앞뒤 공백 제거
        processed_lines = []
        prev_line_empty = False
        
        for line in result_lines:
            line = line.strip()
            is_empty = len(line) == 0
            
            if not (is_empty and prev_line_empty):
                processed_lines.append(line)
            
            prev_line_empty = is_empty
        
        result_text = '\n'.join(processed_lines)
        
        return result_text
    
    except Exception as e:
        print(f"Google Vision API 호출 중 오류 발생: {e}")
        print(traceback.format_exc())
        return ""

def normalize_price(price_text, item_quantity=None, unit_price=None):
    """
    금액 형식을 정규화하고 필요 시 수량과 단가를 비교하여 검증합니다.
    
    Args:
        price_text: 정규화할 가격 텍스트
        item_quantity: 상품 수량 (검증용)
        unit_price: 단가 (검증용)
    
    Returns:
        정규화된 가격 텍스트
    """
    if not price_text:
        return price_text
    
    # 이미 소수점이 있는 경우 그대로 반환
    if '.' in price_text:
        return price_text
    
    # 소수점이 없는 큰 숫자인 경우 처리
    price_match = re.search(r'EUR\s*(\d+)', price_text)
    if price_match:
        try:
            extracted_price = int(price_match.group(1))
            
            # 수량과 단가 정보가 있으면 검증 실행
            if item_quantity is not None and unit_price is not None:
                try:
                    qty = int(item_quantity)
                    unit_price_value = float(re.search(r'EUR\s*(\d+\.*\d*)', unit_price).group(1))
                    expected_total = qty * unit_price_value
                    
                    print(f"검증: 수량({qty}) * 단가({unit_price_value}) = 예상 총액({expected_total:.2f})")
                    
                    # 일반 가격과 예상 가격의 차이가 큰 경우
                    price_ratio = extracted_price / expected_total
                    if price_ratio > 50:  # 가격이 50배 이상 차이나면 소수점 추가
                        corrected_price = extracted_price / 100
                        print(f"가격 수정: {extracted_price} → {corrected_price:.2f} (100으로 나눔)")
                        return f"EUR {corrected_price:.2f}"
                except (ValueError, AttributeError) as e:
                    print(f"가격 검증 중 오류: {e}")
            
            # 또는 가격이 비정상적으로 큰 경우 (10000 이상)
            if extracted_price >= 10000:
                corrected_price = extracted_price / 100
                print(f"가격 수정: {extracted_price} → {corrected_price:.2f} (100으로 나눔, 큰 값)")
                return f"EUR {corrected_price:.2f}"
                
        except ValueError:
            pass
    
    return price_text

def extract_metadata_info(image, full_text):
    """
    문서에서 메타데이터(브랜드, 시즌, 선적 기간, 구매가, 판매가 등) 정보를 추출합니다.
    """
    metadata = {
        'brand': '',
        'season': '',
        'start_ship': '',
        'complete_ship': '',
        'order_id': ''
    }
    
    # 전체 텍스트에서 정보 추출
    lines = full_text.split('\n')
    
    # 주문 ID 추출 - 다양한 패턴 시도
    order_patterns = [
        r'ORDER CONFIRMATION ID:?\s*(\d+)',
        r'PO#:?\s*(\d+)',
        r'C\d+',  # C00994 같은 형식도 주문 ID로 인식
    ]
    
    for pattern in order_patterns:
        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                metadata['order_id'] = match.group(0)
                break
        if metadata['order_id']:
            break
    
    # 이미지에서 OCR로 더 정확한 정보 추출
    _, buffer = cv2.imencode('.jpg', image)
    byte_img = buffer.tobytes()
    vision_image = vision.Image(content=byte_img)
    
    try:
        response = vision_client.text_detection(image=vision_image)
        text_annotations = response.text_annotations[1:]  # 첫 번째는 전체 텍스트
        ocr_text = response.text_annotations[0].description if response.text_annotations else ""
        
        # 브랜드, 시즌 정보 추출을 위한 패턴
        brand_pattern = re.compile(r'TOGA VIRILIS', re.IGNORECASE)
        season_pattern = re.compile(r'(20\d{2})(SS|FW|SP|SU)', re.IGNORECASE)
        
        # 선적 기간 관련 특수 패턴 (Order Information 섹션)
        create_pattern = re.compile(r'Created:?\s*(\d{1,2}/\d{1,2}/\d{4})', re.IGNORECASE)
        start_ship_pattern = re.compile(r'Start Ship:?\s*(\d{1,2}/\d{1,2}/\d{4})', re.IGNORECASE)
        complete_ship_pattern = re.compile(r'Complete Ship:?\s*(\d{1,2}/\d{1,2}/\d{4})', re.IGNORECASE)
        
        # Order Information 섹션 찾기
        order_info_section = ""
        for i, line in enumerate(lines):
            if "Order Information" in line:
                # 이후 5개 라인 정도를 Order Information 섹션으로 간주
                order_info_section = "\n".join(lines[i:i+6])
                break
        
        # Order Information 섹션에서 날짜 찾기 (주문 생성일, 선적 시작일, 선적 완료일)
        if order_info_section:
            # Created 날짜 (주문 생성일)
            create_match = create_pattern.search(order_info_section)
            if create_match:
                metadata['created_date'] = create_match.group(1)
            
            # Start Ship 날짜
            start_match = start_ship_pattern.search(order_info_section)
            if start_match:
                metadata['start_ship'] = start_match.group(1)
            
            # Complete Ship 날짜
            complete_match = complete_ship_pattern.search(order_info_section)
            if complete_match:
                metadata['complete_ship'] = complete_match.group(1)
        
        # 각 텍스트 블록 분석
        for text in text_annotations:
            text_content = text.description
            
            # 브랜드 추출
            brand_match = brand_pattern.search(text_content)
            if brand_match and not metadata['brand']:
                metadata['brand'] = 'TOGA VIRILIS'
            
            # 시즌 추출
            season_match = season_pattern.search(text_content)
            if season_match and not metadata['season']:
                metadata['season'] = season_match.group(0)
            
            # 선적 시작일 추출 (아직 없는 경우)
            if not metadata['start_ship']:
                start_match = start_ship_pattern.search(text_content)
                if start_match:
                    metadata['start_ship'] = start_match.group(1)
            
            # 선적 완료일 추출 (아직 없는 경우)
            if not metadata['complete_ship']:
                complete_match = complete_ship_pattern.search(text_content)
                if complete_match:
                    metadata['complete_ship'] = complete_match.group(1)
        
        # 추가 정보를 전체 텍스트에서 재검색
        if not metadata['brand']:
            for line in lines:
                if 'TOGA VIRILIS' in line:
                    metadata['brand'] = 'TOGA VIRILIS'
                    break
        
        if not metadata['season']:
            for line in lines:
                season_match = season_pattern.search(line)
                if season_match:
                    metadata['season'] = season_match.group(0)
                    break
    
    except Exception as e:
        print(f"[ERROR] 메타데이터 추출 중 오류 발생: {str(e)}")
    
    # 여전히 날짜 정보가 없는 경우 전체 문서에서 찾기
    if not metadata['start_ship'] or not metadata['complete_ship']:
        # 날짜 관련 키워드와 함께 있는 날짜 찾기
        for i, line in enumerate(lines):
            if 'start' in line.lower() and not metadata['start_ship']:
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if date_match:
                    metadata['start_ship'] = date_match.group(1)
            
            if ('complete' in line.lower() or 'end' in line.lower()) and not metadata['complete_ship']:
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if date_match:
                    metadata['complete_ship'] = date_match.group(1)
    
    return metadata

def extract_price_info(image, full_text, model_codes):
    """
    문서에서 각 모델의 구매가와 판매가 정보를 추출합니다.
    """
    price_info = {}
    
    # 모델 코드 패턴 준비
    model_patterns = {code: re.compile(rf'{re.escape(code)}\s+.*', re.IGNORECASE) for code in model_codes}
    
    # 가격 패턴
    wholesale_pattern = re.compile(r'Wholesale:\s*EUR\s+(\d+\.*\d*)', re.IGNORECASE)
    retail_pattern = re.compile(r'Sugg\.\s*Retail:\s*EUR\s+(\d+\.*\d*)', re.IGNORECASE)
    
    # 각 모델 초기화
    for model_code in model_codes:
        price_info[model_code] = {
            'wholesale_price': '',
            'retail_price': ''
        }
    
    # 전체 텍스트에서 각 모델별 정보 추출
    lines = full_text.split('\n')
    
    # 이미지 전체에서 한 번에 모든 가격 정보 추출
    # "AJ모델번호 - ... Wholesale: EUR XXX.XX Sugg. Retail: EUR XXX.XX" 패턴 찾기
    all_price_pattern = re.compile(r'(AJ\d+).*?Wholesale:\s*EUR\s+(\d+\.*\d*).*?Retail:\s*EUR\s+(\d+\.*\d*)', re.DOTALL)
    all_matches = all_price_pattern.findall(full_text)
    
    for model, wholesale, retail in all_matches:
        model_code = model.strip()
        if model_code in price_info:
            price_info[model_code]['wholesale_price'] = f"EUR {wholesale}"
            price_info[model_code]['retail_price'] = f"EUR {retail}"
    
    # 개별 라인 검색 방식도 유지
    for model_code in model_codes:
        if not price_info[model_code]['wholesale_price'] or not price_info[model_code]['retail_price']:
            # 각 모델 코드가 포함된 라인 찾기
            for i, line in enumerate(lines):
                if model_code in line:
                    # 현재 라인과 이후 몇 개 라인에서 가격 정보 찾기
                    search_range = 10  # 검색 범위 확장
                    for j in range(i, min(i + search_range, len(lines))):
                        # 구매가 찾기
                        if not price_info[model_code]['wholesale_price']:
                            wholesale_match = wholesale_pattern.search(lines[j])
                            if wholesale_match:
                                price_info[model_code]['wholesale_price'] = f"EUR {wholesale_match.group(1)}"
                        
                        # 판매가 찾기
                        if not price_info[model_code]['retail_price']:
                            retail_match = retail_pattern.search(lines[j])
                            if retail_match:
                                price_info[model_code]['retail_price'] = f"EUR {retail_match.group(1)}"
                    
                    # 주변 라인에서 가격 정보를 찾았으면 검색 중단
                    if price_info[model_code]['wholesale_price'] and price_info[model_code]['retail_price']:
                        break
    
    # 이미지 OCR을 통한 추가 검색 (필요한 경우)
    missing_prices = any(not (info['wholesale_price'] and info['retail_price']) for info in price_info.values())
    
    if missing_prices:
        _, buffer = cv2.imencode('.jpg', image)
        byte_img = buffer.tobytes()
        vision_image = vision.Image(content=byte_img)
        
        try:
            response = vision_client.text_detection(image=vision_image)
            ocr_text = response.text_annotations[0].description if response.text_annotations else ""
            ocr_lines = ocr_text.split('\n')
            
            # EUR 뒤에 숫자가 오는 패턴 찾기
            eur_pattern = re.compile(r'EUR\s+(\d+\.*\d*)')
            
            for model_code in model_codes:
                if not price_info[model_code]['wholesale_price'] or not price_info[model_code]['retail_price']:
                    # 모델 코드 주변 텍스트 찾기
                    for i, line in enumerate(ocr_lines):
                        if model_code in line:
                            # 주변 20라인 검색 (범위 확장)
                            search_start = max(0, i - 5)
                            search_end = min(i + 15, len(ocr_lines))
                            
                            # 모델 근처의 모든 EUR 값 수집
                            eur_values = []
                            for j in range(search_start, search_end):
                                eur_matches = eur_pattern.findall(ocr_lines[j])
                                for match in eur_matches:
                                    eur_values.append(match)
                            
                            # EUR 값이 충분히 있으면 첫 번째는 구매가, 두 번째는 판매가로 가정
                            if len(eur_values) >= 2:
                                if not price_info[model_code]['wholesale_price']:
                                    price_info[model_code]['wholesale_price'] = f"EUR {eur_values[0]}"
                                if not price_info[model_code]['retail_price']:
                                    price_info[model_code]['retail_price'] = f"EUR {eur_values[1]}"
                            
                            break
            
            # 직접적인 패턴으로 찾지 못한 경우 다른 모델의 가격 참조
            # 같은 유형의 제품은 같은 가격일 가능성이 높음
            for model_code in model_codes:
                if not price_info[model_code]['wholesale_price'] or not price_info[model_code]['retail_price']:
                    # 다른 제품의 가격 정보 참조
                    for ref_model, ref_price in price_info.items():
                        if ref_model != model_code and ref_price['wholesale_price'] and ref_price['retail_price']:
                            if not price_info[model_code]['wholesale_price']:
                                price_info[model_code]['wholesale_price'] = ref_price['wholesale_price']
                            if not price_info[model_code]['retail_price']:
                                price_info[model_code]['retail_price'] = ref_price['retail_price']
                            break
        
        except Exception as e:
            print(f"[ERROR] 가격 정보 추출 중 OCR 오류 발생: {str(e)}")
    
    return price_info

def detect_product_sections(image):
    """문서에서 각 상품 섹션을 감지합니다."""
    # 이미지를 그레이스케일로 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    
    # 수평선 검출을 위한 커널
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    
    # 수평선 위치 찾기
    h_projections = np.sum(horizontal_lines, axis=1)
    
    # 각 수평선의 y 좌표
    horizontal_positions = []
    for i in range(len(h_projections)):
        if h_projections[i] > 100:  # 임계값 조정 필요
            horizontal_positions.append(i)
    
    # 인접한 선 병합
    def merge_adjacent(positions, threshold=10):
        if not positions:
            return []
        
        merged = [positions[0]]
        for i in range(1, len(positions)):
            if positions[i] - merged[-1] <= threshold:
                continue
            merged.append(positions[i])
        
        return merged
    
    horizontal_positions = merge_adjacent(horizontal_positions)
    
    # 상품 모델이 있는 행을 찾기 위한 OCR 수행
    _, buffer = cv2.imencode('.jpg', image)
    byte_img = buffer.tobytes()
    vision_image = vision.Image(content=byte_img)
    
    try:
        response = vision_client.text_detection(image=vision_image)
        
        # 모델 패턴 (예: AJ1323, AJ830 등)을 찾아 해당 행의 위치 파악
        model_pattern = re.compile(r'AJ\d+')
        model_rows = []
        
        for text in response.text_annotations[1:]:  # 첫 번째는 전체 텍스트
            if model_pattern.match(text.description):
                # 텍스트의 중간 y 좌표
                vertices = text.bounding_poly.vertices
                y_coord = sum(vertex.y for vertex in vertices) / 4
                model_rows.append((text.description, int(y_coord)))
        
        # 각 모델 행에 해당하는 테이블 섹션 찾기
        product_sections = []
        
        for model, y_pos in model_rows:
            # 해당 모델 행 아래의 첫 번째 수평선 찾기
            table_start = None
            for pos in horizontal_positions:
                if pos > y_pos:
                    table_start = pos
                    break
            
            if table_start:
                # 테이블 시작점부터 다음 3개의 수평선 찾기
                section_lines = []
                line_idx = horizontal_positions.index(table_start)
                
                if line_idx + 3 < len(horizontal_positions):
                    section_lines = horizontal_positions[line_idx:line_idx+4]
                    
                    if len(section_lines) >= 3:
                        product_sections.append({
                            'model': model,
                            'y_pos': y_pos,
                            'lines': section_lines
                        })
        
        return product_sections
    
    except Exception as e:
        print(f"[ERROR] OCR 수행 중 오류: {str(e)}")
        return []

def find_column_separators_improved(table_image, header_y_start, header_y_end):
    """개선된 방식으로 헤더 영역에서 열 구분선 위치를 찾습니다."""
    # 헤더 영역 추출
    header_image = table_image[header_y_start:header_y_end, :]
    
    # OCR 수행
    _, buffer = cv2.imencode('.jpg', header_image)
    byte_img = buffer.tobytes()
    vision_image = vision.Image(content=byte_img)
    
    try:
        response = vision_client.text_detection(image=vision_image)
        
        # 각 텍스트의 경계 상자 정보 수집
        text_boxes = []
        
        for text in response.text_annotations[1:]:  # 첫 번째는 전체 텍스트
            vertices = text.bounding_poly.vertices
            min_x = min(vertex.x for vertex in vertices)
            max_x = max(vertex.x for vertex in vertices)
            min_y = min(vertex.y for vertex in vertices)
            
            # 사이즈 번호(39, 40, 41 등), Colors, Total, Qty 포함
            if re.match(r'^[0-9]{2}$', text.description) or text.description.upper() in ['COLORS', 'TOTAL', 'QTY']:
                text_boxes.append({
                    'text': text.description,
                    'left': min_x,
                    'right': max_x,
                    'top': min_y
                })
        
        # x 좌표로 정렬
        text_boxes.sort(key=lambda box: box['left'])
        
        # 컬러 열을 추가하기 위해 첫 번째 열 앞에 가상의 구분점 추가
        separators = []
        
        # 첫 번째 열(Colors) 앞에 구분선 추가 (이미지 왼쪽 가장자리)
        separators.append({
            'position': 0,
            'left_text': '',
            'right_text': 'Start'
        })
        
        # 항상 "Colors" 열과 첫 번째 사이즈 사이에 구분선 추가
        colors_pos = None
        first_size_pos = None
        
        for box in text_boxes:
            if box['text'].upper() == 'COLORS':
                colors_pos = box['right']
            elif re.match(r'^[0-9]{2}$', box['text']) and first_size_pos is None:
                first_size_pos = box['left']
        
        if colors_pos and first_size_pos:
            separators.append({
                'position': colors_pos + int((first_size_pos - colors_pos) * 0.6),
                'left_text': 'Colors',
                'right_text': 'First Size'
            })
        
        # 나머지 텍스트 간 간격 분석
        for i in range(len(text_boxes) - 1):
            current_right = text_boxes[i]['right']
            next_left = text_boxes[i+1]['left']
            gap_width = next_left - current_right
            
            # 간격이 일정 이상인 경우 구분선 배치
            if gap_width > 5:  # 임계값 설정
                separator_pos = current_right + int(gap_width * 0.6)
                separators.append({
                    'position': separator_pos,
                    'left_text': text_boxes[i]['text'],
                    'right_text': text_boxes[i+1]['text']
                })
        
        # 마지막 텍스트와 Qty 사이에 구분선 추가
        last_size_pos = None
        qty_pos = None
        
        for box in text_boxes:
            if re.match(r'^[0-9]{2}$', box['text']):
                last_size_pos = box['right']
            elif box['text'].upper() == 'QTY':
                qty_pos = box['left']
        
        if last_size_pos and qty_pos:
            separators.append({
                'position': last_size_pos + int((qty_pos - last_size_pos) * 0.6),
                'left_text': 'Last Size',
                'right_text': 'Qty'
            })
        
        # 마지막 텍스트 뒤 (이미지 오른쪽 가장자리)
        separators.append({
            'position': header_image.shape[1] - 1,
            'left_text': 'End',
            'right_text': ''
        })
        
        # 위치 기준으로 정렬
        separators.sort(key=lambda sep: sep['position'])
        
        return separators
    
    except Exception as e:
        print(f"[ERROR] 열 구분선 찾기 오류: {str(e)}")
        return []

def extract_cell_data_improved(table_image, row_start, row_end, separators):
    """특정 행에서 각 셀의 데이터를 추출합니다."""
    # 행 영역 추출
    row_image = table_image[row_start:row_end, :]
    
    # 결과를 저장할 리스트
    cell_data = []
    
    # 각 셀 추출 및 OCR 수행
    for i in range(len(separators) - 1):
        left = separators[i]['position']
        right = separators[i+1]['position']
        
        # 셀 이미지 추출
        cell_img = row_image[:, left:right]
        
        # 이미지가 비어있는지 확인
        if cell_img.size == 0:
            cell_data.append("0")  # 빈 셀은 "0"으로 저장
            continue
        
        # OCR 수행
        _, buffer = cv2.imencode('.jpg', cell_img)
        byte_img = buffer.tobytes()
        vision_image = vision.Image(content=byte_img)
        
        try:
            response = vision_client.text_detection(image=vision_image)
            
            # 텍스트 추출
            if response.text_annotations:
                cell_text = response.text_annotations[0].description.strip()
                
                # 값이 비어있거나 공백인 경우 "0"으로 처리
                if not cell_text or cell_text.isspace():
                    cell_data.append("0")
                else:
                    # 금액 정보인 경우 쉼표와 공백 정리
                    if "EUR" in cell_text:
                        # "EUR 1,540.00"와 같은 형식으로 표준화
                        cell_text = re.sub(r'EUR\s+(\d+)[,\s]+(\d+)[,\s]+(\d+)', r'EUR \1\2\3', cell_text)
                        cell_text = re.sub(r'EUR\s+(\d+)[,\s]+(\d+)', r'EUR \1\2', cell_text)
                        
                        # 소수점 처리를 위한 정규화
                        cell_text = normalize_price(cell_text)
                    
                    cell_data.append(cell_text)
            else:
                cell_data.append("0")  # 텍스트 감지 못한 경우 "0"으로 저장
        
        except Exception as e:
            print(f"[ERROR] 셀 OCR 오류: {str(e)}")
            cell_data.append("0")  # 오류 발생 시 "0"으로 저장
    
    return cell_data

def process_table_section_improved(image, section):
    """각 상품 테이블 섹션을 처리하고 데이터를 추출합니다."""
    # 테이블 라인 정보
    lines = section['lines']
    
    if len(lines) < 3:
        print(f"[WARNING] {section['model']} 섹션에 충분한 라인이 없습니다.")
        return None
    
    # 헤더 영역 (첫 번째 - 두 번째 선)
    header_start = lines[0]
    header_end = lines[1]
    
    # 데이터 영역 (두 번째 - 세 번째 선)
    data_start = lines[1]
    data_end = lines[2]
    
    # 개선된 방식으로 열 구분선 찾기
    separators = find_column_separators_improved(image, header_start, header_end)
    
    if not separators:
        print(f"[WARNING] {section['model']} 섹션에서 열 구분선을 찾을 수 없습니다.")
        return None
    
    # 디버그 이미지 생성
    debug_image = image.copy()
    
    # 수평선 표시
    for y in lines:
        cv2.line(debug_image, (0, y), (image.shape[1], y), (0, 0, 255), 2)
    
    # 수직선 표시
    for sep in separators:
        x = sep['position']
        cv2.line(debug_image, (x, lines[0]), (x, lines[-1]), (0, 255, 0), 2)
        
        # 디버그용 텍스트 추가
        if 'left_text' in sep and 'right_text' in sep:
            cv2.putText(debug_image, f"{sep['left_text']}-{sep['right_text']}", 
                       (x - 30, lines[0] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    
    # 헤더 데이터 추출
    header_data = extract_cell_data_improved(image, header_start, header_end, separators)
    
    # 데이터 행 추출
    row_data = extract_cell_data_improved(image, data_start, data_end, separators)
    
    # 디버그 이미지 저장
    cv2.imwrite(f"debug_{section['model']}.jpg", debug_image)
    
    # 데이터 정리 및 반환
    return {
        'model': section['model'],
        'headers': header_data,
        'data': row_data,
        'debug_image': debug_image
    }

def clean_extracted_data(product_data, metadata, price_info):
    """추출된 데이터를 정리하고 구조화합니다."""
    if not product_data:
        return None
    
    structured_data = []
    
    for product in product_data:
        if not product:
            continue
        
        model = product['model']
        headers = product['headers']
        data = product['data']
        
        # 필요 정보 구조화
        item = {
            '모델': model,
            '컬러': data[0] if data and len(data) > 0 else '',
            '총_수량': '0',
            '총_금액': '0',
            '브랜드': metadata.get('brand', ''),
            '시즌': metadata.get('season', ''),
            '선적_시작일': metadata.get('start_ship', ''),
            '선적_완료일': metadata.get('complete_ship', ''),
            '주문_ID': metadata.get('order_id', '')
        }
        
        # 가격 정보 추가
        if model in price_info:
            item['구매가'] = price_info[model]['wholesale_price']
            item['판매가'] = price_info[model]['retail_price']
        else:
            item['구매가'] = ''
            item['판매가'] = ''
        
        # 헤더에서 사이즈 찾기
        sizes = []
        for i, header in enumerate(headers):
            if re.match(r'^[0-9]{2}$', header):  # 숫자 두 자리(사이즈)
                sizes.append((i, header))
        
        # 사이즈별 수량 매핑
        total_quantity = 0
        for idx, size in sizes:
            if idx < len(data):
                quantity = data[idx].strip()
                # 수량이 비어있으면 0으로 설정
                if not quantity or quantity == '':
                    quantity = '0'
                item[f'사이즈_{size}'] = quantity
                # 총 수량 누적 계산
                try:
                    total_quantity += int(quantity)
                except ValueError:
                    pass
        
        # 총 수량과 총 금액 찾기
        for i, header in enumerate(headers):
            if header.upper() == 'QTY' and i < len(data):
                item['총_수량'] = data[i].strip()
            elif header.upper() == 'TOTAL' and i < len(data):
                # 마지막 열 또는 그 다음 열에서 금액 찾기
                amount_index = i
                if amount_index < len(data):
                    amount = data[amount_index]
                    # "EUR 1,540.00" 패턴 찾기
                    match = re.search(r'EUR\s+[\d,\s\.]+', amount)
                    if match:
                        # 정규화된 가격 적용 (단가와 수량 정보로 검증)
                        unit_price = item['구매가']
                        item['총_금액'] = normalize_price(match.group(0), 
                                                      item_quantity=item['총_수량'], 
                                                      unit_price=unit_price)
                    else:
                        # 다음 셀에서 찾아보기
                        if amount_index + 1 < len(data):
                            amount = data[amount_index + 1]
                            match = re.search(r'EUR\s+[\d,\s\.]+', amount)
                            if match:
                                item['총_금액'] = normalize_price(match.group(0),
                                                              item_quantity=item['총_수량'],
                                                              unit_price=unit_price)
        
        # 실제 총 수량과 합계가 일치하는지 검증
        if item['총_수량'] == '0' and total_quantity > 0:
            item['총_수량'] = str(total_quantity)
            print(f"[INFO] {model}: 총 수량이 없어서 계산된 값({total_quantity})으로 대체")
        
        structured_data.append(item)
    
    return structured_data

def save_extended_data(structured_data, output_excel="extended_data.xlsx", output_text="extended_data.txt"):
    """확장된 데이터를 엑셀 파일과 텍스트 파일로 저장합니다."""
    if not structured_data:
        print("[ERROR] 저장할 데이터가 없습니다.")
        return False
    
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
    
    # 기본 열 순서 정의 (추가 메타데이터 포함)
    columns = ['주문_ID', '브랜드', '시즌', '선적_시작일', '선적_완료일', 
               '모델', '컬러', '구매가', '판매가'] + sorted_sizes + ['총_수량', '총_금액']
    
    # 엑셀 파일로 저장
    df = pd.DataFrame(structured_data)
    
    # 누락된 열 처리 (추가 메타데이터가 없는 경우를 대비)
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    
    # 열 순서 조정
    df = df[columns]
    df.to_excel(output_excel, index=False)
    print(f"[✅] 데이터가 엑셀 파일에 저장되었습니다: {output_excel}")
    
    # 텍스트 파일로 저장
    with open(output_text, 'w', encoding='utf-8') as f:
        for item in structured_data:
            f.write(f"주문 ID: {item.get('주문_ID', '')}\n")
            f.write(f"브랜드: {item.get('브랜드', '')}\n")
            f.write(f"시즌: {item.get('시즌', '')}\n")
            f.write(f"선적 기간: {item.get('선적_시작일', '')} ~ {item.get('선적_완료일', '')}\n")
            f.write(f"모델: {item['모델']}\n")
            f.write(f"컬러: {item['컬러']}\n")
            f.write(f"구매가: {item.get('구매가', '')}\n")
            f.write(f"판매가: {item.get('판매가', '')}\n")
            
            f.write("사이즈별 수량:\n")
            for size in sorted_sizes:
                size_num = size.split('_')[1]
                f.write(f"  {size_num}: {item[size]}\n")
            
            f.write(f"총 수량: {item['총_수량']}\n")
            f.write(f"총 금액: {item['총_금액']}\n")
            f.write('-' * 50 + '\n')
    
    print(f"[✅] 데이터가 텍스트 파일에 저장되었습니다: {output_text}")
    
    return True

def process_order_document_extended(pdf_path, output_folder="results"):
    """확장된 주문 문서 PDF 처리 메인 함수 - 메타데이터와 가격 정보 포함"""
    # 출력 폴더 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # PDF를 이미지로 변환
    image_paths = pdf_to_image(pdf_path)
    
    if not image_paths:
        print("[ERROR] PDF 변환 실패")
        return None
    
    # 첫 번째 페이지만 처리
    image_path = image_paths[0]
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"[ERROR] 이미지를 로드할 수 없습니다: {image_path}")
        return None
    
    # 전체 텍스트 추출 및 저장
    full_text = extract_text_with_reading_order(image_path)
    with open(f"{output_folder}/full_text.txt", 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"[✅] 전체 텍스트가 저장되었습니다: {output_folder}/full_text.txt")
    
    # 상품 섹션 감지
    product_sections = detect_product_sections(image)
    
    if not product_sections:
        print("[ERROR] 상품 섹션을 찾을 수 없습니다")
        return None
    
    # 모델 코드 목록 추출
    model_codes = [section['model'] for section in product_sections]
    
    # 메타데이터 추출
    print("[INFO] 메타데이터 추출 중...")
    metadata = extract_metadata_info(image, full_text)
    print(f"[INFO] 추출된 메타데이터: 브랜드={metadata['brand']}, 시즌={metadata['season']}, "
          f"선적 기간={metadata['start_ship']}~{metadata['complete_ship']}, 주문 ID={metadata['order_id']}")
    
    # 가격 정보 추출
    print("[INFO] 가격 정보 추출 중...")
    price_info = extract_price_info(image, full_text, model_codes)
    for model, prices in price_info.items():
        print(f"[INFO] 모델 {model} 가격: 구매가={prices['wholesale_price']}, 판매가={prices['retail_price']}")
    
    # 각 섹션 처리
    product_data = []
    
    for section in product_sections:
        print(f"[INFO] 처리 중인 모델: {section['model']}")
        section_data = process_table_section_improved(image, section)
        
        if section_data:
            product_data.append(section_data)
            
            # 디버그 이미지 저장
            cv2.imwrite(f"{output_folder}/debug_{section['model']}.jpg", section_data['debug_image'])
    
    # 데이터 정리 및 저장
    if product_data:
        structured_data = clean_extracted_data(product_data, metadata, price_info)
        save_extended_data(
            structured_data, 
            output_excel=f"{output_folder}/extended_data.xlsx",
            output_text=f"{output_folder}/extended_data.txt"
        )
    
    return product_data, metadata, price_info

def extract_product_info(image, full_text):
    """
    문서에서 모델 정보(전체 모델명, 스타일 코드 등)를 추출합니다.
    여러 형식의 모델명 패턴을 처리합니다.
    """
    # 결과를 저장할 딕셔너리
    product_info = {}
    
    # 전체 텍스트에서 정보 추출
    lines = full_text.split('\n')
    
    # 모델 코드 패턴 (AJ로 시작하는 코드)
    model_code_pattern = re.compile(r'(AJ\d+)')
    
    # 스타일 코드 패턴 (예: "Style #FTVRM132309009")
    style_pattern = re.compile(r'Style\s*#\s*([A-Z0-9]+)')
    
    # 1. 첫 번째 단계: 기본 모델 코드 추출
    for line in lines:
        model_match = model_code_pattern.search(line)
        if model_match:
            model_code = model_match.group(1).strip()
            if model_code not in product_info:
                product_info[model_code] = {
                    'model_code': model_code,
                    'model_description': '',
                    'full_model': model_code,
                    'style_code': ''
                }
    
    # 2. 두 번째 단계: 모델 설명 찾기 (여러 패턴 시도)
    # 패턴 1: "AJ1323 - BLACK LEATHER" (한 줄에 같이 있는 경우)
    pattern1 = re.compile(r'(AJ\d+)\s*-\s*([A-Z\s]+)')
    
    # 패턴 2: "AJ1323" 다음 줄에 "BLACK LEATHER"가 있는 경우
    for i, line in enumerate(lines):
        model_match = model_code_pattern.search(line)
        if model_match:
            model_code = model_match.group(1).strip()
            
            # 패턴 1: 같은 줄에 있는 경우
            pattern1_match = pattern1.search(line)
            if pattern1_match and model_code in product_info:
                model_desc = pattern1_match.group(2).strip()
                product_info[model_code]['model_description'] = model_desc
                product_info[model_code]['full_model'] = f"{model_code}-{model_desc}"
                continue
            
            # 패턴 2: 다음 줄에 "BLACK LEATHER"가 있는 경우
            if i+1 < len(lines) and "BLACK" in lines[i+1] and model_code in product_info:
                next_line = lines[i+1].strip()
                # BLACK LEATHER와 같은 패턴인지 확인
                if re.match(r'^[A-Z\s]+$', next_line) and "BLACK" in next_line:
                    product_info[model_code]['model_description'] = next_line
                    product_info[model_code]['full_model'] = f"{model_code}-{next_line}"
    
    # 3. 세 번째 단계: 스타일 코드 찾기
    # 패턴: "Style #FTVRM132309009 | TOGA VIRILIS - 2024SSMAN"
    style_toga_pattern = re.compile(r'Style\s*#\s*([A-Z0-9]+)\s*\|\s*TOGA VIRILIS\s*-\s*(20\d{2}[A-Z]+)')
    
    for i, line in enumerate(lines):
        style_toga_match = style_toga_pattern.search(line)
        if style_toga_match:
            style_code = style_toga_match.group(1).strip()
            season_code = style_toga_match.group(2).strip()
            
            # 이 스타일 코드와 관련된 모델 코드 찾기
            # 주변 5줄 내에서 모델 코드 검색
            search_range = 5
            for j in range(max(0, i-search_range), min(i+search_range+1, len(lines))):
                for model_code in product_info:
                    if model_code in lines[j]:
                        product_info[model_code]['style_code'] = style_code
                        product_info[model_code]['season_code'] = season_code
                        break
    
    # 4. 네 번째 단계: 아직 모델 설명이 없는 경우, 추가 패턴 시도
    for model_code, info in product_info.items():
        if not info['model_description']:
            # 전체 텍스트에서 해당 모델 근처의 "BLACK LEATHER"와 같은 패턴 찾기
            pattern = re.compile(rf'{re.escape(model_code)}.*?(BLACK\s+[A-Z]+)', re.DOTALL)
            match = pattern.search(full_text)
            if match:
                model_desc = match.group(1).strip()
                info['model_description'] = model_desc
                info['full_model'] = f"{model_code}-{model_desc}"
    
    # 5. 다섯 번째 단계: OCR 결과에서 추가 검색 (필요한 경우)
    # 정보가 누락된 모델이 있는지 확인
    missing_info = any(not info['model_description'] or not info['style_code'] for info in product_info.values())
    
    if missing_info:
        _, buffer = cv2.imencode('.jpg', image)
        byte_img = buffer.tobytes()
        vision_image = vision.Image(content=byte_img)
        
        try:
            response = vision_client.text_detection(image=vision_image)
            ocr_text = response.text_annotations[0].description if response.text_annotations else ""
            
            # OCR 텍스트에서 모델 코드, 설명, 스타일 코드 패턴 찾기
            for model_code, info in product_info.items():
                # 모델 설명이 없는 경우
                if not info['model_description']:
                    pattern = re.compile(rf'{re.escape(model_code)}.*?(BLACK\s+[A-Z]+)', re.DOTALL)
                    match = pattern.search(ocr_text)
                    if match:
                        model_desc = match.group(1).strip()
                        info['model_description'] = model_desc
                        info['full_model'] = f"{model_code}-{model_desc}"
                
                # 스타일 코드가 없는 경우
                if not info['style_code']:
                    # 모델 코드가 있는 위치 주변에서 스타일 코드 패턴 찾기
                    model_index = ocr_text.find(model_code)
                    if model_index >= 0:
                        # 모델 코드 주변 300자 정도 검색
                        search_text = ocr_text[max(0, model_index-150):min(len(ocr_text), model_index+150)]
                        style_match = re.search(r'Style\s*#\s*([A-Z0-9]+)', search_text)
                        if style_match:
                            info['style_code'] = style_match.group(1).strip()
        
        except Exception as e:
            print(f"[ERROR] OCR 기반 제품 정보 추출 중 오류: {str(e)}")
    
    # 6. 마지막 단계: 데이터 후처리
    # 줄바꿈 제거, 여러 공백 제거 등
    for info in product_info.values():
        if info['model_description']:
            # 줄바꿈 및 여러 공백 제거
            info['model_description'] = re.sub(r'\s+', ' ', info['model_description']).strip()
            # 전체 모델명 업데이트
            info['full_model'] = f"{info['model_code']}-{info['model_description']}"
    
    return product_info

def detect_product_sections_improved(image, full_text):
    """개선된 상품 섹션 감지 함수 - 모델명과 스타일 코드 포함"""
    # 기존 함수와 동일한 방식으로 상품 섹션 감지
    product_sections = detect_product_sections(image)
    
    # 모델 정보와 스타일 코드 추출
    product_info = extract_product_info(image, full_text)
    
    # 상품 섹션에 모델 정보 추가
    for section in product_sections:
        model_code = section['model']
        if model_code in product_info:
            section['full_model'] = product_info[model_code]['full_model']
            section['model_description'] = product_info[model_code]['model_description']
            section['style_code'] = product_info[model_code]['style_code']
    
    return product_sections

def clean_extracted_data_with_style(product_data, metadata, price_info):
    """추출된 데이터를 정리하고 구조화합니다. 스타일 코드와 전체 모델명 포함"""
    if not product_data:
        return None
    
    structured_data = []
    
    for product in product_data:
        if not product:
            continue
        
        model_code = product['model']  # AJ1323
        full_model = product.get('full_model', model_code)  # AJ1323-BLACK LEATHER
        model_description = product.get('model_description', '')  # BLACK LEATHER
        style_code = product.get('style_code', '')  # FTVRM132309009
        
        headers = product['headers']
        data = product['data']
        
        # 필요 정보 구조화
        item = {
            '모델코드': model_code,
            '모델명': full_model,
            '모델설명': model_description,
            '스타일코드': style_code,
            '컬러': data[0] if data and len(data) > 0 else '',
            '총_수량': '0',
            '총_금액': '0',
            '브랜드': metadata.get('brand', ''),
            '시즌': metadata.get('season', ''),
            '선적_시작일': metadata.get('start_ship', ''),
            '선적_완료일': metadata.get('complete_ship', ''),
            '주문_ID': metadata.get('order_id', '')
        }
        
        # 가격 정보 추가
        if model_code in price_info:
            item['구매가'] = price_info[model_code]['wholesale_price']
            item['판매가'] = price_info[model_code]['retail_price']
        else:
            item['구매가'] = ''
            item['판매가'] = ''
        
        # 헤더에서 사이즈 찾기
        sizes = []
        for i, header in enumerate(headers):
            if re.match(r'^[0-9]{2}$', header):  # 숫자 두 자리(사이즈)
                sizes.append((i, header))
        
        # 사이즈별 수량 매핑
        total_quantity = 0
        for idx, size in sizes:
            if idx < len(data):
                quantity = data[idx].strip()
                # 수량이 비어있으면 0으로 설정
                if not quantity or quantity == '':
                    quantity = '0'
                item[f'사이즈_{size}'] = quantity
                # 총 수량 누적 계산
                try:
                    total_quantity += int(quantity)
                except ValueError:
                    pass
        
        # 총 수량과 총 금액 찾기
        for i, header in enumerate(headers):
            if header.upper() == 'QTY' and i < len(data):
                item['총_수량'] = data[i].strip()
            elif header.upper() == 'TOTAL' and i < len(data):
                # 마지막 열 또는 그 다음 열에서 금액 찾기
                amount_index = i
                if amount_index < len(data):
                    amount = data[amount_index]
                    # "EUR 1,540.00" 패턴 찾기
                    match = re.search(r'EUR\s+[\d,\s\.]+', amount)
                    if match:
                        # 정규화된 가격 적용 (단가와 수량 정보로 검증)
                        unit_price = item['구매가']
                        item['총_금액'] = normalize_price(match.group(0), 
                                                      item_quantity=item['총_수량'], 
                                                      unit_price=unit_price)
                    else:
                        # 다음 셀에서 찾아보기
                        if amount_index + 1 < len(data):
                            amount = data[amount_index + 1]
                            match = re.search(r'EUR\s+[\d,\s\.]+', amount)
                            if match:
                                item['총_금액'] = normalize_price(match.group(0),
                                                              item_quantity=item['총_수량'],
                                                              unit_price=unit_price)
        
        # 실제 총 수량과 합계가 일치하는지 검증
        if item['총_수량'] == '0' and total_quantity > 0:
            item['총_수량'] = str(total_quantity)
            print(f"[INFO] {model_code}: 총 수량이 없어서 계산된 값({total_quantity})으로 대체")
        
        structured_data.append(item)
    
    return structured_data

def save_extended_data_with_style(structured_data, output_excel="extended_data.xlsx", output_text="extended_data.txt"):
    """확장된 데이터를 엑셀 파일과 텍스트 파일로 저장합니다. 스타일 코드와 모델 정보 포함"""
    if not structured_data:
        print("[ERROR] 저장할 데이터가 없습니다.")
        return False
    
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
    
    # 기본 열 순서 정의 (추가 메타데이터 포함)
    columns = ['주문_ID', '브랜드', '시즌', '선적_시작일', '선적_완료일', 
               '모델코드', '모델명', '모델설명', '스타일코드', '컬러', '구매가', '판매가'] + sorted_sizes + ['총_수량', '총_금액']
    
    # 엑셀 파일로 저장
    df = pd.DataFrame(structured_data)
    
    # 누락된 열 처리 (추가 메타데이터가 없는 경우를 대비)
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    
    # 열 순서 조정
    df = df[columns]
    df.to_excel(output_excel, index=False)
    print(f"[✅] 데이터가 엑셀 파일에 저장되었습니다: {output_excel}")
    
    # 텍스트 파일로 저장
    with open(output_text, 'w', encoding='utf-8') as f:
        for item in structured_data:
            f.write(f"주문 ID: {item.get('주문_ID', '')}\n")
            f.write(f"브랜드: {item.get('브랜드', '')}\n")
            f.write(f"시즌: {item.get('시즌', '')}\n")
            f.write(f"선적 기간: {item.get('선적_시작일', '')} ~ {item.get('선적_완료일', '')}\n")
            f.write(f"모델 코드: {item.get('모델코드', '')}\n")
            f.write(f"모델명: {item.get('모델명', '')}\n")
            f.write(f"모델 설명: {item.get('모델설명', '')}\n")
            f.write(f"스타일 코드: {item.get('스타일코드', '')}\n")
            f.write(f"컬러: {item['컬러']}\n")
            f.write(f"구매가: {item.get('구매가', '')}\n")
            f.write(f"판매가: {item.get('판매가', '')}\n")
            
            f.write("사이즈별 수량:\n")
            for size in sorted_sizes:
                size_num = size.split('_')[1]
                f.write(f"  {size_num}: {item[size]}\n")
            
            f.write(f"총 수량: {item['총_수량']}\n")
            f.write(f"총 금액: {item['총_금액']}\n")
            f.write('-' * 50 + '\n')
    
    print(f"[✅] 데이터가 텍스트 파일에 저장되었습니다: {output_text}")
    
    return True

def process_order_document_with_style(pdf_path, output_folder="results"):
    """모델명과 스타일 코드를 포함한 확장된 주문 문서 PDF 처리 메인 함수"""
    # 출력 폴더 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # PDF를 이미지로 변환
    image_paths = pdf_to_image(pdf_path)
    
    if not image_paths:
        print("[ERROR] PDF 변환 실패")
        return None
    
    # 첫 번째 페이지만 처리
    image_path = image_paths[0]
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"[ERROR] 이미지를 로드할 수 없습니다: {image_path}")
        return None
    
    # 전체 텍스트 추출 및 저장
    full_text = extract_text_with_reading_order(image_path)
    with open(f"{output_folder}/full_text.txt", 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"[✅] 전체 텍스트가 저장되었습니다: {output_folder}/full_text.txt")
    
    # 개선된 상품 섹션 감지 (모델명과 스타일 코드 포함)
    product_sections = detect_product_sections_improved(image, full_text)
    
    if not product_sections:
        print("[ERROR] 상품 섹션을 찾을 수 없습니다")
        return None
    
    # 모델 코드 목록 추출
    model_codes = [section['model'] for section in product_sections]
    
    # 메타데이터 추출
    print("[INFO] 메타데이터 추출 중...")
    metadata = extract_metadata_info(image, full_text)
    print(f"[INFO] 추출된 메타데이터: 브랜드={metadata['brand']}, 시즌={metadata['season']}, "
          f"선적 기간={metadata['start_ship']}~{metadata['complete_ship']}, 주문 ID={metadata['order_id']}")
    
    # 가격 정보 추출
    print("[INFO] 가격 정보 추출 중...")
    price_info = extract_price_info(image, full_text, model_codes)
    for model, prices in price_info.items():
        print(f"[INFO] 모델 {model} 가격: 구매가={prices['wholesale_price']}, 판매가={prices['retail_price']}")
    
    # 각 섹션 처리
    product_data = []
    
    for section in product_sections:
        print(f"[INFO] 처리 중인 모델: {section['model']}, 스타일 코드: {section.get('style_code', '없음')}")
        section_data = process_table_section_improved(image, section)
        
        if section_data:
            # 섹션 데이터에 모델 정보 추가
            section_data['full_model'] = section.get('full_model', section['model'])
            section_data['model_description'] = section.get('model_description', '')
            section_data['style_code'] = section.get('style_code', '')
            
            product_data.append(section_data)
            
            # 디버그 이미지 저장
            cv2.imwrite(f"{output_folder}/debug_{section['model']}.jpg", section_data['debug_image'])
    
    # 데이터 정리 및 저장
    if product_data:
        structured_data = clean_extracted_data_with_style(product_data, metadata, price_info)
        save_extended_data_with_style(
            structured_data, 
            output_excel=f"{output_folder}/extended_data_with_style.xlsx",
            output_text=f"{output_folder}/extended_data_with_style.txt"
        )
    
    return product_data, metadata, price_info

if __name__ == "__main__":
    pdf_path = "eql_in.pdf"  # 주문서 PDF 파일 경로
    result = process_order_document_with_style(pdf_path)
    
    if result:
        product_data, metadata, price_info = result
        print("\n[✅] 처리 완료! 데이터가 'results' 폴더에 저장되었습니다.")
        print(f"추출된 상품 수: {len(product_data)}개")
        
        # 각 상품의 전체 모델명과 스타일 코드 출력
        for product in product_data:
            print(f"모델 코드: {product['model']}")
            print(f"전체 모델명: {product.get('full_model', product['model'])}")
            print(f"모델 설명: {product.get('model_description', '')}")
            print(f"스타일 코드: {product.get('style_code', '없음')}")
            print("-" * 30)
    else:
        print("[ERROR] 처리 중 오류가 발생했습니다.")