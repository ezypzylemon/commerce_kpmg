import os
import json
import random
import datetime
import re
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import img2pdf

# ===== 경로 설정 =====
INVOICE_PDF_PATH = "eql_in.pdf"  # 인보이스 PDF 파일 경로
ORDER_PDF_PATH = "EQL_ORDER.pdf"  # 오더시트 PDF 파일 경로
INVOICE_DATA_JSON = "invoice_data.json"  # 인보이스용 JSON 파일
ORDER_DATA_JSON = "order_data.json"  # 오더시트용 JSON 파일
OUTPUT_DIR = "data"  # 출력 디렉토리
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== 폰트/텍스트 설정 =====
FONT_SIZE = 20
FONT_SIZE_LARGE = 30
BRAND_BOX_FONT_SIZE = 25
TEXT_OFFSET_X = 6
TEXT_OFFSET_Y = 10
LINE_SPACING = 22

# ===== 브랜드/아이템/모델용 랜덤 데이터 =====
brand_list = [
    "PALMES", "BUTTER GOODS", "BATTENWEAR", "WILD DONKEY", "SUNFLOWER",
    "TACH CLOTHING", "HOUSE OF SUNNY", "BIRROT", "PERVERZE",
    "PERKS AND MINI", "TOGA", "COPERNI", "HEREU"
]
style_prefixes = ["FTGPW", "FTVRW", "FTSPW", "FTRRW"]
model_prefixes = ["AJ", "AC", "AR", "AL"]
colors = [
    "BLACK", "WHITE", "BROWN", "GRAY", "BEIGE", "NAVY", "RED", "GREEN",
    "SILVER", "GOLD", "PINK", "ORANGE", "YELLOW", "BLUE"
]
materials = [
    "LEATHER", "POLIDO", "NYLON", "SUEDE", "MESH", "VELVET",
    "RUBBER", "CANVAS", "DENIM", "FAUX LEATHER"
]

def get_random_date(start_year=2023, end_year=2024):
    """랜덤 날짜 생성"""
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    delta = (end_date - start_date).days
    random_days = random.randint(0, delta)
    result_date = start_date + datetime.timedelta(days=random_days)
    return result_date.strftime("%d-%m-%Y"), result_date

def get_random_ship_date(date_obj=None, format="%d %b %y"):
    """랜덤 배송 날짜 생성"""
    if date_obj is None:
        start_date = datetime.date(2023, 1, 1)
        end_date = datetime.date(2024, 12, 31)
        delta = (end_date - start_date).days
        random_days = random.randint(0, delta)
        result_date = start_date + datetime.timedelta(days=random_days)
    else:
        result_date = date_obj
    return result_date.strftime(format), result_date

def get_season_from_date(date_obj):
    """날짜로부터 시즌 생성"""
    year = date_obj.year + 1
    month = date_obj.month
    return f"{year}SS" if month <= 6 else f"{year}FW"

def get_shipping_window(date_obj):
    """배송 기간 생성"""
    start_ship = date_obj + datetime.timedelta(days=120)
    end_ship = date_obj + datetime.timedelta(days=180)
    return start_ship.strftime("%d %b %y"), end_ship.strftime("%d %b %y"), start_ship, end_ship

def generate_random_style():
    """랜덤 스타일 코드 생성"""
    style_prefix = random.choice(style_prefixes)
    num1 = str(random.randint(1000, 9999))
    num2 = str(random.randint(10000, 99999))
    return f"{style_prefix}{num1}", f"{num2}"

def generate_random_model(style_code=None):
    """랜덤 모델명 생성"""
    if style_code:
        model_number_match = re.search(r"(\d{3,})", style_code)
        model_number = model_number_match.group(1) if model_number_match else "0000"
    else:
        model_number = str(random.randint(1000, 9999))
    model_prefix = random.choice(model_prefixes)
    color = random.choice(colors)
    material = random.choice(materials)
    return f"{model_prefix}{model_number} - {color} {material}", color, material

