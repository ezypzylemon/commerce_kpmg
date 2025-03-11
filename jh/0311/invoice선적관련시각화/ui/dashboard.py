import streamlit as st
from datetime import datetime
import calendar
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

class DashboardView:
    def __init__(self, ocr_manager):
        self.ocr_manager = ocr_manager

    def show(self):
        st.title("OCR 문서 관리 대시보드")
        
        # 빠른 액션 섹션
        self.show_quick_actions()
        
        # 알림 및 요약 정보 섹션
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.show_metrics_summary()
        
        with col2:
            self.show_urgent_alerts()
        
        # 탭 기반 콘텐츠
        tab_labels = ["📊 개요", "📅 캘린더", "📑 문서", "⚙️ 설정"]
        tabs = st.tabs(tab_labels)
        
        with tabs[0]:
            self.show_overview()
        with tabs[1]:
            self.show_calendar()
        with tabs[2]:
            self.show_documents()
        with tabs[3]:
            self.show_settings()

    # show_settings 메서드 추가
    def show_settings(self):
        st.subheader("⚙️ 설정")
        
        with st.expander("일반 설정", expanded=True):
            st.checkbox("자동 OCR 처리", value=True)
            st.checkbox("이메일 알림 받기", value=True)
            st.selectbox("기본 문서 유형", ["인보이스", "발주서", "계약서"])
            
        with st.expander("OCR 설정", expanded=False):
            st.slider("OCR 이미지 품질 (DPI)", 150, 600, 300, 50)
            st.slider("이미지 스케일 팩터", 1.0, 2.0, 1.5, 0.1)
            st.selectbox("OCR 엔진 모드", ["기본", "텍스트 우선", "테이블 우선"])
            st.checkbox("캐싱 사용", value=True)
            
        with st.expander("UI 설정", expanded=False):
            st.selectbox("테마", ["라이트", "다크", "시스템 기본값"])
            st.slider("페이지당 항목 수", 5, 50, 10, 5)
            st.selectbox("기본 정렬 기준", ["날짜 (최신순)", "날짜 (오래된순)", "브랜드 (가나다순)"])
            
        with st.expander("데이터 관리", expanded=False):
            st.button("캐시 비우기", type="secondary")
            st.button("모든 데이터 내보내기", type="secondary")
            
            danger_zone = st.toggle("위험 영역 표시")
            if danger_zone:
                st.warning("다음 작업은 데이터를 영구적으로 삭제합니다. 신중하게 진행하세요.")
                st.button("모든 문서 데이터 초기화", type="primary")

    def show_quick_actions(self):
        st.markdown("""
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
            <h3 style="margin: 0; padding-top: 10px; color: #333333;">⚡ 빠른 액션</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.render_action_button("📄 새 문서 업로드", "document_upload", "#3498db")
        
        with col2:
            self.render_action_button("📊 보고서 생성", "report_generation", "#2ecc71")
        
        with col3:
            self.render_action_button("📅 일정 추가", "calendar_add", "#9b59b6")
        
        with col4:
            self.render_action_button("💳 결제 관리", "payment_management", "#e74c3c")

    def render_action_button(self, title, action_key, bg_color):
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; 
                    color: white; text-align: center; cursor: pointer; height: 100px;
                    display: flex; flex-direction: column; justify-content: center;
                    font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
             onclick="alert('기능 준비 중입니다.')">
            <div style="font-size: 24px; color: white !important;">{title.split()[0]}</div>
            <div style="color: white !important;">{' '.join(title.split()[1:])}</div>
        </div>
        """, unsafe_allow_html=True)

    def show_metrics_summary(self):
        st.markdown("""
        <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0; color: #333333;">📈 주요 지표</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.metric_card("처리된 문서", "127", "↑ 12%", "#3498db")
        
        with col2:
            self.metric_card("대기 중인 결제", "8", "↓ 2", "#e74c3c")
        
        with col3:
            self.metric_card("이번 달 선적", "15", "↑ 3", "#2ecc71")
        
        with col4:
            self.metric_card("브랜드 수", "5", "↑ 1", "#9b59b6")

    def metric_card(self, title, value, change, color):
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; 
                    border-top: 5px solid {color}; margin-bottom: 10px; text-align: center;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <h4 style="margin-top: 0; color: #555555 !important; font-size: 1em;">{title}</h4>
            <div style="font-size: 1.8em; font-weight: bold; margin: 10px 0; color: #333333 !important;">{value}</div>
            <div style="color: {'green' if '↑' in change else 'red'} !important; font-size: 0.9em;">{change}</div>
        </div>
        """, unsafe_allow_html=True)

    def show_urgent_alerts(self):
        st.markdown("""
        <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0; color: #333333;">⚠️ 긴급 알림</h3>
        </div>
        """, unsafe_allow_html=True)
        
        alerts = [
            {"severity": "danger", "message": "TOGA VIRILIS 결제기한 임박 (D-day)"},
            {"severity": "warning", "message": "WILD DONKEY 선적 시작"},
            {"severity": "success", "message": "BASERANGE 결제 완료"},
        ]
        
        for alert in alerts:
            severity = alert["severity"]
            message = alert["message"]
            
            if severity == "danger":
                icon = "🚨"
                bg_color = "#ffebee"
                border_color = "#e57373"
                text_color = "#d32f2f"
            elif severity == "warning":
                icon = "⚠️"
                bg_color = "#fff8e1"
                border_color = "#ffca28"
                text_color = "#f57f17"
            else:
                icon = "✅"
                bg_color = "#e8f5e9"
                border_color = "#81c784"
                text_color = "#2e7d32"
                
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 12px 15px; border-radius: 8px; 
                        margin-bottom: 10px; border-left: 5px solid {border_color};">
                <div style="display: flex; align-items: center;">
                    <div style="font-size: 1.2em; margin-right: 10px;">{icon}</div>
                    <div style="color: {text_color} !important;">{message}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def show_overview(self):
        # 브랜드별 결제 현황 그래프
        st.subheader("브랜드별 결제 현황")
        
        # 샘플 데이터
        brands = ["TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"]
        values = [58000, 32000, 44000, 48000, 27000]
        
        fig = px.bar(
            x=brands, 
            y=values,
            labels={"x": "브랜드", "y": "결제 금액 (EUR)"},
            text=values,
            color=values,
            color_continuous_scale="Blues",
        )
        
        fig.update_layout(
            plot_bgcolor="white",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            coloraxis_showscale=False,
            font=dict(color="#333333")
        )
        
        fig.update_traces(
            texttemplate='%{text:,} €',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 문서 처리 현황 및 일정
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_document_processing_status()
        
        with col2:
            self.show_upcoming_events()
    
    def show_document_processing_status(self):
        st.markdown("""
        <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #333333;">📄 문서 처리 현황</h4>
        </div>
        """, unsafe_allow_html=True)
        
        statuses = ["완료", "처리중", "대기중"]
        values = [75, 15, 10]
        colors = ["#2ecc71", "#f39c12", "#e74c3c"]
        
        fig = go.Figure(data=[go.Pie(
            labels=statuses,
            values=values,
            hole=.5,
            marker=dict(colors=colors),
            textinfo="label+percent",
            textfont=dict(color="#333333")
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=-0.2, 
                xanchor="center", 
                x=0.5,
                font=dict(color="#333333")
            ),
            annotations=[dict(text="90<br>총 문서", showarrow=False, font_size=14, font=dict(color="#333333"))]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def show_upcoming_events(self):
        st.markdown("""
        <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #333333;">📅 다가오는 일정</h4>
        </div>
        """, unsafe_allow_html=True)
        
        events = [
            {"date": "오늘", "event": "TOGA VIRILIS - 결제기한", "type": "payment"},
            {"date": "내일", "event": "WILD DONKEY - 선적 시작", "type": "shipping"},
            {"date": "3일 후", "event": "BASERANGE - 결제기한", "type": "payment"},
            {"date": "5일 후", "event": "NOU NOU - 도착 예정", "type": "arrival"}
        ]
        
        for event in events:
            event_type = event["type"]
            
            if event_type == "payment":
                icon = "💳"
                color = "#3498db"
            elif event_type == "shipping":
                icon = "🚢"
                color = "#f39c12"
            else:
                icon = "📦"
                color = "#2ecc71"
                
            st.markdown(f"""
            <div style="display: flex; margin-bottom: 10px; background-color: white; 
                        padding: 10px; border-radius: 8px; border-left: 4px solid {color};">
                <div style="width: 80px; font-weight: bold; color: #555555 !important;">{event["date"]}</div>
                <div style="margin-right: 5px;">{icon}</div>
                <div style="color: #333333 !important;">{event["event"]}</div>
            </div>
            """, unsafe_allow_html=True)

    def show_calendar(self):
        st.subheader("📅 일정 캘린더")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 월 선택
            today = datetime.now()
            selected_month = st.date_input(
                "월 선택",
                today,
                key="dashboard_calendar_month"
            )
            
            # 달력 생성
            self.render_calendar(selected_month.year, selected_month.month)
        
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 15px; border-radius: 10px; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin-top: 0; color: #333333;">🔍 일정 검색</h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.text_input("검색어 입력", placeholder="브랜드 또는 이벤트 검색...")
            
            st.markdown("<h3 style='color: #333333;'>일정 타입</h3>", unsafe_allow_html=True)
            st.checkbox("선적 일정", value=True)
            st.checkbox("결제 일정", value=True)
            st.checkbox("미팅", value=True)
            
            if st.button("새 일정 추가", use_container_width=True, type="primary"):
                st.session_state.show_calendar_modal = True

    def render_calendar(self, year, month):
        cal = calendar.monthcalendar(year, month)
        days = ['월', '화', '수', '목', '금', '토', '일']
        
        # 헤더 스타일
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); background-color: #f8f9fa; 
                    padding: 10px 0; border-radius: 8px 8px 0 0; font-weight: bold; text-align: center;">
            {"".join(f'<div style="color: #333333 !important;">{day}</div>' for day in days)}
        </div>
        """, unsafe_allow_html=True)
        
        # 일정 데이터 (실제로는 DB에서 가져옴)
        events = {
            15: [("TOGA VIRILIS", "결제기한", "#3498db")],
            20: [("WILD DONKEY", "선적 시작", "#f39c12")],
            25: [("BASERANGE", "결제기한", "#3498db")],
            27: [("NOU NOU", "도착 예정", "#2ecc71")]
        }
        
        # 캘린더 그리드 생성
        today = datetime.now().day
        
        html_rows = []
        for week in cal:
            html_cells = []
            
            for day in week:
                if day == 0:
                    # 빈 셀
                    html_cells.append('<div class="calendar-cell empty"></div>')
                else:
                    # 오늘 강조
                    is_today = day == today and month == datetime.now().month and year == datetime.now().year
                    today_class = " today" if is_today else ""
                    
                    # 일정 표시
                    event_html = ""
                    if day in events:
                        for brand, event_type, color in events[day]:
                            event_html += f"""
                            <div style="background-color: {color}; color: white !important; 
                                        padding: 3px 5px; border-radius: 4px; 
                                        margin-top: 2px; font-size: 0.8em; 
                                        overflow: hidden; text-overflow: ellipsis;
                                        white-space: nowrap;">
                                {brand.split()[0]} - {event_type}
                            </div>
                            """
                    
                    html_cells.append(f"""
                    <div class="calendar-cell{today_class}" style="min-height: 80px;">
                        <div style="font-weight: {'bold' if is_today else 'normal'}; 
                                   color: {'#3498db' if is_today else '#333333'} !important;">
                            {day}
                        </div>
                        {event_html}
                    </div>
                    """)
            
            html_rows.append(f"""
            <div style="display: grid; grid-template-columns: repeat(7, 1fr); grid-gap: 1px;">
                {"".join(html_cells)}
            </div>
            """)
        
        # CSS 스타일
        st.markdown("""
        <style>
        .calendar-cell {
            background-color: white;
            padding: 5px;
            min-height: 60px;
            border: 1px solid #e0e0e0;
        }
        .calendar-cell.empty {
            background-color: #f5f5f5;
        }
        .calendar-cell.today {
            background-color: #ebf5fb;
            border: 1px solid #3498db;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 캘린더 렌더링
        st.markdown(f"""
        <div style="background-color: white; border-radius: 0 0 8px 8px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
            {"".join(html_rows)}
        </div>
        """, unsafe_allow_html=True)

    def show_documents(self):
        st.subheader("📑 최근 문서")
        
        # 파일 업로드 영역
        with st.expander("새 문서 업로드", expanded=False):
            uploaded_file = st.file_uploader(
                "PDF 파일을 선택하세요",
                type=["pdf"],
                key="dashboard_file_uploader"
            )
            
            if uploaded_file:
                st.success(f"{uploaded_file.name} 파일이 성공적으로 업로드되었습니다.")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.selectbox("문서 타입", ["인보이스", "발주서", "계약서", "견적서"])
                with col2:
                    st.selectbox("브랜드", ["TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"])
                
                if st.button("OCR 처리 시작", type="primary"):
                    st.info("OCR 처리가 시작되었습니다...")
        
        # 최근 문서 목록
        st.markdown("""
        <div style="background-color: white; padding: 15px; border-radius: 10px; margin-top: 20px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #333333;">최근 처리된 문서</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 샘플 데이터
        recent_docs = [
            {"date": "2025-03-08", "name": "TOGA_VIRILIS_SS24.pdf", "type": "인보이스", "status": "처리완료", "progress": 100},
            {"date": "2025-03-07", "name": "WILD_DONKEY_SS24.pdf", "type": "발주서", "status": "처리중", "progress": 75},
            {"date": "2025-03-06", "name": "BASERANGE_SS24.pdf", "type": "계약서", "status": "대기중", "progress": 0},
            {"date": "2025-03-05", "name": "ATHLETICS_FTWR_SS24.pdf", "type": "인보이스", "status": "처리완료", "progress": 100},
            {"date": "2025-03-04", "name": "NOU_NOU_SS24.pdf", "type": "발주서", "status": "처리완료", "progress": 100}
        ]
        
        for doc in recent_docs:
            status = doc["status"]
            progress = doc["progress"]
            
            # 상태에 따른 배지 색상
            if status == "처리완료":
                badge_color = "#2ecc71"
                badge_bg = "#e8f5e9"
            elif status == "처리중":
                badge_color = "#f39c12"
                badge_bg = "#fff8e1"
            else:
                badge_color = "#e74c3c"
                badge_bg = "#ffebee"
            
            # 문서 카드 렌더링
            st.markdown(f"""
            <div style="display: flex; background-color: white; padding: 15px; border-radius: 8px; 
                        margin-bottom: 10px; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="width: 40px; font-size: 24px;">📄</div>
                <div style="flex: 1; margin-left: 10px;">
                    <div style="font-weight: bold; color: #333333 !important;">{doc["name"]}</div>
                    <div style="display: flex; color: #777777 !important; font-size: 0.9em;">
                        <div style="margin-right: 15px;">{doc["date"]}</div>
                        <div>{doc["type"]}</div>
                    </div>
                </div>
                <div style="margin-right: 15px; width: 150px;">
                    <div style="background-color: #f5f5f5; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background-color: {badge_color}; width: {progress}%; height: 100%;"></div>
                    </div>
                </div>
                <div style="background-color: {badge_bg}; color: {badge_color} !important; padding: 5px 10px; 
                            border-radius: 15px; font-size: 0.8em; font-weight: bold;">
                    {status}
                </div>
                <div style="margin-left: 10px;">
                    <button style="background-color: transparent; border: none; cursor: pointer; font-size: 1.2em;">⋮</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 더 보기 버튼
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px;">
            <button style="background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; 
                          padding: 8px 15px; cursor: pointer; color: #333333 !important;">
                더 보기
            </button>
        </div>
        """, unsafe_allow_html=True)