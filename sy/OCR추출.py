import io
import os
import csv
import re
import pdfplumber

# ✅ PDF에서 텍스트 추출하는 함수
def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text() + "\n"
    return extracted_text

# ✅ OCR 결과에서 필요한 데이터 추출
def extract_invoice_data(text):
    """OCR 결과에서 Season, Brand를 제외한 필드만 추출"""
    extracted_data = {}

    # ORDER CONFIRMATION ID 찾기
    order_id_match = re.search(r'ORDER CONFIRMATION ID:\s*(\d+)', text)
    extracted_data["ORDER CONFIRMATION ID"] = order_id_match.group(1) if order_id_match else "N/A"

    # CUSTOMER 찾기
    customer_match = re.search(r'CUSTOMER:\s*(.*?)\nYour Reference:', text, re.DOTALL)
    extracted_data["CUSTOMER"] = customer_match.group(1).strip() if customer_match else "N/A"

    # Product Line 찾기
    product_line_match = re.search(r'Product Line:\s*([^\n]+)', text)
    extracted_data["Product Line"] = product_line_match.group(1).strip() if product_line_match else "N/A"

    # 테이블 데이터 추출 (제품 리스트)
    items = []
    table_pattern = re.findall(
        r'(FTVRM\d+)\s+(AJ\d+ - [A-Z]+)\s+([\d.]+)\s+([\d.]+%)\s+(\d{2} \w{3} \d{2})\s+(\d{2} \w{3} \d{2})\s+([\d.]+)',
        text
    )

    for match in table_pattern:
        item_data = {
            "ORDER CONFIRMATION ID": extracted_data["ORDER CONFIRMATION ID"],  # 주문 ID 추가
            "ITEM CODE": match[0],
            "MODEL": match[1],
            "UNIT PRICE": match[2],
            "DISCOUNT": match[3],
            "SHIPPING START": match[4],
            "SHIPPING END": match[5],
            "TOTAL PRICE": match[6],
        }
        items.append(item_data)

    extracted_data["ITEMS"] = items
    return extracted_data

# ✅ 주문 정보를 CSV로 저장
def save_order_summary(data, file_name="order_summary.csv"):
    keys = ["ORDER CONFIRMATION ID", "CUSTOMER", "Product Line"]
    
    file_exists = os.path.isfile(file_name)

    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: data[k] for k in keys})

# ✅ 제품 상세 정보를 CSV로 저장
def save_order_items(items, file_name="order_items.csv"):
    keys = ["ORDER CONFIRMATION ID", "ITEM CODE", "MODEL", "UNIT PRICE", "DISCOUNT", "SHIPPING START", "SHIPPING END", "TOTAL PRICE"]
    
    file_exists = os.path.isfile(file_name)

    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        for item in items:
            writer.writerow(item)

# ✅ 메인 실행 함수
def process_document(file_path):
    extracted_text = extract_text_from_pdf(file_path)
    invoice_data = extract_invoice_data(extracted_text)

    # ✅ 주문 요약 저장
    save_order_summary(invoice_data, "order_summary.csv")

    # ✅ 제품 상세 정보 저장
    if invoice_data["ITEMS"]:
        save_order_items(invoice_data["ITEMS"], "order_items.csv")

    print(f"\n✅ CSV 파일 저장 완료: order_summary.csv, order_items.csv")
    return invoice_data

# ✅ 사용 예시 (PDF 경로 지정)
file_path = "C:/Users/Admin/Desktop/PD1/input/OC.pdf"
invoice_data = process_document(file_path)
print(invoice_data)
