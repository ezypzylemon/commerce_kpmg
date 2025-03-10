import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import altair as alt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="OCR 문서 관리 시스템",
    page_icon="📄",
    layout="wide"
)

# 사이드바 생성
with st.sidebar:
    st.title("OCR 문서 관리")
    
    # 메뉴 선택
    selected_menu = st.radio(
        "메뉴",
        ["대시보드", "문서 업로드", "문서 처리", "보고서 생성", "설정"]
    )
    
    # 날짜 필터 (옵션)
    st.subheader("날짜 필터")
    date_range = st.date_input(
        "기간 선택",
        [datetime.now() - timedelta(days=30), datetime.now()]
    )
    
    # 브랜드 필터 (옵션)
    st.subheader("브랜드 필터")
    brands = ["모든 브랜드", "TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"]
    selected_brand = st.multiselect("브랜드 선택", brands, default=["모든 브랜드"])
    
    # 상태 필터 (옵션)
    st.subheader("상태 필터")
    status_options = ["모든 상태", "완료", "검토 필요", "처리 중"]
    selected_status = st.multiselect("상태 선택", status_options, default=["모든 상태"])
    
    st.divider()
    
    # 빠른 액션 버튼
    st.subheader("빠른 액션")
    if st.button("새 문서 업로드", use_container_width=True):
        st.session_state.selected_menu = "문서 업로드"
        
    if st.button("OCR 재처리", use_container_width=True):
        st.info("OCR 재처리가 시작되었습니다.")
        
    if st.button("보고서 생성", use_container_width=True):
        st.session_state.selected_menu = "보고서 생성"
        
    if st.button("AI 문서 비교 어시스턴트", use_container_width=True):
        st.info("AI 어시스턴트가 실행되었습니다.")

# 샘플 데이터 생성 (실제 구현 시에는 데이터베이스에서 가져와야 함)
def load_document_data():
    data = {
        "날짜": ["2025-03-08", "2025-03-07", "2025-03-05", "2025-03-04", "2025-03-01"],
        "브랜드": ["TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"],
        "시즌": ["2024SS", "2024SS", "2024SS", "2024SS", "2024SS"],
        "일치율": [75, 100, 62.5, 40, 100],
        "상태": ["완료", "완료", "완료", "검토 필요", "완료"],
        "문서ID": ["doc001", "doc002", "doc003", "doc004", "doc005"]
    }
    return pd.DataFrame(data)

def load_document_files():
    data = {
        "파일명": ["AF_Sports_Invoice_22-03-2025.pdf", 
                "UrbanStreet_PO_18-03-2025.pdf", 
                "MetroStyles_Invoice_10-03-2025.pdf", 
                "FitPlus_Contract_05-03-2025.pdf"],
        "문서타입": ["인보이스", "발주서", "인보이스", "계약서"],
        "날짜": ["2025-03-09", "2025-03-08", "2025-03-07", "2025-03-05"],
        "상태": ["완료", "검토 중", "검토 필요", "완료"],
        "일치율": [92, 78, 45, 89]
    }
    return pd.DataFrame(data)

def get_document_details(doc_id):
    # 실제 구현에서는 DB에서 특정 문서 상세 정보를 가져와야 함
    details = {
        "doc002": {
            "문서타입": "발주서",
            "브랜드명": "URBAN STREET COLLECTION",
            "메인라인": "메인 라인",
            "금액": "₩8,750",
            "날짜": "2025-03-08",
            "품목": [
                {"품목명": "Casual Shirts", "수량": 40, "단가": "₩95", "합계": "₩3,800"},
                {"품목명": "Jeans", "수량": 35, "단가": "₩125", "합계": "₩4,375"}
            ]
        }
    }
    return details.get(doc_id, {})

