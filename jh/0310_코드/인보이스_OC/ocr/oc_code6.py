import cv2
import numpy as np
import pytesseract
import pandas as pd
from pdf2image import convert_from_path
import os
import re
import argparse
from datetime import datetime

def pdf_to_images(pdf_path, dpi=300):
    """
    PDF 파일을 고해상도 이미지로 변환
    """
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        image_paths = []
        
        for i, image in enumerate(images):
            image_path = f"temp_page_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            image.save(image_path, "JPEG", quality=95)
            image_paths.append(image_path)
        
        return image_paths
    except Exception as e:
        print(f"PDF 변환 오류: {e}")
        return []

def enhance_image_for_ocr(image_path):
    """
    OCR 성능 향상을 위한 이미지 전처리
    """
    try:
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            print(f"이미지를 불러올 수 없습니다: {image_path}")
            return image_path
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거 및 이미지 선명도 향상
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # 대비 향상
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 이미지 경계 강화
        edge_enhance = cv2.Laplacian(opening, cv2.CV_8U, ksize=3)
        sharpened = cv2.addWeighted(opening, 1.5, edge_enhance, -0.5, 0)
        
        # 처리된 이미지 저장
        enhanced_path = f"enhanced_{os.path.basename(image_path)}"
        cv2.imwrite(enhanced_path, sharpened)
        
        return enhanced_path
    except Exception as e:
        print(f"이미지 처리 오류: {e}")
        return image_path

def extract_text_with_improved_ocr(image_path):
    """
    OCR을 적용하여 이미지에서 텍스트 추출
    """
    try:
        # 이미지 향상
        enhanced_path = enhance_image_for_ocr(image_path)
        
        # 일반 텍스트 인식 설정
        general_config = r'--psm 6 --oem 3'
        general_text = pytesseract.image_to_string(enhanced_path, lang='eng', config=general_config)
        
        # 테이블 구조 인식 설정
        table_config = r'--psm 11 --oem 3 -c preserve_interword_spaces=1'
        table_text = pytesseract.image_to_string(enhanced_path, lang='eng', config=table_config)
        
        # 향상된 이미지 정리
        if os.path.exists(enhanced_path) and enhanced_path != image_path:
            os.remove(enhanced_path)
        
        # 두 결과 합치기
        combined_text = general_text + "\n" + table_text
        
        return combined_text
    except Exception as e:
        print(f"OCR 처리 오류: {e}")
        return ""

def clean_ocr_text(text):
    """
    OCR 텍스트 정리 및 정규화
    """
    # 불필요한 문자 제거
    cleaned = re.sub(r'[«»—ooаOO]', '', text)
    # 공백 정규화
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def extract_product_sections(text):
    """
    OCR 텍스트에서 개별 상품 섹션을 분리하여 추출
    """
    # AJ로 시작하는 상품 코드 패턴
    product_pattern = r'(AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE).*?)(?=AJ\d+\s*[-]?\s*(?:BLACK|WHITE|BROWN|RED|BLUE|GREEN|YELLOW|PURPLE|GRAY|GREY|ORANGE|PINK|BEIGE)|$)'
    
    # 정규식을 통해 상품 코드로 시작하는 섹션 찾기
    product_sections = re.findall(product_pattern, text, re.DOTALL | re.IGNORECASE)
    
    # 빈 섹션 제거
    product_sections = [section.strip() for section in product_sections if section.strip()]
    
    return product_sections

def extract_product_info(section):
    """
    상품 섹션에서 기본 제품 정보 추출
    """
    product_info = {}
    
    # 제품 코드 추출 (예: AJ1323)
    product_code_match = re.search(r'(AJ\d+)', section)
    if product_code_match:
        product_info['product_code'] = product_code_match.group(1)
    
    # 색상 추출 - 다양한 색상 패턴 인식
    colors = ['BLACK LEATHER', 'BLACK POLIDO', 'WHITE', 'BROWN', 'RED', 'BLUE', 'GREEN']
    for color in colors:
        if color in section:
            product_info['color'] = color
            break
    
    # 스타일 코드 추출 (다양한 패턴 지원)
    style_match = re.search(r'Style\s*[#]?(\w+)', section)
    if style_match:
        product_info['style'] = style_match.group(1)
    else:
        # 대체 패턴 시도
        alt_style_match = re.search(r'#\s*(\w+)', section)
        if alt_style_match:
            product_info['style'] = alt_style_match.group(1)
    
    # 브랜드 및 시즌 추출
    brand_match = re.search(r'(TOGA VIRILIS|[A-Z\s]+).*?(\d{4}[SF]S\w+)', section)
    if brand_match:
        product_info['brand'] = brand_match.group(1).strip()
        product_info['season'] = brand_match.group(2)
    
    # 가격 정보 추출 (다양한 표기법 지원)
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

