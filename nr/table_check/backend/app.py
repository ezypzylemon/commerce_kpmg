from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
import document_ocr  # 개선된 OCR 처리 모듈
import document_compare  # 문서 비교 모듈
import pandas as pd
import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# 로그 디렉토리 만들기 (추가)
if not os.path.exists('logs'):
    os.makedirs('logs')

app = Flask(__name__)
CORS(app)  # 개발 중 CORS 이슈 해결을 위해

# 업로드 폴더 설정
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB 최대 파일 크기 제한

# 로깅 설정
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.info('OCR 문서 관리 시스템 시작')

# 허용된 파일 확장자 체크
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 문서 저장소 (실제로는 데이터베이스 사용 권장)
documents = {}
comparisons = {}

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # 파일이 요청에 존재하는지 확인
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    doc_type = request.form.get('type', 'invoice')  # 기본값은 인보이스
    debug_mode = request.form.get('debug', 'false').lower() == 'true'  # 디버그 모드 여부
    
    # 파일이 선택되었는지 확인
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # 안전한 파일명 생성 및 저장
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        saved_filename = f"{timestamp}_{unique_id}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)
        
        app.logger.info(f"파일 업로드: {filename} (ID: {unique_id}, 유형: {doc_type})")
        
        # app.py의 업로드 처리 부분 수정
        try:
    # OCR 처리 실행
            output_excel = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{unique_id}_output.xlsx")
    
    # 함수명이 변경된 경우 아래와 같이 수정
            if hasattr(document_ocr, 'process_pdf'):
                ocr_result = document_ocr.process_pdf(file_path, output_excel, verbose=True, debug=debug_mode)
            else:
                ocr_result = document_ocr.process_invoice_pdf(file_path, output_excel, verbose=True, debug=debug_mode)
    
    # 결과를 저장
    # ...나머지 코드는 그대로 유지    
            # 결과를 저장
            documents[unique_id] = {
                'id': unique_id,
                'original_filename': filename,
                'saved_filename': saved_filename,
                'file_path': file_path,
                'output_excel': output_excel,
                'type': doc_type,
                'timestamp': timestamp,
                'processed': True
            }
            
            # 결과를 JSON으로 변환하여 반환
            if isinstance(ocr_result, pd.DataFrame) and not ocr_result.empty:
                if 'msg' in ocr_result.columns and ocr_result['msg'].iloc[0] == '데이터 추출 실패':
                    # 디버깅 정보 포함
                    app.logger.error(f"데이터 추출 실패: {filename}")
                    debug_info = ocr_result.iloc[0].to_dict()
                    return jsonify({
                        'id': unique_id,
                        'filename': filename,
                        'status': 'warning',
                        'message': '데이터를 추출하지 못했습니다. 디버깅 정보를 확인하세요.',
                        'debug_info': debug_info
                    })
                
                ocr_data = ocr_result.to_dict(orient='records')
                
                # 기존 문서와 비교
                comparison_result = document_compare.compare_with_existing(unique_id, ocr_data, documents, comparisons)
                
                app.logger.info(f"파일 {filename} 처리 성공: {len(ocr_data)}개 상품 추출")
                return jsonify({
                    'id': unique_id,
                    'filename': filename,
                    'status': 'success',
                    'message': 'File uploaded and processed successfully',
                    'product_count': len(ocr_data),
                    'comparison': comparison_result
                })
            else:
                app.logger.warning(f"파일 {filename} 처리 완료되었으나 데이터가 없습니다")
                return jsonify({
                    'id': unique_id,
                    'filename': filename,
                    'status': 'warning', 
                    'message': 'File processed but no data extracted',
                    'suggestion': '문서 형식이 맞는지 확인하거나 디버깅 모드로 실행해보세요.'
                })
                
        except Exception as e:
            app.logger.error(f"파일 {filename} 처리 오류: {str(e)}")
            return jsonify({
                'id': unique_id,
                'filename': filename,
                'status': 'error',
                'message': f'Error processing file: {str(e)}'
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """문서 목록 반환"""
    docs_list = []
    for doc_id, doc in documents.items():
        # 필요한 정보만 클라이언트에 전송
        docs_list.append({
            'id': doc_id,
            'filename': doc['original_filename'],
            'type': doc['type'],
            'timestamp': doc['timestamp'],
            'processed': doc['processed']
        })
    
    # 날짜순 정렬
    docs_list.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(docs_list)

@app.route('/api/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """특정 문서 정보 반환"""
    if doc_id in documents:
        doc = documents[doc_id]
        
        # 엑셀 파일에서 데이터 읽기
        data = []
        if os.path.exists(doc['output_excel']):
            try:
                df = pd.read_excel(doc['output_excel'])
                data = df.to_dict(orient='records')
            except Exception as e:
                app.logger.error(f"엑셀 파일 읽기 오류: {str(e)}")
                return jsonify({
                    'id': doc_id,
                    'filename': doc['original_filename'],
                    'type': doc['type'],
                    'timestamp': doc['timestamp'],
                    'error': f"엑셀 파일 읽기 오류: {str(e)}"
                })
            
        return jsonify({
            'id': doc_id,
            'filename': doc['original_filename'],
            'type': doc['type'],
            'timestamp': doc['timestamp'],
            'data': data
        })
    else:
        return jsonify({'error': 'Document not found'}), 404

@app.route('/api/files/<path:filename>', methods=['GET'])
def get_file(filename):
    """파일 다운로드"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)