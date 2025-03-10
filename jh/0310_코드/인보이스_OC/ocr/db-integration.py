import sqlite3
import mysql.connector
import psycopg2
import pandas as pd
import json
import os
import datetime
from pathlib import Path

class DatabaseManager:
    """
    OCR 결과를 다양한 데이터베이스에 저장하는 클래스
    지원 DB: SQLite, MySQL, PostgreSQL
    """
    
    def __init__(self, db_type='sqlite', config=None):
        """
        데이터베이스 매니저 초기화
        
        Parameters:
        -----------
        db_type : str
            사용할 데이터베이스 유형 ('sqlite', 'mysql', 'postgresql')
        config : dict
            데이터베이스 연결 설정 (SQLite 제외)
        """
        self.db_type = db_type.lower()
        self.config = config or {}
        self.conn = None
        self.cursor = None
        
        # 기본 SQLite 설정
        if self.db_type == 'sqlite' and 'db_path' not in self.config:
            self.config['db_path'] = 'ocr_results.db'
    
    def connect(self):
        """데이터베이스 연결 생성"""
        try:
            if self.db_type == 'sqlite':
                self.conn = sqlite3.connect(self.config['db_path'])
                
            elif self.db_type == 'mysql':
                required_fields = ['host', 'user', 'password', 'database']
                if not all(field in self.config for field in required_fields):
                    raise ValueError(f"MySQL 연결에는 다음 필드가. 필요합니다: {', '.join(required_fields)}")
                
                self.conn = mysql.connector.connect(
                    host=self.config['host'],
                    user=self.config['user'],
                    password=self.config['password'],
                    database=self.config['database'],
                    port=self.config.get('port', 3306)
                )
                
            elif self.db_type == 'postgresql':
                required_fields = ['host', 'user', 'password', 'database']
                if not all(field in self.config for field in required_fields):
                    raise ValueError(f"PostgreSQL 연결에는 다음 필드가 필요합니다: {', '.join(required_fields)}")
                
                self.conn = psycopg2.connect(
                    host=self.config['host'],
                    user=self.config['user'],
                    password=self.config['password'],
                    dbname=self.config['database'],
                    port=self.config.get('port', 5432)
                )
            
            else:
                raise ValueError(f"지원되지 않는 데이터베이스 유형: {self.db_type}")
            
            self.cursor = self.conn.cursor()
            return True
            
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return False
    
    def close(self):
        """데이터베이스 연결 종료"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self.cursor = None
            self.conn = None
        except Exception as e:
            print(f"데이터베이스 연결 종료 오류: {e}")
    
    def initialize_tables(self):
        """필요한 테이블을 생성합니다"""
        try:
            # 테이블 생성 SQL 문
            create_comparisons_table = """
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comparison_date TIMESTAMP,
                oc_file_path TEXT,
                invoice_file_path TEXT,
                result_file_path TEXT,
                total_items INTEGER,
                matching_items INTEGER,
                mismatch_items INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            create_products_table = """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comparison_id INTEGER,
                style_code TEXT,
                model TEXT,
                size TEXT,
                oc_quantity INTEGER,
                invoice_quantity INTEGER,
                quantity_match INTEGER,
                oc_price REAL,
                invoice_price REAL,
                price_match INTEGER,
                oc_shipping TEXT,
                invoice_shipping TEXT,
                shipping_match INTEGER,
                all_match INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (comparison_id) REFERENCES comparisons(id)
            )
            """
            
            # SQLite와 다른 DB 간의 SQL 문법 차이 처리
            if self.db_type == 'mysql':
                create_comparisons_table = create_comparisons_table.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
                create_products_table = create_products_table.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
            
            elif self.db_type == 'postgresql':
                create_comparisons_table = create_comparisons_table.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
                create_products_table = create_products_table.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
                
            # 테이블 생성 실행
            self.cursor.execute(create_comparisons_table)
            self.cursor.execute(create_products_table)
            self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"테이블 초기화 오류: {e}")
            return False
    
    def save_comparison_result(self, oc_path, invoice_path, result_path, df_result):
        """
        비교 결과를 데이터베이스에 저장
        
        Parameters:
        -----------
        oc_path : str
            OC 문서 파일 경로
        invoice_path : str
            인보이스 문서 파일 경로
        result_path : str
            결과 엑셀 파일 경로
        df_result : pandas.DataFrame
            비교 결과 데이터프레임
        """
        if not self.connect():
            return None
            
        try:
            self.initialize_tables()
            
            # 비교 결과 통계 계산
            total_items = len(df_result)
            matching_items = 0
            if 'All_Match' in df_result.columns and total_items > 0:
                matching_items = df_result['All_Match'].sum()
            mismatch_items = total_items - matching_items
            status = 'COMPLETE'
            
            # 절대 경로 변환
            oc_path = str(Path(oc_path).resolve())
            invoice_path = str(Path(invoice_path).resolve())
            result_path = str(Path(result_path).resolve())
            
            # 비교 정보 저장
            if self.db_type == 'sqlite':
                insert_comparison = """
                INSERT INTO comparisons 
                (comparison_date, oc_file_path, invoice_file_path, result_file_path, 
                total_items, matching_items, mismatch_items, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            else:
                insert_comparison = """
                INSERT INTO comparisons 
                (comparison_date, oc_file_path, invoice_file_path, result_file_path, 
                total_items, matching_items, mismatch_items, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
            current_time = datetime.datetime.now()
            self.cursor.execute(insert_comparison, 
                              (current_time, oc_path, invoice_path, result_path, 
                               total_items, matching_items, mismatch_items, status, current_time))
            
            # 마지막 삽입된 ID 가져오기
            if self.db_type == 'sqlite':
                comparison_id = self.cursor.lastrowid
            elif self.db_type == 'mysql':
                comparison_id = self.cursor.lastrowid
            elif self.db_type == 'postgresql':
                self.cursor.execute("SELECT lastval()")
                comparison_id = self.cursor.fetchone()[0]
            
            # 각 제품 정보 저장
            if not df_result.empty:
                for _, row in df_result.iterrows():
                    if self.db_type == 'sqlite':
                        insert_product = """
                        INSERT INTO products
                        (comparison_id, style_code, model, size, 
                        oc_quantity, invoice_quantity, quantity_match,
                        oc_price, invoice_price, price_match,
                        oc_shipping, invoice_shipping, shipping_match,
                        all_match, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                    else:
                        insert_product = """
                        INSERT INTO products
                        (comparison_id, style_code, model, size, 
                        oc_quantity, invoice_quantity, quantity_match,
                        oc_price, invoice_price, price_match,
                        oc_shipping, invoice_shipping, shipping_match,
                        all_match, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                    
                    # 필드명이 존재하는지 확인하고 값 가져오기
                    style_code = row.get('Style_Code', '')
                    model = row.get('Model', '')
                    size = ''  # 사이즈 정보가 없는 경우가 많으므로 기본값 설정
                    
                    oc_quantity = row.get('OC_Quantity', 0)
                    invoice_quantity = row.get('Invoice_Quantity', 0)
                    quantity_match = int(row.get('Quantity_Match', False))
                    
                    oc_price = row.get('OC_Price', 0.0)
                    invoice_price = row.get('Invoice_Price', 0.0)
                    price_match = int(row.get('Price_Match', False))
                    
                    oc_shipping = row.get('OC_Shipping', '')
                    invoice_shipping = row.get('Invoice_Shipping', '')
                    shipping_match = int(row.get('Shipping_Match', False))
                    
                    all_match = int(row.get('All_Match', False))
                    
                    self.cursor.execute(insert_product, 
                                      (comparison_id, style_code, model, size,
                                       oc_quantity, invoice_quantity, quantity_match,
                                       oc_price, invoice_price, price_match,
                                       oc_shipping, invoice_shipping, shipping_match,
                                       all_match, current_time))
            
            self.conn.commit()
            return comparison_id
            
        except Exception as e:
            print(f"결과 저장 오류: {e}")
            self.conn.rollback()
            return None
        finally:
            self.close()
    
    def get_comparison_history(self, limit=10):
        """
        최근 비교 이력 조회
        
        Parameters:
        -----------
        limit : int
            조회할 최대 기록 수
            
        Returns:
        --------
        pandas.DataFrame
            비교 이력 데이터프레임
        """
        if not self.connect():
            return pd.DataFrame()
            
        try:
            if self.db_type == 'sqlite':
                query = """
                SELECT id, comparison_date, oc_file_path, invoice_file_path, result_file_path,
                total_items, matching_items, mismatch_items, status, created_at
                FROM comparisons
                ORDER BY created_at DESC
                LIMIT ?
                """
                self.cursor.execute(query, (limit,))
            else:
                query = """
                SELECT id, comparison_date, oc_file_path, invoice_file_path, result_file_path,
                total_items, matching_items, mismatch_items, status, created_at
                FROM comparisons
                ORDER BY created_at DESC
                LIMIT %s
                """
                self.cursor.execute(query, (limit,))
            
            columns = [desc[0] for desc in self.cursor.description]
            data = self.cursor.fetchall()
            
            return pd.DataFrame(data, columns=columns)
            
        except Exception as e:
            print(f"비교 이력 조회 오류: {e}")
            return pd.DataFrame()
        finally:
            self.close()
    
    def get_comparison_details(self, comparison_id):
        """
        특정 비교의 상세 결과 조회
        
        Parameters:
        -----------
        comparison_id : int
            조회할 비교 ID
            
        Returns:
        --------
        tuple
            (비교 정보 DataFrame, 제품 상세 정보 DataFrame)
        """
        if not self.connect():
            return pd.DataFrame(), pd.DataFrame()
            
        try:
            # 비교 정보 조회
            if self.db_type == 'sqlite':
                comparison_query = """
                SELECT * FROM comparisons WHERE id = ?
                """
                products_query = """
                SELECT * FROM products WHERE comparison_id = ?
                """
                self.cursor.execute(comparison_query, (comparison_id,))
            else:
                comparison_query = """
                SELECT * FROM comparisons WHERE id = %s
                """
                products_query = """
                SELECT * FROM products WHERE comparison_id = %s
                """
                self.cursor.execute(comparison_query, (comparison_id,))
            
            columns = [desc[0] for desc in self.cursor.description]
            comparison_data = self.cursor.fetchone()
            
            if comparison_data is None:
                return pd.DataFrame(), pd.DataFrame()
                
            comparison_df = pd.DataFrame([comparison_data], columns=columns)
            
            # 제품 정보 조회
            self.cursor.execute(products_query, (comparison_id,))
            columns = [desc[0] for desc in self.cursor.description]
            products_data = self.cursor.fetchall()
            
            products_df = pd.DataFrame(products_data, columns=columns)
            
            return comparison_df, products_df
            
        except Exception as e:
            print(f"비교 상세 조회 오류: {e}")
            return pd.DataFrame(), pd.DataFrame()
        finally:
            self.close()
    
    def export_to_excel(self, comparison_id, output_path=None):
        """
        특정 비교 결과를 엑셀 파일로 내보내기
        
        Parameters:
        -----------
        comparison_id : int
            내보낼 비교 ID
        output_path : str, optional
            출력 엑셀 파일 경로
            
        Returns:
        --------
        str
            생성된 엑셀 파일 경로
        """
        comparison_df, products_df = self.get_comparison_details(comparison_id)
        
        if comparison_df.empty:
            print(f"ID {comparison_id}에 해당하는 비교 결과가 없습니다.")
            return None
            
        # 출력 경로 설정
        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"comparison_export_{comparison_id}_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                comparison_df.to_excel(writer, sheet_name='비교 정보', index=False)
                if not products_df.empty:
                    products_df.to_excel(writer, sheet_name='제품 상세', index=False)
            
            return output_path
            
        except Exception as e:
            print(f"엑셀 내보내기 오류: {e}")
            return None

# DB 연결 설정 예시
def get_db_config(db_type):
    if db_type == 'sqlite':
        return {
            'db_path': 'ocr_results.db'
        }
    elif db_type == 'mysql':
        return {
            'host': 'localhost',
            'user': 'username',
            'password': 'password',
            'database': 'ocr_database',
            'port': 3306
        }
    elif db_type == 'postgresql':
        return {
            'host': 'localhost',
            'user': 'username',
            'password': 'password',
            'database': 'ocr_database',
            'port': 5432
        }
    else:
        return {}

# 사용 예시
def save_results_to_db(oc_path, invoice_path, result_path, df_result, db_type='sqlite'):
    """
    비교 결과를 데이터베이스에 저장하는 함수
    
    Parameters:
    -----------
    oc_path : str
        OC 문서 파일 경로
    invoice_path : str
        인보이스 문서 파일 경로
    result_path : str
        결과 엑셀 파일 경로
    df_result : pandas.DataFrame
        비교 결과 데이터프레임
    db_type : str, optional
        데이터베이스 유형 ('sqlite', 'mysql', 'postgresql')
        
    Returns:
    --------
    int
        저장된 비교 ID (실패 시 None)
    """
    config = get_db_config(db_type)
    db_manager = DatabaseManager(db_type, config)
    return db_manager.save_comparison_result(oc_path, invoice_path, result_path, df_result)

# 통계 및 이력 조회 함수
def get_comparison_history(limit=10, db_type='sqlite'):
    """최근 비교 이력 조회"""
    config = get_db_config(db_type)
    db_manager = DatabaseManager(db_type, config)
    return db_manager.get_comparison_history(limit)

def get_comparison_details(comparison_id, db_type='sqlite'):
    """특정 비교의 상세 결과 조회"""
    config = get_db_config(db_type)
    db_manager = DatabaseManager(db_type, config)
    return db_manager.get_comparison_details(comparison_id)

def export_comparison_to_excel(comparison_id, output_path=None, db_type='sqlite'):
    """특정 비교 결과를 엑셀 파일로 내보내기"""
    config = get_db_config(db_type)
    db_manager = DatabaseManager(db_type, config)
    return db_manager.export_to_excel(comparison_id, output_path)
