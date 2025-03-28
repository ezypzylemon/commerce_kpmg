# routes.py 수정

import os
import logging
import json
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from .services.ocr_service import OCRProcessor
from .services.document_parser import DocumentParser
from .services.document_comparator import DocumentComparator

# 라우트 블루프린트 생성
orders_bp = Blueprint('orders', __name__)

# 서비스 초기화
ocr_processor = OCRProcessor()
document_parser = DocumentParser()
document_comparator = DocumentComparator()

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
            
            # 문서 유형 정보 가져오기 (옵션)
            doc_type = request.form.get('docType', 'auto')
            if doc_type == '자동 감지':
                doc_type = 'auto'
            
            # OCR 처리
            try:
                # OCR로 텍스트 추출
                df_result, output_excel = ocr_processor.process_pdf(
                    filepath, 
                    output_dir=PROCESSED_FOLDER, 
                    verbose=False
                )
                
                if output_excel:
                    # 파일명에서 문서 ID 추출 (엑셀 파일을 나중에 식별하기 위함)
                    doc_id = os.path.basename(output_excel).split('.')[0]
                    
                    # 엑셀 파일 정보 반환
                    return jsonify({
                        'message': '문서 처리 완료',
                        'excel_filename': os.path.basename(output_excel),
                        'document_id': doc_id,
                        'total_products': len(df_result),
                        'data_preview': df_result.head().to_dict(orient='records')
                    }), 200
                else:
                    return jsonify({'error': '문서 처리 중 오류가 발생했습니다.'}), 500
            
            except Exception as e:
                return jsonify({'error': f'문서 처리 중 오류: {str(e)}'}), 500
        
        else:
            return jsonify({'error': '허용되지 않은 파일 형식입니다.'}), 400
    
    except Exception as e:
        return jsonify({'error': '예상치 못한 오류가 발생했습니다.'}), 500

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
        return jsonify({'error': '다운로드 중 오류가 발생했습니다.'}), 500

@orders_bp.route('/documents', methods=['GET'])
def list_documents():
    """처리된 문서 목록 조회"""
    try:
        processed_files = [f for f in os.listdir(PROCESSED_FOLDER) if f.endswith('.xlsx')]
        return jsonify({
            'documents': processed_files,
            'total_count': len(processed_files)
        }), 200
    
    except Exception as e:
        return jsonify({'error': '문서 목록 조회 중 오류가 발생했습니다.'}), 500