def generate_common_data(num_products=4):
    """인보이스와 오더시트 간 공통 데이터 생성"""
    random_date_str, random_date_obj = get_random_date()
    season_str = get_season_from_date(random_date_obj)
    ship_start_str, ship_end_str, ship_start_obj, ship_end_obj = get_shipping_window(random_date_obj)
    brand_name = random.choice(brand_list)
    
    # 사이즈 매핑 테이블 (오더시트 -> 인보이스)
    size_mapping = {
        "390": "39",
        "400": "40", 
        "410": "41",
        "420": "42",
        "430": "43", 
        "440": "44"
    }
    
    products = []
    for _ in range(num_products):
        style_code1, style_code2 = generate_random_style()
        model_name, color, material = generate_random_model(style_code1)
        
        # 가격 정보
        unit_price = random.choice(range(140, 221, 10))
        retail_price = unit_price * 2.5
        
        # 사이즈 정보
        sizes = {}  # 오더시트용 사이즈 (390-440)
        sizes_invoice = {}  # 인보이스용 사이즈 (39-46)
        total_qty = 0
        
        # 오더시트용 사이즈 (390-440)에 0~5 범위의 랜덤 수량 생성
        for size in ["390", "400", "410", "420", "430", "440"]:
            qty = random.randint(0, 5)  # 0부터 시작 (0은 공백/주문 없음)
            sizes[size] = qty
            if qty > 0:  # 0인 경우는 합계에 포함하지 않음
                total_qty += qty
        
        # 인보이스용 사이즈 (39-46) 매핑
        for order_size, invoice_size in size_mapping.items():
            sizes_invoice[invoice_size] = sizes[order_size]
        
        # 인보이스에만 있는 45, 46 사이즈는 0(공백)으로 설정
        sizes_invoice["45"] = 0
        sizes_invoice["46"] = 0
        
        product = {
            "style_code": style_code1 + style_code2,
            "style_code1": style_code1,
            "style_code2": style_code2,
            "model_name": model_name,
            "color": color,
            "material": material,
            "color_material": f"{color} {material}",
            "unit_price": unit_price,
            "retail_price": retail_price,
            "sizes": sizes,
            "sizes_invoice": sizes_invoice,
            "total_qty": total_qty,
            "total_price": unit_price * total_qty
        }
        products.append(product)
    
    common_data = {
        "date": random_date_str,
        "date_obj": random_date_obj,
        "season": season_str,
        "brand": brand_name,
        "ship_start": ship_start_str,
        "ship_end": ship_end_str,
        "ship_start_obj": ship_start_obj,
        "ship_end_obj": ship_end_obj,
        "products": products,
        "total_quantity": sum(p["total_qty"] for p in products),
        "total_price": sum(p["total_price"] for p in products)
    }
    return common_data

def introduce_error_to_data(data, error_type):
    """데이터에 의도적인 오류를 주입하는 함수"""
    modified_data = data.copy()
    
    if error_type == 'price_mismatch':
        # 무작위 제품의 가격을 5-15% 변경
        product_idx = random.randint(0, len(modified_data["products"]) - 1)
        modified_data["products"][product_idx]["unit_price"] *= random.uniform(1.05, 1.15)
        modified_data["products"][product_idx]["total_price"] = (
            modified_data["products"][product_idx]["unit_price"] * 
            modified_data["products"][product_idx]["total_qty"]
        )
        modified_data["total_price"] = sum(p["total_price"] for p in modified_data["products"])
    
    elif error_type == 'quantity_mismatch':
        # 무작위 제품의 특정 사이즈 수량 변경
        product_idx = random.randint(0, len(modified_data["products"]) - 1)
        size_keys = list(modified_data["products"][product_idx]["sizes"].keys())
        size_key = random.choice(size_keys)
        
        # 오더시트 수량만 변경
        old_qty = modified_data["products"][product_idx]["sizes"][size_key]
        new_qty = old_qty + random.choice([-2, -1, 1, 2])
        if new_qty < 0:
            new_qty = 0
        
        # 총 수량 조정
        qty_diff = new_qty - old_qty
        modified_data["products"][product_idx]["sizes"][size_key] = new_qty
        modified_data["products"][product_idx]["total_qty"] += qty_diff
        modified_data["products"][product_idx]["total_price"] = (
            modified_data["products"][product_idx]["unit_price"] * 
            modified_data["products"][product_idx]["total_qty"]
        )
        modified_data["total_quantity"] = sum(p["total_qty"] for p in modified_data["products"])
        modified_data["total_price"] = sum(p["total_price"] for p in modified_data["products"])
    
    elif error_type == 'product_code_mismatch':
        # 무작위 제품의 스타일 코드 변경
        product_idx = random.randint(0, len(modified_data["products"]) - 1)
        new_style = generate_random_style()
        modified_data["products"][product_idx]["style_code1"] = new_style[0]
        modified_data["products"][product_idx]["style_code"] = new_style[0] + modified_data["products"][product_idx]["style_code2"]
    
    elif error_type == 'brand_mismatch':
        # 브랜드명 변경
        current_brand = modified_data["brand"]
        available_brands = [b for b in brand_list if b != current_brand]
        modified_data["brand"] = random.choice(available_brands)
    
    elif error_type == 'date_mismatch':
        # 날짜 변경
        new_date_str, new_date_obj = get_random_date()
        modified_data["date"] = new_date_str
        modified_data["date_obj"] = new_date_obj
    
    return modified_data

