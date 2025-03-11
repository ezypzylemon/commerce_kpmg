import streamlit as st
import pandas as pd
from datetime import datetime

class DocumentView:
    def __init__(self, ocr_processor):
        self.ocr_processor = ocr_processor

    def show_upload(self):
        st.title("문서 업로드 및 OCR 처리")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_single_upload()
        
        with col2:
            self.show_bulk_upload()

    def show_single_upload(self):
        st.subheader("단일 문서 업로드")
        uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type=["pdf"])
        
        if uploaded_file is not None:
            st.success(f"{uploaded_file.name}이 업로드 되었습니다.")
            
            # PDF 저장
            temp_dir = tempfile.mkdtemp()
            temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.info(f"파일이 임시 저장되었습니다: {temp_pdf_path}")
            
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
                with st.spinner("OCR 처리 중..."):
                    result_df, excel_path = process_invoice_pdf(temp_pdf_path, temp_dir, verbose=True)
                    
                    if not result_df.empty:
                        st.success("문서가 성공적으로 처리되었습니다.")
                        
                        # 결과 표시
                        st.subheader("OCR 결과")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # 엑셀 다운로드 버튼
                        if excel_path:
                            with open(excel_path, "rb") as f:
                                file_bytes = f.read()
                                st.download_button(
                                    label="결과 다운로드 (Excel)",
                                    data=file_bytes,
                                    file_name=os.path.basename(excel_path),
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    else:
                        st.error("OCR 처리 결과가 없습니다. 문서를 확인하세요.")

    def show_bulk_upload(self):
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
                
                # 임시 디렉토리 생성
                temp_dir = tempfile.mkdtemp()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                all_results = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    file_progress = i / len(uploaded_files)
                    progress_bar.progress(file_progress)
                    status_text.text(f"파일 {i+1}/{len(uploaded_files)} 처리 중: {uploaded_file.name}")
                    
                    # PDF 저장
                    temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_pdf_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # OCR 처리
                    result_df, excel_path = process_invoice_pdf(temp_pdf_path, temp_dir, verbose=False)
                    
                    if not result_df.empty:
                        all_results.append({
                            "파일명": uploaded_file.name,
                            "처리상태": "성공",
                            "추출항목수": len(result_df),
                            "저장경로": excel_path
                        })
                    else:
                        all_results.append({
                            "파일명": uploaded_file.name,
                            "처리상태": "실패",
                            "추출항목수": 0,
                            "저장경로": ""
                        })
                
                progress_bar.progress(1.0)
                status_text.text("모든 처리가 완료되었습니다!")
                
                # 결과 요약
                st.subheader("처리 결과 요약")
                summary_df = pd.DataFrame(all_results)
                st.dataframe(summary_df, use_container_width=True)
                
                # 모든 결과를 하나의 ZIP 파일로 압축
                if any(result["처리상태"] == "성공" for result in all_results):
                    st.info("개별 파일 또는 전체 결과를 다운로드 할 수 있습니다.")
                    
                    for i, result in enumerate(all_results):
                        if result["처리상태"] == "성공" and result["저장경로"]:
                            with open(result["저장경로"], "rb") as f:
                                file_bytes = f.read()
                                st.download_button(
                                    label=f"{result['파일명']} 결과 다운로드",
                                    data=file_bytes,
                                    file_name=os.path.basename(result["저장경로"]),
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_{i}"
                                )