# 패션 키워드 분석 대시보드

패션 매거진 콘텐츠의 키워드와 트렌드를 분석하기 위한 Streamlit 기반 대시보드입니다.

## 주요 기능

- **키워드 트렌드 분석**: 시간에 따른 인기 패션 키워드 추적
- **TF-IDF 분석**: 패션 기사에서 주요 용어 추출
- **키워드 네트워크 시각화**: 패션 키워드 간의 관계 확인
- **아이템 증감률 분석**: 다양한 시간대에 걸친 아이템 언급 비교
- **매거진별 분석**: 패션 매거진 간 키워드 사용 차이 분석

## 요구 사항

- Python 3.8 이상
- 토큰화된 패션 기사 데이터가 있는 MySQL 데이터베이스
- 필요한 Python 패키지 (requirements.txt 참조)

## 설치 방법

1. 리포지토리 복제:
```
git clone https://github.com/yourusername/fashion-analysis-dashboard.git
cd fashion-analysis-dashboard
```

2. 필수 패키지 설치:
```
pip install -r requirements.txt
```

3. MySQL 연결 설정이 포함된 `config.py` 파일 생성:
```python
MYSQL_CONFIG = {
    'host': 'your_host',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database'
}
```

## 사용 방법

다음 명령으로 대시보드 실행:
```
streamlit run dashdash.py
```

## 대시보드 구조

대시보드는 다섯 개의 주요 탭으로 구성되어 있습니다: (근데 1,2,3은 일단 무시하고 4,5만 보셈)

1. **📊 키워드 트렌드**: 
   - 선택한 카테고리의 상위 20개 키워드 확인
   - 워드클라우드를 통한 키워드 빈도 시각화

2. **📈 TF-IDF 분석**: 
   - 개별 기사에서 가장 중요한 키워드 탐색
   - 고유하거나 특징적인 용어 식별

3. **🕸️ 키워드 네트워크**: 
   - 키워드 간의 관계 시각화
   - 함께 자주 등장하는 용어 확인

4. **📉 아이템 증감률 분석**: 
   - 서로 다른 기간에 걸친 특정 아이템의 언급 비교
   - 패션 아이템, 컬러, 소재, 프린트, 스타일의 변화 추적
   - 시간별 주간 트렌드 확인

5. **📰 매거진별 분석**:
   - 다양한 패션 매거진 간 상위 키워드 비교
   - 매거진별 공통 및 고유 키워드 식별
   - 각 매거진의 TF-IDF 대표 키워드 분석
   - 매거진 간 키워드 사용 트렌드 추적

## 데이터 형식

대시보드는 다음 필드를 포함하는 `tokenised` 테이블이 있는 MySQL 데이터베이스를 필요로 합니다:
- `category`: 패션 카테고리
- `upload_date`: 발행일
- `tokens`: 토큰화된 텍스트 (Python 리스트의 문자열 표현으로 저장)
- `source`: 매거진 또는 발행물 이름

## 불용어(Stopwords)

대시보드는 의미 없는 일반적인 용어를 필터링하기 위해 미리 정의된 한국어 불용어 목록을 사용합니다.

## 라이센스

[라이센스 정보]

## 제작자

[이름/회사]
