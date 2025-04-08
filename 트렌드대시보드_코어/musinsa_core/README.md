# 무신사 경쟁사 분석 시스템

무신사 데이터를 분석하여 브랜드, 카테고리, 가격대별 트렌드를 제공하는 웹 애플리케이션입니다.

## 기능

- 기간별 무신사 데이터 분석
- 브랜드별 트렌드 분석
- 카테고리별 분포 분석
- 가격대별 분포 분석
- 상위 10개 브랜드 목록 제공

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 데이터 파일 준비:
- `data/musinsa_data.csv` 파일을 준비합니다.
- CSV 파일은 다음 컬럼을 포함해야 합니다:
  - date 또는 published_at: 날짜 정보
  - brand: 브랜드 정보
  - category: 카테고리 정보
  - price: 가격 정보

## 실행 방법

```bash
python app.py
```

서버가 시작되면 웹 브라우저에서 `http://localhost:5001`로 접속할 수 있습니다.

## 데이터 형식

musinsa_data.csv 파일은 다음과 같은 형식이어야 합니다:

```csv
date,brand,category,price
2024-01-01,브랜드A,상의,29000
2024-01-02,브랜드B,하의,39000
...
```

- date: YYYY-MM-DD 형식의 날짜
- brand: 브랜드명
- category: 카테고리명
- price: 상품 가격 (원) 