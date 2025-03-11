import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

class ScheduleView:
    def __init__(self):
        self.event_types = {
            "shipping_start": "선적 시작",
            "shipping_complete": "선적 완료",
            "arrival": "도착 예정",
            "payment": "결제",
            "meeting": "미팅"
        }
        
        # 선적 상태 색상 매핑
        self.status_colors = {
            "선적 전": "#ff9f9f",
            "선적 중": "#ffd699",
            "선적 완료": "#99ff99",
            "도착": "#9999ff"
        }

    def show(self):
        st.title("📅 일정 관리")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.show_calendar_view()
        
        with col2:
            self.show_shipping_status()
            
            # 일정 추가 버튼
            if st.button("+ 새 일정 추가", use_container_width=True):
                st.session_state.show_schedule_modal = True
        
        # 일정 추가 모달
        if st.session_state.get("show_schedule_modal", False):
            self.show_schedule_modal()

    def show_calendar_view(self):
        st.subheader("선적 일정 캘린더")
        
        # 월 선택
        today = datetime.now()
        selected_month = st.date_input(
            "월 선택",
            today,
            key="calendar_month"
        )
        
        # 캘린더 그리드 생성
        cal = calendar.monthcalendar(selected_month.year, selected_month.month)
        
        # 일정 데이터 (실제로는 DB에서 가져와야 함)
        events = {
            15: [("TOGA VIRILIS", "선적 시작", "#ffd699")],
            20: [("WILD DONKEY", "선적 완료", "#99ff99")],
            25: [("BASERANGE", "도착 예정", "#9999ff")],
        }
        
        # 요일 헤더
        cols = st.columns(7)
        for i, day in enumerate(['월', '화', '수', '목', '금', '토', '일']):
            cols[i].markdown(f"**{day}**")
        
        # 날짜 및 일정 표시
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    container = cols[i].container()
                    container.markdown(f"**{day}**", help="클릭하여 일정 추가")
                    
                    if day in events:
                        for brand, status, color in events[day]:
                            container.markdown(
                                f"""
                                <div style="padding: 5px; background-color: {color}; 
                                border-radius: 5px; margin: 2px 0;">
                                    {brand}<br/>
                                    <small>{status}</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

    def show_shipping_status(self):
        st.subheader("선적 현황")
        
        # 선적 상태 데이터
        shipping_data = pd.DataFrame({
            "브랜드": ["TOGA VIRILIS", "WILD DONKEY", "BASERANGE"],
            "상태": ["선적 중", "선적 완료", "선적 전"],
            "시작일": ["2024-03-15", "2024-03-10", "2024-03-25"],
            "완료예정": ["2024-05-15", "2024-05-10", "2024-05-25"]
        })
        
        for _, row in shipping_data.iterrows():
            status_color = self.status_colors.get(row["상태"], "#cccccc")
            st.markdown(
                f"""
                <div style="padding: 10px; background-color: {status_color}; 
                border-radius: 5px; margin: 5px 0;">
                    <strong>{row['브랜드']}</strong><br/>
                    상태: {row['상태']}<br/>
                    <small>
                        {row['시작일']} → {row['완료예정']}
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )

    def show_schedule_modal(self):
        with st.form("schedule_modal"):
            st.subheader("새 일정 등록")
            
            col1, col2 = st.columns(2)
            
            with col1:
                brand = st.selectbox(
                    "브랜드",
                    ["TOGA VIRILIS", "WILD DONKEY", "BASERANGE"]
                )
                event_type = st.selectbox(
                    "일정 유형",
                    list(self.event_types.values())
                )
            
            with col2:
                start_date = st.date_input("시작일")
                end_date = st.date_input("종료일")
            
            note = st.text_area("비고")
            
            col3, col4 = st.columns(2)
            
            with col3:
                if st.form_submit_button("저장"):
                    # 여기에 일정 저장 로직 구현
                    st.success("일정이 등록되었습니다.")
                    st.session_state.show_schedule_modal = False
                    st.experimental_rerun()
            
            with col4:
                if st.form_submit_button("취소"):
                    st.session_state.show_schedule_modal = False
                    st.experimental_rerun()