# ===== PDF 변환 및 이미지 처리 함수 =====
def transform_coordinates(data_json, img_size):
    """JSON 좌표를 이미지 크기에 맞게 변환하는 함수"""
    image_width, image_height = img_size
    
    def transform_x(x):
        doc_start_x = data_json["document_bounds"]["start_x"]
        doc_end_x = data_json["document_bounds"]["end_x"]
        doc_width = doc_end_x - doc_start_x
        relative_x = (x - doc_start_x) / doc_width
        return int(relative_x * image_width)
    
    def transform_y(y):
        doc_start_y = data_json["document_bounds"]["start_y"]
        doc_end_y = data_json["document_bounds"]["end_y"]
        doc_height = doc_end_y - doc_start_y
        relative_y = (y - doc_start_y) / doc_height
        return int(relative_y * image_height)
    
    def transform_width(width):
        doc_start_x = data_json["document_bounds"]["start_x"]
        doc_end_x = data_json["document_bounds"]["end_x"]
        doc_width = doc_end_x - doc_start_x
        relative_width = width / doc_width
        return int(relative_width * image_width)
    
    def transform_height(height):
        doc_start_y = data_json["document_bounds"]["start_y"]
        doc_end_y = data_json["document_bounds"]["end_y"]
        doc_height = doc_end_y - doc_start_y
        relative_height = height / doc_height
        return int(relative_height * image_height)
    
    return {
        "transform_x": transform_x,
        "transform_y": transform_y,
        "transform_width": transform_width,
        "transform_height": transform_height
    }

def load_fonts():
    """폰트 로드 함수"""
    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZE)
        font_large = ImageFont.truetype("arial.ttf", FONT_SIZE_LARGE)
        font_brand = ImageFont.truetype("arial.ttf", BRAND_BOX_FONT_SIZE)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        # 폰트를 찾을 수 없을 경우 기본 폰트 사용
        font = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_brand = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    return {
        "font": font,
        "font_large": font_large,
        "font_brand": font_brand,
        "font_small": font_small
    }

