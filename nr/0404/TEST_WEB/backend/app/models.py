# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Invoice(db.Model):
    """인보이스 문서 모델"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.String(20), primary_key=True)  # 'invo_1', 'invo_2', ...
    filename = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100))
    season = db.Column(db.String(50))
    total_amount = db.Column(db.String(50))
    total_quantity = db.Column(db.Integer, default=0)
    excel_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정 - 인보이스에 포함된 품목들
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Invoice {self.id}>'

class InvoiceItem(db.Model):
    """인보이스 품목 모델"""
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(20), db.ForeignKey('invoices.id'), nullable=False)
    model_code = db.Column(db.String(50))
    model_name = db.Column(db.String(255))
    color = db.Column(db.String(100))
    wholesale_price = db.Column(db.String(50))  # 'EUR 150.00' 형식
    retail_price = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)  # 총 수량
    total_price = db.Column(db.String(50))  # 품목별 총액
    
    # 사이즈별 수량
    size_39 = db.Column(db.Integer, default=0)
    size_40 = db.Column(db.Integer, default=0)
    size_41 = db.Column(db.Integer, default=0)
    size_42 = db.Column(db.Integer, default=0)
    size_43 = db.Column(db.Integer, default=0)
    size_44 = db.Column(db.Integer, default=0)
    size_45 = db.Column(db.Integer, default=0)
    size_46 = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<InvoiceItem {self.model_code}>'

class Order(db.Model):
    """오더시트 문서 모델"""
    __tablename__ = 'orders'
    
    id = db.Column(db.String(20), primary_key=True)  # 'order_1', 'order_2', ...
    filename = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100))
    season = db.Column(db.String(50))
    total_amount = db.Column(db.String(50))
    total_quantity = db.Column(db.Integer, default=0)
    excel_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정 - 오더시트에 포함된 품목들
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    """오더시트 품목 모델"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), db.ForeignKey('orders.id'), nullable=False)
    model_code = db.Column(db.String(50))
    model_name = db.Column(db.String(255))
    color = db.Column(db.String(100))
    wholesale_price = db.Column(db.String(50))  # 구매가
    quantity = db.Column(db.Integer, default=0)  # 총 수량
    total_price = db.Column(db.String(50))  # 품목별 총액
    shipping_start = db.Column(db.String(50))  # 선적 시작일
    shipping_end = db.Column(db.String(50))  # 선적 완료일
    
    # 사이즈별 수량
    size_39 = db.Column(db.Integer, default=0)
    size_40 = db.Column(db.Integer, default=0)
    size_41 = db.Column(db.Integer, default=0)
    size_42 = db.Column(db.Integer, default=0)
    size_43 = db.Column(db.Integer, default=0)
    size_44 = db.Column(db.Integer, default=0)
    size_45 = db.Column(db.Integer, default=0)
    size_46 = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<OrderItem {self.model_code}>'

# 문서 비교 결과 모델 추가
class DocumentComparison(db.Model):
    """문서 비교 결과 모델"""
    __tablename__ = 'document_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    document1_id = db.Column(db.String(20), nullable=False)
    document1_type = db.Column(db.String(20), nullable=False)  # invoice 또는 order
    document2_id = db.Column(db.String(20), nullable=False)
    document2_type = db.Column(db.String(20), nullable=False)  # invoice 또는 order
    
    match_percentage = db.Column(db.Float, nullable=False)  # 일치율 (0-100)
    matched_items = db.Column(db.Integer, default=0)        # 일치 항목 수
    mismatched_items = db.Column(db.Integer, default=0)     # 불일치 항목 수
    total_items = db.Column(db.Integer, default=0)          # 전체 항목 수
    
    brand = db.Column(db.String(100))                       # 브랜드 정보
    season = db.Column(db.String(50))                       # 시즌 정보
    
    # JSON 형태로 저장된 상세 비교 결과
    comparison_data = db.Column(db.Text)  
    comparison_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DocumentComparison {self.document1_id} vs {self.document2_id} ({self.match_percentage}%)>'
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'document1_id': self.document1_id,
            'document1_type': self.document1_type,
            'document2_id': self.document2_id,
            'document2_type': self.document2_type,
            'match_percentage': self.match_percentage,
            'matched_items': self.matched_items,
            'mismatched_items': self.mismatched_items,
            'total_items': self.total_items,
            'brand': self.brand,
            'season': self.season,
            'comparison_date': self.comparison_date.isoformat(),
            'comparison_data': json.loads(self.comparison_data) if self.comparison_data else None
        }

# init_db 함수 업데이트
def init_db():
    """데이터베이스 테이블 초기화"""
    db.create_all()