def extract_sizes_and_quantities(section):
    """
    상품 섹션에서 사이즈 및 수량 정보 추출
    """
    if not section or not isinstance(section, str):
        return []
    
    # 숫자만 존재하는 라인 찾기 (사이즈 라인)
    lines = section.split('\n')
    size_line = None
    quantity_line = None
    
    # "Colors" 또는 "Sizes" 부분 찾기
    colors_idx = -1
    for i, line in enumerate(lines):
        if 'Colors' in line or 'Sizes' in line:
            colors_idx = i
            break
    
    if colors_idx >= 0 and colors_idx + 1 < len(lines):
        # Colors 다음 라인에서 사이즈 번호 추출 시도
        size_candidates = []
        for i in range(colors_idx + 1, min(colors_idx + 4, len(lines))):
            if re.search(r'\b(3\d|4\d)\b.*\b(3\d|4\d)\b', lines[i]):
                size_candidates.append((i, lines[i]))
        
        if size_candidates:
            # 가장 많은 숫자가 포함된 라인을 사이즈 라인으로 선택
            size_line_idx, size_line = max(size_candidates, key=lambda x: len(re.findall(r'\b\d+\b', x[1])))
            
            # 사이즈 라인 다음에 나오는 BLACK BLACK 라인 찾기
            for i in range(size_line_idx + 1, min(size_line_idx + 4, len(lines))):
                if 'BLACK' in lines[i] and re.search(r'\b\d+\b', lines[i]):
                    quantity_line = lines[i]
                    break
    
    # 사이즈 라인이나 수량 라인을 찾지 못한 경우
    if not size_line or not quantity_line:
        # 대체 방법: 모든 30-40대 숫자를 사이즈로 간주
        sizes = []
        for line in lines:
            sizes.extend(re.findall(r'\b(3\d|4\d)\b', line))
        
        # BLACK BLACK 이후 숫자들을 수량으로 간주
        quantities = []
        black_match = None
        for line in lines:
            if 'BLACK BLACK' in line:
                black_match = re.search(r'BLACK BLACK\s+([\d\s]+)', line)
                if black_match:
                    quantities = re.findall(r'\b\d+\b', black_match.group(1))
                    break
        
        # 사이즈와 수량 매핑
        size_quantity_pairs = []
        min_length = min(len(sizes), len(quantities)) if quantities else 0
        
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
    try:
        return str(value).zfill(length)
    except:
        return "0" * length

def generate_custom_code(product_info, size):
    """
    개별 상품 사이즈별 품번코드 생성
    """
    # 기본값 설정
    style = product_info.get('style', '')
    color = product_info.get('color', '')
    product_code = product_info.get('product_code', '')
    
    # 연도 추출 (스타일 코드 마지막 2자리)
    year = "00"
    if style and len(style) >= 2:
        try:
            year = format_code(style[-2:])
        except:
            year = "00"
    
    # 시즌 (색상 첫 글자)
    season = "X"
    if color:
        season = color[0]
    
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
    
    # 품번코드 형식: {year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item}{option1}
    custom_code = f"{year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item_code}{option1}"
    
    return custom_code

