import cv2
import numpy as np
import pytesseract
import pandas as pd
from pdf2image import convert_from_path
import os
import re

def pdf_to_images(pdf_path, dpi=300):
    """
    PDF 파일을 고해상도 이미지로 변환 (DPI 향상)
    """
    images = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = f"page_{i}.jpg"
        image.save(image_path, "JPEG", quality=95)  # 고품질 이미지 저장
        image_paths.append(image_path)
    
    return image_paths

def enhance_image_for_ocr(image_path):
    """
    OCR 성능 향상을 위한 이미지 전처리 기능 향상
    """
    # 이미지 로드
    image = cv2.imread(image_path)
    
    # 그레이스케일 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 노이즈 제거 및 이미지 선명도 향상
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # 대비 향상
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # 처리된 이미지 저장
    enhanced_path = f"enhanced_{os.path.basename(image_path)}"
    cv2.imwrite(enhanced_path, opening)
    
    return enhanced_path

def extract_text_with_improved_ocr(image_path):
    """
    OCR을 적용하여 이미지에서 텍스트 추출 (테이블 인식 최적화)
    """
    # 이미지 향상
    enhanced_path = enhance_image_for_ocr(image_path)
    
    # 테이블 구조 OCR 최적화 설정
    # PSM 모드:
    # 6: 단일 텍스트 블록 (기본값)
    # 11: 구조화된 텍스트 블록 (테이블에 적합)
    # 4: 가변 크기 텍스트 (열/세로 텍스트 인식)
    custom_config = r'--psm 11 --oem 3 -c preserve_interword_spaces=1'
    
    # 테이블 인식을 위한 OCR 처리
    text = pytesseract.image_to_string(enhanced_path, lang='eng', config=custom_config)
    
    # 테이블 데이터 추출을 위한 별도 설정
    table_config = r'--psm 6 --oem 3'
    table_text = pytesseract.image_to_string(enhanced_path, lang='eng', config=table_config)
    
    # 향상된 이미지 정리
    if os.path.exists(enhanced_path):
        os.remove(enhanced_path)
    
    return text, table_text

def clean_ocr_text(text):
    """
    OCR 텍스트 정리 및 정규화 (특수문자 제거, 공백 정리)
    """
    # 불필요한 문자 제거
    text = re.sub(r'[«»—ooаOO]', '', text)
    # 공백 정규화
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_product_info(text):
    """
    제품 기본정보 추출 (코드, 스타일, 색상, 가격 등)
    """
    product_info = {}
    
    # 제품 코드 추출 (예: AJ1323)
    product_code_match = re.search(r'(AJ\d+)', text)
    if product_code_match:
        product_info['product_code'] = product_code_match.group(1)
    
    # 색상 추출
    color_match = re.search(r'(BLACK LEATHER|BLACK POLIDO)', text)
    if color_match:
        product_info['color'] = color_match.group(1)
    
    # 스타일 코드 추출
    style_match = re.search(r'Style\s*[#]?(\w+)', text)
    if style_match:
        product_info['style'] = style_match.group(1)
    
    # 브랜드 및 시즌 추출
    brand_match = re.search(r'(TOGA VIRILIS).*?(\d{4}[SF]S\w+)', text)
    if brand_match:
        product_info['brand'] = brand_match.group(1)
        product_info['season'] = brand_match.group(2)
    
    # 가격 정보 추출
    wholesale_match = re.search(r'Wholesale:?\s*EUR\s*(\d+\.\d+)', text)
    retail_match = re.search(r'(?:Sugg\.|Suggested)\s+Retail:?\s*EUR\s*(\d+\.\d+)', text)
    
    if wholesale_match:
        product_info['wholesale_price'] = wholesale_match.group(1)
    if retail_match:
        product_info['retail_price'] = retail_match.group(1)
    
    # 제품 카테고리 추출
    category_match = re.search(r'Silhouette:\s*(.+?)(?=Country|$)', text)
    if category_match:
        product_info['category'] = category_match.group(1).strip()
    
    # 원산지 추출
    origin_match = re.search(r'Country of Origin:\s*(.+?)(?=Colors|$)', text)
    if origin_match:
        product_info['origin'] = origin_match.group(1).strip()
    
    return product_info