def generate_invoice(common_data, json_file, pdf_file, output_path):
    """인보이스 PDF 생성 함수"""
    # JSON 데이터 로드
    try:
        with open(json_file, "r") as f:
            invoice_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"인보이스 JSON 로드 오류: {e}")
        return False
    
    # PDF 변환
    try:
        images = convert_from_path(pdf_file, dpi=300)
        img = images[0]
        draw = ImageDraw.Draw(img)
    except Exception as e:
        print(f"인보이스 PDF 변환 오류: {e}")
        return False
    
    # 이미지 크기
    image_size = img.size
    
    # 좌표 변환 함수
    transform = transform_coordinates(invoice_data, image_size)
    
    # 폰트 로드
    fonts = load_fonts()
    
    # ===== 배송 날짜 처리 =====
    # 시작일
    start_date = invoice_data["shipping_dates"]["start_date"]
    start_x = transform["transform_x"](start_date["x"])
    start_y = transform["transform_y"](start_date["y"])
    start_width = transform["transform_width"](start_date["width"])
    start_height = transform["transform_height"](start_date["height"])
    
    draw.rectangle((start_x, start_y, start_x + start_width, start_y + start_height),
                  fill="white", outline="white", width=2)
    draw.text((start_x + TEXT_OFFSET_X, start_y + TEXT_OFFSET_Y),
              common_data["ship_start"], fill="black", font=fonts["font"])
    
    # 완료일
    end_date = invoice_data["shipping_dates"]["end_date"]
    end_x = transform["transform_x"](end_date["x"])
    end_y = transform["transform_y"](end_date["y"])
    end_width = transform["transform_width"](end_date["width"])
    end_height = transform["transform_height"](end_date["height"])
    
    draw.rectangle((end_x, end_y, end_x + end_width, end_y + end_height),
                  fill="white", outline="white", width=2)
    draw.text((end_x + TEXT_OFFSET_X, end_y + TEXT_OFFSET_Y),
              common_data["ship_end"], fill="black", font=fonts["font"])
    
    # ===== 제품 정보 처리 =====
    total_quantity = 0
    total_price = 0
    
    for idx, product in enumerate(common_data["products"]):
        if idx >= len(invoice_data["products"]):
            break  # JSON에 정의된 제품 수보다 많으면 중단
            
        invoice_product = invoice_data["products"][idx]
        
        # 제품명 표시
        name_info = invoice_product["name"]
        name_x = transform["transform_x"](name_info["x"])
        name_y = transform["transform_y"](name_info["y"])
        name_width = transform["transform_width"](name_info["width"])
        name_height = transform["transform_height"](name_info["height"])
        
        draw.rectangle((name_x, name_y, name_x + name_width, name_y + name_height),
                      fill="white", outline="white", width=2)
        draw.text((name_x + TEXT_OFFSET_X, name_y + TEXT_OFFSET_Y),
                  product["model_name"], fill="black", font=fonts["font"])
        
        # 스타일 코드 표시
        style_info = invoice_product["style_code"]
        style_x = transform["transform_x"](style_info["x"])
        style_y = transform["transform_y"](style_info["y"])
        style_width = transform["transform_width"](style_info["width"])
        style_height = transform["transform_height"](style_info["height"])
        
        draw.rectangle((style_x, style_y, style_x + style_width, style_y + style_height),
                      fill="white", outline="white", width=2)
        draw.text((style_x + TEXT_OFFSET_X, style_y + TEXT_OFFSET_Y),
                  product["style_code"], fill="black", font=fonts["font_small"])
        
        # 브랜드 표시
        brand_info = invoice_product["brand"]
        brand_x = transform["transform_x"](brand_info["x"])
        brand_y = transform["transform_y"](brand_info["y"])
        brand_width = transform["transform_width"](brand_info["width"])
        brand_height = transform["transform_height"](brand_info["height"])
        
        draw.rectangle((brand_x, brand_y, brand_x + brand_width, brand_y + brand_height),
                      fill="white", outline="white", width=2)
        draw.text((brand_x + TEXT_OFFSET_X, brand_y + TEXT_OFFSET_Y),
                  common_data["brand"], fill="black", font=fonts["font_small"])
        
        # 시즌 표시
        season_info = invoice_product["season"]
        season_x = transform["transform_x"](season_info["x"])
        season_y = transform["transform_y"](season_info["y"])
        season_width = transform["transform_width"](season_info["width"])
        season_height = transform["transform_height"](season_info["height"])
        
        draw.rectangle((season_x, season_y, season_x + season_width, season_y + season_height),
                      fill="white", outline="white", width=2)
        draw.text((season_x + TEXT_OFFSET_X, season_y + TEXT_OFFSET_Y),
                  common_data["season"], fill="black", font=fonts["font_small"])
        
        # 색상 표시
        color_info = invoice_product["color"]
        color_x = transform["transform_x"](color_info["x"])
        color_y = transform["transform_y"](color_info["y"])
        color_width = transform["transform_width"](color_info["width"])
        color_height = transform["transform_height"](color_info["height"])
        
        draw.rectangle((color_x, color_y, color_x + color_width, color_y + color_height),
                      fill="white", outline="white", width=2)
        draw.text((color_x + TEXT_OFFSET_X, color_y + TEXT_OFFSET_Y),
                  product["color_material"], fill="black", font=fonts["font_small"])
        
        # Wholesale 가격 표시
        wholesale_info = invoice_product["wholesale_price"]
        wholesale_x = transform["transform_x"](wholesale_info["x"])
        wholesale_y = transform["transform_y"](wholesale_info["y"])
        wholesale_width = transform["transform_width"](wholesale_info["width"])
        wholesale_height = transform["transform_height"](wholesale_info["height"])
        
        draw.rectangle((wholesale_x, wholesale_y, wholesale_x + wholesale_width, wholesale_y + wholesale_height),
                      fill="white", outline="white", width=2)
        draw.text((wholesale_x + TEXT_OFFSET_X, wholesale_y + TEXT_OFFSET_Y),
                  f"EUR {product['unit_price']:.2f}", fill="black", font=fonts["font"])
        
        # Retail 가격 표시
        retail_info = invoice_product["retail_price"]
        retail_x = transform["transform_x"](retail_info["x"])
        retail_y = transform["transform_y"](retail_info["y"])
        retail_width = transform["transform_width"](retail_info["width"])
        retail_height = transform["transform_height"](retail_info["height"])
        
        draw.rectangle((retail_x, retail_y, retail_x + retail_width, retail_y + retail_height),
                      fill="white", outline="white", width=2)
        draw.text((retail_x + TEXT_OFFSET_X, retail_y + TEXT_OFFSET_Y),
                  f"EUR {product['retail_price']:.2f}", fill="black", font=fonts["font"])
        
        # 사이즈별 수량 처리
        qty_total = 0
        for size, size_info in invoice_product["sizes"].items():
            if size == "qty":  # qty는 건너뛰기 (나중에 계산된 값으로 채움)
                continue

            size_x = transform["transform_x"](size_info["x"])
            size_y = transform["transform_y"](size_info["y"])
            size_width = transform["transform_width"](size_info["width"])
            size_height = transform["transform_height"](size_info["height"])

            # 사이즈별 수량 가져오기
            quantity = product["sizes_invoice"].get(size, 0)
            if quantity > 0:  # 0보다 큰 경우만 총량에 추가
                qty_total += quantity

            draw.rectangle((size_x, size_y, size_x + size_width, size_y + size_height),
                        fill="white")

            # 0인 경우 공백으로 표시, 그렇지 않으면 숫자 표시
            quantity_text = "" if quantity == 0 else str(quantity)
            draw.text((size_x + 5, size_y + 5),
                    quantity_text, fill="black", font=fonts["font"])
        
        # 수량 합계 표시
        qty_info = invoice_product["sizes"]["qty"]
        qty_x = transform["transform_x"](qty_info["x"])
        qty_y = transform["transform_y"](qty_info["y"])
        qty_width = transform["transform_width"](qty_info["width"])
        qty_height = transform["transform_height"](qty_info["height"])
        
        draw.rectangle((qty_x, qty_y, qty_x + qty_width, qty_y + qty_height),
                      fill="white")
        draw.text((qty_x + 5, qty_y + 5),
                  str(qty_total), fill="black", font=fonts["font"])
        
        # 제품별 총액 표시
        product_total = product["unit_price"] * qty_total
        total_quantity += qty_total
        total_price += product_total
        
        total_price_info = invoice_product["total_price"]
        total_price_x = transform["transform_x"](total_price_info["x"])
        total_price_y = transform["transform_y"](total_price_info["y"])
        total_price_width = transform["transform_width"](total_price_info["width"])
        total_price_height = transform["transform_height"](total_price_info["height"])
        
        draw.rectangle((total_price_x, total_price_y, 
                        total_price_x + total_price_width, total_price_y + total_price_height),
                      fill="white", outline="white", width=2)
        draw.text((total_price_x + 5, total_price_y + 5),
                  f"     {product_total:.2f}", fill="black", font=fonts["font"])
    
    # ===== 요약 정보 처리 =====
    # 총 수량
    total_qty_info = invoice_data["summary"]["total_quantity"]
    total_qty_x = transform["transform_x"](total_qty_info["x"])
    total_qty_y = transform["transform_y"](total_qty_info["y"])
    total_qty_width = transform["transform_width"](total_qty_info["width"])
    total_qty_height = transform["transform_height"](total_qty_info["height"])
    
    draw.rectangle((total_qty_x, total_qty_y, 
                    total_qty_x + total_qty_width, total_qty_y + total_qty_height),
                  fill="white")
    draw.text((total_qty_x + 5, total_qty_y + 5),
              str(total_quantity), fill="black", font=fonts["font_large"])
    
    # Total 금액
    total_info = invoice_data["summary"]["total"]
    total_x = transform["transform_x"](total_info["x"])
    total_y = transform["transform_y"](total_info["y"])
    total_width = transform["transform_width"](total_info["width"])
    total_height = transform["transform_height"](total_info["height"])
    
    draw.rectangle((total_x, total_y, total_x + total_width, total_y + total_height),
                  fill="white", outline="white", width=2)
    draw.text((total_x + 5, total_y + 5),
              f"EUR {total_price:.2f}", fill="black", font=fonts["font_large"])
    
    # Grand Total 금액 (일반적으로 Total과 동일)
    grand_total_info = invoice_data["summary"]["grand_total"]
    grand_total_x = transform["transform_x"](grand_total_info["x"])
    grand_total_y = transform["transform_y"](grand_total_info["y"])
    grand_total_width = transform["transform_width"](grand_total_info["width"])
    grand_total_height = transform["transform_height"](grand_total_info["height"])
    
    draw.rectangle((grand_total_x, grand_total_y, 
                    grand_total_x + grand_total_width, grand_total_y + grand_total_height),
                  fill="white", outline="white", width=2)
    draw.text((grand_total_x + 5, grand_total_y + 5),
              f"EUR {total_price:.2f}", fill="black", font=fonts["font_large"])
    
    # 결과 저장
    img.save(output_path)

