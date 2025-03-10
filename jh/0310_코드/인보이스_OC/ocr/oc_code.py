import cv2
import pytesseract
import pandas as pd
from openpyxl import Workbook
from pdf2image import convert_from_path
import os
import platform
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
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    
    custom_config = '--psm 6'
    text = pytesseract.image_to_string(gray, lang='eng', config=custom_config)
    
    text = re.sub(r'[^\w\s\-.]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def parse_text(text):
    """ OCR로 추출한 텍스트에서 데이터를 정리하여 추출 """
    lines = text.split("\n")
    extracted_data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        style_match = re.search(r"Style\s?#?(\w+)", line)
        color_match = re.search(r"(\w+)\s+LEATHER|\w+\s+POLIDO", line)
        wholesale_match = re.search(r"Wholesale\s+EUR\s+([\d,.]+)", line)
        retail_match = re.search(r"Sugg\.\s+Retail\s+EUR\s+([\d,.]+)", line)
        
        if style_match and color_match and wholesale_match and retail_match:
            extracted_data.append([
                style_match.group(1),
                color_match.group(1),
                wholesale_match.group(1),
                retail_match.group(1)
            ])
    
    return extracted_data

def generate_custom_code(style, color, wholesale, retail):
    """ 자사품번코드 생성 """
    return f"{style}-{color}-{wholesale}-{retail}"

def process_invoice_pdf(pdf_path, output_excel):
    """ PDF에서 OCR 처리 후 데이터 비교 및 엑셀 저장 """
    image_paths = pdf_to_images(pdf_path)
    
    ocr_texts = [extract_text_with_improved_ocr(img) for img in image_paths]
    for img in image_paths:
        os.remove(img)
    
    structured_data = [parse_text(text) for text in ocr_texts]
    df_parsed = pd.DataFrame(
        [item for sublist in structured_data for item in sublist],
        columns=["Style", "Color", "Wholesale_EUR", "Retail_EUR"]
    )
    
    df_parsed["Custom_Code"] = df_parsed.apply(
        lambda row: generate_custom_code(row["Style"], row["Color"], row["Wholesale_EUR"], row["Retail_EUR"]), axis=1
    )
    
    df_parsed.to_excel(output_excel, index=False)
    print(f"비교 결과가 {output_excel} 파일로 저장되었습니다.")

# 실행 코드
invoice_pdf_path = "invoice_document.pdf"
output_excel_path = "final_comparison_result.xlsx"
process_invoice_pdf(invoice_pdf_path, output_excel_path)
