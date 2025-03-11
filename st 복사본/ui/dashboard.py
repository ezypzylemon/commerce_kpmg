import streamlit as st
from datetime import datetime
import calendar
import pandas as pd
import plotly.express as px
import numpy as np

class DashboardView:
    def __init__(self, ocr_manager):
        self.ocr_manager = ocr_manager

    def show(self):
        st.title("OCR 문서 관리 대시보드")
        self.show_quick_actions()
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "📅 캘린더", "📑 문서", "⚙️ 설정"])
        
        with tab1:
            self.show_overview()
        with tab2:
            self.show_calendar()
        with tab3:
            self.show_documents()
        with tab4:
            self.show_settings()

    def show_quick_actions(self):
        st.subheader("⚡ 빠른 액션")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📄 새 문서 업로드", use_container_width=True):
                st.session_state.selected_menu = "문서 업로드"
        
        with col2:
            if st.button("📊 보고서 생성", use_container_width=True):
                st.session_state.selected_menu = "보고서 생성"
        
        with col3:
            if st.button("📅 일정 추가", use_container_width=True):
                st.success("일정 추가 모달이 열립니다.")
        
        with col4:
            if st.button("💳 결제 관리", use_container_width=True):
                st.success("결제 관리 페이지로 이동합니다.")

    def show_calendar(self):
        st.subheader("📅 일정 캘린더")
        today = datetime.now()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_date = st.date_input(
                "날짜 선택",
                today,
                key="calendar_date_input"
            )
        
        with col2:
            view_type = st.selectbox(
                "보기 방식",
                ["월간", "주간"],
                key="calendar_view_type"
            )
        
        # 캘린더 그리드 생성
        cal = calendar.monthcalendar(selected_date.year, selected_date.month)
        days = ['월', '화', '수', '목', '금', '토', '일']
        
        cols = st.columns(7)
        for i, day in enumerate(days):
            cols[i].markdown(f"**{day}**")
        
        # 일정 데이터 (실제로는 DB에서 가져와야 함)
        events = {
            15: ["TOGA VIRILIS 선적"],
            20: ["WILD DONKEY 결제"],
            25: ["BASERANGE 도착"]
        }
        
        # 달력 날짜 표시
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    # 해당 날짜에 일정이 있는지 확인
                    if day in events:
                        cols[i].markdown(f"**{day}**")
                        for event in events[day]:
                            cols[i].info(event)
                    else:
                        cols[i].write(str(day))

    def show_overview(self):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📅 주요 일정")
            events_data = {
                "오늘": [
                    "TOGA VIRILIS - 결제기한 D-day",
                    "WILD DONKEY - 선적 예정일"
                ],
                "이번 주": [
                    "BASERANGE - 결제기한 (3일 후)",
                    "NOU NOU - 도착 예정 (4일 후)"
                ]
            }
            
            for period, events in events_data.items():
                st.write(f"**{period}**")
                for event in events:
                    st.info(event)
        
        with col2:
            st.subheader("⚡ 긴급 알림")
            st.error("🚨 TOGA VIRILIS 결제기한 임박")
            st.warning("📦 WILD DONKEY 선적 시작")

    def show_documents(self):
        st.subheader("📑 최근 문서")
        
        uploaded_file = st.file_uploader(
            "PDF 파일을 선택하세요",
            type=["pdf"],
            key="dashboard_file_uploader"
        )
        if uploaded_file:
            self.show_document_preview(uploaded_file)
        
        # 최근 문서 목록
        recent_docs = pd.DataFrame({
            "날짜": ["2025-03-08", "2025-03-07", "2025-03-06"],
            "문서명": ["TOGA_VIRILIS_SS24.pdf", "WILD_DONKEY_SS24.pdf", "BASERANGE_SS24.pdf"],
            "상태": ["처리완료", "처리중", "대기중"]
        })
        st.dataframe(recent_docs, use_container_width=True)

    def show_settings(self):
        st.subheader("⚙️ 설정")
        st.checkbox("자동 OCR 처리", value=True)
        st.checkbox("이메일 알림 받기", value=True)
        st.selectbox("기본 문서 유형", ["인보이스", "발주서", "계약서"])