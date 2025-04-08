# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from .services.ocr_service import OCRProcessor
from .models import db, init_db  # 모델 모듈 임포트

# 전역 변수로 migrate 객체 선언
migrate = Migrate()

def create_app():
    """Flask 애플리케이션 생성 및 설정"""
    app = Flask(__name__)
    
    # 데이터베이스 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/ocr_documents.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS 설정 (모든 오리진 허용)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 최대 업로드 파일 크기 설정 (16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 마이그레이션 설정 추가
    migrate.init_app(app, db)
    
    # 컨텍스트 내에서 데이터베이스 테이블 생성
    # 참고: 마이그레이션을 사용하므로 init_db() 호출은 주석 처리하거나 제거해도 됨
    # with app.app_context():
    #    init_db()
    
    # 라우트 블루프린트 등록
    from .routes import orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')
    
    return app