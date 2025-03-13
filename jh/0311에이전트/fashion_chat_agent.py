import mysql.connector
import google.generativeai as genai
from config import MYSQL_CONFIG, GEMINI_API_KEY
import re
from fashion_analyzer import FashionAnalyzer

class FashionChatbot:
    def __init__(self):
        self.setup_gemini()
        self.tables = ['vogue_trends', 'wkorea_trends', 'jentestore_trends', 
                      'wwdkorea_trends', 'marieclaire_trends']
        self.analyzer = FashionAnalyzer()
        
    def setup_gemini(self):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # 모델 초기화 시 safety_settings 추가
            generation_config = {
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40
            }
            self.model = genai.GenerativeModel(model_name="gemini-pro",  # 수정된 모델명
                                             generation_config=generation_config)
        except Exception as e:
            print(f"Gemini API 설정 오류: {str(e)}")
            raise
        
    def execute_query(self, query):
        try:
            with mysql.connector.connect(**MYSQL_CONFIG) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            return f"쿼리 실행 오류: {str(e)}"

    def natural_to_sql(self, user_input):
        try:
            # 데이터베이스 조회 관련 키워드 처리
            if '조회' in user_input or 'db' in user_input.lower():
                return """
                SELECT 
                    table_name as '테이블명',
                    CONCAT(COUNT(*), '건') as '데이터 수'
                FROM (
                    SELECT 'vogue_trends' as table_name, COUNT(*) as cnt FROM vogue_trends
                    UNION ALL
                    SELECT 'wkorea_trends', COUNT(*) FROM wkorea_trends
                    UNION ALL
                    SELECT 'jentestore_trends', COUNT(*) FROM jentestore_trends
                    UNION ALL
                    SELECT 'wwdkorea_trends', COUNT(*) FROM wwdkorea_trends
                    UNION ALL
                    SELECT 'marieclaire_trends', COUNT(*) FROM marieclaire_trends
                ) as stats;
                """
            # 트렌드 분석 명령 처리
            analysis_keywords = ['분석', '트렌드', '리포트']
            if any(keyword in user_input for keyword in analysis_keywords):
                period = 30  # 기본값
                if '일주일' in user_input or '7일' in user_input:
                    period = 7
                elif '한달' in user_input or '30일' in user_input:
                    period = 30
                
                result = self.analyzer.analyze_trend(period=period)
                if not result:
                    return "죄송합니다. 분석할 데이터가 충분하지 않습니다."
                
                report_file = self.analyzer.generate_report(result)
                keywords = ', '.join(list(result['top_keywords'].keys())[:5])  # 상위 5개만 표시
                return f"트렌드 분석 리포트가 생성되었습니다: {report_file}\n\n주요 키워드(상위 5개): {keywords}"

            # 기본적인 인사말 처리
            greetings = ['안녕', '하이', '헬로', '반가워', '안녕하세요']
            if any(greeting in user_input for greeting in greetings):
                return "안녕하세요! 패션 트렌드 검색을 도와드릴 수 있습니다. 어떤 정보를 찾으시나요?"
            
            # SQL 생성을 위한 프롬프트
            prompt = f"""
            당신은 패션 트렌드 검색 전문가입니다. 다음과 같은 데이터베이스 테이블이 있습니다:
            {', '.join(self.tables)}
            
            테이블 구조:
            - scraping_date: 크롤링 날짜 (YYYY.MM.DD)
            - upload_date: 기사 업로드 날짜
            - editor: 에디터 정보
            - title: 기사 제목
            - content: 기사 본문
            - article_url: 기사 URL
            
            사용자의 질문을 이해하고, 적절한 SQL 쿼리나 답변을 제공하세요.
            사용자 질문: {user_input}
            """
            
            response = self.model.generate_content(prompt)
            if not response.text:
                return "죄송합니다. 질문을 이해하지 못했습니다. 다시 질문해 주시겠어요?"
                
            # 일반 대화인 경우 그대로 반환
            if not response.text.strip().upper().startswith('SELECT'):
                return response.text.strip()
                
            # SQL 쿼리인 경우 검증 후 반환
            sql_query = response.text.strip()
            if any(keyword in sql_query.lower() for keyword in ['drop', 'delete', 'update', 'insert']):
                return "조회 작업만 가능합니다."
                
            return sql_query
            
        except Exception as e:
            print(f"자연어 처리 오류: {str(e)}")
            return "죄송합니다. 오류가 발생했습니다. 다시 시도해 주세요."

    def process_query(self, user_input):
        try:
            response = self.natural_to_sql(user_input)
            
            # SQL이 아닌 일반 응답인 경우
            if not response.strip().upper().startswith('SELECT'):
                return response
            
            # SQL 쿼리 실행
            print(f"\n생성된 SQL 쿼리: {response}\n")
            results = self.execute_query(response)
            return results
            
        except Exception as e:
            return f"오류 발생: {str(e)}"

def main():
    chatbot = FashionChatbot()
    print("패션 트렌드 검색 챗봇이 시작되었습니다. '종료'를 입력하면 프로그램이 종료됩니다.")
    
    while True:
        user_input = input("\n질문을 입력하세요: ")
        if user_input.lower() == '종료':
            break
            
        results = chatbot.process_query(user_input)
        print("\n검색 결과:")
        
        # 에러 메시지인 경우 직접 출력
        if isinstance(results, str):
            print(results)
        # 쿼리 결과인 경우 행별로 출력
        elif isinstance(results, list):
            if not results:
                print("검색 결과가 없습니다.")
            else:
                for row in results:
                    print("-" * 80)
                    for key, value in row.items():
                        if value:  # None이나 빈 문자열이 아닌 경우만 출력
                            print(f"{key}: {value}")
        else:
            print("알 수 없는 결과 형식입니다.")

if __name__ == "__main__":
    main()
