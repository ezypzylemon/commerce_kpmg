import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from naverKeywordsAPI import NaverKeywordTool
import mysql.connector
from config import MYSQL_CONFIG
from datetime import datetime

# 1. 환경 변수 불러오기
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Gemini 모델 세팅
model = genai.GenerativeModel("gemini-2.0-flash")

# 3. 프롬프트 생성 함수
def generate_prompt(keyword, rel_keywords, docs_text):
    prompt = f"""
    주요 키워드: {keyword}
    연관 키워드: {', '.join(rel_keywords)}
    관련 문서 내용:
    {docs_text}

    위 정보를 기반으로 패션 바잉MD를 위한 분석을 해 주세요

    다음 ReAct 프레임워크를 사용하여 시각화 데이터를 넘어선 심층 분석을 수행해주세요:

    사고(Reasoning): 핵심키워드와 연관 키워드에서 어떤 패턴이나 관계성을 찾아볼 수 있을지 계획하세요. 상관관계, 시간적 변화, 매거진 간 차이점 등을 고려하세요.
    행동(Acting): 다음과 같은 구체적인 분석을 수행하세요:
    키워드와 컬러/소재/프린트 간의 연관성 파악
    특정 시즌이나 이벤트가 트렌드에 미치는 영향 분석
    글로벌 이슈(지속가능성, 팬데믹 등)와 트렌드 연결점 찾기
    매거진별 독특한 편집 경향과 타겟 소비자층 유추
    관찰(Observation): 분석 결과에서 발견한 인사이트를 구체적으로 기록하세요. 숫자와 사실을 넘어 맥락과 의미를 파악하세요.
    다음 단계 계획: 발견한 인사이트를 바탕으로 더 심층적인 질문이나 가설을 설정하세요.

    각 주제별로 위 과정을 최소 2회 이상 반복하며, 다음 질문들에 답해주세요:

    왜 특정 키워드/컬러/소재가 지금 부상하고 있는가? (사회문화적 맥락 연결)
    이 트렌드는 어떤 소비자 심리나 니즈를 반영하는가?
    현재 트렌드의 지속 기간은 얼마나 될 것으로 예상되는가?
    다음 시즌에는 어떤 요소가 더 강화되거나 약화될 것인가?
    이 트렌드가 실제 판매와 소비자 행동에 어떻게 영향을 미칠 것인가?

    최종 산출물로 다음을 제공해주세요:

    주요 3-5개 트렌드의 심층 스토리텔링 (단순 데이터를 넘어선 맥락과 의미 부여)
    브랜드 전략 추천: 발견한 트렌드를 활용한 실용적 마케팅/제품 전략

    """
    return prompt

# 4. Gemini 응답 생성 함수
def generate_response_from_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text

# 5. MySQL 연결 함수
def get_mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

# 6. 관련 문서 추출 함수 (최신순 + 링크 포함)
def fetch_docs_text(keyword, rel_keywords, limit=10):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    all_keywords = [keyword] + rel_keywords
    like_clauses = " OR ".join(["content LIKE %s"] * len(all_keywords))
    query = f"""
        SELECT content, article_url
        FROM all_trends
        WHERE {like_clauses}
        ORDER BY upload_date DESC
        LIMIT {limit}
    """
    values = [f"%{kw}%" for kw in all_keywords]
    cursor.execute(query, values)
    rows = cursor.fetchall()

    docs_text = "\n\n".join([row[0] for row in rows])  # 기사 본문 합치기
    urls = [row[1] for row in rows]                   # 기사 링크 리스트

    cursor.close()
    conn.close()
    return docs_text, urls

# 7. txt 저장 함수
def save_output_to_txt(keyword, rel_keywords, urls, gemini_text, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"output_{keyword}_{now}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"[키워드]\n{keyword}\n\n")
        f.write(f"[연관 키워드]\n{', '.join(rel_keywords)}\n\n")
        f.write("[참고 문서 링크]\n")
        for i, link in enumerate(urls, 1):
            f.write(f"{i}. {link}\n")
        f.write("\n[Gemini 트렌드 분석 결과]\n")
        f.write(gemini_text)

    print(f"\n📁 결과가 TXT 파일로 저장되었습니다: {filepath}")


# 8. Naver API 연결
API_KEY = os.getenv("NAVER_API_KEY")
SECRET_KEY = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID = os.getenv("NAVER_CUSTOMER_ID")
tool = NaverKeywordTool(API_KEY, SECRET_KEY, CUSTOMER_ID)

# 9. 실행 로직
if __name__ == "__main__":
    keyword = input("분석할 키워드를 입력하세요: ")

    # (1) 연관 키워드 추출
    df = tool.get_related_keywords(keyword)
    if df is None or df.empty:
        print("❌ 연관 키워드를 찾을 수 없습니다.")
        exit()
    
    rel_keywords = df["relKeyword"].tolist()[:20]

    print("\n✅ 입력한 키워드:", keyword)
    print("🔗 연관 키워드:", ", ".join(rel_keywords))

    # (2) 문서 본문 + 링크 추출 (최신순)
    docs_text, urls = fetch_docs_text(keyword, rel_keywords)

    if not docs_text:
        print("❗ 관련 문서를 찾을 수 없습니다.")
        exit()

    print("\n🔗 참고 문서 링크:")
    for i, link in enumerate(urls, 1):
        print(f"{i}. {link}")

    # (3) Gemini 요약 생성
    prompt = generate_prompt(keyword, rel_keywords, docs_text)
    response = generate_response_from_gemini(prompt)

    print("\n🧠 [Gemini 트렌드 분석 결과]")
    print(response)

    # (4) txt 저장
    save_output_to_txt(keyword, rel_keywords, urls, response)
