from kiwipiepy import Kiwi
import mysql.connector
import pandas as pd
import re
import json
from tqdm import tqdm  # 진행 상황 표시용
from config import MYSQL_CONFIG


# Kiwipiepy 버전 확인
try:
    import pkg_resources
    kiwi_version = pkg_resources.get_distribution("kiwipiepy").version
    print(f"[INFO] Kiwipiepy 버전: {kiwi_version}")
except:
    print("[INFO] Kiwipiepy 버전을 확인할 수 없습니다.")

# Kiwi 객체 생성 (v0.8.0 호환)
kiwi = Kiwi(
    num_workers=4,         # 병렬 처리 워커 수
    load_default_dict=True # 기본 사전 로드
)
print("[INFO] Kiwi 객체가 성공적으로 생성되었습니다.")

# 불용어 정의 (필요에 따라 확장 가능)
stopwords = set([
    '있다', '하다', '되다', '등', '이', '그', '저', '것', '수', '더',
    '은', '는', '도', '으로', '들', '및', '의', '가', '에', '을', '를', '로', '과', '와',
    '한', '또한', '이번', '위한', '통해', '대한'
])

# 형태소 분석 함수: 명사만 추출 + 불용어 제거 + 1글자 이상 (v0.8.0 호환)
def extract_nouns(text):
    try:
        if not text or not isinstance(text, str):
            return []
            
        # v0.8.0 방식으로 형태소 분석 수행
        tokens = kiwi.tokenize(text)
        
        # 명사만 추출 (NNG: 일반명사, NNP: 고유명사)
        nouns = []
        for token in tokens:
            word = token[0]  # 단어
            pos = token[1]   # 품사 태그
            
            # 명사이고 불용어가 아니며 2글자 이상인 경우만 추출
            if pos.startswith('NN') and word not in stopwords and len(word) > 1:
                nouns.append(word)
                
        return nouns
    except Exception as e:
        print(f"[ERROR] 형태소 분석 실패: {str(e)[:100]}")
        return []

# MySQL 연결 함수
def get_mysql_connection():
    # MySQL 설정은 사용자가 제공해야 함
    return mysql.connector.connect(**MYSQL_CONFIG)

# DB에서 content 컬럼 있는 테이블 불러오기
def load_table_content(table_name, content_col="content"):
    try:
        # 테이블명 검증 로직 추가
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise ValueError("테이블명에 허용되지 않은 문자가 포함되어 있습니다")
            
        # 컬럼명 검증 로직 추가
        if not re.match(r'^[a-zA-Z0-9_]+$', content_col):
            raise ValueError("컬럼명에 허용되지 않은 문자가 포함되어 있습니다")
            
        conn = get_mysql_connection()
        
        # pandas.read_sql 사용 시 경고 회피 (SQLAlchemy 사용 권장)
        try:
            from sqlalchemy import create_engine
            # SQLAlchemy 엔진 생성 (여기에 실제 연결 정보 넣어야 함)
            # engine = create_engine('mysql+mysqlconnector://user:password@host/database')
            # df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
            
            # 위 코드가 구현되지 않았으므로 기본 방식 사용
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            cursor.close()
        except ImportError:
            # SQLAlchemy가 없는 경우 기존 방식 사용
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, conn)
            
        conn.close()
        
        if content_col not in df.columns:
            raise ValueError(f"'{content_col}' 컬럼이 {table_name} 테이블에 없습니다.")
        
        return df
    except Exception as e:
        print(f"[ERROR] 테이블 로드 실패: {e}")
        return None

