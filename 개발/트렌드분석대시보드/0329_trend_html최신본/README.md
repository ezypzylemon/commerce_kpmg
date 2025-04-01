# Fashion Trend Dashboard

패션 트렌드 분석 대시보드는 패션 산업의 트렌드를 실시간으로 모니터링하고 분석하기 위한 웹 애플리케이션입니다. 뉴스, 매거진, 무신사 등 다양한 데이터 소스에서 수집한 정보를 시각화하여 패션 트렌드를 직관적으로 이해할 수 있게 해줍니다.

## 주요 기능

- **통합 대시보드**: 매거진별 주요 키워드, 카드 뉴스, 키워드 네트워크, 카테고리 분포 등 종합적인 정보 제공
- **뉴스 탭**: 최신 뉴스 기사 헤드라인, 키워드 트렌드, 긍정/부정 기사 분석
- **무신사/경쟁사 분석 탭**: 인기 아이템, 카테고리별 추이, 인기 브랜드 등 경쟁사 분석
- **매거진 탭**: 주요 패션 매거진별 키워드 분석, 카테고리별 트렌드 분석

## 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **데이터베이스**: MySQL
- **시각화**: Matplotlib, NetworkX, WordCloud
- **데이터 분석**: Pandas, NumPy, Scikit-learn

## 설치 방법

1. 저장소 클론
   ```bash
   git clone https://github.com/yourusername/fashion-trend-dashboard.git
   cd fashion-trend-dashboard
   ```

2. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정
   - `.env.example` 파일을 `.env`로 복사하고 적절한 값 설정
   ```bash
   cp .env.example .env
   ```

5. 애플리케이션 실행
   ```bash
   python app.py
   ```

## 환경 변수

`.env` 파일에 다음 환경 변수를 설정해야 합니다:

```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=fashion_trend
DB_CHARSET=utf8mb4

APP_DEBUG=True
SECRET_KEY=your_secret_key
```

## 프로젝트 구조

```
fashion-trend-dashboard/
├── app.py                   # 메인 애플리케이션 파일
├── config.py                # 설정 파일
├── requirements.txt         # 의존성 목록
├── .env                     # 환경 변수 (git에 포함되지 않음)
├── .gitignore
├── README.md
├── data/
│   ├── analyzer.py          # 데이터 분석 모듈
│   ├── db_connector.py      # 데이터베이스 연결 모듈
│   ├── magazine_data_loader.py  # 매거진 데이터 로더
│   └── data_loader.py       # 일반 데이터 로더
├── static/
│   ├── images/              # 차트 이미지 저장 디렉토리
│   └── style.css            # 스타일시트
├── templates/
│   ├── base.html            # 기본 템플릿
│   ├── dashboard.html       # 통합 대시보드 템플릿
│   ├── news.html            # 뉴스 탭 템플릿
│   ├── magazine.html        # 매거진 탭 템플릿
│   ├── competitor_analysis.html  # 경쟁사 분석 탭 템플릿
│   └── error.html           # 오류 페이지 템플릿
└── utils/
    ├── cache_helper.py      # 캐싱 유틸리티
    ├── chart_utils.py       # 차트 생성 유틸리티
    └── visualizer.py        # 시각화 모듈
```

## 데이터베이스 스키마

주요 테이블 구조:

- `magazine_tokenised`: 토큰화된 매거진/뉴스 데이터
  - `id`: 문서 ID
  - `doc_domain`: 문서 도메인 (매거진, 뉴스, 무신사 등)
  - `upload_date`: 업로드 날짜
  - `tokens`: 토큰화된 텍스트
  - `source`: 출처 (Vogue, W, Harper's 등)

## 캐싱 전략

- 빈번히 접근되는 데이터와 계산 비용이 큰 연산 결과를 캐싱합니다.
- 기본 캐싱 시간은 1시간으로 설정되어 있습니다.
- `cache_helper.py`에서 캐싱 관련 유틸리티 함수를 제공합니다.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.