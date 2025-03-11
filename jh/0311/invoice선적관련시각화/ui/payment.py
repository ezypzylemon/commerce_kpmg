import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

class PaymentView:
    def __init__(self):
        self.payment_status = {
            "pending": "대기중",
            "processing": "처리중",
            "completed": "완료",
            "overdue": "연체"
        }

    def show(self):
        st.title("💳 결제 관리")
        
        tab1, tab2 = st.tabs(["결제 현황", "결제 등록"])
        
        with tab1:
            self.show_payment_status()
        with tab2:
            self.show_payment_registration()

    def show_payment_status(self):
        # 결제 현황 데이터 (실제로는 DB에서 가져와야 함)
        payments_df = pd.DataFrame({
            "브랜드": ["TOGA VIRILIS", "WILD DONKEY", "BASERANGE"],
            "인보이스 번호": ["INV-2024-001", "INV-2024-002", "INV-2024-003"],
            "결제 금액": ["€5,600.00", "€3,200.00", "€4,800.00"],
            "결제 기한": ["2024-03-15", "2024-03-20", "2024-03-25"],
            "상태": ["대기중", "처리중", "완료"]
        })

        st.dataframe(payments_df, use_container_width=True)

        # 결제 상세 정보
        selected_payment = st.selectbox("상세 정보 조회", payments_df["인보이스 번호"])
        if selected_payment:
            self.show_payment_detail(selected_payment)

    def show_payment_registration(self):
        with st.form("payment_registration"):
            st.subheader("새 결제 등록")
            
            brand = st.text_input("브랜드명")
            invoice_no = st.text_input("인보이스 번호")
            amount = st.number_input("결제 금액 (EUR)", min_value=0.0)
            due_date = st.date_input("결제 기한")
            
            if st.form_submit_button("결제 등록"):
                if brand and invoice_no and amount > 0:
                    st.success("결제가 등록되었습니다.")
                else:
                    st.error("모든 필드를 입력해주세요.")

    def show_payment_detail(self, invoice_no):
        st.subheader(f"결제 상세 정보: {invoice_no}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("결제 상태", "대기중")
            st.metric("남은 기한", "D-7")
        
        with col2:
            st.metric("결제 금액", "€5,600.00")
            st.metric("부가세", "€560.00")
