# app/routes.py
import os
import logging
import json
import uuid
import re
import sqlite3
from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from .services.ocr_service import OCRProcessor
from .models import db, Invoice, InvoiceItem, Order, OrderItem, DocumentComparison, ShippingSchedule, PersonalEvent

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

# 날짜 문자열을 date 객체로 변환하는 함수
def parse_date_string(date_str):
    """다양한 형식의 날짜 문자열을 date 객체로 변환"""
    if not date_str or date_str.strip() == "":
        return None
    
    date_str = date_str.strip()
    
    # MM/DD/YYYY 형식
    try:
        month, day, year = date_str.split('/')
        return date(int(year), int(month), int(day))
    except ValueError:
        pass
    
    # DD-MM-YYYY 형식
    try:
        day, month, year = date_str.split('-')
        return date(int(year), int(month), int(day))
    except ValueError:
        pass
    
    # YYYY-MM-DD 형식
    try:
        year, month, day = date_str.split('-')
        return date(int(year), int(month), int(day))
    except ValueError:
        pass
    
    # 기타 형식은 datetime 파서로 시도
    try:
        dt = datetime.strptime(date_str, '%Y%m%d')
        return dt.date()
    except ValueError:
        pass
    
    return None

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
                        
                        # 변경사항 저장
                        db.session.commit()
                    
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
                        
                        # 품목 레코드 생성 및 선적 일정 추출
                        if not df_result.empty:
                            total_amount_value = 0
                            shipping_schedules = []  # 선적 일정 저장 리스트
                            
                            for idx, row in df_result.iterrows():
                                # 품목 정보 추출
                                model_code = row.get('모델코드', row.get('model', ''))
                                model_name = row.get('모델명', row.get('full_model', ''))
                                color = row.get('컬러', row.get('color', ''))
                                wholesale_price = row.get('구매가', row.get('wholesale_price', ''))
                                total_item_price = row.get('총_금액', row.get('total_price', ''))
                                
                                # 선적 일정 정보 추출
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
                                
                                # 선적 시작일 일정 추가
                                if shipping_start:
                                    start_date = parse_date_string(shipping_start)
                                    if start_date:
                                        start_schedule = ShippingSchedule(
                                            title=f"{brand} 선적 시작 - {model_name or model_code}",
                                            date=start_date,
                                            description=f"{model_name or model_code} 선적 시작, 수량: {item_quantity}",
                                            document_id=doc_id,
                                            document_type='order',
                                            item_id=idx+1,  # 임시 item_id, 실제로는 DB에 저장 후 ID를 가져와야 함
                                            schedule_type='start',
                                            brand=brand,
                                            model_code=model_code,
                                            model_name=model_name,
                                            is_confirmed=False  # 초기에는 미확정 상태
                                        )
                                        shipping_schedules.append(start_schedule)
                                
                                # 선적 완료일 일정 추가
                                if shipping_end:
                                    end_date = parse_date_string(shipping_end)
                                    if end_date:
                                        end_schedule = ShippingSchedule(
                                            title=f"{brand} 선적 완료 - {model_name or model_code}",
                                            date=end_date,
                                            description=f"{model_name or model_code} 선적 완료, 수량: {item_quantity}",
                                            document_id=doc_id,
                                            document_type='order',
                                            item_id=idx+1,  # 임시 item_id, 실제로는 DB에 저장 후 ID를 가져와야 함
                                            schedule_type='end',
                                            brand=brand,
                                            model_code=model_code,
                                            model_name=model_name,
                                            is_confirmed=False  # 초기에는 미확정 상태
                                        )
                                        shipping_schedules.append(end_schedule)
                            
                            # 오더시트 총액 업데이트
                            order.total_amount = f"EUR {total_amount_value:.2f}"
                    
                            # 변경사항 저장
                            db.session.commit()

                            # 실제 item_id를 가진 선적 일정 저장
                            # 저장된 OrderItem 객체 가져오기
                            saved_items = OrderItem.query.filter_by(order_id=doc_id).all()
                            item_map = {}
                            for idx, item in enumerate(saved_items):
                                item_map[idx+1] = item.id

                            # 선적 일정 업데이트 및 저장
                            for schedule in shipping_schedules:
                                if schedule.item_id in item_map:
                                    schedule.item_id = item_map[schedule.item_id]
                                    db.session.add(schedule)
                            
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
    """두 문서 비교 및 결과 저장"""
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
        
        # 기존 비교 결과 확인 (문서 ID 순서에 상관없이)
        existing_comparison = DocumentComparison.query.filter(
            ((DocumentComparison.document1_id == doc1_id) & 
             (DocumentComparison.document2_id == doc2_id)) |
            ((DocumentComparison.document1_id == doc2_id) & 
             (DocumentComparison.document2_id == doc1_id))
        ).order_by(DocumentComparison.comparison_date.desc()).first()
        
        # 이미 최근에 비교한 결과가 있다면 해당 결과 반환
        if existing_comparison and (datetime.utcnow() - existing_comparison.comparison_date).total_seconds() < 3600:  # 1시간 이내
            comparison_data = json.loads(existing_comparison.comparison_data)
            return jsonify(comparison_data), 200

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
        
        # 모델 코드 표준화 함수
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
            doc1_product_map[key] = product

        doc2_product_map = {}
        for product in doc2_products:
            std_model_code = standardize_model_code(product['model_code'])
            # 모델 코드만으로 키 생성 (색상 제외)
            key = std_model_code
            doc2_product_map[key] = product
                
        # 모든 제품 키 합집합
        all_product_keys = set(doc1_product_map.keys()) | set(doc2_product_map.keys())
        comparison_result['summary']['total_items'] = len(all_product_keys)
        
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
        
        # 비교 결과 저장
        try:
            # 브랜드 및 시즌 정보 가져오기
            brand = doc1.brand if doc1.brand else (doc2.brand if doc2.brand else '')
            season = doc1.season if doc1.season else (doc2.season if doc2.season else '')
            
            # 이미 존재하는 비교 결과가 있으면 업데이트
            if existing_comparison:
                existing_comparison.match_percentage = comparison_result['summary']['match_percentage']
                existing_comparison.matched_items = comparison_result['summary']['matched_items']
                existing_comparison.mismatched_items = comparison_result['summary']['mismatched_items']
                existing_comparison.total_items = comparison_result['summary']['total_items']
                existing_comparison.comparison_data = json.dumps(comparison_result)
                existing_comparison.comparison_date = datetime.utcnow()
                existing_comparison.brand = brand
                existing_comparison.season = season
                
                db.session.commit()
                comparison_id = existing_comparison.id
            else:
                # 새 비교 결과 생성
                new_comparison = DocumentComparison(
                    document1_id=doc1_id,
                    document1_type=doc1_type,
                    document2_id=doc2_id,
                    document2_type=doc2_type,
                    match_percentage=comparison_result['summary']['match_percentage'],
                    matched_items=comparison_result['summary']['matched_items'],
                    mismatched_items=comparison_result['summary']['mismatched_items'],
                    total_items=comparison_result['summary']['total_items'],
                    comparison_data=json.dumps(comparison_result),
                    brand=brand,
                    season=season
                )
                db.session.add(new_comparison)
                db.session.commit()
                comparison_id = new_comparison.id
            
            # 일정 확정 로직
            try:
                # 일치율이 높을 경우 (80% 이상) 관련 일정 확정
                if comparison_result['summary']['match_percentage'] >= 80:
                    # 오더 문서 ID 확인
                    order_id = None
                    if doc1_type == 'order':
                        order_id = doc1_id
                    elif doc2_type == 'order':
                        order_id = doc2_id
                    
                    if order_id:
                        # 일치 항목 키 추출
                        matched_product_keys = []
                        for item in comparison_result.get('matches', []):
                            if 'product_key' in item:
                                matched_product_keys.append(item['product_key'].lower())
                        
                        # 오더 문서의 모든 품목 가져오기
                        order_items = OrderItem.query.filter_by(order_id=order_id).all()
                        
                        for item in order_items:
                            # 제품 키 생성 (비교 결과의 키와 동일한 방식)
                            model_code = item.model_code.lower() if item.model_code else ''
                            model_code_match = re.search(r'(aj\d+)', model_code)
                            product_key = model_code_match.group(1) if model_code_match else model_code
                            
                            # 해당 제품이 일치 목록에 있으면 관련 일정 확정
                            if product_key and any(key.startswith(product_key) for key in matched_product_keys):
                                # 해당 품목의 선적 일정을 확정 상태로 업데이트
                                ShippingSchedule.query.filter_by(
                                    document_id=order_id,
                                    item_id=item.id
                                ).update({
                                    'is_confirmed': True,
                                    'comparison_id': comparison_id
                                })
                        
                        # 변경사항 커밋
                        db.session.commit()
                        logging.info(f"문서 {doc1_id}와 {doc2_id}의 비교 결과에 따라 일정이 확정되었습니다.")

            except Exception as e:
                logging.error(f"일정 확정 중 오류: {str(e)}")
                # 일정 확정 실패해도 비교 결과는 반환
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"비교 결과 저장 중 오류: {str(e)}")
            # 저장 실패해도 비교 결과는 반환
        
        return jsonify(comparison_result), 200
    
    except Exception as e:
        return jsonify({'error': f'문서 비교 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/comparison-history', methods=['GET'])
def get_comparison_history():
    """문서 비교 이력 조회"""
    try:
        # 필터 파라미터
        brand = request.args.get('brand')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        min_match = request.args.get('min_match')
        max_match = request.args.get('max_match')
        limit = request.args.get('limit', 100, type=int)
        
        # 기본 쿼리
        query = DocumentComparison.query
        
        # 필터 적용
        if brand:
            query = query.filter(DocumentComparison.brand == brand)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(DocumentComparison.comparison_date >= start_date_obj)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                # 날짜 범위에 end_date 포함하기 위해 다음 날짜로 설정
                end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(DocumentComparison.comparison_date <= end_date_obj)
            except ValueError:
                pass
        
        if min_match:
            try:
                min_match_val = float(min_match)
                query = query.filter(DocumentComparison.match_percentage >= min_match_val)
            except ValueError:
                pass
        
        if max_match:
            try:
                max_match_val = float(max_match)
                query = query.filter(DocumentComparison.match_percentage <= max_match_val)
            except ValueError:
                pass
        
        # 최신 순으로 정렬하고 제한
        comparisons = query.order_by(DocumentComparison.comparison_date.desc()).limit(limit).all()
        
        # 결과 변환
        result = []
        for comparison in comparisons:
            # document1 정보 가져오기
            doc1_info = {}
            if comparison.document1_type == 'invoice':
                doc1 = Invoice.query.get(comparison.document1_id)
                if doc1:
                    doc1_info = {
                        'id': doc1.id,
                        'filename': doc1.filename,
                        'type': 'invoice',
                        'created_at': doc1.created_at.isoformat()
                    }
            else:
                doc1 = Order.query.get(comparison.document1_id)
                if doc1:
                    doc1_info = {
                        'id': doc1.id,
                        'filename': doc1.filename,
                        'type': 'order',
                        'created_at': doc1.created_at.isoformat()
                    }
            
            # document2 정보 가져오기
            doc2_info = {}
            if comparison.document2_type == 'invoice':
                doc2 = Invoice.query.get(comparison.document2_id)
                if doc2:
                    doc2_info = {
                        'id': doc2.id,
                        'filename': doc2.filename,
                        'type': 'invoice',
                        'created_at': doc2.created_at.isoformat()
                    }
            else:
                doc2 = Order.query.get(comparison.document2_id)
                if doc2:
                    doc2_info = {
                        'id': doc2.id,
                        'filename': doc2.filename,
                        'type': 'order',
                        'created_at': doc2.created_at.isoformat()
                    }
            
            # 비교 결과 정보
            result.append({
                'id': comparison.id,
                'document1': doc1_info,
                'document2': doc2_info,
                'match_percentage': comparison.match_percentage,
                'matched_items': comparison.matched_items,
                'mismatched_items': comparison.mismatched_items,
                'total_items': comparison.total_items,
                'brand': comparison.brand,
                'season': comparison.season,
                'comparison_date': comparison.comparison_date.isoformat()
            })
        
        return jsonify({
            'comparisons': result,
            'total_count': len(result)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'비교 이력 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/document-comparisons/<doc_id>', methods=['GET'])
def get_document_comparisons(doc_id):
    """특정 문서의 모든 비교 결과 조회"""
    try:
        # 필터 파라미터
        limit = request.args.get('limit', 100, type=int)
        
        # 해당 문서가 포함된 모든 비교 결과 쿼리
        comparisons = DocumentComparison.query.filter(
            (DocumentComparison.document1_id == doc_id) | 
            (DocumentComparison.document2_id == doc_id)
        ).order_by(DocumentComparison.comparison_date.desc()).limit(limit).all()
        
        # 결과 변환
        result = []
        for comparison in comparisons:
            # 비교 대상 문서 결정 (doc_id가 아닌 다른 문서)
            other_doc_id = comparison.document2_id if comparison.document1_id == doc_id else comparison.document1_id
            other_doc_type = comparison.document2_type if comparison.document1_id == doc_id else comparison.document1_type
            
            # 다른 문서 정보 가져오기
            other_doc_info = {}
            if other_doc_type == 'invoice':
                other_doc = Invoice.query.get(other_doc_id)
                if other_doc:
                    other_doc_info = {
                        'id': other_doc.id,
                        'filename': other_doc.filename,
                        'type': 'invoice',
                        'created_at': other_doc.created_at.isoformat()
                    }
            else:
                other_doc = Order.query.get(other_doc_id)
                if other_doc:
                    other_doc_info = {
                        'id': other_doc.id,
                        'filename': other_doc.filename,
                        'type': 'order',
                        'created_at': other_doc.created_at.isoformat()
                    }
            
            # 비교 결과 정보
            result.append({
                'id': comparison.id,
                'compared_with': other_doc_info,
                'match_percentage': comparison.match_percentage,
                'matched_items': comparison.matched_items,
                'mismatched_items': comparison.mismatched_items,
                'total_items': comparison.total_items,
                'brand': comparison.brand,
                'season': comparison.season,
                'comparison_date': comparison.comparison_date.isoformat()
            })
        
        return jsonify({
            'document_id': doc_id,
            'comparisons': result,
            'total_count': len(result)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'문서 비교 결과 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """통계 데이터 API"""
    try:
        # 필터 파라미터
        brand = request.args.get('brand')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = DocumentComparison.query
        
        # 필터 적용
        if brand:
            query = query.filter(DocumentComparison.brand == brand)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(DocumentComparison.comparison_date >= start_date_obj)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                # 날짜 범위에 end_date 포함하기 위해 다음 날짜로 설정
                end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(DocumentComparison.comparison_date <= end_date_obj)
            except ValueError:
                pass
        
        # 전체 비교 건수
        total_comparisons = query.count()
        
        # 평균 일치율
        avg_match_percentage = db.session.query(db.func.avg(DocumentComparison.match_percentage)).filter(
            query.whereclause
        ).scalar() or 0
        
        # 낮은 일치율(80% 미만) 문서 수
        low_match_count = query.filter(DocumentComparison.match_percentage < 80).count()
        
        # 추가 통계: 브랜드별 평균 일치율
        brand_stats = []
        brands_query = db.session.query(DocumentComparison.brand, 
                                      db.func.avg(DocumentComparison.match_percentage).label('avg_match'),
                                      db.func.count(DocumentComparison.id).label('count'))\
                                .filter(DocumentComparison.brand != '')\
                                .group_by(DocumentComparison.brand)\
                                .order_by(db.desc('avg_match'))
        
        if query.whereclause:
            brands_query = brands_query.filter(query.whereclause)
        
        for brand_result in brands_query.all():
            brand_stats.append({
                'brand': brand_result.brand,
                'avg_match_percentage': round(brand_result.avg_match, 2),
                'comparison_count': brand_result.count
            })
        
        # 최근 7일간 일치율 추이 
        today = datetime.utcnow().date()
        daily_stats = []
        
        for i in range(6, -1, -1):
            target_date = today - timedelta(days=i)
            next_date = target_date + timedelta(days=1)
            
            daily_query = query.filter(
                DocumentComparison.comparison_date >= datetime.combine(target_date, datetime.min.time()),
                DocumentComparison.comparison_date < datetime.combine(next_date, datetime.min.time())
            )
            
            daily_count = daily_query.count()
            daily_avg = db.session.query(db.func.avg(DocumentComparison.match_percentage))\
                                 .filter(daily_query.whereclause).scalar() or 0
            
            daily_stats.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'avg_match_percentage': round(daily_avg, 2),
                'comparison_count': daily_count
            })
        
        return jsonify({
            'total_comparisons': total_comparisons,
            'avg_match_percentage': round(avg_match_percentage, 2),
            'low_match_count': low_match_count,
            'brand_stats': brand_stats,
            'daily_stats': daily_stats
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'통계 데이터 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/calendar/events', methods=['GET'])
def get_calendar_events():
    try:
        # SQLite 직접 연결 로깅
        db_path = 'instance/ocr_documents.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("데이터베이스 테이블:", tables)
        
        # shipping_schedules 테이블 데이터 확인
        cursor.execute("SELECT * FROM shipping_schedules")
        shipping_data = cursor.fetchall()
        print("선적 일정 데이터:", shipping_data)
        
        conn.close()
        
        # 기존 ShippingSchedule 쿼리 로직
        shipping_query = ShippingSchedule.query
        shipping_events = shipping_query.all()
        
        result = {
            'shipping_events': [event.to_dict() for event in shipping_events],
            'personal_events': []
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"일정 조회 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/calendar/event/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_calendar_event(event_id):
    """캘린더 일정 조회/수정/삭제 API"""
    try:
        # 이벤트 유형 확인 (shipping 또는 personal)
        event_type = request.args.get('type', 'shipping')
        
        if event_type == 'shipping':
            event = ShippingSchedule.query.get(event_id)
        else:
            event = PersonalEvent.query.get(event_id)
        
        if not event:
            return jsonify({'error': '일정을 찾을 수 없습니다.'}), 404
        
        # GET 요청: 일정 조회
        if request.method == 'GET':
            return jsonify(event.to_dict()), 200
        
        # PUT 요청: 일정 수정
        elif request.method == 'PUT':
            data = request.json
            
            # 일정 정보 수정
            if event_type == 'shipping':
                if 'title' in data:
                    event.title = data['title']
                if 'description' in data:
                    event.description = data['description']
                if 'date' in data:
                    try:
                        event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                # ShippingSchedule의 경우 is_confirmed 상태 수동 변경 가능
                if 'is_confirmed' in data:
                    event.is_confirmed = data['is_confirmed']
            else:
                # PersonalEvent 수정 로직
                if 'title' in data:
                    event.title = data['title']
                if 'description' in data:
                    event.description = data['description']
                if 'date' in data:
                    try:
                        event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                if 'start_time' in data:
                    event.start_time = data['start_time']
                if 'end_time' in data:
                    event.end_time = data['end_time']
                if 'all_day' in data:
                    event.all_day = data['all_day']
                if 'category' in data:
                    event.category = data['category']
                if 'repeat' in data:
                    event.repeat = data['repeat']
                if 'repeat_type' in data:
                    event.repeat_type = data['repeat_type']
                if 'repeat_until' in data and data['repeat_until']:
                    try:
                        event.repeat_until = datetime.strptime(data['repeat_until'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
            
            # 수정된 일정 저장
            event.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'message': '일정이 수정되었습니다.',
                'event': event.to_dict()
            }), 200
        
        # DELETE 요청: 일정 삭제
        elif request.method == 'DELETE':
            db.session.delete(event)
            db.session.commit()
            
            return jsonify({
                'message': '일정이 삭제되었습니다.'
            }), 200
    
    except Exception as e:
        return jsonify({'error': f'일정 관리 중 오류가 발생했습니다: {str(e)}'}), 500
   
    except Exception as e:
        return jsonify({'error': f'일정 관리 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/calendar/personal-events', methods=['POST'])
def create_personal_event():
   """개인 일정 생성 API"""
   try:
       data = request.json
       
       # 필수 필드 확인
       if not data.get('title') or not data.get('date'):
           return jsonify({'error': '제목과 날짜는 필수 항목입니다.'}), 400
       
       # 날짜 변환
       try:
           event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
       except ValueError:
           return jsonify({'error': '날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)'}), 400
       
       # 새 일정 생성
       new_event = PersonalEvent(
           title=data['title'],
           date=event_date,
           start_time=data.get('start_time'),
           end_time=data.get('end_time'),
           all_day=data.get('all_day', False),
           category=data.get('category', 'personal'),
           description=data.get('description', ''),
           repeat=data.get('repeat', False),
           user_id=data.get('user_id', 'admin')
       )
       
       # 반복 정보 추가
       if data.get('repeat'):
           new_event.repeat_type = data.get('repeat_type')
           if data.get('repeat_until'):
               try:
                   repeat_until = datetime.strptime(data['repeat_until'], '%Y-%m-%d').date()
                   new_event.repeat_until = repeat_until
               except ValueError:
                   pass
       
       # 일정 저장
       db.session.add(new_event)
       db.session.commit()
       
       return jsonify({
           'message': '일정이 생성되었습니다.',
           'event': new_event.to_dict()
       }), 201
   
   except Exception as e:
       return jsonify({'error': f'일정 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@orders_bp.route('/health', methods=['GET'])
def health_check():
   """서버 상태 확인"""
   return jsonify({
       'status': 'healthy',
       'upload_folder': UPLOAD_FOLDER,
       'processed_folder': PROCESSED_FOLDER,
       'database': 'connected'
   }), 200