@orders_bp.route('/compare', methods=['POST'])
def compare_documents():
    """문서 비교 엔드포인트"""
    try:
        # 요청 데이터 확인
        data = request.json
        if not data:
            return jsonify({'error': '요청 데이터가 없습니다.'}), 400
        
        # 방법 1: 두 개의 파일 ID를 받아 비교
        if 'document1_id' in data and 'document2_id' in data:
            doc1_id = data['document1_id']
            doc2_id = data['document2_id']
            
            # 문서 유형 확인 (옵션)
            doc1_type = data.get('document1_type', 'auto')
            doc2_type = data.get('document2_type', 'auto')
            
            # 파일 경로 생성
            doc1_path = find_document_by_id(doc1_id)
            doc2_path = find_document_by_id(doc2_id)
            
            if not doc1_path:
                return jsonify({'error': f'첫 번째 문서를 찾을 수 없습니다: {doc1_id}'}), 404
            
            if not doc2_path:
                return jsonify({'error': f'두 번째 문서를 찾을 수 없습니다: {doc2_id}'}), 404
            
            # OCR 처리 및 문서 파싱
            doc1_text = ocr_processor.extract_text_from_pdf(doc1_path)
            doc2_text = ocr_processor.extract_text_from_pdf(doc2_path)
            
            doc1_data = document_parser.parse_document(doc1_text, doc1_type)
            doc2_data = document_parser.parse_document(doc2_text, doc2_type)
            
        # 방법 2: 두 개의 파일을 직접 업로드 받아 비교
        elif 'file1' in request.files and 'file2' in request.files:
            file1 = request.files['file1']
            file2 = request.files['file2']
            
            # 파일명이 비어있는 경우 처리
            if file1.filename == '' or file2.filename == '':
                return jsonify({'error': '선택된 파일이 없습니다.'}), 400
            
            # 파일 확장자 검증
            if not (allowed_file(file1.filename) and allowed_file(file2.filename)):
                return jsonify({'error': '허용되지 않은 파일 형식입니다.'}), 400
            
            # 안전한 파일명 생성 및 저장
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            
            filepath1 = os.path.join(UPLOAD_FOLDER, filename1)
            filepath2 = os.path.join(UPLOAD_FOLDER, filename2)
            
            file1.save(filepath1)
            file2.save(filepath2)
            
            # 문서 유형 정보 가져오기 (옵션)
            doc1_type = request.form.get('docType1', 'auto')
            doc2_type = request.form.get('docType2', 'auto')
            
            # OCR 처리 및 문서 파싱
            doc1_text = ocr_processor.extract_text_from_pdf(filepath1)
            doc2_text = ocr_processor.extract_text_from_pdf(filepath2)
            
            doc1_data = document_parser.parse_document(doc1_text, doc1_type)
            doc2_data = document_parser.parse_document(doc2_text, doc2_type)
            
        else:
            return jsonify({'error': '문서 정보가 제공되지 않았습니다.'}), 400
        
        # 문서 비교
        comparison_result = document_comparator.compare_documents(doc1_data, doc2_data)
        
        # 비교 결과 저장 (옵션)
        if data.get('save_result', False):
            result_filename = f"comparison_{doc1_data.get('document_id', 'doc1')}_{doc2_data.get('document_id', 'doc2')}.json"
            result_filepath = os.path.join(PROCESSED_FOLDER, result_filename)
            
            with open(result_filepath, 'w', encoding='utf-8') as f:
                json.dump(comparison_result, f, ensure_ascii=False, indent=2)
            
            comparison_result['result_filename'] = result_filename
        
        return jsonify({
            'message': '문서 비교 완료',
            'result': comparison_result
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'문서 비교 중 오류: {str(e)}'}), 500

@orders_bp.route('/classify', methods=['POST'])
def classify_document():
    """문서 유형 감지 엔드포인트"""
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
            
            # OCR 처리
            doc_text = ocr_processor.extract_text_from_pdf(filepath)
            
            # 문서 유형 감지
            doc_type = document_parser.detect_document_type(doc_text)
            
            return jsonify({
                'message': '문서 유형 감지 완료',
                'document_type': doc_type,
                'filename': filename
            }), 200
        
        else:
            return jsonify({'error': '허용되지 않은 파일 형식입니다.'}), 400
    
    except Exception as e:
        return jsonify({'error': f'문서 유형 감지 중 오류: {str(e)}'}), 500

@orders_bp.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'healthy',
        'upload_folder': UPLOAD_FOLDER,
        'processed_folder': PROCESSED_FOLDER
    }), 200

def find_document_by_id(doc_id):
    """문서 ID로 파일 찾기 (파일명 또는 ID 기준)"""
    # 파일명으로 직접 찾기
    direct_path = os.path.join(PROCESSED_FOLDER, f"{doc_id}.xlsx")
    if os.path.exists(direct_path):
        return direct_path
    
    # ID가 파일명에 포함된 파일 찾기
    for filename in os.listdir(PROCESSED_FOLDER):
        if doc_id in filename and filename.endswith('.xlsx'):
            return os.path.join(PROCESSED_FOLDER, filename)
    
    # PDF 파일도 검색
    for filename in os.listdir(UPLOAD_FOLDER):
        if doc_id in filename and filename.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            return os.path.join(UPLOAD_FOLDER, filename)
    
    return None