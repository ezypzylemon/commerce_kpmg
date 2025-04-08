# 매거진 트렌드 분석 모듈

## 주요 기능
1. 매거진별 키워드 분석
2. 공통 키워드 추출
3. 키워드 트렌드 분석
4. TF-IDF 기반 워드클라우드
5. 연관어 네트워크 분석
6. 카테고리별 분포 분석
7. 카드뉴스 표시

## 파일 구조
```
magazine_core/
├── templates/
│   └── magazine.html        # 매거진 탭 메인 템플릿
├── static/                  # 정적 파일 (CSS, JS, 이미지 등)
│   └── style.css           # 스타일시트
├── analyzer.py             # 데이터 분석 로직
├── magazine_data_loader.py # 매거진 데이터 로딩 및 처리
├── app.py                  # Flask 애플리케이션 및 라우팅
└── config.py              # 설정 파일
```

## 주요 클래스 및 함수
1. `Analyzer` 클래스 (analyzer.py)
   - 키워드 분석
   - TF-IDF 분석
   - 연관어 분석
   - 트렌드 분석

2. `MagazineDataLoader` 클래스 (magazine_data_loader.py)
   - 매거진 데이터 로딩
   - 키워드 추출
   - 데이터 전처리

## 사용된 라이브러리
- Flask
- Pandas
- NumPy
- Matplotlib
- NetworkX (연관어 네트워크)
- WordCloud

## 설치 및 실행
1. 필요한 패키지 설치:
```bash
pip install flask pandas numpy matplotlib networkx wordcloud
```

2. 애플리케이션 실행:
```bash
python app.py
```

## 주의사항
- 데이터 캐싱 시간은 config.py에서 설정 가능
- 매거진 데이터는 정기적으로 업데이트 필요
- 이미지 파일은 static 디렉터리에 자동 저장