# MySQL 테이블에 결과 저장하는 함수
def save_to_tokenized_trends(df, table_name):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Category 설정: all_trends인 경우 magazine으로 설정
        category = "magazine" if table_name == "all_trends" else table_name
        
        print(f"[INFO] 결과를 tokenized_trends 테이블에 저장합니다. (카테고리: {category})")
        
        # 데이터 삽입
        insert_count = 0
        for _, row in df.iterrows():
            # 필수 필드 확인
            title = row.get('title', None)
            content = row.get('content', None)
            tokens = row.get('tokens', [])
            
            # SQL 삽입 쿼리 생성
            query = """
            INSERT INTO tokenized_trends (category, title, content, tokens)
            VALUES (%s, %s, %s, %s)
            """
            
            # JSON 형식으로 토큰 변환
            tokens_json = json.dumps(tokens, ensure_ascii=False)
            
            # 쿼리 실행
            cursor.execute(query, (category, title, content, tokens_json))
            insert_count += 1
            
            # 1000개 단위로 커밋
            if insert_count % 1000 == 0:
                conn.commit()
                print(f"[INFO] {insert_count}개 레코드 처리 완료...")
        
        # 남은 내용 커밋
        conn.commit()
        
        print(f"[✓] 총 {insert_count}개 레코드를 tokenized_trends 테이블에 저장했습니다.")
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] MySQL 저장 실패: {e}")
        if 'conn' in locals() and conn.is_connected():
            conn.close()
        return False

# 분석 실행 함수
def run_tokenization(table_name, content_col="content", batch_size=1000):
    try:
        print(f"[+] '{table_name}' 테이블에서 형태소 분석 실행 중...")
        df = load_table_content(table_name, content_col)
        
        if df is None or df.empty:
            print("[WARNING] 처리할 데이터가 없습니다.")
            return None
            
        # 첫 번째 데이터에 대한 디버그 출력
        if not df.empty:
            sample_text = df.iloc[0][content_col]
            print(f"\n[DEBUG] 첫 번째 텍스트 샘플: {sample_text[:50]}...")
            
            # 첫 번째 텍스트에 대한 토큰화 테스트
            sample_tokens = kiwi.tokenize(sample_text)
            print(f"[DEBUG] 토큰화 결과 구조: {type(sample_tokens)}")
            if sample_tokens:
                print(f"[DEBUG] 첫 번째 토큰 예시: {sample_tokens[0]}")
                
            # 명사 추출 테스트
            sample_nouns = extract_nouns(sample_text)
            print(f"[DEBUG] 추출된 명사: {sample_nouns}")
            
        # 형태소 분석 시작
        print("[+] 형태소 분석 시작...")
        
        # tqdm으로 진행 상황 표시하며 배치 처리
        tokens_list = []
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size]
            batch_tokens = []
            
            for text in batch[content_col]:
                nouns = extract_nouns(text)
                batch_tokens.append(nouns)
                
            tokens_list.extend(batch_tokens)
        
        # 결과를 데이터프레임에 추가
        df['tokens'] = tokens_list
        
        # 토큰 수 통계
        token_counts = df['tokens'].apply(len)
        total_tokens = token_counts.sum()
        empty_tokens = (token_counts == 0).sum()
        
        print(f"[INFO] 총 {len(df)}개 텍스트에서 {total_tokens}개 명사 추출 완료")
        print(f"[INFO] 빈 토큰 비율: {empty_tokens}/{len(df)} ({empty_tokens/len(df)*100:.1f}%)")
        
        # 결과 컬럼 선택
        if 'id' in df.columns and 'title' in df.columns:
            result_df = df[['id', 'title', content_col, 'tokens']]
        elif 'id' in df.columns:
            result_df = df[['id', content_col, 'tokens']]
        else:
            result_df = df[[content_col, 'tokens']]
            
        print("[✓] 형태소 분석 완료!")
        
        # MySQL에 결과 저장
        save_to_tokenized_trends(df, table_name)
        
        return result_df
    except Exception as e:
        print(f"[ERROR] 토큰화 과정 실패: {e}")
        return None

# 실행 예시
if __name__ == "__main__":
    try:
        # 테이블명 지정
        table_name = "all_trends"  # ← 여기만 바꾸면 됨
        
        # 토큰화 실행
        df_tokens = run_tokenization(table_name)
        
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
            
            # CSV 파일로도 저장 (기존 기능 유지)
            output_file = f"{table_name}_tokenized.csv"
            df_tokens.to_csv(output_file, index=False)
            print(f"[✓] 결과가 {output_file} 파일로 저장되었습니다.")
    except Exception as e:
        print(f"[ERROR] 실행 중 오류 발생: {e}")