import cv2
import numpy as np
import os
import pandas as pd
import re
import json
from pdf2image import convert_from_path
from google.cloud import vision

def extract_and_clean_model_name(model_text):
    """
    모델명을 추출하고 정리하는 강력한 함수
    
    1. 개행 문자 제거
    2. 연속된 공백 제거
    3. 모델 코드 추출
    4. 모델 설명 정리
    """
    # 개행 문자를 공백으로 대체하고 여러 공백을 단일 공백으로 줄임
    cleaned_text = ' '.join(model_text.split())
    
    # 모델 코드 추출
    model_code_match = re.search(r'(AJ\d+)', cleaned_text)
    if not model_code_match:
        return cleaned_text
    
    model_code = model_code_match.group(1)
    
    # 모델 코드 제거 후 남은 텍스트
    model_description = cleaned_text.replace(model_code, '').strip()
    
    # 하이픈으로 시작하는 특수 문자 제거
    model_description = model_description.lstrip('-').strip()
    
    # 최종 모델명 구성
    return f"{model_code}-{model_description}"

def adjust_size_quantities(sizes_list):
    """수량 리스트를 39-46 형식으로 변환"""
    converted_sizes = {}
    for size, quantity in zip(range(39, 45), sizes_list):
        converted_sizes[size] = int(quantity)
    
    # 45, 46 사이즈는 0으로 고정
    converted_sizes[45] = 0
    converted_sizes[46] = 0
    
    return converted_sizes

def process_order_sheet(pdf_path, json_path, output_folder="result"):
    # 출력 폴더 생성
    os.makedirs(output_folder, exist_ok=True)
    
    # PDF를 이미지로 변환
    images = convert_from_path(pdf_path, dpi=300)
    
    # 첫 페이지 이미지 저장
    first_page_path = os.path.join(output_folder, "first_page.jpg")
    images[0].save(first_page_path, 'JPEG')
    
    # JSON 데이터 로드
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Google Vision 클라이언트 초기화
    vision_client = vision.ImageAnnotatorClient()
    
    # 이미지 로드
    img = cv2.imread(first_page_path)
    
    def extract_text_from_region(x, y, width, height):
        """지정된 영역의 텍스트 추출"""
        region = img[y:y+height, x:x+width]
        
        # 이미지를 메모리에 저장
        _, buffer = cv2.imencode('.jpg', region)
        byte_img = buffer.tobytes()
        
        # Vision API로 텍스트 추출
        vision_image = vision.Image(content=byte_img)
        response = vision_client.text_detection(image=vision_image)
        
        if response.text_annotations:
            return response.text_annotations[0].description.strip()
        return ""
    
    # 데이터 추출
    extracted_data = []
    
    # 각 제품 행 처리
    for row_config in config['product_rows']:
        # 모델명 추출
        model_text = extract_text_from_region(
            row_config['model']['x'], 
            row_config['model']['y'], 
            row_config['model']['width'], 
            row_config['model']['height']
        )
        
        # 모델명 추출 및 정리
        model_name = extract_and_clean_model_name(model_text)
        
        # 모델 코드 다시 추출
        model_code_match = re.search(r'(AJ\d+)', model_name)
        모델코드 = model_code_match.group(1) if model_code_match else ''
        
        # 단가 추출
        unit_price = extract_text_from_region(
            row_config['unit_price']['x'], 
            row_config['unit_price']['y'], 
            row_config['unit_price']['width'], 
            row_config['unit_price']['height']
        )
        
        # 할인율 추출
        할인율 = extract_text_from_region(
            row_config['disc_prcnt']['x'], 
            row_config['disc_prcnt']['y'], 
            row_config['disc_prcnt']['width'], 
            row_config['disc_prcnt']['height']
        )
        
        # 선적 시작일 추출
        선적_시작일 = extract_text_from_region(
            row_config['shipping_start']['x'], 
            row_config['shipping_start']['y'], 
            row_config['shipping_start']['width'], 
            row_config['shipping_start']['height']
        )
        
        # 선적 완료일 추출
        선적_완료일 = extract_text_from_region(
            row_config['shipping_end']['x'], 
            row_config['shipping_end']['y'], 
            row_config['shipping_end']['width'], 
            row_config['shipping_end']['height']
        )
        
        # 수량 추출
        sizes_quantities = []
        for size_key in ['390', '400', '410', '420', '430', '440']:
            size_region = row_config['sizes'][size_key]
            size_quantity = extract_text_from_region(
                size_region['x'], 
                size_region['y'], 
                size_region['width'], 
                size_region['height']
            )
            sizes_quantities.append(int(size_quantity) if size_quantity.isdigit() else 0)
        
        # 사이즈 변환
        converted_sizes = adjust_size_quantities(sizes_quantities)
        
        # 제품 정보 딕셔너리 생성
        product = {
            '모델코드': 모델코드,
            '모델명': model_name,
            '구매가': f"EUR {unit_price}",
            '할인율': 할인율,
            '선적_시작일': 선적_시작일,
            '선적_완료일': 선적_완료일,
            '총_수량': sum(converted_sizes.values())
        }
        
        # 사이즈별 수량을 개별 컬럼으로 추가
        for size in range(39, 47):
            product[f'사이즈_{size}'] = converted_sizes.get(size, 0)
        
        extracted_data.append(product)
    
    # 엑셀로 저장
    excel_path = os.path.join(output_folder, "order_sheet_data.xlsx")
    df = pd.DataFrame(extracted_data)
    
    # 컬럼 순서 지정
    columns_order = [
        '모델코드', '모델명', '구매가', '할인율', 
        '선적_시작일', '선적_완료일', '총_수량'
    ] + [f'사이즈_{size}' for size in range(39, 47)]
    
    df = df[columns_order]
    df.to_excel(excel_path, index=False)
    
    # 추출된 텍스트 저장
    extracted_text_path = os.path.join(output_folder, "extracted_text.txt")
    with open(extracted_text_path, 'w', encoding='utf-8') as f:
        for product in extracted_data:
            f.write(f"Model Code: {product['모델코드']}\n")
            f.write(f"Model Name: {product['모델명']}\n")
            f.write(f"Unit Price: {product['구매가']}\n")
            f.write(f"Discount Rate: {product['할인율']}\n")
            f.write(f"Shipping Start: {product['선적_시작일']}\n")
            f.write(f"Shipping End: {product['선적_완료일']}\n")
            f.write("Sizes:\n")
            for size in range(39, 47):
                f.write(f"  Size {size}: {product[f'사이즈_{size}']}\n")
            f.write(f"Total Quantity: {product['총_수량']}\n")
            f.write("-" * 30 + "\n")
    
    print(f"[✅] 데이터 처리 완료. 결과는 {output_folder} 폴더에 저장되었습니다.")
    
    return extracted_data

# 스크립트 직접 실행 시
if __name__ == "__main__":
    pdf_path = "EQL_ORDER.pdf"
    json_path = "order_data.json"
    process_order_sheet(pdf_path, json_path)