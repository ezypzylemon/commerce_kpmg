import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
import time

class DocumentView:
    def __init__(self, ocr_processor):
        self.ocr_processor = ocr_processor
        
        # 상태 초기화
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = None
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = []

    def show_upload(self):
        st.title("📑 문서 업로드 및 OCR 처리")
        
        # 문서 처리 탭
        tab1, tab2, tab3 = st.tabs(["단일 문서 업로드", "대량 업로드", "처리 결과"])
        
        with tab1:
            self.show_single_upload()
        
        with tab2:
            self.show_bulk_upload()
            
        with tab3:
            self.show_processing_results()

    def show_single_upload(self):
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #333;">단일 문서 업로드</h3>
            <p style="color: #666;">PDF 파일을 업로드하여 OCR 처리를 시작하세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type=["pdf"], key="single_upload")
        
        if uploaded_file is not None:
            st.success(f"'{uploaded_file.name}'이 업로드 되었습니다.")
            
            # 파일 미리보기
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                <div style="border: 1px dashed #ccc; height: 300px; display: flex; 
                            align-items: center; justify-content: center; background-color: #f9f9f9;
                            border-radius: 5px;">
                    <div style="text-align: center;">
                        <div style="font-size: 48px;">📄</div>
                        <div>PDF 미리보기</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background-color: white; padding: 15px; border-radius: 10px; 
                            box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <h4 style="margin-top: 0;">문서 정보</h4>
                </div>
                """, unsafe_allow_html=True)
                
                doc_type = st.selectbox(
                    "문서 타입",
                    ["인보이스", "발주서", "계약서", "견적서", "기타"],
                    key="single_doc_type"
                )
                
                brand = st.selectbox(
                    "브랜드",
                    ["TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"],
                    key="single_brand"
                )
                
                season = st.selectbox(
                    "시즌",
                    ["2024SS", "2024FW", "2025SS", "2025FW"],
                    key="single_season"
                )
                
                st.markdown("### 옵션")
                advanced_options = st.expander("고급 설정", expanded=False)
                with advanced_options:
                    st.checkbox("자동 품번 생성", value=True)
                    st.checkbox("결제 정보 추출", value=True)
                    st.checkbox("선적 정보 추출", value=True)
                    st.checkbox("이미지 품질 개선", value=True)
                    ocr_quality = st.select_slider(
                        "OCR 품질",
                        options=["빠름", "균형", "정확함"],
                        value="균형"
                    )
            
            # OCR 처리 시작 버튼
            if st.button("OCR 처리 시작", type="primary", use_container_width=True):
                # 임시 파일로 저장
                with st.spinner("PDF 처리 준비 중..."):
                    temp_dir = tempfile.mkdtemp()
                    temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_pdf_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 처리 상태 초기화
                    st.session_state.processing_status = {
                        "file": uploaded_file.name,
                        "start_time": datetime.now(),
                        "status": "처리중",
                        "progress": 0,
                        "type": doc_type,
                        "brand": brand,
                        "season": season
                    }
                
                # 처리 상태 화면 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # OCR 처리 시뮬레이션 (실제로는 ocr_processor 호출)
                for i in range(1, 101):
                    time.sleep(0.05)  # 처리 시간 시뮬레이션
                    progress_bar.progress(i)
                    status_text.text(f"OCR 처리 중... ({i}%)")
                    st.session_state.processing_status["progress"] = i
                
                # 처리 완료 후 상태 업데이트
                st.session_state.processing_status["status"] = "완료"
                st.session_state.processing_status["end_time"] = datetime.now()
                
                # 처리된 파일 목록에 추가
                st.session_state.processed_files.append(st.session_state.processing_status.copy())
                
                # 결과 표시
                st.success("문서가 성공적으로 처리되었습니다!")
                
                # 결과 미리보기
                self.show_ocr_result_preview()

    def show_bulk_upload(self):
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #333;">대량 문서 업로드</h3>
            <p style="color: #666;">여러 PDF 파일을 한 번에 업로드하여 배치 처리하세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "여러 파일을 선택하세요", 
            type=["pdf"], 
            accept_multiple_files=True,
            key="bulk_upload"
        )
        
        if uploaded_files:
            st.success(f"{len(uploaded_files)}개의 파일이 업로드 되었습니다.")
            
            # 파일 목록 표시
            st.markdown("""
            <div style="background-color: white; padding: 15px; border-radius: 10px; 
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin-top: 0;">업로드된 파일 목록</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for i, file in enumerate(uploaded_files):
                st.markdown(f"""
                <div style="display: flex; background-color: #f8f9fa; padding: 10px; 
                            border-radius: 5px; margin-bottom: 5px; align-items: center;">
                    <div style="width: 30px; font-size: 18px;">📄</div>
                    <div style="flex: 1;">{file.name}</div>
                    <div style="width: 80px; font-size: 0.8em; color: #777;">{round(file.size/1024, 1)} KB</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 배치 설정
            col1, col2, col3 = st.columns(3)
            
            with col1:
                default_doc_type = st.selectbox(
                    "기본 문서 타입",
                    ["자동 감지", "인보이스", "발주서", "계약서", "견적서"],
                    key="bulk_doc_type"
                )
            
            with col2:
                default_brand = st.selectbox(
                    "기본 브랜드",
                    ["파일명에서 감지", "TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"],
                    key="bulk_brand"
                )
            
            with col3:
                default_season = st.selectbox(
                    "기본 시즌",
                    ["파일명에서 감지", "2024SS", "2024FW", "2025SS", "2025FW"],
                    key="bulk_season"
                )
            
            # 고급 설정
            with st.expander("고급 배치 설정", expanded=False):
                st.checkbox("자동 품번 생성", value=True, key="bulk_code_gen")
                st.checkbox("결제 정보 추출", value=True, key="bulk_payment_extract")
                st.checkbox("선적 정보 추출", value=True, key="bulk_shipping_extract")
                st.checkbox("이미지 품질 개선", value=True, key="bulk_quality")
                
                col1, col2 = st.columns(2)
                with col1:
                    ocr_quality = st.select_slider(
                        "OCR 품질",
                        options=["빠름", "균형", "정확함"],
                        value="균형",
                        key="bulk_ocr_quality"
                    )
                with col2:
                    max_threads = st.slider("동시 처리 작업 수", 1, 8, 4, key="bulk_threads")
            
            # 대량 처리 시작 버튼
            if st.button("대량 처리 시작", type="primary", use_container_width=True):
                with st.spinner("대량 처리 준비 중..."):
                    # 임시 디렉토리 생성
                    temp_dir = tempfile.mkdtemp()
                    
                    # 처리 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 각 파일에 대해 OCR 처리 시뮬레이션
                    for i, file in enumerate(uploaded_files):
                        # 현재 파일의 진행 상태
                        file_progress = i / len(uploaded_files)
                        progress_bar.progress(file_progress)
                        status_text.text(f"파일 {i+1}/{len(uploaded_files)} 처리 중: {file.name}")
                        
                        # 임시 파일 저장
                        temp_pdf_path = os.path.join(temp_dir, file.name)
                        with open(temp_pdf_path, "wb") as f:
                            f.write(file.getbuffer())
                        
                        # 각 파일별 진행도 시뮬레이션
                        current_file_status = st.empty()
                        current_file_progress = st.progress(0)
                        
                        for j in range(1, 101):
                            time.sleep(0.01)  # 빠른 처리 시뮬레이션
                            current_file_progress.progress(j)
                            current_file_status.text(f"{file.name} - OCR 처리 중... ({j}%)")
                            
                            # 전체 진행 상황 업데이트
                            total_progress = (file_progress + (j / 100) / len(uploaded_files)) * 100
                            progress_bar.progress(min(total_progress, 1.0))
                        
                        # 처리된 파일 목록에 추가
                        st.session_state.processed_files.append({
                            "file": file.name,
                            "start_time": datetime.now() - pd.Timedelta(seconds=1),  # 시뮬레이션용
                            "end_time": datetime.now(),
                            "status": "완료",
                            "progress": 100,
                            "type": default_doc_type if default_doc_type != "자동 감지" else "인보이스",
                            "brand": default_brand if default_brand != "파일명에서 감지" else "TOGA VIRILIS",
                            "season": default_season if default_season != "파일명에서 감지" else "2025SS"
                        })
                    
                    # 처리 완료
                    progress_bar.progress(1.0)
                    status_text.text("모든 파일 처리가 완료되었습니다!")
                
                # 결과 요약
                st.success(f"모든 파일({len(uploaded_files)}개)이 성공적으로 처리되었습니다.")
                
                # 탭 전환 안내
                st.info("'처리 결과' 탭에서 처리된 모든 문서의 결과를 확인할 수 있습니다.")

    def show_ocr_result_preview(self):
        st.markdown("""
        <div style="background-color: white; padding: 15px; border-radius: 10px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 20px 0;">
            <h4 style="margin-top: 0;">OCR 처리 결과 미리보기</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 샘플 데이터
        sample_data = pd.DataFrame({
            "Product_Code": ["AJ1323", "AJ1323", "AJ826", "AJ826", "AJ830"],
            "Style": ["FTVRM20SS", "FTVRM20SS", "FTVRM20SS", "FTVRM20SS", "FTVRM20SS"],
            "Color": ["BLACK LEATHER", "BLACK LEATHER", "BLACK POLIDO", "BLACK POLIDO", "BLACK LEATHER"],
            "Size": ["39", "40", "41", "42", "43"],
            "Quantity": ["2", "3", "1", "4", "2"],
            "Wholesale_EUR": ["280", "280", "310", "310", "320"],
            "Brand": ["TOGA VIRILIS", "TOGA VIRILIS", "TOGA VIRILIS", "TOGA VIRILIS", "TOGA VIRILIS"],
            "Custom_Code": ["20B01AF-SHTVONMFL-132339", "20B01AF-SHTVONMFL-132340", "21X01AF-SHTVONMFL-82641", "21X01AF-SHTVONMFL-82642", "20B01AF-SHTVONMFL-83043"]
        })
        
        # 데이터프레임 스타일링
        st.dataframe(
            sample_data, 
            use_container_width=True,
            height=250,
            column_config={
                "Custom_Code": st.column_config.TextColumn(
                    "품번코드",
                    help="자동 생성된 품번코드"
                ),
                "Product_Code": st.column_config.TextColumn(
                    "상품 코드",
                    help="제품 코드"
                ),
                "Size": st.column_config.TextColumn(
                    "사이즈",
                    help="신발 사이즈"
                ),
                "Quantity": st.column_config.NumberColumn(
                    "수량",
                    help="주문 수량",
                    format="%d"
                ),
                "Wholesale_EUR": st.column_config.NumberColumn(
                    "도매가(EUR)",
                    help="유로 단위 도매가",
                    format="€%d"
                )
            }
        )
        
        # 결과 다운로드 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.download_button(
                "Excel 다운로드",
                data=sample_data.to_csv(index=False).encode('utf-8-sig'),
                file_name=f"OCR_결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                "CSV 다운로드",
                data=sample_data.to_csv(index=False).encode('utf-8-sig'),
                file_name=f"OCR_결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            st.button(
                "결과 저장",
                type="primary",
                use_container_width=True
            )

    def show_processing_results(self):
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #333;">OCR 처리 결과</h3>
            <p style="color: #666;">처리된 모든 문서의 결과를 확인하고 관리합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 검색 및 필터 도구
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input("검색", placeholder="파일명 또는 브랜드 검색...")
        
        with col2:
            filter_type = st.selectbox(
                "문서 유형",
                ["전체", "인보이스", "발주서", "계약서", "견적서"]
            )
        
        with col3:
            filter_status = st.selectbox(
                "상태",
                ["전체", "완료", "처리중", "실패"]
            )
        
        # 처리된 파일 목록
        if st.session_state.processed_files:
            st.markdown("""
            <div style="background-color: white; padding: 15px; border-radius: 10px; 
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin: 20px 0;">
                <h4 style="margin-top: 0;">처리된 문서 목록</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for file_data in reversed(st.session_state.processed_files):
                # 파일 정보
                file_name = file_data["file"]
                status = file_data["status"]
                progress = file_data["progress"]
                doc_type = file_data.get("type", "인보이스")
                brand = file_data.get("brand", "TOGA VIRILIS")
                
                # 검색 및 필터 적용
                if search_query and search_query.lower() not in file_name.lower() and search_query.lower() not in brand.lower():
                    continue
                
                if filter_type != "전체" and doc_type != filter_type:
                    continue
                    
                if filter_status != "전체" and status != filter_status:
                    continue
                
                # 상태에 따른 배지 색상
                if status == "완료":
                    badge_color = "#2ecc71"
                    badge_bg = "#e8f5e9"
                elif status == "처리중":
                    badge_color = "#f39c12"
                    badge_bg = "#fff8e1"
                else:
                    badge_color = "#e74c3c"
                    badge_bg = "#ffebee"
                
                # 처리 시간 계산
                if "start_time" in file_data and "end_time" in file_data:
                    processing_time = (file_data["end_time"] - file_data["start_time"]).total_seconds()
                    time_str = f"{processing_time:.1f}초"
                else:
                    time_str = "N/A"
                
                # 문서 카드 렌더링
                st.markdown(f"""
                <div style="display: flex; background-color: white; padding: 15px; border-radius: 8px; 
                            margin-bottom: 10px; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="width: 40px; font-size: 24px;">📄</div>
                    <div style="flex: 1; margin-left: 10px;">
                        <div style="font-weight: bold;">{file_name}</div>
                        <div style="display: flex; color: #777; font-size: 0.9em;">
                            <div style="margin-right: 15px;">{doc_type}</div>
                            <div style="margin-right: 15px;">{brand}</div>
                            <div>처리 시간: {time_str}</div>
                        </div>
                    </div>
                    <div style="margin-right: 15px; width: 150px;">
                        <div style="background-color: #f5f5f5; border-radius: 4px; height: 8px; overflow: hidden;">
                            <div style="background-color: {badge_color}; width: {progress}%; height: 100%;"></div>
                        </div>
                    </div>
                    <div style="background-color: {badge_bg}; color: {badge_color}; padding: 5px 10px; 
                                border-radius: 15px; font-size: 0.8em; font-weight: bold;">
                        {status}
                    </div>
                    <div style="margin-left: 15px;">
                        <button style="background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; 
                                      padding: 5px 10px; cursor: pointer; font-size: 0.9em;">
                            보기
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("처리된 문서가 없습니다. 단일 또는 대량 업로드 탭에서 문서를 업로드하세요.")