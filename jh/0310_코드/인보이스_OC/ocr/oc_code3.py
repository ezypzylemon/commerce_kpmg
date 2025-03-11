import cv2
import pytesseract
import pandas as pd
from openpyxl import Workbook
from pdf2image import convert_from_path
import os
import re

def pdf_to_images(pdf_path):
    """ PDF 파일을 이미지로 변환 """
    images = convert_from_path(pdf_path)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = f"page_{i}.jpg"
        image.save(image_path, "JPEG")
        image_paths.append(image_path)
    
    return image_paths

def extract_text_with_improved_ocr(image_path):
    """ OCR을 적용하여 이미지에서 텍스트 추출 (전처리 포함) """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 이미지 전처리
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    
    # OCR 적용
    custom_config = '--psm 6'
    text = pytesseract.image_to_string(gray, lang='eng', config=custom_config)
    
    return text

def clean_ocr_text(text):
    """
    Clean OCR text by removing unwanted characters and normalizing spaces
    """
    # Remove special characters and normalize spaces
    text = re.sub(r'[«»—ooаOO]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_product_sections(text):
    """
    Extract individual product sections from OCR text
    """
    product_sections = re.split(r'(AJ\d+)', text)[1:]  # Split by product code (AJ###)
    
    products = []
    for i in range(0, len(product_sections), 2):  # Pair product codes with their details
        if i + 1 < len(product_sections):
            product_code = product_sections[i].strip()
            product_details = product_sections[i + 1].strip()
            products.append((product_code, product_details))
            
    return products

def extract_style_info(details):
    """
    Extract style code and color from product details
    """
    style_match = re.search(r'Style\s?#?(\w+)', details)
    color_match = re.search(r'(BLACK LEATHER|BLACK POLIDO)', details)
    
    style = style_match.group(1) if style_match else ""
    color = color_match.group(1) if color_match else ""
    
    return style, color

def extract_sizes_and_quantities(details):
    """
    Extract sizes and quantities from product details
    """
    # Extract sizes after "Clrs" or "Colors"
    sizes_match = re.search(r'(?:Clrs|Colors)\s+([\d\s\-\.]+)', details)
    
    # Extract quantities after "BLACK BLACK"
    quantities_match = re.search(r'BLACK BLACK\s+([\d\s]+)', details)
    
    if not sizes_match or not quantities_match:
        return []
    
    # Parse sizes and quantities into arrays of numbers
    sizes = re.findall(r'\b\d+\b', sizes_match.group(1))
    quantities = re.findall(r'\b\d+\b', quantities_match.group(1))
    
    # Match sizes with quantities (only keep items with quantity > 0)
    result = []
    min_length = min(len(sizes), len(quantities))
    
    for i in range(min_length):
        if int(quantities[i]) > 0:
            result.append((sizes[i], quantities[i]))
    
    return result

def format_code(value, length=2):
    """
    Format code value to specified length (maintaining leading zeros)
    """
    return str(value).zfill(length)

def generate_multi_custom_code(product_code, style, color, size):
    """
    Generate custom code for individual product variant
    """
    # Extract year from style (last 2 digits)
    year = format_code(style[-2:]) if style else "00"
    
    # Extract season from color (first letter)
    season = color[0] if color else "B"  # B for BLACK as default
    
    # Fixed values
    batch = "01"
    vendor = "AF"
    category = "SH"  # Shoes category
    brand = "TV"     # TOGA VIRILIS
    sale_type = "ON" # Online
    line = "M"       # Mens
    sub_category = "FL"  # Footwear
    item = product_code.replace("AJ", "")  # Item code from AJxxx
    
    # Size as option1
    option1 = size
    
    # Format the custom code
    return f"{year}{season}{batch}{vendor}-{category}{brand}{sale_type}{line}{sub_category}-{item}{option1}"

def extract_wholesale_retail_prices(details):
    """
    Extract wholesale and retail prices from product details
    """
    wholesale_match = re.search(r'Wholesale[:\s]+EUR\s+([\d,.]+)', details)
    retail_match = re.search(r'(?:Sugg\.|Suggested)\s+Retail[:\s]+EUR\s+([\d,.]+)', details)
    
    wholesale = wholesale_match.group(1) if wholesale_match else ""
    retail = retail_match.group(1) if retail_match else ""
    
    return wholesale, retail

def process_ocr_data(ocr_text):
    """
    Process OCR text to extract product information and generate custom codes
    """
    # Clean the OCR text
    cleaned_text = clean_ocr_text(ocr_text)
    
    # Extract product sections
    products = extract_product_sections(cleaned_text)
    
    # Storage for final data
    all_products = []
    
    # Process each product
    for product_code, product_details in products:
        # Extract style and color information
        style, color = extract_style_info(product_details)
        
        # Extract wholesale and retail prices
        wholesale, retail = extract_wholesale_retail_prices(product_details)
        
        # Extract sizes and quantities
        size_quantity_pairs = extract_sizes_and_quantities(product_details)
        
        # Generate custom code for each size
        for size, quantity in size_quantity_pairs:
            custom_code = generate_multi_custom_code(product_code, style, color, size)
            
            # Add to final data list
            all_products.append({
                'Product_Code': product_code,
                'Style': style,
                'Color': color,
                'Size': size,
                'Quantity': quantity,
                'Wholesale_EUR': wholesale,
                'Retail_EUR': retail,
                'Custom_Code': custom_code
            })
    
    # Create DataFrame from the product data
    df = pd.DataFrame(all_products)
    
    return df

def process_invoice_pdf(pdf_path, output_excel):
    """ PDF에서 OCR 처리 후 데이터 비교 및 엑셀 저장 """
    # PDF를 이미지로 변환
    image_paths = pdf_to_images(pdf_path)
    
    # 각 이미지에 OCR 적용하여 텍스트 추출
    ocr_texts = [extract_text_with_improved_ocr(img) for img in image_paths]
    
    # 임시 이미지 파일 삭제
    for img in image_paths:
        os.remove(img)
    
    # 모든 OCR 텍스트 결합
    combined_ocr_text = "\n".join(ocr_texts)
    
    # OCR 데이터 처리 및 품번 생성
    df_result = process_ocr_data(combined_ocr_text)
    
    # 결과를 엑셀 파일로 저장
    df_result.to_excel(output_excel, index=False)
    print(f"비교 결과가 {output_excel} 파일로 저장되었습니다.")

# 실행 코드
if __name__ == "__main__":
    invoice_pdf_path = "invoice_document.pdf"
    output_excel_path = "final_multi_item_result.xlsx"
    process_invoice_pdf(invoice_pdf_path, output_excel_path)