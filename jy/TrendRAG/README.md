# TrendRAG

TrendRAG는 Retrieval-Augmented Generation (RAG)을 사용하여 패션 트렌드 분석을 위한 구조화된 보고서를 생성하는 시스템입니다. 이 프로젝트는 다양한 라이브러리와 API를 활용하여 관련 문서를 가져오고, 임베딩을 생성하며, 입력 쿼리에 기반한 구조화된 보고서를 작성합니다.

## 기능

- `.env` 파일에서 API 키 로드
- ChromaDB에서 관련 문서 가져오기
- `SentenceTransformer`를 사용하여 임베딩 생성
- Google Gemini API를 사용하여 구조화된 보고서 생성
- `StateGraph`를 사용하여 워크플로우 정의 및 실행

## 설치

1. 리포지토리 클론:
    ```sh
    git clone https://github.com/yourusername/TrendRAG.git
    cd TrendRAG
    ```

2. 가상 환경 생성 및 활성화:
    ```sh
    python -m venv venv
    venv\Scripts\activate  # Windows에서 사용
    ```

3. 필요한 패키지 설치:
    ```sh
    pip install -r requirements.txt
    ```

4. 루트 디렉토리에 `.env` 파일을 생성하고 API 키 추가:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    ```

## 사용법

1. Jupyter Notebook 실행:
    ```sh
    jupyter notebook TrendRAG.ipynb
    ```

2. 노트북은 입력 쿼리에 기반하여 구조화된 보고서를 생성하고 콘솔에 출력합니다.

## 예제

```python
query = "2025년 패션 바잉 전략을 위한 트렌드 분석"
report = run_rag(query)
print("\n📊 패션 바잉 전략 보고서:\n")
print(report)