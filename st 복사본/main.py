import streamlit as st
from datetime import datetime, timedelta
from ocr.processor import OCRProcessor
from ui.dashboard import DashboardView
from ui.document import DocumentView
from ui.payment import PaymentView
from ui.report import ReportView
from ui.schedule import ScheduleView

st.set_page_config(
    page_title="OCR 문서 관리 시스템",
    page_icon="📄",
    layout="wide"
)

class OCRApp:
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.dashboard_view = DashboardView(self.ocr_processor)
        self.document_view = DocumentView(self.ocr_processor)
        self.payment_view = PaymentView()
        self.report_view = ReportView()
        self.schedule_view = ScheduleView()

    def run(self):
        menu = self.create_sidebar()
        
        if menu == "대시보드":
            self.dashboard_view.show()
        elif menu == "문서 업로드":
            self.document_view.show_upload()
        elif menu == "결제 관리":
            self.payment_view.show()
        elif menu == "보고서 생성":
            self.report_view.show()
        elif menu == "일정 관리":
            self.schedule_view.show()

    def create_sidebar(self):
        with st.sidebar:
            st.title("OCR 문서 관리")
            
            # 메뉴 선택
            selected_menu = st.radio(
                "메뉴",
                ["대시보드", "문서 업로드", "결제 관리", "보고서 생성", "일정 관리"],
                key="sidebar_menu"
            )
            
            # 날짜 필터
            st.subheader("날짜 필터")
            date_range = st.date_input(
                "기간 선택",
                [datetime.now() - timedelta(days=30), datetime.now()],
                key="sidebar_date_range"
            )
            
            # 브랜드 필터
            st.subheader("브랜드 필터")
            brands = ["모든 브랜드", "TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"]
            selected_brand = st.multiselect(
                "브랜드 선택",
                brands,
                default=["모든 브랜드"],
                key="sidebar_brand_filter"
            )
            
            # 상태 필터
            st.subheader("상태 필터")
            status_options = ["모든 상태", "완료", "검토 필요", "처리 중"]
            selected_status = st.multiselect(
                "상태 선택", 
                status_options, 
                default=["모든 상태"],
                key="sidebar_status_filter"
            )

            return selected_menu

if __name__ == "__main__":
    app = OCRApp()
    app.run()
