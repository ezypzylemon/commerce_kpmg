from flask import Flask
from flask_cors import CORS
from .services.ocr_service import OCRProcessor

def create_app():
    """Flask 애플리케이션 생성 및 설정"""
    app = Flask(__name__)
    
    # CORS 설정 (모든 오리진 허용)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 최대 업로드 파일 크기 설정 (16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # 라우트 블루프린트 등록
    from .routes import orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')
    
    return app