def process_ocr_data(ocr_text):
    """
    OCR 텍스트를 처리하여 여러 상품의 정보 및 품번코드 생성
    """
    # OCR 텍스트 정리
    cleaned_text = clean_ocr_text(ocr_text)
    
    # 상품 섹션 분리
    product_sections = extract_product_sections(cleaned_text)
    print(f"총 {len(product_sections)}개의 상품 섹션이 추출되었습니다.")
    
    all_products = []
    
    # 각 상품 섹션 처리
    for i, section in enumerate(product_sections):
        print(f"\n상품 {i+1}/{len(product_sections)} 처리 중...")
        
        # 상품 기본정보 추출
        product_info = extract_product_info(section)
        print(f"상품 코드: {product_info.get('product_code', 'N/A')}")
        print(f"스타일: {product_info.get('style', 'N/A')}")
        print(f"색상: {product_info.get('color', 'N/A')}")
        
        # 사이즈 및 수량 정보 추출
        size_quantity_pairs = extract_sizes_and_quantities(section)
        print(f"추출된 사이즈 및 수량 쌍: {len(size_quantity_pairs)}개")
        
        # 사이즈 및 수량 추출 실패 시 확인
        if not size_quantity_pairs:
            print(f"주의: 상품 {product_info.get('product_code', 'N/A')}에서 사이즈 및 수량 정보를 추출하지 못했습니다.")
        
        # 각 사이즈별 품번코드 생성
        for size, quantity in size_quantity_pairs:
            custom_code = generate_custom_code(product_info, size)
            
            # 데이터 추가
            all_products.append({
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
    
    return all_products

def process_invoice_pdf(pdf_path, output_excel, verbose=True):
    """
    PDF 인보이스에서 OCR 처리 후 데이터 추출 및 엑셀 저장
    """
    if verbose:
        print(f"PDF 파일 처리 시작: {pdf_path}")
    
    # PDF를 고해상도 이미지로 변환
    image_paths = pdf_to_images(pdf_path, dpi=300)
    
    if not image_paths:
        print("PDF 변환 실패: 이미지가 생성되지 않았습니다.")
        return pd.DataFrame()
    
    if verbose:
        print(f"PDF에서 {len(image_paths)}개 이미지 생성됨")
    
    all_products = []
    
    # 각 이미지에 OCR 적용
    for i, image_path in enumerate(image_paths):
        if verbose:
            print(f"\n이미지 {i+1}/{len(image_paths)} 처리 중: {image_path}")
        
        # OCR 처리
        ocr_text = extract_text_with_improved_ocr(image_path)
        
        if verbose:
            print(f"이미지 {i+1}에서 상품 데이터 추출 중...")
        
        # 상품 데이터 처리
        product_data = process_ocr_data(ocr_text)
        all_products.extend(product_data)
        
        # 임시 이미지 파일 삭제
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # 데이터프레임 생성
    if all_products:
        df_result = pd.DataFrame(all_products)
        
        # 결과를 엑셀 파일로 저장
        df_result.to_excel(output_excel, index=False)
        
        if verbose:
            print(f"\n처리 결과가 {output_excel} 파일로 저장되었습니다.")
            print(f"총 {len(df_result)}개 상품 데이터가 추출되었습니다.")
        
        return df_result
    else:
        if verbose:
            print("\n추출된 상품 데이터가 없습니다. OCR 처리 결과를 확인해주세요.")
        
        return pd.DataFrame()

def main():
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='PDF 인보이스에서 상품 정보 추출하여 품번코드 생성')
    parser.add_argument('pdf_path', nargs='?', default='invoice_document.pdf', 
                        help='처리할 PDF 파일 경로 (기본값: invoice_document.pdf)')
    parser.add_argument('--output', '-o', default='',
                        help='결과 저장할 엑셀 파일 경로 (기본값: product_codes_현재날짜.xlsx)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='상세 로그 출력')
    
    args = parser.parse_args()
    
    # 출력 파일명 설정
    if not args.output:
        output_excel = f"product_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    else:
        output_excel = args.output
    
    # PDF 파일 존재 확인
    if not os.path.exists(args.pdf_path):
        print(f"오류: 파일을 찾을 수 없습니다: {args.pdf_path}")
        print(f"현재 작업 디렉토리: {os.getcwd()}")
        return
    
    # PDF 처리 실행
    process_invoice_pdf(args.pdf_path, output_excel, verbose=args.verbose)

# 스크립트가 직접 실행될 때
if __name__ == "__main__":
    main()