// API 기본 URL 설정 (개발 환경) - 백엔드 경로와 일치시킴
const API_BASE_URL = 'http://localhost:5000/orders';

document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 선택
    const uploadDropzone = document.querySelector('.upload-dropzone');
    const fileUploadInput = document.getElementById('fileUpload');
    const uploadStatusDiv = document.getElementById('uploadStatus');
    const uploadResultDiv = document.getElementById('uploadResult');
    const resultPreview = document.getElementById('resultPreview');
    const downloadExcelBtn = document.getElementById('downloadExcelBtn');
    
    // 드래그 앤 드롭 이벤트 처리
    uploadDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadDropzone.classList.add('dragover');
    });
    
    uploadDropzone.addEventListener('dragleave', () => {
        uploadDropzone.classList.remove('dragover');
    });
    
    uploadDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadDropzone.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });
    
    // 파일 업로드 버튼 클릭 이벤트
    const uploadButton = document.querySelector('.upload-dropzone .btn-primary');
    uploadButton.addEventListener('click', () => {
        fileUploadInput.click();
    });
    
    // 파일 선택 이벤트
    fileUploadInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });
    
    // 시작 버튼 클릭 이벤트 (업로드 및 OCR 시작 버튼)
    const startButton = document.querySelector('.upload-actions .btn-primary');
    if (startButton) {
        startButton.addEventListener('click', () => {
            if (fileUploadInput.files[0]) {
                handleFileUpload(fileUploadInput.files[0]);
            } else {
                alert('먼저 파일을 선택해주세요.');
            }
        });
    }
    
    // 파일 업로드 처리 함수
    function handleFileUpload(file) {
        // PDF 파일인지 확인
        if (file.type !== 'application/pdf') {
            alert('PDF 파일만 업로드 가능합니다.');
            return;
        }
        
        // 문서 유형 확인
        const docType = document.querySelector('select[name="docType"]')?.value || '';
        if (!docType) {
            alert('문서 유형을 선택해주세요.');
            return;
        }

        if (docType !== 'invoice' && docType !== 'order') {
            alert('올바른 문서 유형을 선택해주세요 (인보이스 또는 발주서).');
            return;
        }
        
        // 옵션 값 가져오기
        const brand = document.querySelector('select[name="brand"]')?.value || '자동 감지';
        const season = document.querySelector('select[name="season"]')?.value || '';
        const ocrLang = document.querySelector('select[name="ocrLang"]')?.value || '자동 감지';
        const enhanceTables = document.getElementById('enhance-tables')?.checked || false;
        const extractFields = document.getElementById('extract-fields')?.checked || false;
        const autoCompare = document.getElementById('auto-compare')?.checked || false;
        
        // 업로드 상태 표시
        uploadStatusDiv.style.display = 'block';
        uploadResultDiv.style.display = 'none';
        const uploadStatusIcon = document.getElementById('uploadStatusIcon');
        const uploadStatusMessage = document.getElementById('uploadStatusMessage');
        uploadStatusIcon.className = 'fas fa-spinner fa-spin';
        uploadStatusMessage.textContent = '문서를 처리하고 있습니다...';
        
        // 진행 상태 표시 (시각적 효과)
        let progress = 0;
        const progressBar = document.querySelector('#uploadStatus .progress');
        const progressInterval = setInterval(() => {
            if (progress < 90) {
                progress += 5;
                progressBar.style.width = progress + '%';
            }
        }, 500);
        
        // FormData 생성
        const formData = new FormData();
        formData.append('file', file);
        formData.append('docType', docType);
        formData.append('brand', brand);
        formData.append('season', season);
        formData.append('ocrLang', ocrLang);
        formData.append('enhanceTables', enhanceTables);
        formData.append('extractFields', extractFields);
        formData.append('autoCompare', autoCompare);
        
        // 파일 업로드 요청 - 백엔드 API 경로와 일치
        fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(progressInterval);
            if (!response.ok) {
                throw new Error('파일 업로드 실패');
            }
            return response.json();
        })
        .then(data => {
            // 업로드 성공
            progressBar.style.width = '100%';
            
            console.log('서버 응답 데이터:', data);
            
            setTimeout(() => {
                uploadStatusDiv.style.display = 'none';
                uploadResultDiv.style.display = 'block';
                
                // 히스토리에 항목 추가
                addToHistory(file.name, data);
                
                // 결과 미리보기 생성 - 백엔드 응답 구조에 맞게 조정
                let previewHtml = `
                    <div class="result-summary">
                        <div class="summary-item">
                            <span class="summary-label">처리된 상품 수:</span>
                            <span class="summary-value">${data.total_products || 0}개</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">문서 ID:</span>
                            <span class="summary-value">${data.document_id || ''}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">파일명:</span>
                            <span class="summary-value">${data.excel_filename || ''}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">문서 유형:</span>
                            <span class="summary-value">${docType === 'invoice' ? '인보이스' : '발주서'}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">브랜드:</span>
                            <span class="summary-value">${brand}</span>
                        </div>
                    </div>
                    
                    <h3>데이터 미리보기</h3>
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    ${data.data_preview && data.data_preview.length > 0 ? 
                                        Object.keys(data.data_preview[0]).map(key => `<th>${key}</th>`).join('') : ''}
                                </tr>
                            </thead>
                            <tbody>
                                ${data.data_preview ? data.data_preview.map(row => `
                                    <tr>
                                        ${Object.values(row).map(value => `<td>${value}</td>`).join('')}
                                    </tr>
                                `).join('') : ''}
                            </tbody>
                        </table>
                    </div>
                `;
                
                resultPreview.innerHTML = previewHtml;
                
                // 다운로드 버튼 활성화 - 백엔드 다운로드 경로와 일치
                downloadExcelBtn.onclick = () => {
                    window.open(`${API_BASE_URL}/download/${data.excel_filename}`, '_blank');
                };
            }, 500);
        })
        .catch(error => {
            // 업로드 실패
            clearInterval(progressInterval);
            uploadStatusDiv.style.display = 'block';
            uploadStatusIcon.className = 'fas fa-exclamation-circle';
            uploadStatusMessage.textContent = `업로드 중 오류 발생: ${error.message}`;
            
            console.error('업로드 중 오류:', error);
        });
    }
    
    // 히스토리에 항목 추가하는 함수
    function addToHistory(fileName, data) {
        const historyItems = document.querySelector('.history-items');
        if (!historyItems) return;
        
        const timestamp = new Date().toLocaleTimeString();
        
        // 상태 클래스 결정 (기본값: 성공)
        let statusClass = 'success';
        let statusBadge = 'complete';
        let statusIcon = 'check';
        
        // 첫 번째 항목에 삽입할 HTML 생성
        const historyItemHTML = `
            <div class="history-item" data-id="${data.document_id}">
                <div class="history-icon ${statusClass}">
                    <i class="fas fa-${statusIcon}"></i>
                </div>
                <div class="history-content">
                    <div class="history-header">
                        <h3>${fileName}</h3>
                        <span class="status-badge ${statusBadge}">${statusBadge === 'complete' ? '완료' : '검토 필요'}</span>
                    </div>
                    <div class="history-details">
                        <span><i class="fas fa-clock"></i> ${timestamp}</span>
                        <span><i class="fas fa-file-alt"></i> ${data.total_products || 0}개 항목</span>
                        <span><i class="fas fa-tag"></i> ${document.querySelector('select[name="brand"]')?.value || '자동 감지'}</span>
                        <span><i class="fas fa-id-card"></i> ${data.document_id}</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn btn-icon view-btn" data-id="${data.document_id}"><i class="fas fa-eye"></i></button>
                    <button class="btn btn-icon download-btn" data-filename="${data.excel_filename}"><i class="fas fa-download"></i></button>
                </div>
            </div>
        `;
        
        // 처리 중인 항목 제거 (있는 경우)
        const processingItem = historyItems.querySelector('.history-icon.processing');
        if (processingItem) {
            const itemToRemove = processingItem.closest('.history-item');
            if (itemToRemove) {
                historyItems.removeChild(itemToRemove);
            }
        }
        
        // 새 항목을 첫 번째 위치에 추가
        historyItems.insertAdjacentHTML('afterbegin', historyItemHTML);
        
        // 다운로드 버튼에 이벤트 리스너 추가
        const downloadBtn = historyItems.querySelector('.history-item:first-child .download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                const filename = downloadBtn.getAttribute('data-filename');
                if (filename) {
                    window.open(`${API_BASE_URL}/download/${filename}`, '_blank');
                }
            });
        }
        
        // 보기 버튼에 이벤트 리스너 추가
        const viewBtn = historyItems.querySelector('.history-item:first-child .view-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => {
                const docId = viewBtn.getAttribute('data-id');
                if (docId) {
                    // orders.html로 이동하면서 문서 ID 전달
                    window.location.href = `orders.html?doc=${docId}`;
                }
            });
        }
    }
    
    // 모든 업로드 기록 보기 버튼 이벤트
    const viewAllHistoryBtn = document.getElementById('viewAllHistory');
    if (viewAllHistoryBtn) {
        viewAllHistoryBtn.addEventListener('click', () => {
            window.location.href = 'orders.html';
        });
    }
    
    // 새로고침 버튼 이벤트
    const refreshHistoryBtn = document.getElementById('refreshHistory');
    if (refreshHistoryBtn) {
        refreshHistoryBtn.addEventListener('click', () => {
            loadHistoryFromAPI();
        });
    }
    
    // API에서 히스토리 로드
    function loadHistoryFromAPI() {
        const historyItems = document.querySelector('.history-items');
        if (!historyItems) return;
        
        // 로딩 표시
        historyItems.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 히스토리 로드 중...</div>';
        
        // 인보이스 목록 가져오기
        fetch(`${API_BASE_URL}/documents/invoice`)
            .then(response => response.json())
            .then(invoiceData => {
                // 오더시트 목록 가져오기
                return fetch(`${API_BASE_URL}/documents/order`)
                    .then(response => response.json())
                    .then(orderData => {
                        return {
                            invoices: invoiceData.invoices || [],
                            orders: orderData.orders || []
                        };
                    });
            })
            .then(data => {
                // 모든 문서 목록 병합 및 날짜순 정렬
                const allDocuments = [
                    ...data.invoices.map(doc => ({...doc, document_type_label: '인보이스'})),
                    ...data.orders.map(doc => ({...doc, document_type_label: '발주서'}))
                ];
                
                // 최신 문서부터 정렬
                allDocuments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                
                // 히스토리 항목 초기화
                historyItems.innerHTML = '';
                
                // 최근 5개 문서만 표시
                const recentDocuments = allDocuments.slice(0, 5);
                
                if (recentDocuments.length === 0) {
                    historyItems.innerHTML = '<div class="info-message">업로드된 문서가 없습니다.</div>';
                    return;
                }
                
                // 히스토리 항목 생성
                recentDocuments.forEach(doc => {
                    const historyItemHTML = `
                        <div class="history-item" data-id="${doc.id}">
                            <div class="history-icon success">
                                <i class="fas fa-check"></i>
                            </div>
                            <div class="history-content">
                                <div class="history-header">
                                    <h3>${doc.filename}</h3>
                                    <span class="status-badge complete">완료</span>
                                </div>
                                <div class="history-details">
                                    <span><i class="fas fa-clock"></i> ${new Date(doc.created_at).toLocaleString()}</span>
                                    <span><i class="fas fa-file-alt"></i> ${doc.total_quantity || 0}개 항목</span>
                                    <span><i class="fas fa-tag"></i> ${doc.brand || '정보 없음'}</span>
                                    <span><i class="fas fa-file-invoice"></i> ${doc.document_type_label}</span>
                                </div>
                            </div>
                            <div class="history-actions">
                                <button class="btn btn-icon view-btn" data-id="${doc.id}"><i class="fas fa-eye"></i></button>
                                <button class="btn btn-icon download-btn" data-filename="${doc.excel_filename}"><i class="fas fa-download"></i></button>
                            </div>
                        </div>
                    `;
                    
                    historyItems.insertAdjacentHTML('beforeend', historyItemHTML);
                });
                
                // 보기 버튼에 이벤트 리스너 추가
                const viewButtons = historyItems.querySelectorAll('.view-btn');
                viewButtons.forEach(btn => {
                    btn.addEventListener('click', () => {
                        const docId = btn.getAttribute('data-id');
                        if (docId) {
                            window.location.href = `orders.html?doc=${docId}`;
                        }
                    });
                });
                
                // 다운로드 버튼에 이벤트 리스너 추가
                const downloadButtons = historyItems.querySelectorAll('.download-btn');
                downloadButtons.forEach(btn => {
                    btn.addEventListener('click', () => {
                        const filename = btn.getAttribute('data-filename');
                        if (filename) {
                            window.open(`${API_BASE_URL}/download/${filename}`, '_blank');
                        }
                    });
                });
            })
            .catch(error => {
                console.error('히스토리 로드 중 오류:', error);
                historyItems.innerHTML = '<div class="error-message">히스토리를 불러오는 중 오류가 발생했습니다.</div>';
            });
    }
    
    // 페이지 로드 시 히스토리 로드
    loadHistoryFromAPI();
});