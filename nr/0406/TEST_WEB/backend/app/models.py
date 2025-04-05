# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import sqlite3

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

# 문서 비교 결과 모델
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

    # 새로 추가된 필드
    manually_compared = db.Column(db.Boolean, default=False)  # 수동 비교 여부

    
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

# 캘린더 일정 모델 (추가)
class ShippingSchedule(db.Model):
    """선적 일정 모델"""
    __tablename__ = 'shipping_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # 일정 제목
    date = db.Column(db.Date, nullable=False)  # 일정 날짜
    description = db.Column(db.Text)  # 일정 설명
    
    document_id = db.Column(db.String(20), nullable=False)  # 관련 문서 ID
    document_type = db.Column(db.String(20), nullable=False)  # 문서 유형 (invoice 또는 order)
    item_id = db.Column(db.Integer, nullable=True)  # 관련 품목 ID
    
    schedule_type = db.Column(db.String(20), nullable=False)  # start 또는 end
    brand = db.Column(db.String(100))  # 브랜드 정보
    model_code = db.Column(db.String(50))  # 모델 코드
    model_name = db.Column(db.String(255))  # 모델명
    
    is_confirmed = db.Column(db.Boolean, default=False)  # 확정 여부
    comparison_id = db.Column(db.Integer, db.ForeignKey('document_comparisons.id'), nullable=True)  # 관련 비교 ID
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        status = "확정" if self.is_confirmed else "미확정"
        return f'<ShippingSchedule {self.title} ({status})>'
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'document_id': self.document_id,
            'document_type': self.document_type,
            'item_id': self.item_id,
            'schedule_type': self.schedule_type,
            'brand': self.brand,
            'model_code': self.model_code,
            'model_name': self.model_name,
            'is_confirmed': self.is_confirmed,
            'comparison_id': self.comparison_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 개인 일정 모델 (추가)
class PersonalEvent(db.Model):
    """개인 일정 모델"""
    __tablename__ = 'personal_events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # 일정 제목
    date = db.Column(db.Date, nullable=False)  # 일정 날짜
    start_time = db.Column(db.String(10))  # 시작 시간 (HH:MM)
    end_time = db.Column(db.String(10))  # 종료 시간 (HH:MM)
    all_day = db.Column(db.Boolean, default=False)  # 종일 이벤트 여부
    category = db.Column(db.String(50), default='personal')  # 카테고리 (personal, business)
    description = db.Column(db.Text)  # 일정 설명
    
    repeat = db.Column(db.Boolean, default=False)  # 반복 여부
    repeat_type = db.Column(db.String(20))  # 반복 유형 (daily, weekly, monthly)
    repeat_until = db.Column(db.Date)  # 반복 종료일
    
    user_id = db.Column(db.String(50), default='admin')  # 사용자 ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PersonalEvent {self.title}>'
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'all_day': self.all_day,
            'category': self.category,
            'description': self.description,
            'repeat': self.repeat,
            'repeat_type': self.repeat_type,
            'repeat_until': self.repeat_until.isoformat() if self.repeat_until else None,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# init_db 함수 업데이트
def init_db():
    """데이터베이스 테이블 초기화"""
    db.create_all()