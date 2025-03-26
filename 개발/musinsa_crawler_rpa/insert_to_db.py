import csv
import mysql.connector
from mysql.connector import Error
import glob
import os
from datetime import datetime

def create_connection(host_name, user_name, user_password, db_name=None):
    """MySQL 데이터베이스 연결 생성"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL 데이터베이스에 성공적으로 연결되었습니다")
    except Error as e:
        print(f"에러: {e}")
    
    return connection

def create_database(connection, query):
    """데이터베이스 생성"""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("데이터베이스가 성공적으로 생성되었습니다")
    except Error as e:
        print(f"에러: {e}")

def execute_query(connection, query):
    """쿼리 실행 (테이블 생성, 데이터 삽입 등)"""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("쿼리가 성공적으로 실행되었습니다")
    except Error as e:
        print(f"에러: {e}")

def insert_csv_data(connection, csv_file_path, table_name, columns):
    """CSV 파일 데이터를 MySQL 테이블에 삽입"""
    cursor = connection.cursor()
    
    # 삽입할 데이터를 저장할 리스트
    data_to_insert = []
    
    # CSV 파일 읽기
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        
        # 헤더가 있으면 다음 행부터 시작
        next(csvreader, None)  # 헤더 건너뛰기 (첫 번째 행이 헤더인 경우)
        
        # 각 행을 읽어 데이터 리스트에 추가
        for row in csvreader:
            data_to_insert.append(tuple(row))
    
    # 쿼리 준비
    placeholders = ', '.join(['%s'] * len(columns.split(',')))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    try:
        # 대량 데이터 삽입 실행
        cursor.executemany(query, data_to_insert)
        connection.commit()
        print(f"{cursor.rowcount} 개의 레코드가 테이블에 성공적으로 삽입되었습니다.")
    except Error as e:
        print(f"에러: {e}")

# 사용 예시
def main():
    # 데이터베이스 연결 정보
    host = "localhost"
    user = "root"
    password = "9999"  # 여기에 설정한, 실제 비밀번호를 입력하세요
    database_name = "fashion_trend"  # 사용할 데이터베이스 이름
    
    # 오늘 날짜 기준 경로 설정
    today = datetime.today().strftime('%Y-%m-%d')
    reports_dir = f"/Users/jiyeonjoo/Documents/GitHub/commerce_kpmg/yj/0324/fashion_trend_analysis/reports/{today}"

    # 가장 최신의 musinsa_products CSV 파일 찾기
    product_csv_candidates = glob.glob(os.path.join(reports_dir, "musinsa_products_*.csv"))
    if not product_csv_candidates:
        raise FileNotFoundError(f"{reports_dir} 안에 musinsa_products_*.csv 파일이 없습니다.")
    csv_file = max(product_csv_candidates, key=os.path.getmtime)
    
    # 테이블 정보
    table_name = "musinsa_products"  # 삽입할 테이블 이름
    table_columns = "product_id, brand, name, price, category, category_code, rating, review_count, link, crawled_at"  # 테이블 컬럼 이름 (CSV 파일 순서와 일치해야 함)
    
    # 1. 초기 연결 (데이터베이스 없이)
    connection = create_connection(host, user, password)
    
    # 2. 데이터베이스 생성 (필요한 경우)
    create_database_query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
    create_database(connection, create_database_query)
    
    # 3. 데이터베이스에 연결
    connection = create_connection(host, user, password, database_name)
    
    # 4. 테이블 생성 (필요한 경우)
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        product_id VARCHAR(50) PRIMARY KEY,
        brand VARCHAR(100),
        name TEXT,
        price VARCHAR(20),
        category VARCHAR(100),
        category_code INT,
        rating FLOAT,
        review_count INT,
        link TEXT,
        crawled_at DATETIME
    )
    """
    execute_query(connection, create_table_query)
    
    # 5. CSV 데이터 삽입
    insert_csv_data(connection, csv_file, table_name, table_columns)
    
    # 6. 연결 종료
    if connection and connection.is_connected():
        connection.close()
        print("MySQL 연결이 종료되었습니다")

if __name__ == "__main__":
    main()