# 대시보드 화면
def show_dashboard():
    st.title("OCR 문서 관리 대시보드")
    
    # 검색창
    st.text_input("브랜드 또는 시즌 검색...", placeholder="검색어를 입력하세요")
    
    # 첫 번째 행: 핵심 지표
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="총 문서 수", value="125")
    
    with col2:
        st.metric(label="평균 일치율", value="75.5%")
    
    with col3:
        st.metric(label="검토 필요", value="12")
    
    with col4:
        st.metric(label="이번 주 처리", value="28", delta="+5")
    
    # 두 번째 행: 차트와 그래프
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("전체 일치/불일치 비율")
        match_rate = 77
        
        # 파이 차트
        fig = go.Figure(data=[go.Pie(
            labels=['일치', '불일치'],
            values=[match_rate, 100-match_rate],
            hole=.3,
            marker_colors=['#4CAF50', '#E57373']
        )])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("알림")
        
        alert1 = st.error("BASERANGE 검토 필요: 일치율 40% - 3개 항목 불일치")
        alert2 = st.warning("ATHLETICS FTWR 검토 완료: 3일 전 - 일치율 62.5%")
        alert3 = st.success("NOU NOU 완전 일치: 9일 전 - 일치율 100%")
    
    # 세 번째 행: 최근 문서 비교 결과 테이블
    st.subheader("최근 문서 비교 결과")
    
    df = load_document_data()
    
    # 상태 색상 적용
    def highlight_status(val):
        if val == "완료":
            return 'background-color: #C8E6C9; color: #2E7D32'
        elif val == "검토 필요":
            return 'background-color: #FFCDD2; color: #C62828'
        else:
            return 'background-color: #FFE0B2; color: #E65100'
    
    # 일치율 색상 적용
    def highlight_match_rate(val):
        if val >= 90:
            return 'color: #2E7D32'
        elif val >= 60:
            return 'color: #E65100'
        else:
            return 'color: #C62828'
    
    # 스타일 적용
    styled_df = df.style.applymap(highlight_status, subset=['상태'])
    styled_df = styled_df.applymap(highlight_match_rate, subset=['일치율'])
    
    # 일치율 표시를 퍼센트로 변경
    df['일치율'] = df['일치율'].astype(str) + '%'
    
    # 테이블 표시
    st.dataframe(df, use_container_width=True)
    
    # 네 번째 행: 일치율 추이
    st.subheader("일치율 추이 (최근 30일)")
    
    # 샘플 일치율 추이 데이터
    dates = pd.date_range(end=datetime.now(), periods=30)
    rates = np.random.randint(60, 100, size=30)
    trend_df = pd.DataFrame({'날짜': dates, '일치율': rates})
    
    # 추이 차트
    chart = alt.Chart(trend_df).mark_line(point=True).encode(
        x='날짜:T',
        y=alt.Y('일치율:Q', scale=alt.Scale(domain=[50, 100])),
        tooltip=['날짜', '일치율']
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)

# 문서 업로드 화면
def show_document_upload():
    st.title("문서 업로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("새 문서 업로드")
        uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type=["pdf"])
        
        if uploaded_file is not None:
            st.success(f"{uploaded_file.name}이 업로드 되었습니다.")
            
            doc_type = st.selectbox(
                "문서 타입 선택",
                ["인보이스", "발주서", "계약서", "견적서", "기타"]
            )
            
            brand = st.text_input("브랜드명")
            
            season = st.selectbox(
                "시즌",
                ["2024SS", "2024FW", "2025SS", "2025FW"]
            )
            
            if st.button("OCR 처리 시작", type="primary", use_container_width=True):
                st.info("OCR 처리가 시작되었습니다. 잠시만 기다려주세요...")
                st.success("문서가 성공적으로 처리되었습니다.")
    
    with col2:
        st.subheader("대량 업로드")
        uploaded_files = st.file_uploader("여러 파일을 선택하세요", type=["pdf"], accept_multiple_files=True)
        
        if uploaded_files:
            st.write(f"{len(uploaded_files)}개의 파일이 업로드 되었습니다.")
            
            default_type = st.selectbox(
                "기본 문서 타입 선택",
                ["자동 감지", "인보이스", "발주서", "계약서"]
            )
            
            if st.button("대량 처리 시작", type="primary", use_container_width=True):
                st.info("대량 처리가 시작되었습니다. 이 작업은 시간이 소요될 수 있습니다...")
                progress_bar = st.progress(0)
                
                for i in range(100):
                    # 실제 구현에서는 여기에 처리 로직 구현
                    progress_bar.progress(i + 1)
                
                st.success("모든 문서가 성공적으로 처리되었습니다.")

