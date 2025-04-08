from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from core.competitor_analyzer import generate_competitor_analysis, generate_competitor_analysis_by_date

# 데이터 디렉토리 생성
DATA_DIR = os.path.join('data')
os.makedirs(DATA_DIR, exist_ok=True)

# 정적 파일 디렉토리 생성
STATIC_DIR = os.path.join('static', 'images', 'competitor')
os.makedirs(STATIC_DIR, exist_ok=True)

# Flask 애플리케이션 생성
app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/')
def index():
    """메인 페이지 - 경쟁사 분석 페이지로 리다이렉트"""
    return redirect(url_for('competitor_analysis'))

@app.route('/competitor')
def competitor_analysis():
    """경쟁사 분석 페이지"""
    # URL 파라미터에서 기간 또는 날짜 범위 가져오기
    period = request.args.get('period', '1개월')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 기간 옵션 매핑
    period_options = {
        '1w': '1주일',
        '1m': '1개월',
        '3m': '3개월',
        '6m': '6개월',
        '1y': '1년',
        '2y': '2년'
    }
    
    # 약어 변환
    if period in period_options:
        period = period_options[period]
    
    # 데이터 파일 경로
    data_path = os.path.join(DATA_DIR, 'musinsa_data.csv')
    
    # 파일이 존재하지 않으면 에러 페이지
    if not os.path.exists(data_path):
        error_message = "데이터 파일이 존재하지 않습니다. data 디렉토리에 musinsa_data.csv 파일을 넣어주세요."
        return render_template('error.html', error=error_message)
    
    # 결과 데이터
    result = None
    
    # 데이터 로딩
    try:
        if start_date and end_date:
            result = generate_competitor_analysis_by_date(data_path, start_date, end_date)
        else:
            result = generate_competitor_analysis(data_path, period)
        
        # 전달할 데이터 없는 경우
        if result is None:
            error_message = "데이터 분석 중 오류가 발생했습니다."
            return render_template('error.html', error=error_message)
        
        # 현재 선택된 기간
        current_period = period
        
        # 선택된 날짜 범위가 있는 경우
        date_range = None
        if start_date and end_date:
            date_range = {
                'start': start_date,
                'end': end_date
            }
            current_period = '직접설정'
        
        # 결과 반환
        return render_template(
            'competitor_analysis.html',
            data=result,
            current_period=current_period,
            date_range=date_range
        )
    
    except Exception as e:
        error_message = f"데이터 분석 중 오류가 발생했습니다: {str(e)}"
        return render_template('error.html', error=error_message)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 