def generate_order(common_data, json_file, pdf_file, output_path):
    """오더시트 PDF 생성 함수"""
    # JSON 데이터 로드
    try:
        with open(json_file, "r") as f:
            order_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"오더시트 JSON 로드 오류: {e}")
        return False
    
    # PDF 변환
    try:
        images = convert_from_path(pdf_file, dpi=300)
        img = images[0]
        draw = ImageDraw.Draw(img)
    except Exception as e:
        print(f"오더시트 PDF 변환 오류: {e}")
        return False
    
    # 이미지 크기
    image_size = img.size
    
    # 좌표 변환 함수
    transform = transform_coordinates(order_data, image_size)
    
    # 폰트 로드
    fonts = load_fonts()
    
    # ===== 날짜/시즌/브랜드 정보 =====
    # 날짜 영역
    date_info = order_data["header_fields"]["date"]
    date_x = transform["transform_x"](date_info["x"])
    date_y = transform["transform_y"](date_info["y"])
    date_width = transform["transform_width"](date_info["width"])
    date_height = transform["transform_height"](date_info["height"])
    
    draw.rectangle((date_x, date_y, date_x + date_width, date_y + date_height),
                  fill="white", outline="white", width=2)
    draw.text((date_x + TEXT_OFFSET_X, date_y + TEXT_OFFSET_Y),
              common_data["date"], fill="black", font=fonts["font_large"])
    
    # 시즌 영역
    season_info = order_data["header_fields"]["season"]
    season_x = transform["transform_x"](season_info["x"])
    season_y = transform["transform_y"](season_info["y"])
    season_width = transform["transform_width"](season_info["width"])
    season_height = transform["transform_height"](season_info["height"])
    
    draw.rectangle((season_x, season_y, season_x + season_width, season_y + season_height),
                  fill="white", outline="white", width=2)
    draw.text((season_x + TEXT_OFFSET_X, season_y + TEXT_OFFSET_Y),
              common_data["season"], fill="black", font=fonts["font_large"])
    
    # 브랜드 영역
    brand_info = order_data["header_fields"]["brand"]
    brand_x = transform["transform_x"](brand_info["x"])
    brand_y = transform["transform_y"](brand_info["y"])
    brand_width = transform["transform_width"](brand_info["width"])
    brand_height = transform["transform_height"](brand_info["height"])
    
    draw.rectangle((brand_x, brand_y, brand_x + brand_width, brand_y + brand_height),
                  fill="white", outline="white", width=2)
    draw.text((brand_x + TEXT_OFFSET_X, brand_y + TEXT_OFFSET_Y),
              common_data["brand"], fill="black", font=fonts["font_brand"])
    
    # ===== 제품 정보 처리 =====
    # 6x5 행렬 초기화 (4개 제품 행 + 1개 합계 행, 사이즈 열 6개)
    matrix = [[0 for _ in range(6)] for _ in range(5)]
    
    # 각 제품 행 처리
    for row_idx, product in enumerate(common_data["products"]):
        if row_idx >= len(order_data["product_rows"]):
            break  # JSON에 정의된 제품 수보다 많으면 중단
            
        product_row = order_data["product_rows"][row_idx]
        
        # ITEM CODE 처리
        item_code_info = product_row["item_code"]
        item_x = transform["transform_x"](item_code_info["x"])
        item_y = transform["transform_y"](item_code_info["y"])
        item_width = transform["transform_width"](item_code_info["width"])
        item_height = transform["transform_height"](item_code_info["height"])
        
        # ITEM 박스 덮어쓰기
        draw.rectangle((item_x, item_y, item_x + item_width, item_y + item_height), 
                       fill="white", outline="white", width=2)
        draw.text((item_x + TEXT_OFFSET_X, item_y + TEXT_OFFSET_Y), 
                  product["style_code1"], fill="black", font=fonts["font"])
        draw.text((item_x + TEXT_OFFSET_X, item_y + TEXT_OFFSET_Y + LINE_SPACING), 
                  product["style_code2"], fill="black", font=fonts["font"])
        
        # MODEL 처리
        model_info = product_row["model"]
        model_x = transform["transform_x"](model_info["x"])
        model_y = transform["transform_y"](model_info["y"])
        model_width = transform["transform_width"](model_info["width"])
        model_height = transform["transform_height"](model_info["height"])
        
        draw.rectangle((model_x, model_y, model_x + model_width, model_y + model_height), 
                       fill="white", outline="white", width=2)
        
        parts = product["model_name"].split(" ", 2)
        line1 = " ".join(parts[:2]) if len(parts) > 2 else product["model_name"]
        line2 = parts[2] if len(parts) > 2 else ""
        draw.text((model_x + TEXT_OFFSET_X, model_y + TEXT_OFFSET_Y), 
                  line1, fill="black", font=fonts["font"])
        draw.text((model_x + TEXT_OFFSET_X, model_y + TEXT_OFFSET_Y + LINE_SPACING), 
                  line2, fill="black", font=fonts["font"])
        
        # UNIT PRICE 처리
        price_info = product_row["unit_price"]
        price_x = transform["transform_x"](price_info["x"])
        price_y = transform["transform_y"](price_info["y"])
        price_width = transform["transform_width"](price_info["width"])
        price_height = transform["transform_height"](price_info["height"])
        
        draw.rectangle((price_x, price_y, price_x + price_width, price_y + price_height), 
                       fill="white", outline="white", width=2)
        draw.text((price_x + TEXT_OFFSET_X, price_y + TEXT_OFFSET_Y), 
                  f"{product['unit_price']:.2f}", fill="black", font=fonts["font"])
        
        # DISC PRCNT 처리
        disc_info = product_row["disc_prcnt"]
        disc_x = transform["transform_x"](disc_info["x"])
        disc_y = transform["transform_y"](disc_info["y"])
        disc_width = transform["transform_width"](disc_info["width"])
        disc_height = transform["transform_height"](disc_info["height"])
        
        draw.rectangle((disc_x, disc_y, disc_x + disc_width, disc_y + disc_height), 
                       fill="white", outline="white", width=2)
        draw.text((disc_x + TEXT_OFFSET_X, disc_y + TEXT_OFFSET_Y), 
                  "0.00%", fill="black", font=fonts["font"])
        
        # SHIPPING WINDOW 처리 (시작일)
        ship_start_info = product_row["shipping_start"]
        ship_start_x = transform["transform_x"](ship_start_info["x"])
        ship_start_y = transform["transform_y"](ship_start_info["y"])
        ship_start_width = transform["transform_width"](ship_start_info["width"])
        ship_start_height = transform["transform_height"](ship_start_info["height"])
        
        draw.rectangle((ship_start_x, ship_start_y, 
                        ship_start_x + ship_start_width, ship_start_y + ship_start_height), 
                       fill="white", outline="white", width=2)
        draw.text((ship_start_x + TEXT_OFFSET_X, ship_start_y + TEXT_OFFSET_Y), 
                  common_data["ship_start"], fill="black", font=fonts["font"])
        
        # SHIPPING WINDOW 처리 (종료일)
        ship_end_info = product_row["shipping_end"]
        ship_end_x = transform["transform_x"](ship_end_info["x"])
        ship_end_y = transform["transform_y"](ship_end_info["y"])
        ship_end_width = transform["transform_width"](ship_end_info["width"])
        ship_end_height = transform["transform_height"](ship_end_info["height"])
        
        draw.rectangle((ship_end_x, ship_end_y, 
                        ship_end_x + ship_end_width, ship_end_y + ship_end_height), 
                       fill="white", outline="white", width=2)
        draw.text((ship_end_x + TEXT_OFFSET_X, ship_end_y + TEXT_OFFSET_Y), 
                  common_data["ship_end"], fill="black", font=fonts["font"])
        
        # 사이즈별 수량의 합계 계산을 위한 변수
        row_total = 0
        
        # 각 사이즈별 수량 처리
        for size_idx, (size_name, size_info) in enumerate(product_row["sizes"].items()):
            if size_name == "total":  # 합계 열은 건너뛰기
                continue
                
            size_x = transform["transform_x"](size_info["x"])
            size_y = transform["transform_y"](size_info["y"])
            size_width = transform["transform_width"](size_info["width"])
            size_height = transform["transform_height"](size_info["height"])
            
            # 사이즈별 수량 가져오기
            quantity = product["sizes"].get(size_name, 0)
            
            # 행렬에 저장
            if size_name == "390":
                matrix[row_idx][0] = quantity
            elif size_name == "400":
                matrix[row_idx][1] = quantity
            elif size_name == "410":
                matrix[row_idx][2] = quantity
            elif size_name == "420":
                matrix[row_idx][3] = quantity
            elif size_name == "430":
                matrix[row_idx][4] = quantity
            elif size_name == "440":
                matrix[row_idx][5] = quantity
            
            # 0보다 큰 경우만 행 합계에 추가
            if quantity > 0:
                row_total += quantity
            
            # 수량 표시
            draw.rectangle((size_x, size_y, size_x + size_width, size_y + size_height), 
                           fill="white")
            
            # 0인 경우 공백으로 표시, 그렇지 않으면 숫자 표시
            quantity_text = "" if quantity == 0 else str(quantity)
            draw.text((size_x + 5, size_y + 5), 
                      quantity_text, fill="black", font=fonts["font"])
        
        # 행 합계 표시
        row_total_info = product_row["sizes"]["total"]
        row_total_x = transform["transform_x"](row_total_info["x"])
        row_total_y = transform["transform_y"](row_total_info["y"])
        row_total_width = transform["transform_width"](row_total_info["width"])
        row_total_height = transform["transform_height"](row_total_info["height"])
        
        draw.rectangle((row_total_x, row_total_y, 
                        row_total_x + row_total_width, row_total_y + row_total_height), 
                       fill="white")
        draw.text((row_total_x + 5, row_total_y + 5), 
                  str(row_total), fill="black", font=fonts["font"])
        
        # TOTAL PRICE 처리
        total_price_info = product_row["total_price"]
        total_price_x = transform["transform_x"](total_price_info["x"])
        total_price_y = transform["transform_y"](total_price_info["y"])
        total_price_width = transform["transform_width"](total_price_info["width"])
        total_price_height = transform["transform_height"](total_price_info["height"])
        
        # 총 가격 계산 및 표시
        total_price = product["unit_price"] * row_total
        
        draw.rectangle((total_price_x, total_price_y, 
                        total_price_x + total_price_width, total_price_y + total_price_height), 
                       fill="white", outline="white", width=2)
        draw.text((total_price_x + TEXT_OFFSET_X, total_price_y + TEXT_OFFSET_Y), 
                  f"{total_price:.2f}", fill="black", font=fonts["font"])
    
    # ===== 총합계 행 처리 =====
    # 각 열의 합계 계산
    col_totals = [0] * 6  # 6개 사이즈에 맞게 수정
    for col_idx in range(6):  # 6개 열 처리
        for row_idx in range(len(common_data["products"])):
            if row_idx < len(matrix):
                col_totals[col_idx] += matrix[row_idx][col_idx]
    
    # 총합계 계산
    grand_total = sum(col_totals)
    
    # 각 열의 합계 표시
    for size_idx, (size_name, size_info) in enumerate(order_data["total_row"]["sizes"].items()):
        if size_name == "total":  # 총합계
            total_x = transform["transform_x"](size_info["x"])
            total_y = transform["transform_y"](size_info["y"])
            total_width = transform["transform_width"](size_info["width"])
            total_height = transform["transform_height"](size_info["height"])
            
            draw.rectangle((total_x, total_y, total_x + total_width, total_y + total_height), 
                          fill="white")
            draw.text((total_x + 5, total_y + 5), 
                      str(grand_total), fill="black", font=fonts["font"])
        elif size_name in ["390", "400", "410", "420", "430", "440"]:
            # 각 열의 합계
            size_list = ["390", "400", "410", "420", "430", "440"]
            col_idx = size_list.index(size_name)
            col_total = col_totals[col_idx] if col_idx < len(col_totals) else 0
            
            col_x = transform["transform_x"](size_info["x"])
            col_y = transform["transform_y"](size_info["y"])
            col_width = transform["transform_width"](size_info["width"])
            col_height = transform["transform_height"](size_info["height"])
            
            draw.rectangle((col_x, col_y, col_x + col_width, col_y + col_height), 
                          fill="white")
            draw.text((col_x + 5, col_y + 5), 
                      str(col_total), fill="black", font=fonts["font"])
    
    # 결과 저장
    img.save(output_path)
    return True