# 문서 처리 화면
def show_document_processing():
    st.title("문서 처리")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("문서 목록")
        
        df = load_document_files()
        
        for index, row in df.iterrows():
            with st.container():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    doc_name = row["파일명"]
                    st.write(f"**{doc_name}**")
                    st.caption(f"{row['문서타입']} • {row['날짜']}")
                    
                    # 프로그레스 바 색상
                    bar_color = "green"
                    if row["일치율"] < 60:
                        bar_color = "red"
                    elif row["일치율"] < 90:
                        bar_color = "orange"
                    
                    st.progress(row["일치율"] / 100, text=f"{row['일치율']}%")
                
                with col_b:
                    if st.button("보기", key=f"view_{index}"):
                        st.session_state.selected_doc = "doc002" if index == 1 else "unknown"
                
                st.divider()
    
    with col2:
        st.subheader("문서 상세")
        
        if "selected_doc" in st.session_state:
            doc_id = st.session_state.selected_doc
            doc_details = get_document_details(doc_id)
            
            if doc_details:
                st.write(f"### {doc_id}")
                
                col_a, col_b = st.columns([1, 1])
                
                with col_a:
                    st.write("**원본 문서**")
                    st.image("https://via.placeholder.com/400x500?text=PDF+Preview", use_column_width=True)
                
                with col_b:
                    st.write("**문서 정보**")
                    
                    # 기본 정보
                    info_table = pd.DataFrame({
                        "필드": ["문서 타입", "인식된 브랜드명", "메인라인 브랜드", "금액", "날짜"],
                        "값": [
                            doc_details.get("문서타입", ""),
                            doc_details.get("브랜드명", ""),
                            doc_details.get("메인라인", ""),
                            doc_details.get("금액", ""),
                            doc_details.get("날짜", "")
                        ]
                    })
                    
                    st.table(info_table)
                    
                    # 품목 정보
                    if "품목" in doc_details:
                        st.write("**품목 정보**")
                        items_df = pd.DataFrame(doc_details["품목"])
                        st.table(items_df)
                    
                    # 알림 상자
                    st.warning(
                        """
                        **브랜드 매핑 필요**
                        
                        "URBAN STREET COLLECTION"는 어떤 마스터 브랜드와 연결합니까?
                        """
                    )
                    
                    col_x, col_y = st.columns([3, 1])
                    
                    with col_x:
                        brand_mapping = st.selectbox(
                            "브랜드 선택",
                            ["브랜드 선택...", "Urban Street", "UrbanStreet Collection", "Urban Collection"]
                        )
                    
                    with col_y:
                        if st.button("매핑 저장"):
                            st.success("브랜드 매핑이 저장되었습니다.")
            else:
                st.info("문서를 선택하세요")
        else:
            st.info("왼쪽에서 문서를 선택하세요")

