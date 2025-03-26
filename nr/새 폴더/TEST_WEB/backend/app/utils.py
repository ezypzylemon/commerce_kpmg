import re
from datetime import datetime

def clean_ocr_text(text):
    """OCR 텍스트 정리 및 정규화"""
    cleaned = re.sub(r'[«»—ooаOO]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def format_code(value, length=2):
    """코드값 포맷팅"""
    try:
        return str(value).zfill(length)
    except:
        return "0" * length

def generate_custom_code(product_info, size):
    """개별 상품 사이즈별 품번코드 생성"""
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