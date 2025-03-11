import streamlit as st
import os
import tempfile
import numpy as np
from datetime import datetime, timedelta
from ocr.processor import OCRProcessor
from ui.dashboard import DashboardView
from ui.document import DocumentView
from ui.payment import PaymentView
from ui.report import ReportView
from ui.schedule import ScheduleView

# 스트림릿 페이지 설정
st.set_page_config(
    page_title="OCR 문서 관리 시스템",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일 적용
def load_css():
    css = """
    <style>
    /* 기본 테마 커스터마이징 */
    .main {
        background-color: #f0f2f6;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg, .css-1wrcr25, .css-12oz5g7 {
        background-color: #2c2c3c;
    }
    
    .sidebar .sidebar-content {
        background-color: #2c2c3c;
    }
    
    /* 사이드바 텍스트 색상 강화 */
    .sidebar h1, .sidebar h2, .sidebar h3, .sidebar .stMarkdown, .sidebar p, 
    .sidebar span, .sidebar div, .sidebar label, .sidebar button, .sidebar a {
        color: white !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }
    
    /* 캘린더 셀 색상 개선 */
    .calendar-cell div {
        color: #333333 !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    try:
        css_file_path = os.path.join("static", "css", "custom_theme.css")
        if os.path.exists(css_file_path):
            with open(css_file_path, "r", encoding="utf-8") as f:
                css_content = f.read()
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        pass

class OCRApp:
    def __init__(self):
        # 임시 디렉토리 생성 - 파일 업로드 및 처리를 위한 공간
        self.temp_dir = tempfile.mkdtemp()
        
        # 서브모듈 초기화
        self.ocr_processor = OCRProcessor()
        self.dashboard_view = DashboardView(self.ocr_processor)
        self.document_view = DocumentView(self.ocr_processor)
        self.payment_view = PaymentView()
        self.report_view = ReportView()
        self.schedule_view = ScheduleView()
        
        # 세션 상태 초기화
        if 'selected_menu' not in st.session_state:
            st.session_state.selected_menu = "대시보드"
        
        # 필터 상태 초기화
        if 'date_filter' not in st.session_state:
            today = datetime.now()
            st.session_state.date_filter = [today - timedelta(days=30), today]
        
        if 'brand_filter' not in st.session_state:
            st.session_state.brand_filter = ["모든 브랜드"]
            
        if 'status_filter' not in st.session_state:
            st.session_state.status_filter = ["모든 상태"]

    def run(self):
        load_css()
        self.create_sidebar()
        
        selected_menu = st.session_state.selected_menu
        
        if selected_menu == "대시보드":
            self.dashboard_view.show()
        elif selected_menu == "문서 업로드":
            self.document_view.show_upload()
        elif selected_menu == "결제 관리":
            self.payment_view.show()
        elif selected_menu == "보고서 생성":
            self.report_view.show()
        elif selected_menu == "일정 관리":
            self.schedule_view.show()

    def create_sidebar(self):
        with st.sidebar:
            # 앱 타이틀
            st.title("OCR 문서 관리")
            st.markdown("---")
            
            # 메뉴 선택 (라디오 버튼 대신 커스텀 버튼 스타일 적용)
            st.subheader("메뉴")
            
            menu_options = {
                "대시보드": "📊",
                "문서 업로드": "📄",
                "결제 관리": "💳",
                "보고서 생성": "📈",
                "일정 관리": "📅"
            }
            
            for menu, icon in menu_options.items():
                col1, col2 = st.columns([1, 6])
                with col1:
                    st.markdown(f"<div style='font-size:1.2em; color:white;'>{icon}</div>", unsafe_allow_html=True)
                with col2:
                    is_selected = st.session_state.selected_menu == menu
                    if st.button(
                        menu, 
                        key=f"btn_{menu}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True
                    ):
                        st.session_state.selected_menu = menu
                        st.rerun()
            
            st.markdown("---")
            
            # 날짜 필터
            st.subheader("날짜 필터")
            date_range = st.date_input(
                "기간 선택",
                st.session_state.date_filter,
                key="sidebar_date_range"
            )
            if len(date_range) == 2:
                st.session_state.date_filter = date_range
                
            st.markdown("---")
            
            # 브랜드 필터
            st.subheader("브랜드 필터")
            brands = ["모든 브랜드", "TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"]
            selected_brand = st.multiselect(
                "브랜드 선택",
                brands,
                default=st.session_state.brand_filter,
                key="sidebar_brand_filter"
            )
            if selected_brand:
                st.session_state.brand_filter = selected_brand
                
            st.markdown("---")
            
            # 상태 필터
            st.subheader("상태 필터")
            status_options = ["모든 상태", "완료", "처리중", "대기중"]
            selected_status = st.multiselect(
                "상태 선택", 
                status_options, 
                default=st.session_state.status_filter,
                key="sidebar_status_filter"
            )
            if selected_status:
                st.session_state.status_filter = selected_status
                
            st.markdown("---")
            
            # 필터 적용/초기화 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("필터 적용", type="primary", use_container_width=True):
                    st.success("필터가 적용되었습니다.")
            with col2:
                if st.button("필터 초기화", use_container_width=True):
                    st.session_state.date_filter = [datetime.now() - timedelta(days=30), datetime.now()]
                    st.session_state.brand_filter = ["모든 브랜드"]
                    st.session_state.status_filter = ["모든 상태"]
                    st.rerun()

if __name__ == "__main__":
    app = OCRApp()
    app.run()