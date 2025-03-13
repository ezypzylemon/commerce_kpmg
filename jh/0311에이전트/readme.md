# 패션 트렌드 크롤링 에이전트

이 프로젝트는 주요 패션 매체들의 트렌드 기사를 자동으로 수집하여 데이터베이스에 저장하는 크롤링 에이전트입니다.

## 수집 대상 매체
- Vogue Korea
- W Korea
- Jente Store
- WWD Korea
- Marie Claire Korea

## 기능
- 매일 오후 1시에 자동 실행
- 각 매체별 최신 트렌드 기사 수집
- SQLite 데이터베이스에 저장
- 로그 기록 관리

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 프로그램 실행:
```bash
python fashion_trend_agent.py
```

## 데이터베이스 구조

각 매체별로 다음과 같은 테이블이 생성됩니다:
- vogue_trends
- wkorea_trends
- jentestore_trends
- wwdkorea_trends
- marieclaire_trends

### 테이블 구조
- id: 기본 키
- scraping_date: 크롤링 날짜
- upload_date: 기사 업로드 날짜
- editor: 에디터 정보
- title: 기사 제목
- content: 기사 본문
- article_url: 기사 URL (중복 방지용 unique 키)
- created_at: 레코드 생성 시간

## 로그 관리

모든 크롤링 작업의 로그는 `fashion_trend_crawler.log` 파일에 기록됩니다.