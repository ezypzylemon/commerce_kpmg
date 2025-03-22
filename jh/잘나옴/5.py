import cv2
import numpy as np
import os
from pdf2image import convert_from_path
from google.cloud import vision
import pandas as pd
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# Google Cloud Vision API 키 설정
vision_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if vision_key_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = vision_key_path
else:
    print("[ERROR] GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 .env 파일에 설정되지 않았습니다.")
    print("         .env 파일에 GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/vision-key.json 형식으로 추가하세요.")
    exit(1)

# Vision 클라이언트 초기화
try:
    vision_client = vision.ImageAnnotatorClient()
    print("[INFO] Google Cloud Vision API 클라이언트가 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"[ERROR] Google Cloud Vision API 클라이언트 초기화 실패: {str(e)}")
    exit(1)

def pdf_to_image(pdf_path, output_folder="temp_images"):
    """PDF를 이미지로 변환합니다."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    images = convert_from_path(pdf_path, dpi=400, first_page=1, last_page=1)
    image_paths = []
    
    for i, image in enumerate(images):
        output_path = f"{output_folder}/page_{i+1}.jpg"
        image.save(output_path, 'JPEG')
        image_paths.append(output_path)
    
    return image_paths

def find_table_in_image(image_path):
    """이미지에서 테이블 영역을 찾습니다."""
    # 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] 이미지를 로드할 수 없습니다: {image_path}")
        return None, None
    
    # 그레이스케일 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    
    # 수평선, 수직선 감지를 위한 커널
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    
    # 수평선 감지
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    horizontal_lines = cv2.dilate(horizontal_lines, horizontal_kernel, iterations=1)
    
    # 수직선 감지
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
    vertical_lines = cv2.dilate(vertical_lines, vertical_kernel, iterations=1)
    
    # 선 결합
    table_lines = cv2.bitwise_or(horizontal_lines, vertical_lines)
    
    # 디버깅 이미지 저장
    cv2.imwrite("horizontal_lines.jpg", horizontal_lines)
    cv2.imwrite("vertical_lines.jpg", vertical_lines)
    cv2.imwrite("table_lines.jpg", table_lines)
    
    # 테이블 외곽선 검출
    contours, _ = cv2.findContours(table_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 면적 기준으로 정렬
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # 가장 큰 윤곽선이 테이블일 가능성이 높음
    if contours:
        table_contour = contours[0]
        x, y, w, h = cv2.boundingRect(table_contour)
        
        # 디버깅 이미지
        table_area = image.copy()
        cv2.rectangle(table_area, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imwrite("detected_table_area.jpg", table_area)
        
        # 테이블 영역 추출
        table_image = image[y:y+h, x:x+w]
        
        return table_image, (x, y, w, h)
    
    return None, None

def detect_table_structure(table_image, offset=(0, 0)):
    """테이블 구조(행과 열)를 감지합니다."""
    # 그레이스케일 변환
    gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    
    # 수평선, 수직선 감지를 위한 커널
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    
    # 수평선 감지
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    
    # 수직선 감지
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
    
    # 행과 열 좌표 추출
    h_projections = np.sum(horizontal_lines, axis=1)
    v_projections = np.sum(vertical_lines, axis=0)
    
    # 행 위치 찾기 (수평선 위치)
    row_positions = []
    for i in range(len(h_projections)):
        if h_projections[i] > 0:
            row_positions.append(i)
    
    # 열 위치 찾기 (수직선 위치)
    col_positions = []
    for i in range(len(v_projections)):
        if v_projections[i] > 0:
            col_positions.append(i)
    
    # 인접한 좌표 병합 (노이즈 제거)
    def merge_adjacent(positions, threshold=10):
        if not positions:
            return []
        
        merged = [positions[0]]
        for i in range(1, len(positions)):
            if positions[i] - merged[-1] <= threshold:
                continue
            merged.append(positions[i])
        
        return merged
    
    row_positions = merge_adjacent(row_positions)
    col_positions = merge_adjacent(col_positions)
    
    # 행과 열 좌표로 셀 생성
    cells = []
    for i in range(len(row_positions) - 1):
        row_cells = []
        for j in range(len(col_positions) - 1):
            x1 = col_positions[j]
            y1 = row_positions[i]
            x2 = col_positions[j+1]
            y2 = row_positions[i+1]
            
            # 전체 이미지 좌표계로 변환
            cell = (
                x1 + offset[0],  # x
                y1 + offset[1],  # y
                x2 - x1,         # width
                y2 - y1          # height
            )
            row_cells.append(cell)
        cells.append(row_cells)
    
    return cells

def extract_text_from_cell(image, cell):
    """셀 영역에서 텍스트를 추출합니다."""
    x, y, w, h = cell
    
    # 셀 이미지 추출 (패딩 적용)
    padding = 2
    y_min = max(0, y - padding)
    x_min = max(0, x - padding)
    y_max = min(image.shape[0], y + h + padding)
    x_max = min(image.shape[1], x + w + padding)
    
    cell_img = image[y_min:y_max, x_min:x_max]
    
    # 셀 이미지가 비어있는지 확인
    if cell_img.size == 0:
        return ""
    
    # Vision API로 전송하기 위해 인코딩
    _, buffer = cv2.imencode('.jpg', cell_img)
    byte_img = buffer.tobytes()
    
    try:
        # Vision API로 OCR 수행
        vision_image = vision.Image(content=byte_img)
        response = vision_client.text_detection(image=vision_image)
        
        # 오류 체크
        if response.error.message:
            print(f"[ERROR] OCR 오류: {response.error.message}")
            return ""
        
        # 텍스트 추출
        if response.text_annotations:
            return response.text_annotations[0].description.strip()
        return ""
    except Exception as e:
        print(f"[ERROR] OCR 예외: {str(e)}")
        return ""

def process_table_with_fixed_columns(image_path, column_count=13):
    """고정된, 예상된 열 수를 가진 테이블을 처리합니다."""
    # 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] 이미지를 로드할 수 없습니다: {image_path}")
        return None
    
    # 테이블 영역 찾기
    table_image, table_offset = find_table_in_image(image_path)
    if table_image is None:
        print("[ERROR] 테이블을 찾을 수 없습니다")
        return None
    
    # 테이블 셀 구조 감지
    cells = detect_table_structure(table_image, table_offset)
    if not cells:
        print("[ERROR] 테이블 구조를 감지할 수 없습니다")
        return None
    
    # 디버깅 이미지 생성
    debug_image = image.copy()
    
    # 테이블 데이터 저장
    table_data = []
    
    # 각 행과 셀에서 텍스트 추출
    for row_idx, row in enumerate(cells):
        row_data = []
        for col_idx, cell in enumerate(row):
            x, y, w, h = cell
            
            # 디버깅 이미지에 셀 표시
            cv2.rectangle(debug_image, (x, y), (x+w, y+h), (0, 255, 0), 1)
            cv2.putText(debug_image, f"{row_idx},{col_idx}", (x+5, y+15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
            # OCR 수행
            text = extract_text_from_cell(image, cell)
            row_data.append(text)
            print(f"셀 ({row_idx},{col_idx}): {text}")
        
        # 행 데이터가 비어있지 않은 경우만 추가
        if any(col.strip() for col in row_data):
            # 행의 열 수가 예상된 열 수와 다른 경우 패딩
            if len(row_data) < column_count:
                row_data.extend([""] * (column_count - len(row_data)))
            elif len(row_data) > column_count:
                row_data = row_data[:column_count]
            
            table_data.append(row_data)
    
    # 디버깅 이미지 저장
    cv2.imwrite("detected_cells.jpg", debug_image)
    
    return table_data

def process_with_explicit_column_positions(image_path):
    """명시적인 열 위치를 정의하여 테이블을 처리합니다."""
    # 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] 이미지를 로드할 수 없습니다: {image_path}")
        return None
    
    # 테이블 영역 찾기
    table_image, (table_x, table_y, table_w, table_h) = find_table_in_image(image_path)
    if table_image is None:
        print("[ERROR] 테이블을 찾을 수 없습니다")
        return None
    
    # 이미지의 테이블 구조를 분석한 결과 명시적인 열 위치를 정의합니다.
    # 이는 테이블 구조에 맞게 조정해야 합니다.
    column_ratios = [0.07, 0.17, 0.08, 0.09, 0.08, 0.13, 0.08, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    
    # 열 위치 계산
    column_positions = [0]
    cumulative_ratio = 0
    for ratio in column_ratios:
        cumulative_ratio += ratio
        column_positions.append(int(cumulative_ratio * table_w))
    
    # 그레이스케일 변환
    gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    
    # 수평선 감지를 위한 커널
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    
    # 수평선 감지
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    
    # 행 위치 찾기 (수평선 위치)
    h_projections = np.sum(horizontal_lines, axis=1)
    row_positions = []
    for i in range(len(h_projections)):
        if h_projections[i] > 0:
            row_positions.append(i)
    
    # 인접한 행 병합
    def merge_adjacent(positions, threshold=10):
        if not positions:
            return []
        
        merged = [positions[0]]
        for i in range(1, len(positions)):
            if positions[i] - merged[-1] <= threshold:
                continue
            merged.append(positions[i])
        
        return merged
    
    row_positions = merge_adjacent(row_positions)
    
    # 디버깅 이미지 생성
    debug_image = image.copy()
    
    # 테이블 데이터 저장
    table_data = []
    
    # 각 행과 열에서 텍스트 추출
    for i in range(len(row_positions) - 1):
        row_data = []
        for j in range(len(column_positions) - 1):
            # 셀 좌표 계산
            x1 = column_positions[j] + table_x
            y1 = row_positions[i] + table_y
            x2 = column_positions[j+1] + table_x
            y2 = row_positions[i+1] + table_y
            
            # 셀 영역 그리기
            cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.putText(debug_image, f"{i},{j}", (x1+5, y1+15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
            # OCR 수행
            text = extract_text_from_cell(image, (x1, y1, x2-x1, y2-y1))
            row_data.append(text)
            print(f"셀 ({i},{j}): {text}")
        
        # 행 데이터가 비어있지 않은 경우만 추가
        if any(col.strip() for col in row_data):
            table_data.append(row_data)
    
    # 디버깅 이미지 저장
    cv2.imwrite("explicit_columns.jpg", debug_image)
    
    return table_data

def process_order_confirmation(pdf_path, output_file="explicit_columns_table.xlsx"):
    """주문 확인서 PDF를 처리하여 테이블 데이터 추출"""
    # PDF를 이미지로 변환
    image_paths = pdf_to_image(pdf_path)
    
    if not image_paths:
        print("[ERROR] PDF 변환 실패")
        return None
    
    # 명시적 열 위치로 테이블 처리
    table_data = process_with_explicit_column_positions(image_paths[0])
    
    if not table_data:
        print("[ERROR] 테이블 추출 실패")
        return None
    
    # DataFrame 생성
    df = pd.DataFrame(table_data)
    
    # 첫 번째 행을 헤더로 사용
    if len(df) > 0:
        header_row = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        df.columns = header_row
    
    # 엑셀 파일로 저장
    df.to_excel(output_file, index=False)
    print(f"[✅] 명시적 열 위치로 데이터 저장 완료: {output_file}")
    
    # 대체 방법도 시도
    alt_table_data = process_table_with_fixed_columns(image_paths[0])
    
    if alt_table_data:
        alt_df = pd.DataFrame(alt_table_data)
        if len(alt_df) > 0:
            header_row = alt_df.iloc[0]
            alt_df = alt_df[1:].reset_index(drop=True)
            alt_df.columns = header_row
        
        alt_df.to_excel("alternative_table.xlsx", index=False)
        print("[✅] 대체 방법으로 데이터 저장 완료: alternative_table.xlsx")
    
    return df

if __name__ == "__main__":
    pdf_path = "EQL_ORDER.pdf"
    result_df = process_order_confirmation(pdf_path)
    
    if result_df is not None:
        print("\n--- 추출된 데이터 미리보기 ---")
        print(result_df.head())