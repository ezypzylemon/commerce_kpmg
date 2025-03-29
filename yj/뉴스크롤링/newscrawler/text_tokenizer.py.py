import pandas as pd
import mysql.connector
from konlpy.tag import Okt  # 또는 Mecab, Hannanum, Kkma 등 사용 가능
from tqdm import tqdm
import re
from datetime import datetime

# MySQL 연결 설정
def get_mysql_connection(config):
    """MySQL 연결을 생성합니다"""
    return mysql.connector.connect(**config)

# 뉴스 데이터 가져오기
def load_news_data(config, table_name="knews_articles"):
    """지정된 테이블에서 뉴스 데이터를 로드합니다"""
    conn = get_mysql_connection(config)
    query = f"SELECT id, keyword, title, content, published FROM {table_name}"
    
    try:
        df = pd.read_sql(query, conn)
        print(f"총 {len(df)}개의 기사를 로드했습니다.")
        return df
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {e}")
        return None
    finally:
        conn.close()

# 텍스트 전처리
def preprocess_text(text):
    """텍스트를 전처리합니다"""
    if not isinstance(text, str):
        return ""
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', text)
    # 특수문자 제거
    text = re.sub(r'[^\w\s]', ' ', text)
    # 여러 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# 명사 추출
def extract_nouns(text, okt):
    """텍스트에서 명사를 추출합니다"""
    text = preprocess_text(text)
    nouns = okt.nouns(text)
    # 한 글자 명사 제거 (옵션)
    nouns = [noun for noun in nouns if len(noun) > 1]
    return nouns

def save_to_tokenised(config, df, tokenised_db="hyungtaeso", tokenised_table="tokenised"):
    """토큰화 결과를 데이터베이스에 저장합니다"""
    conn = get_mysql_connection(config)
    cursor = conn.cursor()
    
    # 테이블 생성 (없는 경우)
   # 테이블 생성 쿼리에서 외래 키 제약 조건 제거
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {tokenised_db}.{tokenised_table} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        article_id INT NOT NULL,
        category VARCHAR(100),
        title VARCHAR(500),
        content TEXT,
        tokens TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    
    # 데이터 삽입
    insert_query = f"""
    INSERT INTO {tokenised_db}.{tokenised_table}
    (article_id, category, title, content, tokens)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    # 나머지 코드는 동일...
    
    count = 0
    for _, row in tqdm(df.iterrows(), total=len(df), desc="토큰화 결과 저장 중"):
        try:
            cursor.execute(insert_query, (
                row['id'],
                row['keyword'],
                row['title'],
                row['content'][:1000],  # 내용이 너무 길 경우 처음 1000자만 저장
                row['tokens']
            ))
            count += 1
            
            # 100개마다 커밋
            if count % 100 == 0:
                conn.commit()
                
        except Exception as e:
            print(f"ID {row['id']} 저장 중 오류: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"총 {count}개 기사의 토큰화 결과가 저장되었습니다.")

# 다음 부분을 찾아서 수정
def run_tokenization(config, news_table="knews_articles", tokenised_db="hyungtaeso", tokenised_table="tokenised", batch_size=100):
    """전체 토큰화 과정을 실행합니다"""
    print(f"=== {datetime.now()} 토큰화 작업 시작 ===")
    
    # 기존 토큰화 결과 수 확인
    conn = get_mysql_connection(config)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {tokenised_db}.{tokenised_table}")
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"이미 {existing_count}개의 토큰화 결과가 있습니다.")
        choice = input("기존 데이터를 모두 삭제하고 다시 시작하시겠습니까? (y/n): ")
        if choice.lower() == 'y':
            cursor.execute(f"TRUNCATE TABLE {tokenised_db}.{tokenised_table}")
            conn.commit()
            print("기존 데이터를 모두 삭제했습니다.")
        else:
            print("기존 데이터를 유지하고 계속합니다.")
            # 이미 처리된 article_id 목록
            cursor.execute(f"SELECT article_id FROM {tokenised_db}.{tokenised_table}")
            processed_ids = [row[0] for row in cursor.fetchall()]
    else:
        processed_ids = []
    
    cursor.close()
    conn.close()
    
    # 뉴스 데이터 로드
    news_df = load_news_data(config, table_name=news_table)
    if news_df is None or len(news_df) == 0:
        print("처리할 뉴스 데이터가 없습니다.")
        return
    
    # 미처리 데이터만 필터링
    if processed_ids:
        news_df = news_df[~news_df['id'].isin(processed_ids)]
        print(f"미처리 기사 {len(news_df)}개를 처리합니다.")
    
    if len(news_df) == 0:
        print("모든 기사가 이미 처리되었습니다.")
        return
    
    # 형태소 분석기 초기화
    okt = Okt()
    print("형태소 분석기가 초기화되었습니다.")
    
    # 배치 처리
    for i in range(0, len(news_df), batch_size):
        batch_df = news_df.iloc[i:i+batch_size].copy()
        
        print(f"배치 {i//batch_size + 1}/{(len(news_df)-1)//batch_size + 1} 처리 중...")
        
        # 제목과 내용 토큰화
        batch_df['tokens'] = batch_df.apply(
            lambda row: ' '.join(
                extract_nouns(row['title'], okt) + 
                extract_nouns(row['content'], okt)
            ), 
            axis=1
        )
        
        # 결과 저장
        save_to_tokenised(config, batch_df, tokenised_table)
    
    print(f"=== {datetime.now()} 토큰화 작업 완료 ===")

if __name__ == "__main__":
    try:
        # 테이블명 지정 - 한국섬유신문 테이블로 변경
        table_name = "knews_articles"  # 뉴스 테이블명
        content_col = "content"        # 내용 컬럼명
        
        # 토큰화 실행
        df_tokens = run_tokenization(table_name, content_col)
        
        if df_tokens is not None:
            # 샘플 확인
            print("\n[+] 처리 결과 샘플:")
            print(df_tokens.head(10))
            
            # 토큰 추출 통계
            empty_tokens = df_tokens['tokens'].apply(lambda x: len(x) == 0).sum()
            total_rows = len(df_tokens)
            print(f"\n[INFO] 총 {total_rows}개 중 {empty_tokens}개 행의 토큰이 비어 있습니다. ({empty_tokens/total_rows*100:.1f}%)")
            
            # 가장 많이 등장하는 명사 Top 20 출력
            all_nouns = []
            for tokens in df_tokens['tokens']:
                all_nouns.extend(tokens)
                
            from collections import Counter
            noun_counter = Counter(all_nouns)
            print("\n[INFO] 가장 많이 등장하는 명사 Top 20:")
            for noun, count in noun_counter.most_common(20):
                print(f"  - {noun}: {count}회")

    except Exception as e:
        print(f"[ERROR] 실행 중 오류 발생: {e}")