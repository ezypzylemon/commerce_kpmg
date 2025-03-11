import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import xlsxwriter
from io import BytesIO

class ReportView:
    def __init__(self):
        self.report_types = {
            "brand_analysis": "브랜드별 분석",
            "season_analysis": "시즌별 분석",
            "payment_analysis": "결제 현황 분석",
            "shipping_analysis": "선적 현황 분석"
        }

    def show(self):
        st.title("📊 보고서 생성")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("보고서 설정")
            self.show_report_settings()
        
        with col2:
            st.subheader("보고서 미리보기")
            self.show_report_preview()

    def show_report_settings(self):
        with st.form("report_settings"):
            report_type = st.selectbox(
                "보고서 유형",
                list(self.report_types.values())
            )
            
            date_range = st.date_input(
                "기간 선택",
                [datetime.now() - timedelta(days=30), datetime.now()]
            )
            
            brands = st.multiselect(
                "브랜드 선택",
                ["TOGA VIRILIS", "WILD DONKEY", "BASERANGE"],
                default=["TOGA VIRILIS"]
            )
            
            output_format = st.radio(
                "출력 형식",
                ["Excel", "PDF", "CSV"]
            )
            
            if st.form_submit_button("보고서 생성"):
                if brands and date_range:
                    report_data = self.generate_report_data(report_type, date_range, brands)
                    output_file = self.save_report(report_data, report_type, output_format)
                    
                    if output_file:
                        st.success("보고서가 생성되었습니다.")
                        # 다운로드 버튼 생성
                        with open(output_file, "rb") as f:
                            st.download_button(
                                label="보고서 다운로드",
                                data=f.read(),
                                file_name=os.path.basename(output_file),
                                mime=self.get_mime_type(output_format)
                            )
                else:
                    st.error("필수 항목을 모두 선택해주세요.")

    def show_report_preview(self):
        # 샘플 데이터로 차트 표시
        sample_data = pd.DataFrame({
            "브랜드": ["TOGA VIRILIS", "WILD DONKEY", "BASERANGE"],
            "주문량": [120, 85, 95],
            "매출액": [58000, 32000, 48000]
        })
        
        fig = px.bar(sample_data, x="브랜드", y="매출액", title="브랜드별 매출 현황")
        st.plotly_chart(fig, use_container_width=True)

    def generate_report_data(self, report_type, date_range, brands):
        # 실제 구현에서는 DB에서 데이터를 가져와야 함
        data = {
            "브랜드별 분석": pd.DataFrame({
                "브랜드": brands,
                "주문량": [120, 85, 95],
                "매출액": [58000, 32000, 48000],
                "평균단가": [483, 376, 505]
            }),
            "시즌별 분석": pd.DataFrame({
                "시즌": ["2024SS", "2024FW", "2025SS"],
                "주문건수": [45, 38, 52],
                "평균단가": [420, 380, 450]
            })
        }
        return data.get(report_type, pd.DataFrame())

    def save_report(self, data, report_type, output_format):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_type}_{timestamp}"
            
            if output_format == "Excel":
                output_file = f"{filename}.xlsx"
                self.save_excel_report(data, output_file)
                return output_file
            elif output_format == "CSV":
                output_file = f"{filename}.csv"
                data.to_csv(output_file, index=False, encoding='utf-8-sig')
                return output_file
            elif output_format == "PDF":
                output_file = f"{filename}.pdf"
                self.save_pdf_report(data, output_file)
                return output_file
                
            return None
        except Exception as e:
            st.error(f"보고서 저장 중 오류 발생: {str(e)}")
            return None

    def save_excel_report(self, data, output_file):
        # Excel 파일 생성
        workbook = xlsxwriter.Workbook(output_file)
        worksheet = workbook.add_worksheet()
        
        # 헤더 스타일
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#CCE5FF',
            'border': 1
        })
        
        # 데이터 스타일
        data_format = workbook.add_format({
            'border': 1
        })
        
        # 헤더 작성
        for col, header in enumerate(data.columns):
            worksheet.write(0, col, header, header_format)
        
        # 데이터 작성
        for row, row_data in enumerate(data.values):
            for col, value in enumerate(row_data):
                worksheet.write(row + 1, col, value, data_format)
        
        workbook.close()

    def save_pdf_report(self, data, output_file):
        # PDF 저장 로직 구현
        # 실제 구현 시 reportlab 등의 라이브러리 사용
        pass

    def get_mime_type(self, output_format):
        mime_types = {
            "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "PDF": "application/pdf",
            "CSV": "text/csv"
        }
        return mime_types.get(output_format, "application/octet-stream")
