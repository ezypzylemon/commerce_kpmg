import os
import logging
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from .services.ocr_service import OCRProcessor
from .models import db, Invoice, InvoiceItem, Order, OrderItem

# 라우트 블루프린트 생성
orders_bp = Blueprint('orders', __name__)

# 서비스 초기화
ocr_processor = OCRProcessor()

# 파일 업로드 설정
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'temporary')
PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'processed')

# 폴더 생성 (존재하지 않는 경우)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    """파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@orders_bp.route('/upload', methods=['POST'])
def upload_document():
    """문서 업로드 및 OCR 처리 엔드포인트"""
    try:
        # 파일이 없는 경우 처리
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다.'}), 400
        
        file = request.files['file']
        
        # 파일명이 비어있는 경우 처리
        if file.filename == '':
            return jsonify({'error': '선택된 파일이 없습니다.'}), 400
        
        # 파일 확장자 검증
        if file and allowed_file(file.filename):
            # 안전한 파일명 생성
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # 문서 유형 정보 가져오기
            doc_type = request.form.get('docType', '')
            if not doc_type or doc_type not in ['invoice', 'order']:
                return jsonify({'error': '올바른 문서 유형을 선택해주세요.'}), 400
            
            # 처리 방식 결정
            processing_method = "standard"
            if doc_type == "invoice":
                processing_method = "invoice_json"
            elif doc_type == "order":
                processing_method = "order_json"
            
            # OCR 처리
            try:
                # 선택된 방식으로 PDF 처리
                df_result, output_excel = ocr_processor.process_pdf(
                    filepath, 
                    output_dir=PROCESSED_FOLDER,
                    processing_method=processing_method,
                    verbose=False
                )
                
                if output_excel:
                    # 브랜드와 시즌 정보 가져오기
                    brand = request.form.get('brand', '자동 감지')
                    season = request.form.get('season', '')
                    
                    # 총 수량 계산
                    total_quantity = len(df_result) if not df_result.empty else 0
                    
                    # 문서 ID 생성 (prefix_number 형식)
                    if doc_type == 'invoice':
                        # 가장 큰 인보이스 ID 번호 가져오기
                        latest_invoice = Invoice.query.order_by(db.func.substr(Invoice.id, 6).desc()).first()
                        if latest_invoice and latest_invoice.id.startswith('invo_'):
                            try:
                                last_num = int(latest_invoice.id.split('_')[1])
                                doc_id = f"invo_{last_num + 1}"
                            except:
                                doc_id = f"invo_1"
                        else:
                            doc_id = "invo_1"
                        
                        # 인보이스 레코드 생성
                        invoice = Invoice(
                            id=doc_id,
                            filename=filename,
                            brand=brand,
                            season=season,
                            total_amount="",  # 나중에 계산
                            total_quantity=total_quantity,
                            excel_filename=os.path.basename(output_excel)
                        )
                        db.session.add(invoice)
                        
                        # 품목 레코드 생성
                        if not df_result.empty:
                            total_amount_value = 0
                            
                            for _, row in df_result.iterrows():
                                # 품목 정보 추출
                                model_code = row.get('모델코드', row.get('model', ''))
                                model_name = row.get('모델명', row.get('full_model', ''))
                                color = row.get('컬러', row.get('color', ''))
                                wholesale_price = row.get('구매가', row.get('wholesale_price', ''))
                                retail_price = row.get('판매가', row.get('retail_price', ''))
                                total_item_price = row.get('총_금액', row.get('total_price', ''))
                                
                                # 사이즈별 수량 추출
                                size_39 = int(row.get('사이즈_39', row.get('size_39', 0)) or 0)
                                size_40 = int(row.get('사이즈_40', row.get('size_40', 0)) or 0)
                                size_41 = int(row.get('사이즈_41', row.get('size_41', 0)) or 0)
                                size_42 = int(row.get('사이즈_42', row.get('size_42', 0)) or 0)
                                size_43 = int(row.get('사이즈_43', row.get('size_43', 0)) or 0)
                                size_44 = int(row.get('사이즈_44', row.get('size_44', 0)) or 0)
                                size_45 = int(row.get('사이즈_45', row.get('size_45', 0)) or 0)
                                size_46 = int(row.get('사이즈_46', row.get('size_46', 0)) or 0)
                                
                                # 총 수량 계산
                                item_quantity = size_39 + size_40 + size_41 + size_42 + size_43 + size_44 + size_45 + size_46
                                if not item_quantity and '총_수량' in row:
                                    item_quantity = int(row['총_수량'])
                                
                                # 품목 레코드 생성
                                item = InvoiceItem(
                                    invoice_id=doc_id,
                                    model_code=model_code,
                                    model_name=model_name,
                                    color=color,
                                    wholesale_price=wholesale_price,
                                    retail_price=retail_price,
                                    quantity=item_quantity,
                                    total_price=total_item_price,
                                    size_39=size_39,
                                    size_40=size_40,
                                    size_41=size_41,
                                    size_42=size_42,
                                    size_43=size_43,
                                    size_44=size_44,
                                    size_45=size_45,
                                    size_46=size_46
                                )
                                db.session.add(item)
                                
                                # 총액 계산
                                try:
                                    price_str = total_item_price.replace('EUR', '').replace('$', '').strip()
                                    total_amount_value += float(price_str)
                                except:
                                    pass
                            
                            # 인보이스 총액 업데이트
                            invoice.total_amount = f"EUR {total_amount_value:.2f}"
                    
                    else:  # 오더시트(order) 처리
                        # 가장 큰 오더 ID 번호 가져오기
                        latest_order = Order.query.order_by(db.func.substr(Order.id, 7).desc()).first()
                        if latest_order and latest_order.id.startswith('order_'):
                            try:
                                last_num = int(latest_order.id.split('_')[1])
                                doc_id = f"order_{last_num + 1}"
                            except:
                                doc_id = f"order_1"
                        else:
                            doc_id = "order_1"
                        
                        # 오더시트 레코드 생성
                        order = Order(
                            id=doc_id,
                            filename=filename,
                            brand=brand,
                            season=season,
                            total_amount="",  # 나중에 계산
                            total_quantity=total_quantity,
                            excel_filename=os.path.basename(output_excel)
                        )
                        db.session.add(order)
                        
                        # 품목 레코드 생성
                        if not df_result.empty:
                            total_amount_value = 0
                            
                            for _, row in df_result.iterrows():
                                # 품목 정보 추출
                                model_code = row.get('모델코드', row.get('model', ''))
                                model_name = row.get('모델명', row.get('full_model', ''))
                                color = row.get('컬러', row.get('color', ''))
                                wholesale_price = row.get('구매가', row.get('wholesale_price', ''))
                                total_item_price = row.get('총_금액', row.get('total_price', ''))
                                shipping_start = row.get('선적_시작일', row.get('shipping_start', ''))
                                shipping_end = row.get('선적_완료일', row.get('shipping_end', ''))
                                
                                # 사이즈별 수량 추출
                                size_39 = int(row.get('사이즈_39', row.get('size_39', 0)) or 0)
                                size_40 = int(row.get('사이즈_40', row.get('size_40', 0)) or 0)
                                size_41 = int(row.get('사이즈_41', row.get('size_41', 0)) or 0)
                                size_42 = int(row.get('사이즈_42', row.get('size_42', 0)) or 0)
                                size_43 = int(row.get('사이즈_43', row.get('size_43', 0)) or 0)
                                size_44 = int(row.get('사이즈_44', row.get('size_44', 0)) or 0)
                                size_45 = int(row.get('사이즈_45', row.get('size_45', 0)) or 0)
                                size_46 = int(row.get('사이즈_46', row.get('size_46', 0)) or 0)
                                
                                # 총 수량 계산
                                item_quantity = size_39 + size_40 + size_41 + size_42 + size_43 + size_44 + size_45 + size_46
                                if not item_quantity and '총_수량' in row:
                                    item_quantity = int(row['총_수량'])
                                
                                # 품목 레코드 생성
                                item = OrderItem(
                                    order_id=doc_id,
                                    model_code=model_code,
                                    model_name=model_name,
                                    color=color,
                                    wholesale_price=wholesale_price,
                                    quantity=item_quantity,
                                    total_price=total_item_price,
                                    shipping_start=shipping_start,
                                    shipping_end=shipping_end,
                                    size_39=size_39,
                                    size_40=size_40,
                                    size_41=size_41,
                                    size_42=size_42,
                                    size_43=size_43,
                                    size_44=size_44,
                                    size_45=size_45,
                                    size_46=size_46
                                )
                                db.session.add(item)
                                
                                # 총액 계산
                                try:
                                    price_str = total_item_price.replace('EUR', '').replace('$', '').strip()
                                    total_amount_value += float(price_str)
                                except:
                                    pass
                            
                            # 오더시트 총액 업데이트
                            order.total_amount = f"EUR {total_amount_value:.2f}"
                    
                    # 변경사항 저장
                    db.session.commit()
                    
                    # 응답 데이터 생성
                    response_data = {
                        'message': '문서 처리 완료',
                        'document_id': doc_id,
                        'document_type': doc_type,
                        'excel_filename': os.path.basename(output_excel),
                        'total_products': total_quantity,
                        'data_preview': df_result.head().to_dict(orient='records')
                    }
                    
                    return jsonify(response_data), 200
                else:
                    return jsonify({'error': '문서 처리 중 오류가 발생했습니다.'}), 500
            
            except Exception as e:
                return jsonify({'error': f'문서 처리 중 오류: {str(e)}'}), 500
        
        else:
            return jsonify({'error': '허용되지 않은 파일 형식입니다.'}), 400
    
    except Exception as e:
        return jsonify({'error': f'예상치 못한 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """처리된 엑셀 파일 다운로드"""
    try:
        filepath = os.path.join(PROCESSED_FOLDER, filename)
        
        if os.path.exists(filepath):
            return send_file(filepath, 
                             as_attachment=True, 
                             download_name=filename,
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    
    except Exception as e:
        return jsonify({'error': f'다운로드 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/documents/invoice', methods=['GET'])
def list_invoices():
    """인보이스 문서 목록 조회"""
    try:
        invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
        
        # 응답 데이터 생성
        invoice_list = []
        for invoice in invoices:
            invoice_list.append({
                'id': invoice.id,
                'filename': invoice.filename,
                'brand': invoice.brand,
                'season': invoice.season,
                'total_amount': invoice.total_amount,
                'total_quantity': invoice.total_quantity,
                'excel_filename': invoice.excel_filename,
                'created_at': invoice.created_at.isoformat(),
                'document_type': 'invoice'
            })
        
        return jsonify({
            'invoices': invoice_list,
            'total_count': len(invoice_list)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'인보이스 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/documents/order', methods=['GET'])
def list_orders():
    """오더시트 문서 목록 조회"""
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        
        # 응답 데이터 생성
        order_list = []
        for order in orders:
            order_list.append({
                'id': order.id,
                'filename': order.filename,
                'brand': order.brand,
                'season': order.season,
                'total_amount': order.total_amount,
                'total_quantity': order.total_quantity,
                'excel_filename': order.excel_filename,
                'created_at': order.created_at.isoformat(),
                'document_type': 'order'
            })
        
        return jsonify({
            'orders': order_list,
            'total_count': len(order_list)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'오더시트 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/document/<document_id>', methods=['GET'])
def get_document(document_id):
    """문서 상세 정보 조회"""
    try:
        # 문서 ID 접두사로 문서 유형 확인
        if document_id.startswith('invo_'):
            # 인보이스 조회
            invoice = Invoice.query.get(document_id)
            if not invoice:
                return jsonify({'error': '문서를 찾을 수 없습니다.'}), 404
            
            # 관련 품목 조회
            items = []
            for item in invoice.items:
                items.append({
                    'model_code': item.model_code,
                    'model_name': item.model_name,
                    'color': item.color,
                    'wholesale_price': item.wholesale_price,
                    'retail_price': item.retail_price,
                    'quantity': item.quantity,
                    'total_price': item.total_price,
                    'size_39': item.size_39,
                    'size_40': item.size_40,
                    'size_41': item.size_41,
                    'size_42': item.size_42,
                    'size_43': item.size_43,
                    'size_44': item.size_44,
                    'size_45': item.size_45,
                    'size_46': item.size_46
                })
            
            # 응답 데이터 생성
            document_data = {
                'id': invoice.id,
                'document_type': 'invoice',
                'filename': invoice.filename,
                'brand': invoice.brand,
                'season': invoice.season,
                'total_amount': invoice.total_amount,
                'total_quantity': invoice.total_quantity,
                'excel_filename': invoice.excel_filename,
                'created_at': invoice.created_at.isoformat(),
                'items': items
            }
            
            return jsonify(document_data), 200
        
        elif document_id.startswith('order_'):
            # 오더시트 조회
            order = Order.query.get(document_id)
            if not order:
                return jsonify({'error': '문서를 찾을 수 없습니다.'}), 404
            
            # 관련 품목 조회
            items = []
            for item in order.items:
                items.append({
                    'model_code': item.model_code,
                    'model_name': item.model_name,
                    'color': item.color,
                    'wholesale_price': item.wholesale_price,
                    'quantity': item.quantity,
                    'total_price': item.total_price,
                    'shipping_start': item.shipping_start,
                    'shipping_end': item.shipping_end,
                    'size_39': item.size_39,
                    'size_40': item.size_40,
                    'size_41': item.size_41,
                    'size_42': item.size_42,
                    'size_43': item.size_43,
                    'size_44': item.size_44,
                    'size_45': item.size_45,
                    'size_46': item.size_46
                })
            
            # 응답 데이터 생성
            document_data = {
                'id': order.id,
                'document_type': 'order',
                'filename': order.filename,
                'brand': order.brand,
                'season': order.season,
                'total_amount': order.total_amount,
                'total_quantity': order.total_quantity,
                'excel_filename': order.excel_filename,
                'created_at': order.created_at.isoformat(),
                'items': items
            }
            
            return jsonify(document_data), 200
        
        else:
            return jsonify({'error': '잘못된 문서 ID 형식입니다.'}), 400
    
    except Exception as e:
        return jsonify({'error': f'문서 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/compare/<doc1_id>/<doc2_id>', methods=['GET'])
def compare_documents(doc1_id, doc2_id):
    """두 문서 비교"""
    try:
        # 문서 ID 접두사로 문서 유형 확인
        doc1_type = 'invoice' if doc1_id.startswith('invo_') else 'order'
        doc2_type = 'invoice' if doc2_id.startswith('invo_') else 'order'
        
        # 문서 1 가져오기
        doc1 = None
        doc1_items = []
        if doc1_type == 'invoice':
            doc1 = Invoice.query.get(doc1_id)
            if doc1:
                doc1_items = InvoiceItem.query.filter_by(invoice_id=doc1_id).all()
        else:
            doc1 = Order.query.get(doc1_id)
            if doc1:
                doc1_items = OrderItem.query.filter_by(order_id=doc1_id).all()
        
        # 문서 2 가져오기
        doc2 = None
        doc2_items = []
        if doc2_type == 'invoice':
            doc2 = Invoice.query.get(doc2_id)
            if doc2:
                doc2_items = InvoiceItem.query.filter_by(invoice_id=doc2_id).all()
        else:
            doc2 = Order.query.get(doc2_id)
            if doc2:
                doc2_items = OrderItem.query.filter_by(order_id=doc2_id).all()
        
        # 문서 존재 확인
        if not doc1 or not doc2:
            return jsonify({'error': '비교할 문서를 찾을 수 없습니다.'}), 404
        
        # 문서 비교 결과 초기화
        comparison_result = {
            'document_types': {
                'doc1': doc1_type,
                'doc2': doc2_type
            },
            'matches': [],
            'mismatches': [],
            'summary': {
                'total_items': 0,
                'matched_items': 0,
                'mismatched_items': 0,
                'match_percentage': 0
            }
        }
        
        # 품목 정보 표준화
        doc1_products = []
        for item in doc1_items:
            product = {
                'model_code': item.model_code,
                'model_name': item.model_name,
                'color': item.color,
                'quantity': item.quantity,
                'wholesale_price': item.wholesale_price
            }
            
            # 사이즈별 수량 추가
            for size in range(39, 47):
                size_attr = f'size_{size}'
                if hasattr(item, size_attr):
                    product[f'사이즈_{size}'] = getattr(item, size_attr)
            
            doc1_products.append(product)
        
        doc2_products = []
        for item in doc2_items:
            product = {
                'model_code': item.model_code,
                'model_name': item.model_name,
                'color': item.color,
                'quantity': item.quantity,
                'wholesale_price': item.wholesale_price
            }
            
            # 사이즈별 수량 추가
            for size in range(39, 47):
                size_attr = f'size_{size}'
                if hasattr(item, size_attr):
                    product[f'사이즈_{size}'] = getattr(item, size_attr)
            
            doc2_products.append(product)
        
        # 제품 맵 생성 (강화된 표준화 로직 적용)
        import re
        
        def standardize_model_code(code):
            """모델 코드 표준화"""
            if not code:
                return ""
            # AJ 다음에 오는 숫자 추출 (예: AJ1323-BLACK -> AJ1323)
            match = re.search(r'(AJ\d+)', code)
            if match:
                return match.group(1).lower()
            return code.lower()
        
        def standardize_color(color):
            """색상 표준화"""
            if not color:
                return ""
            # 공백, 하이픈 제거하고 소문자로 변환
            return color.lower().replace(' ', '').replace('-', '').replace('_', '')
        
        def standardize_price(price):
            """가격 표준화"""
            if not price:
                return 0
            # 숫자만 추출
            match = re.search(r'[\d.]+', str(price))
            if match:
                try:
                    return float(match.group(0))
                except:
                    return 0
            return 0
        
        # 제품 맵 생성 (강화된 표준화 로직 적용)
        doc1_product_map = {}
        for product in doc1_products:
            std_model_code = standardize_model_code(product['model_code'])
            # 모델 코드만으로 키 생성 (색상 제외)
            key = std_model_code

            # 디버깅용 로그
            print(f"Doc1 Key: {key} from {product['model_code']}")

            doc1_product_map[key] = product

        doc2_product_map = {}
        for product in doc2_products:
            std_model_code = standardize_model_code(product['model_code'])
            # 모델 코드만으로 키 생성 (색상 제외)
            key = std_model_code

            # 디버깅용 로그
            print(f"Doc2 Key: {key} from {product['model_code']}")

            doc2_product_map[key] = product
                
        # 모든 제품 키 합집합
        all_product_keys = set(doc1_product_map.keys()) | set(doc2_product_map.keys())
        comparison_result['summary']['total_items'] = len(all_product_keys)
        
        # 디버깅용 로그
        print(f"Total unique keys: {len(all_product_keys)}")
        print(f"Doc1 keys: {list(doc1_product_map.keys())}")
        print(f"Doc2 keys: {list(doc2_product_map.keys())}")
        
        # 제품별 비교
        for key in all_product_keys:
            product1 = doc1_product_map.get(key)
            product2 = doc2_product_map.get(key)
            
            if not product1 or not product2:
                # 한쪽에만 존재하는 항목
                product = product1 or product2
                product_name = product.get('model_name', key)
                # 모델명이 비어있으면 모델코드 사용
                if not product_name or product_name.strip() == "":
                    product_name = product.get('model_code', key)
                
                comparison_result['mismatches'].append({
                    'product_key': key,
                    'product_name': product_name,
                    'doc1_exists': bool(product1),
                    'doc2_exists': bool(product2),
                    'reason': '한쪽 문서에만 존재'
                })
                comparison_result['summary']['mismatched_items'] += 1
                continue
            
            # 필드 비교
            mismatched_fields = []
            
            # 수량 비교 (표준화된 정수 비교)
            qty1 = int(product1.get('quantity', 0) or 0)
            qty2 = int(product2.get('quantity', 0) or 0)
            if qty1 != qty2:
                mismatched_fields.append({
                    'field': '총 수량',
                    'value1': qty1,
                    'value2': qty2
                })
            
            # 가격 비교 (표준화된 가격 비교)
            price1 = standardize_price(product1.get('wholesale_price', 0))
            price2 = standardize_price(product2.get('wholesale_price', 0))
            if abs(price1 - price2) > 0.01:  # 소수점 오차 허용
                mismatched_fields.append({
                    'field': '단가',
                    'value1': product1.get('wholesale_price', ''),
                    'value2': product2.get('wholesale_price', '')
                })
            
            # 사이즈별 수량 비교
            for size in range(39, 47):
                size_key = f'사이즈_{size}'
                size1 = int(product1.get(size_key, 0) or 0)
                size2 = int(product2.get(size_key, 0) or 0)
                if size1 != size2:
                    mismatched_fields.append({
                        'field': f'사이즈 {size}',
                        'value1': size1,
                        'value2': size2
                    })
            
            if mismatched_fields:
                product_name = product1.get('model_name', key)
                # 모델명이 비어있으면 모델코드 사용
                if not product_name or product_name.strip() == "":
                    product_name = product1.get('model_code', key)
                
                comparison_result['mismatches'].append({
                    'product_key': key,
                    'product_name': product_name,
                    'doc1_exists': True,
                    'doc2_exists': True,
                    'mismatched_fields': mismatched_fields
                })
                comparison_result['summary']['mismatched_items'] += 1
            else:
                # 사이즈 요약 생성
                size_summary = []
                for size in range(39, 47):
                    size_key = f'사이즈_{size}'
                    size_qty = int(product1.get(size_key, 0) or 0)
                    if size_qty:
                        size_summary.append(f"{size}({size_qty})")
                
                size_summary_str = ", ".join(size_summary) if size_summary else "-"
                
                product_name = product1.get('model_name', key)
                # 모델명이 비어있으면 모델코드 사용
                if not product_name or product_name.strip() == "":
                    product_name = product1.get('model_code', key)
                
                comparison_result['matches'].append({
                    'product_key': key,
                    'product_name': product_name,
                    'size': size_summary_str,
                    'quantity': product1.get('quantity', 0),
                    'price': product1.get('wholesale_price', '')
                })
                comparison_result['summary']['matched_items'] += 1
        
        # 일치율 계산
        if comparison_result['summary']['total_items'] > 0:
            comparison_result['summary']['match_percentage'] = round(
                (comparison_result['summary']['matched_items'] / 
                comparison_result['summary']['total_items']) * 100,
                2
            )
        
        return jsonify(comparison_result), 200
    
    except Exception as e:
        return jsonify({'error': f'문서 비교 중 오류가 발생했습니다: {str(e)}'}), 500
    

@orders_bp.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'healthy',
        'upload_folder': UPLOAD_FOLDER,
        'processed_folder': PROCESSED_FOLDER,
        'database': 'connected'
    }), 200