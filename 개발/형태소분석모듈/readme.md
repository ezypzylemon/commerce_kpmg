# Hyungtaeso Kiwi

## 개요 (Overview)
`hyungtaeso_kiwi.py`는 Kiwipiepy 라이브러리를 사용하여 한국어 텍스트 데이터에서 명사를 추출하고 분석하는 Python 스크립트입니다. MySQL 데이터베이스에서 텍스트 데이터를 가져와 형태소 분석을 수행하고, 결과를 다시 데이터베이스에 저장합니다.

## 기능 (Features)
- Kiwipiepy를 활용한 한국어 형태소 분석
- MySQL 데이터베이스 연동
- 불용어(stopwords) 필터링
- 명사 추출 및 분석
- 대량 데이터의 배치 처리
- 분석 결과의 데이터베이스 저장
- 분석 통계 제공

## 설치 요구사항 (Requirements)
```
kiwipiepy>=0.8.0
mysql-connector-python
pandas
tqdm
```

## 설치 방법 (Installation)
```bash
pip install kiwipiepy mysql-connector-python pandas tqdm
```

## 설정 (Configuration)
`config.py` 파일을 생성하고 다음과 같이 MySQL 연결 정보를 설정해야 합니다:

```python
# config.py
MYSQL_CONFIG = {
    'host': 'your_mysql_host',
    'user': 'your_mysql_user',
    'password': 'your_mysql_password',
    'database': 'your_mysql_database'
}
```

## 사용 방법 (Usage)
1. `config.py` 파일에 MySQL 연결 정보를 입력합니다.
2. 스크립트 내에서 분석할 테이블 이름을 설정합니다:
   ```python
   table_name = "your_table_name"  # 분석할 테이블 이름
   ```
3. 스크립트를 실행합니다:
   ```bash
   python hyungtaeso_kiwi.py
   ```

## 주요 함수 (Main Functions)
- `extract_nouns(text)`: 텍스트에서 명사만 추출하는 함수
- `get_mysql_connection()`: MySQL 연결을 생성하는 함수
- `load_table_content(table_name, content_col)`: DB에서 콘텐츠를 불러오는 함수
- `save_to_tokenised(df, table_name)`: 분석 결과를 DB에 저장하는 함수
- `run_tokenization(table_name, content_col, batch_size)`: 전체 분석 과정을 실행하는 함수

## 결과 (Output)
- `tokenised` 테이블에 분석 결과 저장
- 빈도가 높은 상위 20개 명사 출력

## MYSQL Table Info
```
CREATE TABLE `tokenised` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'from은 MySQL 예약어이므로 백틱으로 감싸야 함',
  `upload_date` date DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `tokens` json DEFAULT NULL COMMENT '추출된 명사 토큰을 JSON 배열로 저장',
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`)
) ENGINE=InnoDB AUTO_INCREMENT=119 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

## 예시 (Example)
```python
if __name__ == "__main__":
    table_name = "all_trends"
    df_tokens = run_tokenization(table_name)
    # 결과 확인 및 처리...
```

## 주의사항 (Notes)
- MySQL 연결 정보는 `config.py` 파일에 별도로 관리해야 합니다.
- 대량의 데이터를 처리할 경우 메모리 사용에 주의하세요.
- 불용어 목록은 필요에 따라 확장할 수 있습니다.

## 라이센스 (License)
이 프로젝트는 사용자가 지정한 라이센스를 따릅니다.