def extract_sizes_and_quantities(table_text):
    """
    테이블 텍스트에서 사이즈 및 수량 정보 추출
    """
    if not table_text or not isinstance(table_text, str):
        return []  # 빈 리스트 반환
    
    # 사이즈 라인 찾기 (39, 40, 41 등의 숫자가 연속된 라인)
    size_line = None
    quantity_line = None
    
    for line in table_text.split('\n'):
        if re.search(r'\b(3\d|4\d)\b.*\b(3\d|4\d)\b', line):  # 여러 30-40대 숫자 포함
            size_line = line
        elif 'BLACK BLACK' in line and re.search(r'\b\d+\b', line):
            quantity_line = line
    
    if not size_line or not quantity_line:
        # 정규식을 좀 더 유연하게 적용
        size_pattern = r'\b(3\d|4\d)\b'
        sizes = re.findall(size_pattern, table_text)
        
        # BLACK BLACK 이후 숫자 패턴 찾기
        black_match = re.search(r'BLACK BLACK\s+([\d\s]+)', table_text)
        quantities = []
        if black_match:
            quantities = re.findall(r'\b\d+\b', black_match.group(1))
        
        # 사이즈와 수량 매핑
        size_quantity_pairs = []
        min_length = min(len(sizes), len(quantities))
        
        for i in range(min_length):
            if int(quantities[i]) > 0:
                size_quantity_pairs.append((sizes[i], quantities[i]))
                
        return size_quantity_pairs
    
    # 사이즈 추출
    sizes = re.findall(r'\b(3\d|4\d)\b', size_line)
    
    # 수량 추출 (BLACK BLACK 이후의 숫자들)
    quantities = []
    qty_match = re.search(r'BLACK BLACK\s+([\d\s]+)', quantity_line)
    if qty_match:
        quantities = re.findall(r'\b\d+\b', qty_match.group(1))
    
    # 사이즈와 수량 매핑
    size_quantity_pairs = []
    min_length = min(len(sizes), len(quantities))
    
    for i in range(min_length):
        if int(quantities[i]) > 0:
            size_quantity_pairs.append((sizes[i], quantities[i]))
    
    return size_quantity_pairs

def format_code(value, length=2):
    """
    코드값 포맷팅 (앞자리 0 유지)
    """
    return str(value).zfill(length)

def generate_custom_code(product_info, size):
    """
    개별 상품 사이즈별 품번코드 생성
    """
    # 기본값 설정
    style = product_info.get('style', '')
    color = product_info.get('color', 'BLACK LEATHER')
    product_code = product_info.get('product_code', '')
    
    # 연도 추출 (스타일 코드 마지막 2자리)
    year = format_code(style[-2:]) if style and len(style) >= 2 else "00"
    
    # 시즌 (색상 첫 글자)
    season = color[0] if color else "B"  # B for BLACK
    
    # 브랜드 코드 설정
    brand_name = product_info.get('brand', '')
    if 'TOGA VIRILIS' in brand_name:
        brand = "TV"
    else:
        brand = "XX"  # 기본값
    
    # 상품 카테고리 설정
    category_name = product_info.get('category', '')
    if 'Shoes' in category_name or 'SHOES' in category_name:
        category = "SH"
    else:
        category = "XX"  # 기본값
    
    # 고정 값
    batch = "01"
    vendor = "AF"
    sale_type = "ON"  # Online
    line = "M"  # Mens
    sub_category = "FL"  # Footwear
    
    # 품번코드에서 번호 부분 추출
    item_code = product_code.replace("AJ", "") if product_code else "000"
    
    # 사이즈를 option1으로 사용
    option1 = size
    
    # 품번코드 형식: {year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item}{option1}
    custom_code = f"{year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
    
    return custom_code

