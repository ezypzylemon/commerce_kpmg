# 한국섬유신문 크롤러

한국섬유신문(ktnews.com)의 기사를 자동으로 수집하여 MySQL 데이터베이스에 저장하는 크롤러입니다.

## 기능

- 한국섬유신문 기사 자동 수집
- MySQL 데이터베이스에 기사 저장
- 중복 기사 방지
- 로깅 시스템
- 정기적 크롤링 스케줄링

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/knews-crawler.git
cd knews-crawler
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 설정
`.env` 파일을 수정하여 데이터베이스 접속 정보 등을 설정합니다.

## 사용 방법

### 데이터베이스 초기화
```bash
python main.py --init
```

### 기사 크롤링
```bash
python main.py --pages 10
```

### 특정 페이지부터 크롤링
```bash
python main.py --start-page 5 --pages 10
```

### 정기적 크롤링 설정
```bash
python scheduler.py
```

## 파일 구조

- `main.py`: 메인 실행 파일
- `run_knews_crawler.py`: 크롤링 코드
- `utils.py`: 유틸리티 함수
- `database.py`: 데이터베이스 초기화
- `config.py`: 설정 파일
- `scheduler.py`: 크롤링 스케줄러
- `.env`: 환경 변수 설정
- `requirements.txt`: 필요 패키지 목록

## 데이터베이스 구조

### knews_articles 테이블
- `id`: 기본키
- `keyword`: 키워드
- `title`: 기사 제목
- `link`: 기사 URL (고유)
- `published`: 발행일
- `source`: 출처 (한국섬유신문)
- `content`: 기사 본문
- `created_at`: 저장 시간

## 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다.
