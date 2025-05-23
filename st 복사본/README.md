# OCR 문서 관리 시스템

## 프로젝트 개요
OCR을 활용한 인보이스 및 문서 관리 시스템으로, 문서 처리 자동화와 데이터 분석을 제공합니다.

## 시스템 구조

### 1. 메인 애플리케이션 (`main.py`)
- 애플리케이션의 진입점
- 전체 UI 컴포넌트 통합 관리
- 사이드바를 통한 메뉴 네비게이션
- 필터링 기능 (날짜, 브랜드, 상태)

### 2. OCR 처리 모듈

#### 2.1. OCR 프로세서 (`ocr/processor.py`)
- PDF to Image 변환 기능
- 이미지 전처리 및 품질 개선
- OCR 텍스트 추출 및 정규화
- 품번코드 생성 및 데이터 구조화

#### 2.2. OCR 유틸리티 (`ocr/utils.py`)
- OCR 텍스트 정리 함수
- 코드 포맷팅 유틸리티
- 커스텀 코드 생성 기능

### 3. UI 컴포넌트

#### 3.1. 대시보드 (`ui/dashboard.py`)
- 주요 지표 요약 표시
- 실시간 알림 기능
- 캘린더 뷰
- 최근 문서 목록

#### 3.2. 문서 관리 (`ui/document.py`)
- 단일/대량 문서 업로드
- OCR 처리 진행 상황 모니터링
- 처리 결과 미리보기
- 엑셀 파일 다운로드

#### 3.3. 결제 관리 (`ui/payment.py`)
- 결제 현황 대시보드
- 결제 등록 및 관리
- 결제 상세 정보 조회
- 결제 기한 관리

#### 3.4. 보고서 생성 (`ui/report.py`)
- 다양한 보고서 템플릿
- 데이터 시각화
- Excel/PDF/CSV 출력
- 브랜드/시즌별 분석

#### 3.5. 일정 관리 (`ui/schedule.py`)
- 캘린더 기반 일정 관리
- 선적 현황 모니터링
- 일정 등록 및 알림
- 선적 상태 추적

## 주요 기능

### 1. OCR 처리
- PDF 문서 자동 처리
- 텍스트 추출 및 정규화
- 상품 정보 자동 인식
- 품번코드 자동 생성

### 2. 데이터 관리
- 브랜드별 데이터 관리
- 시즌별 데이터 분류
- 결제 정보 관리
- 선적 일정 관리

### 3. 보고서 및 분석
- 브랜드별 분석
- 시즌별 분석
- 결제/선적 현황 분석
- 맞춤형 보고서 생성

### 4. 일정 관리
- 선적 일정 관리
- 결제 일정 관리
- 알림 및 리마인더
- 캘린더 통합 관리

## 기술 스택
- Python 3.8+
- Streamlit
- OpenCV
- Tesseract OCR
- Pandas
- Plotly
- XlsxWriter

## 설치 및 실행 방법
```bash
# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
streamlit run main.py
```