def convert_to_pdf(image_path, pdf_path):
    """이미지를 PDF로 변환하는 함수"""
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_path))
        return True
    except Exception as e:
        print(f"PDF 변환 오류: {e}")
        return False

def generate_error_log(index, error_type):
    """오류 정보를 저장하는 함수"""
    return {
        "index": index,
        "error_type": error_type
    }

def main():
    """메인 함수"""
    # 설정값
    NUM_SAMPLES = 500
    ERROR_RATE = 0.2  # 20%의 데이터에 오류 포함
    
    error_logs = []
    
    # 각 샘플 생성
    for i in range(1, NUM_SAMPLES + 1):
        print(f"생성 중: {i}/{NUM_SAMPLES}")
        
        # 로그에 표시할 파일명
        invoice_filename = f"invoice_{i}"
        order_filename = f"order_confirmation_{i}"
        
        # 출력 경로
        invoice_img_path = os.path.join(OUTPUT_DIR, f"{invoice_filename}.jpg")
        invoice_pdf_path = os.path.join(OUTPUT_DIR, f"{invoice_filename}.pdf")
        order_img_path = os.path.join(OUTPUT_DIR, f"{order_filename}.jpg")
        order_pdf_path = os.path.join(OUTPUT_DIR, f"{order_filename}.pdf")
        
        # 공통 데이터 생성
        common_data = generate_common_data()
        
        # 20%의 확률로 오류 데이터 생성
        introduce_error = (random.random() < ERROR_RATE)
        
        if introduce_error:
            # 오류 유형을 무작위로 선택
            error_type = random.choice([
                'price_mismatch',         # 가격 불일치
                'quantity_mismatch',      # 수량 불일치
                'product_code_mismatch',  # 제품 코드 불일치
                'brand_mismatch',         # 브랜드명 불일치
                'date_mismatch'           # 날짜 불일치
            ])
            
            # 오류 유형에 따라 데이터 수정
            modified_data = introduce_error_to_data(common_data, error_type)
            
            # 오류 로그 기록
            error_logs.append(generate_error_log(i, error_type))
            
            # 오류가 포함된 문서 생성
            generate_invoice(modified_data, INVOICE_DATA_JSON, INVOICE_PDF_PATH, invoice_img_path)
            generate_order(common_data, ORDER_DATA_JSON, ORDER_PDF_PATH, order_img_path)
            
            print(f"생성 완료(오류 포함): {i}/{NUM_SAMPLES} - 오류 유형: {error_type}")
        else:
            # 정상 문서 생성
            generate_invoice(common_data, INVOICE_DATA_JSON, INVOICE_PDF_PATH, invoice_img_path)
            generate_order(common_data, ORDER_DATA_JSON, ORDER_PDF_PATH, order_img_path)
            
            print(f"생성 완료(정상): {i}/{NUM_SAMPLES}")
        
        # 이미지를 PDF로 변환
        convert_to_pdf(invoice_img_path, invoice_pdf_path)
        convert_to_pdf(order_img_path, order_pdf_path)
    
    # 오류 로그 저장
    error_log_path = os.path.join(OUTPUT_DIR, "error_log.json")
    with open(error_log_path, "w", encoding="utf-8") as f:
        json.dump(error_logs, f, indent=2)
    
    print(f"\n✅ 생성 완료: 총 {NUM_SAMPLES}개 (정상: {NUM_SAMPLES - len(error_logs)}개, 오류: {len(error_logs)}개)")
    print(f"결과는 {OUTPUT_DIR} 폴더에 저장되었습니다.")
    print(f"오류 로그: {error_log_path}")

if __name__ == "__main__":
    main()