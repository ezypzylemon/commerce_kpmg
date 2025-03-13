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
        
        // 옵션 값 가져오기
        const docType = document.querySelector('select[name="docType"]')?.value || '자동 감지';
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
            
            // 세션 스토리지에 문서 정보 저장 (orders.js와 연동을 위함)
            const documentInfo = storeDocumentInfo(file.name, data);
            console.log('저장된 문서 정보:', documentInfo);
            
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
                            <span class="summary-label">파일명:</span>
                            <span class="summary-value">${data.excel_filename || ''}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">문서 유형:</span>
                            <span class="summary-value">${docType}</span>
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
            <div class="history-item">
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
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn btn-icon"><i class="fas fa-eye"></i></button>
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
    }
    
    // 문서 정보를 세션 스토리지에 저장하는 함수 (업데이트됨)
    function storeDocumentInfo(fileName, data) {
        // 문서 기본 정보 구성
        const documentInfo = {
            id: data.document_id || data.excel_filename || generateUniqueId(),
            filename: fileName,
            excel_filename: data.excel_filename,
            date: new Date().toISOString().split('T')[0],
            document_type: document.querySelector('select[name="docType"]')?.value || '자동 감지',
            brand: document.querySelector('select[name="brand"]')?.value || '자동 감지',
            season: document.querySelector('select[name="season"]')?.value || '',
            status: 'complete',
            match_rate: 100, // 초기 일치율 (비교 전)
            total_products: data.total_products || 0,
            preview_data: data.data_preview || []
        };
        
        // 문서 유형 정규화
        if (documentInfo.document_type === '자동 감지' || documentInfo.document_type === '인보이스') {
            // 파일명 기반 문서 유형 추정
            if (fileName.toLowerCase().includes('invoice')) {
                documentInfo.document_type = 'invoice';
            } else if (fileName.toLowerCase().includes('po') || fileName.toLowerCase().includes('order')) {
                documentInfo.document_type = 'purchase_order';
            } else if (fileName.toLowerCase().includes('contract')) {
                documentInfo.document_type = 'contract';
            } else {
                documentInfo.document_type = 'unknown';
            }
        }
        
        // 금액 정보 추출 시도
        try {
            // 미리보기 데이터에서 총액 찾기
            if (data.data_preview && data.data_preview.length > 0) {
                // 'Total_Amount' 또는 'total_amount' 열이 있는지 확인
                const firstRow = data.data_preview[0];
                if (firstRow.hasOwnProperty('Total_Amount') || firstRow.hasOwnProperty('total_amount')) {
                    const amountKey = firstRow.hasOwnProperty('Total_Amount') ? 'Total_Amount' : 'total_amount';
                    documentInfo.amount = firstRow[amountKey];
                } else if (firstRow.hasOwnProperty('Wholesale_Price') || firstRow.hasOwnProperty('wholesale_price')) {
                    // 금액 필드가 없을 경우 도매가 사용
                    const priceKey = firstRow.hasOwnProperty('Wholesale_Price') ? 'Wholesale_Price' : 'wholesale_price';
                    documentInfo.amount = firstRow[priceKey];
                }
            }

            // orders.js에서 기대하는 필드 추가
            if (!documentInfo.amount && data.total_amount) {
                documentInfo.amount = data.total_amount;
            }
        } catch (e) {
            console.log('금액 정보 추출 실패:', e);
        }
        
        // 세션 스토리지에서 기존 문서 목록 가져오기
        let documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        
        // 중복 확인 (같은 ID의 문서가 있으면 업데이트)
        const existingIndex = documents.findIndex(doc => doc.id === documentInfo.id);
        if (existingIndex >= 0) {
            documents[existingIndex] = documentInfo;
        } else {
            // 새 문서 추가
            documents.push(documentInfo);
        }
        
        // 세션 스토리지에 저장
        sessionStorage.setItem('ocr_documents', JSON.stringify(documents));
        
        console.log('문서 정보가 세션 스토리지에 저장되었습니다:', documentInfo);
        
        return documentInfo; // 저장된 문서 정보 반환 (디버깅용)
    }
    
    // 고유 ID 생성 함수
    function generateUniqueId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
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
            loadHistoryFromStorage();
        });
    }
    
    // 세션 스토리지에서 히스토리 로드
    function loadHistoryFromStorage() {
        const historyItems = document.querySelector('.history-items');
        if (!historyItems) return;
        
        // 세션 스토리지에서 문서 정보 가져오기
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        
        if (documents.length === 0) {
            console.log('저장된 문서 정보가 없습니다.');
            return;
        }
        
        // 히스토리 항목 초기화
        historyItems.innerHTML = '';
        
        // 최근 문서부터 표시 (최대 5개)
        const recentDocuments = documents.slice(0, 5);
        
        recentDocuments.forEach(doc => {
            // 상태 클래스 결정
            let statusClass = 'success';
            let statusBadge = 'complete';
            let statusIcon = 'check';
            
            if (doc.status === 'error') {
                statusClass = 'error';
                statusBadge = 'error';
                statusIcon = 'exclamation-triangle';
            } else if (doc.status === 'processing') {
                statusClass = 'processing';
                statusBadge = 'processing';
                statusIcon = 'spinner fa-spin';
            }
            
            // 히스토리 항목 HTML 생성
            const historyItemHTML = `
                <div class="history-item" data-id="${doc.id}">
                    <div class="history-icon ${statusClass}">
                        <i class="fas fa-${statusIcon}"></i>
                    </div>
                    <div class="history-content">
                        <div class="history-header">
                            <h3>${doc.filename}</h3>
                            <span class="status-badge ${statusBadge}">${statusBadge === 'complete' ? '완료' : statusBadge === 'error' ? '오류' : '처리 중'}</span>
                        </div>
                        <div class="history-details">
                            <span><i class="fas fa-clock"></i> ${doc.date}</span>
                            <span><i class="fas fa-file-alt"></i> ${doc.total_products || 0}개 항목</span>
                            <span><i class="fas fa-tag"></i> ${doc.brand}</span>
                        </div>
                    </div>
                    <div class="history-actions">
                        <button class="btn btn-icon view-btn" data-id="${doc.id}"><i class="fas fa-eye"></i></button>
                        <button class="btn btn-icon download-btn" data-filename="${doc.excel_filename}"><i class="fas fa-download"></i></button>
                    </div>
                </div>
            `;
            
            // 히스토리 목록에 추가
            historyItems.insertAdjacentHTML('beforeend', historyItemHTML);
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
        
        // 보기 버튼에 이벤트 리스너 추가
        const viewButtons = historyItems.querySelectorAll('.view-btn');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const docId = btn.getAttribute('data-id');
                if (docId) {
                    // orders.html로 이동하면서 문서 ID 전달
                    window.location.href = `orders.html?doc=${docId}`;
                }
            });
        });
    }
    
    // 디버깅 도구 추가 (개발 환경에서만)
    function addDebugTools() {
        // 개발 환경인지 확인
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            const debugSection = document.createElement('div');
            debugSection.className = 'debug-section mt-4 p-3 bg-light border';
            debugSection.innerHTML = `
                <h4>디버깅 도구</h4>
                <button id="debug-show-storage" class="btn btn-info btn-sm">세션 스토리지 내용 보기</button>
                <button id="debug-clear-storage" class="btn btn-danger btn-sm ml-2">세션 스토리지 초기화</button>
                <div id="debug-output" class="mt-3 p-2 bg-dark text-light" style="max-height: 300px; overflow: auto; display: none;"></div>
            `;
            
            // 디버깅 섹션 추가
            document.querySelector('.upload-history').after(debugSection);
            
            // 디버깅 버튼 이벤트 리스너
            document.getElementById('debug-show-storage').addEventListener('click', function() {
                const debugOutput = document.getElementById('debug-output');
                const storageData = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
                
                debugOutput.style.display = 'block';
                debugOutput.innerHTML = `<pre>${JSON.stringify(storageData, null, 2)}</pre>`;
            });
            
            document.getElementById('debug-clear-storage').addEventListener('click', function() {
                sessionStorage.removeItem('ocr_documents');
                alert('세션 스토리지가 초기화되었습니다.');
                // 히스토리 새로고침
                loadHistoryFromStorage();
                // 디버그 출력 초기화
                const debugOutput = document.getElementById('debug-output');
                debugOutput.style.display = 'none';
                debugOutput.innerHTML = '';
            });
        }
    }
    
    // 페이지 로드 시 히스토리 로드
    loadHistoryFromStorage();
    
    // 디버깅 도구 추가
    addDebugTools();
});