# 보고서 생성 화면
def show_report_generation():
    st.title("보고서 생성")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("보고서 유형")
        
        report_type = st.selectbox(
            "보고서 유형 선택",
            ["일치율 보고서", "브랜드별 통계", "문서 처리 현황", "오류 분석"]
        )
        
        date_range = st.date_input(
            "기간 선택",
            [datetime.now() - timedelta(days=30), datetime.now()]
        )
        
        st.multiselect(
            "브랜드 선택",
            ["모든 브랜드", "TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"],
            default=["모든 브랜드"]
        )
        
        format_options = st.radio(
            "출력 형식",
            ["PDF", "Excel", "CSV", "온라인 대시보드"]
        )
        
        if st.button("보고서 생성", type="primary", use_container_width=True):
            st.success("보고서가 생성되었습니다.")
            st.download_button(
                label="보고서 다운로드",
                data="샘플 보고서 데이터",
                file_name=f"OCR_{report_type}_{date_range[0]}-{date_range[1]}.pdf",
                mime="application/pdf"
            )
    
    with col2:
        st.subheader("보고서 미리보기")
        
        if report_type == "일치율 보고서":
            # 샘플 일치율 데이터
            brands = ["TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"]
            match_rates = [75, 100, 62.5, 40, 100]
            
            fig = px.bar(
                x=brands, 
                y=match_rates,
                title="브랜드별 평균 일치율",
                labels={'x':'브랜드', 'y':'일치율 (%)'},
                color=match_rates,
                color_continuous_scale=[(0, "red"), (0.6, "orange"), (1, "green")],
                range_color=[0, 100]
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 일치율 추세
            dates = pd.date_range(start=date_range[0], end=date_range[1])
            trend_data = pd.DataFrame({
                '날짜': dates,
                '일치율': np.random.normal(75, 10, size=len(dates))
            })
            
            fig2 = px.line(
                trend_data, 
                x='날짜', 
                y='일치율',
                title="기간별 일치율 추세"
            )
            
            st.plotly_chart(fig2, use_container_width=True)

# 설정 화면
def show_settings():
    st.title("시스템 설정")
    
    tab1, tab2, tab3 = st.tabs(["기본 설정", "OCR 설정", "사용자 관리"])
    
    with tab1:
        st.subheader("기본 설정")
        
        st.toggle("브랜드 자동 매핑 활성화", value=True)
        st.toggle("새 문서 알림 받기", value=True)
        st.toggle("일치율 낮은 문서 자동 플래그", value=True)
        
        threshold = st.slider("일치율 임계값 설정", 0, 100, 60, 5, format="%d%%")
        st.write(f"일치율이 {threshold}% 미만인 문서는 자동으로 '검토 필요'로 표시됩니다.")
        
        default_lang = st.selectbox(
            "기본 OCR 언어",
            ["한국어", "영어", "일본어", "중국어", "자동 감지"]
        )
    
    with tab2:
        st.subheader("OCR 설정")
        
        ocr_engine = st.selectbox(
            "OCR 엔진 선택",
            ["기본 OCR", "고급 OCR", "AI 강화 OCR"]
        )
        
        st.write("**인식 최적화**")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.checkbox("표 인식 향상", value=True)
            st.checkbox("로고 인식", value=True)
            st.checkbox("날짜 형식 자동 변환", value=True)
        
        with col_b:
            st.checkbox("통화 기호 인식", value=True)
            st.checkbox("손글씨 인식", value=False)
            st.checkbox("바코드/QR코드 인식", value=True)
        
        st.write("**처리 설정**")
        
        batch_size = st.number_input("배치 처리 크기", min_value=1, max_value=100, value=10)
        threads = st.slider("동시 처리 스레드", 1, 8, 4)
    
    with tab3:
        st.subheader("사용자 관리")
        
        users = pd.DataFrame({
            "사용자": ["관리자", "사용자1", "사용자2", "사용자3"],
            "역할": ["관리자", "편집자", "뷰어", "편집자"],
            "마지막 로그인": ["2025-03-10", "2025-03-09", "2025-03-08", "2025-03-07"]
        })
        
        st.dataframe(users, use_container_width=True)
        
        with st.expander("새 사용자 추가"):
            st.text_input("이메일 주소")
            st.selectbox("역할 부여", ["관리자", "편집자", "뷰어"])
            st.button("사용자 추가")

# 메인 앱 로직
if __name__ == "__main__":
    # 선택된 메뉴에 따라 화면 표시
    if selected_menu == "대시보드":
        show_dashboard()
    elif selected_menu == "문서 업로드":
        show_document_upload()
    elif selected_menu == "문서 처리":
        show_document_processing()
    elif selected_menu == "보고서 생성":
        show_report_generation()
    elif selected_menu == "설정":
        show_settings()