def process_product_data(ocr_text, table_text):
    """
    OCR 텍스트와 테이블 텍스트를 처리하여 상품 정보 및 품번코드 생성
    """
    # OCR 텍스트 정리
    cleaned_text = clean_ocr_text(ocr_text)
    cleaned_table_text = clean_ocr_text(table_text)
    
    # 디버깅 출력
    print("정리된 OCR 텍스트:")
    print(cleaned_text[:200] + "...")  # 처음 200자만 출력
    print("\n정리된 테이블 텍스트:")
    print(cleaned_table_text[:200] + "...")  # 처음 200자만 출력
    
    # 상품 기본정보 추출
    product_info = extract_product_info(cleaned_text)
    print("\n추출된 상품 정보:")
    for key, value in product_info.items():
        print(f"{key}: {value}")
    
    # 사이즈 및 수량 정보 추출
    size_quantity_pairs = extract_sizes_and_quantities(cleaned_table_text)
    print("\n추출된 사이즈 및 수량:")
    for size, qty in size_quantity_pairs:
        print(f"사이즈: {size}, 수량: {qty}")
    
    # 결과 데이터 생성
    product_data = []
    
    for size, quantity in size_quantity_pairs:
        # 품번코드 생성
        custom_code = generate_custom_code(product_info, size)
        
        # 데이터 추가
        product_data.append({
            'Product_Code': product_info.get('product_code', ''),
            'Style': product_info.get('style', ''),
            'Color': product_info.get('color', ''),
            'Size': size,
            'Quantity': quantity,
            'Wholesale_EUR': product_info.get('wholesale_price', ''),
            'Retail_EUR': product_info.get('retail_price', ''),
            'Origin': product_info.get('origin', ''),
            'Category': product_info.get('category', ''),
            'Brand': product_info.get('brand', ''),
            'Season': product_info.get('season', ''),
            'Custom_Code': custom_code
        })
    
    return product_data

def process_invoice_pdf(pdf_path, output_excel):
    """
    PDF 인보이스에서 OCR 처리 후 데이터 추출 및 엑셀 저장
    """
    print(f"PDF 파일 처리 시작: {pdf_path}")
    
    # PDF를 고해상도 이미지로 변환
    image_paths = pdf_to_images(pdf_path, dpi=300)
    print(f"PDF에서 {len(image_paths)}개 이미지 생성됨")
    
    all_products = []
    
    # 각 이미지에 OCR 적용
    for i, image_path in enumerate(image_paths):
        print(f"\n이미지 {i+1}/{len(image_paths)} 처리 중: {image_path}")
        
        # OCR 처리
        ocr_text, table_text = extract_text_with_improved_ocr(image_path)
        
        # 상품 데이터 처리
        print(f"이미지 {i+1}에서 상품 데이터 추출 중...")
        product_data = process_product_data(ocr_text, table_text)
        all_products.extend(product_data)
        
        # 임시 이미지 파일 삭제
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # 데이터프레임 생성
    if all_products:
        df_result = pd.DataFrame(all_products)
        
        # 결과를 엑셀 파일로 저장
        df_result.to_excel(output_excel, index=False)
        print(f"\n처리 결과가 {output_excel} 파일로 저장되었습니다.")
        print(f"총 {len(df_result)}개 상품 데이터가 추출되었습니다.")
        return df_result
    else:
        print("\n추출된 상품 데이터가 없습니다. OCR 처리 결과를 확인해주세요.")
        return pd.DataFrame()

# 샘플 텍스트로 테스트 실행 (디버깅용)
def test_with_sample():
    sample_text = """
    AJ1323 - BLACK LEATHER
    Style #FTVRM132309009 | TOGA VIRILIS - 2024SSMAN
    Wholesale: EUR 220.00 Sugg. Retail: EUR 550.00
    Silhouette: General Shoes
    Country of Origin: PORTUGAL
    
    Colors      39  40  41  42  43  44  45  46  Qty
    BLACK BLACK  1   1   2   2   1   0   0   0   7
    """
    
    product_info = extract_product_info(sample_text)
    print("샘플 텍스트에서 추출된 상품 정보:")
    for key, value in product_info.items():
        print(f"{key}: {value}")
    
    size_quantity_pairs = extract_sizes_and_quantities(sample_text)
    print("\n샘플 텍스트에서 추출된 사이즈 및 수량:")
    for size, qty in size_quantity_pairs:
        print(f"사이즈: {size}, 수량: {qty}")
        
    for size, qty in size_quantity_pairs:
        custom_code = generate_custom_code(product_info, size)
        print(f"사이즈 {size}의 품번코드: {custom_code}")

# 실행 코드
if __name__ == "__main__":
    # 전체 처리 전에 샘플 텍스트로 테스트 실행
    print("샘플 텍스트로 테스트 실행:")
    test_with_sample()
    print("\n" + "="*50 + "\n")
    
    # 실제 PDF 처리
    invoice_pdf_path = "invoice_document.pdf"
    output_excel_path = "improved_multi_item_result.xlsx"
    
    if os.path.exists(invoice_pdf_path):
        process_invoice_pdf(invoice_pdf_path, output_excel_path)
    else:
        print(f"파일을 찾을 수 없습니다: {invoice_pdf_path}")
        print("작업 디렉토리에 PDF 파일이 있는지 확인하세요.")
        print(f"현재 작업 디렉토리: {os.getcwd()}")