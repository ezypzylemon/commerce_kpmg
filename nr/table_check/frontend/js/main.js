// API 베이스 URL
const API_BASE_URL = 'http://localhost:5000/api';

// 전역 상태 변수
let documents = [];
let comparisons = [];
let selectedDocumentId = null;

// DOM 요소
const documentList = document.getElementById('document-list');
const documentInfo = document.getElementById('document-info');
const documentPreview = document.getElementById('document-preview');
const documentTitle = document.querySelector('.doc-preview-title');
const uploadButton = document.getElementById('upload-button');
const uploadNewDocButton = document.getElementById('upload-new-doc-button');
const compareButton = document.getElementById('compare-button');
const reportButton = document.getElementById('report-button');
const searchButton = document.getElementById('search-button');
const searchInput = document.getElementById('search-input');
const notificationArea = document.getElementById('notification-area');
const notificationsList = document.getElementById('notifications-list');
const aiAssistantButton = document.getElementById('ai-assistant-button');
const comparisonTableBody = document.getElementById('comparison-table-body');

// 모달 관련 요소
const uploadModal = document.getElementById('upload-modal');
const uploadModalClose = document.getElementById('upload-modal-close');
const uploadForm = document.getElementById('upload-form');
const uploadProgressContainer = document.getElementById('upload-progress-container');
const uploadProgressBar = document.getElementById('upload-progress-bar');
const uploadResult = document.getElementById('upload-result');

const compareModal = document.getElementById('compare-modal');
const compareModalClose = document.getElementById('compare-modal-close');
const compareForm = document.getElementById('compare-form');
const doc1Select = document.getElementById('doc1-select');
const doc2Select = document.getElementById('doc2-select');
const compareProgressContainer = document.getElementById('compare-progress-container');
const compareProgressBar = document.getElementById('compare-progress-bar');
const compareResult = document.getElementById('compare-result');

const comparisonDetailModal = document.getElementById('comparison-detail-modal');
const comparisonDetailModalClose = document.getElementById('comparison-detail-modal-close');
const comparisonDetailContent = document.getElementById('comparison-detail-content');

// 차트 관련
let matchRateChart = null;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    // 문서 목록 로드
    loadDocuments();
    
    // 비교 결과 로드
    loadComparisons();
    
    // 매치율 차트 초기화
    initMatchRateChart();
    
    // 알림 목록 로드
    loadNotifications();
    
    // 이벤트 리스너 설정
    setupEventListeners();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 업로드 버튼 클릭 이벤트
    uploadButton.addEventListener('click', () => {
        openUploadModal();
    });
    
    uploadNewDocButton.addEventListener('click', () => {
        openUploadModal();
    });
    
    // 업로드 모달 닫기
    uploadModalClose.addEventListener('click', () => {
        closeUploadModal();
    });
    
    // 비교 버튼 클릭 이벤트
    compareButton.addEventListener('click', () => {
        openCompareModal();
    });
    
    // 비교 모달 닫기
    compareModalClose.addEventListener('click', () => {
        closeCompareModal();
    });
    
    // 상세 비교 모달 닫기
    comparisonDetailModalClose.addEventListener('click', () => {
        closeComparisonDetailModal();
    });
    
    // 파일 업로드 폼 제출
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        uploadFile();
    });
    
    // 비교 폼 제출
    compareForm.addEventListener('submit', (e) => {
        e.preventDefault();
        compareDocuments();
    });
    
    // 검색 입력 이벤트
    searchInput.addEventListener('input', () => {
        filterDocuments(searchInput.value);
    });
    
    // AI 어시스턴트 버튼 클릭
    aiAssistantButton.addEventListener('click', () => {
        showNotification('AI 문서 비교 어시스턴트가 준비 중입니다.', 'warning');
    });
    
    // 보고서 생성 버튼 클릭
    reportButton.addEventListener('click', () => {
        showNotification('보고서 생성 기능이 준비 중입니다.', 'warning');
    });
    
    // 고급 검색 버튼 클릭
    searchButton.addEventListener('click', () => {
        showNotification('고급 검색 기능이 준비 중입니다.', 'warning');
    });
    
    // 모달 외부 클릭시 닫기
    window.addEventListener('click', (e) => {
        if (e.target === uploadModal) {
            closeUploadModal();
        }
        if (e.target === compareModal) {
            closeCompareModal();
        }
        if (e.target === comparisonDetailModal) {
            closeComparisonDetailModal();
        }
    });
}

// 문서 목록 로드
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);
        if (!response.ok) {
            throw new Error('문서 목록을 불러오는데 실패했습니다.');
        }
        
        documents = await response.json();
        renderDocumentList();
        populateCompareSelects();
        
    } catch (error) {
        console.error('문서 목록 로드 오류:', error);
        showNotification('문서 목록을 불러오는데 실패했습니다.', 'error');
        documentList.innerHTML = '<div class="doc-item error">문서 목록을 불러오는데 실패했습니다.</div>';
    }
}

// 문서 목록 렌더링
function renderDocumentList() {
    if (documents.length === 0) {
        documentList.innerHTML = '<div class="doc-item">문서가 없습니다. 새 문서를 업로드하세요.</div>';
        return;
    }
    
    documentList.innerHTML = '';
    
    documents.forEach(doc => {
        const docItem = document.createElement('div');
        docItem.className = 'doc-item';
        docItem.dataset.id = doc.id;
        
        if (doc.id === selectedDocumentId) {
            docItem.classList.add('active');
        }
        
        const typeLabel = getDocTypeLabel(doc.type);
        const date = new Date(doc.timestamp.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
        const dateFormatted = date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
        
        docItem.innerHTML = `
            <div class="doc-item-title">${doc.filename}</div>
            <div class="doc-item-date">${typeLabel} • ${dateFormatted}</div>
        `;
        
        docItem.addEventListener('click', () => {
            selectDocument(doc.id);
        });
        
        documentList.appendChild(docItem);
    });
}

// 비교 셀렉트 박스 채우기
function populateCompareSelects() {
    // 옵션 초기화
    doc1Select.innerHTML = '<option value="">문서 선택...</option>';
    doc2Select.innerHTML = '<option value="">문서 선택...</option>';
    
    // 문서 옵션 추가
    documents.forEach(doc => {
        const typeLabel = getDocTypeLabel(doc.type);
        const option1 = document.createElement('option');
        option1.value = doc.id;
        option1.textContent = `${doc.filename} (${typeLabel})`;
        
        const option2 = option1.cloneNode(true);
        
        doc1Select.appendChild(option1);
        doc2Select.appendChild(option2);
    });
}

// 문서 타입 레이블 반환
function getDocTypeLabel(type) {
    switch (type) {
        case 'invoice':
            return '인보이스';
        case 'order':
            return '오더시트';
        case 'packing':
            return '패킹리스트';
        default:
            return '문서';
    }
}

// 문서 선택
async function selectDocument(docId) {
    selectedDocumentId = docId;
    
    // 활성화 클래스 업데이트
    const docItems = documentList.querySelectorAll('.doc-item');
    docItems.forEach(item => {
        if (item.dataset.id === docId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // 문서 상세 정보 불러오기
    try {
        const response = await fetch(`${API_BASE_URL}/documents/${docId}`);
        if (!response.ok) {
            throw new Error('문서 정보를 불러오는데 실패했습니다.');
        }
        
        const docData = await response.json();
        renderDocumentDetails(docData);
        
    } catch (error) {
        console.error('문서 로드 오류:', error);
        showNotification('문서 정보를 불러오는데 실패했습니다.', 'error');
        documentInfo.innerHTML = '<p class="error-message">문서 정보를 불러오는데 실패했습니다.</p>';
    }
}

// 문서 상세 정보 렌더링
function renderDocumentDetails(doc) {
    const typeLabel = getDocTypeLabel(doc.type);
    const date = new Date(doc.timestamp.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
    const dateFormatted = date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
    
    // 문서 제목 업데이트
    documentTitle.textContent = doc.filename;
    
    // 데이터가 없는 경우
    if (!doc.data || doc.data.length === 0) {
        documentInfo.innerHTML = `
            <div class="info-section">
                <h4 class="info-title">문서 정보</h4>
                <table class="info-table">
                    <tr>
                        <td>문서 타입</td>
                        <td>${typeLabel}</td>
                    </tr>
                    <tr>
                        <td>날짜</td>
                        <td>${dateFormatted}</td>
                    </tr>
                </table>
            </div>
            <p>이 문서에서 추출된 데이터가 없습니다.</p>
        `;
        return;
    }
    
    // 첫 번째 상품 데이터에서 일반 정보 추출
    const firstProduct = doc.data[0];
    
    // 브랜드 및 시즌 정보
    const brandName = firstProduct.Brand || firstProduct.브랜드 || 'N/A';
    const seasonInfo = firstProduct.Season || 'N/A';
    
    // 주문 정보
    const poNumber = firstProduct.발주번호 || firstProduct.po_number || 'N/A';
    const shipStartDate = firstProduct.선적시작일 || firstProduct.start_ship || 'N/A';
    const shipEndDate = firstProduct.선적완료일 || firstProduct.complete_ship || 'N/A';
    const paymentTerms = firstProduct.결제조건 || firstProduct.terms || 'N/A';
    const totalQuantity = firstProduct.총수량 || firstProduct.total_quantity || 'N/A';
    const totalAmount = `${firstProduct.통화 || 'EUR'} ${firstProduct.총금액 || firstProduct.total_amount || 'N/A'}`;
    
    // HTML 생성
    documentInfo.innerHTML = `
        <div class="info-section">
            <h4 class="info-title">문서 정보</h4>
            <table class="info-table">
                <tr>
                    <td>문서 타입</td>
                    <td>${typeLabel}</td>
                </tr>
                <tr>
                    <td>인식된 브랜드명</td>
                    <td>${brandName}</td>
                </tr>
                <tr>
                    <td>시즌</td>
                    <td>${seasonInfo}</td>
                </tr>
                <tr>
                    <td>발주번호</td>
                    <td>${poNumber}</td>
                </tr>
                <tr>
                    <td>날짜</td>
                    <td>${dateFormatted}</td>
                </tr>
            </table>
        </div>
        
        <div class="info-section">
            <h4 class="info-title">선적 정보</h4>
            <table class="info-table">
                <tr>
                    <td>선적 시작일</td>
                    <td>${shipStartDate}</td>
                </tr>
                <tr>
                    <td>선적 완료일</td>
                    <td>${shipEndDate}</td>
                </tr>
                <tr>
                    <td>결제 조건</td>
                    <td>${paymentTerms}</td>
                </tr>
                <tr>
                    <td>총 수량</td>
                    <td>${totalQuantity}</td>
                </tr>
                <tr>
                    <td>총 금액</td>
                    <td>${totalAmount}</td>
                </tr>
            </table>
        </div>
        
        <div class="info-section">
            <h4 class="info-title">상품 정보</h4>
            <div style="max-height: 300px; overflow-y: auto;">
                <table class="product-table">
                    <thead>
                        <tr>
                            <th>상품 코드</th>
                            <th>색상</th>
                            <th>사이즈</th>
                            <th>수량</th>
                            <th>가격(€)</th>
                        </tr>
                    </thead>
                    <tbody id="product-table-body">
                        ${renderProductRows(doc.data)}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// 상품 테이블 행 생성
function renderProductRows(products) {
    return products.map(product => {
        const code = product.Product_Code || 'N/A';
        const color = product.Color || 'N/A';
        const size = product.Size || 'N/A';
        const quantity = product.Quantity || 'N/A';
        const price = product.Wholesale_EUR || 'N/A';
        
        return `
            <tr>
                <td>${code}</td>
                <td>${color}</td>
                <td>${size}</td>
                <td>${quantity}</td>
                <td>${price}</td>
            </tr>
        `;
    }).join('');
}

// 문서 필터링
function filterDocuments(query) {
    if (!query) {
        renderDocumentList();
        return;
    }
    
    query = query.toLowerCase();
    
    const filteredDocs = documents.filter(doc => {
        const filename = doc.filename.toLowerCase();
        return filename.includes(query);
    });
    
    if (filteredDocs.length === 0) {
        documentList.innerHTML = '<div class="doc-item">검색 결과가 없습니다.</div>';
        return;
    }
    
    documentList.innerHTML = '';
    
    filteredDocs.forEach(doc => {
        const docItem = document.createElement('div');
        docItem.className = 'doc-item';
        docItem.dataset.id = doc.id;
        
        if (doc.id === selectedDocumentId) {
            docItem.classList.add('active');
        }
        
        const typeLabel = getDocTypeLabel(doc.type);
        const date = new Date(doc.timestamp.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
        const dateFormatted = date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
        
        docItem.innerHTML = `
            <div class="doc-item-title">${doc.filename}</div>
            <div class="doc-item-date">${typeLabel} • ${dateFormatted}</div>
        `;
        
        docItem.addEventListener('click', () => {
            selectDocument(doc.id);
        });
        
        documentList.appendChild(docItem);
    });
}

// 파일 업로드 모달 열기
function openUploadModal() {
    uploadModal.style.display = 'block';
    uploadForm.reset();
    uploadProgressContainer.style.display = 'none';
    uploadResult.style.display = 'none';
}

// 파일 업로드 모달 닫기
function closeUploadModal() {
    uploadModal.style.display = 'none';
}

// 비교 모달 열기
function openCompareModal() {
    compareModal.style.display = 'block';
    compareForm.reset();
    compareProgressContainer.style.display = 'none';
    compareResult.style.display = 'none';
    
    // 드롭다운 옵션 채우기
    populateCompareSelects();
}

// 비교 모달 닫기
function closeCompareModal() {
    compareModal.style.display = 'none';
}

// 비교 상세 모달 열기
function openComparisonDetailModal(comparisonId) {
    comparisonDetailModal.style.display = 'block';
    loadComparisonDetails(comparisonId);
}

// 비교 상세 모달 닫기
function closeComparisonDetailModal() {
    comparisonDetailModal.style.display = 'none';
}

// 파일 업로드 처리
async function uploadFile() {
    const fileInput = document.getElementById('file-upload');
    const docType = document.getElementById('doc-type').value;
    
    if (!fileInput.files[0]) {
        showNotification('파일을 선택해주세요.', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('type', docType);
    
    // UI 상태 업데이트
    uploadForm.style.display = 'none';
    uploadProgressContainer.style.display = 'block';
    uploadProgressBar.style.width = '0%';
    
    // 프로그레스 바 애니메이션
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 5;
        if (progress > 90) {
            clearInterval(progressInterval);
        }
        uploadProgressBar.style.width = `${progress}%`;
    }, 300);
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        uploadProgressBar.style.width = '100%';
        
        const result = await response.json();
        
        if (response.ok) {
            // 업로드 성공
            uploadResult.style.display = 'block';
            uploadResult.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <div>파일 업로드 및 처리 완료</div>
                        <p>${result.filename} 처리 완료 (${result.product_count || 0}개 상품 추출)</p>
                    </div>
                </div>
            `;
            
            // 문서 목록 새로고침
            await loadDocuments();
            
            // 3초 후 모달 닫기
            setTimeout(() => {
                closeUploadModal();
                
                // 새로 업로드한 문서 선택
                if (result.id) {
                    selectDocument(result.id);
                }
                
                // 비교 결과가 있으면 알림 표시
                if (result.comparison && result.comparison.status === 'comparison_found') {
                    const matchRate = result.comparison.best_match.match_rate;
                    const filename = result.comparison.best_match.filename;
                    
                    let alertType = 'success';
                    if (matchRate < 50) {
                        alertType = 'error';
                    } else if (matchRate < 90) {
                        alertType = 'warning';
                    }
                    
                    showNotification(`문서 "${filename}"와(과) ${matchRate}% 일치합니다.`, alertType);
                    
                    // 비교 결과 새로고침
                    loadComparisons();
                }
                
            }, 3000);
            
        } else {
            // 업로드 실패
            uploadResult.style.display = 'block';
            uploadResult.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div>
                        <div>업로드 실패</div>
                        <p>${result.error || '파일 처리 중 오류가 발생했습니다.'}</p>
                    </div>
                </div>
            `;
            
            // 폼 다시 표시
            setTimeout(() => {
                uploadForm.style.display = 'block';
            }, 3000);
        }
        
    } catch (error) {
        clearInterval(progressInterval);
        console.error('파일 업로드 오류:', error);
        
        uploadResult.style.display = 'block';
        uploadResult.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <div>업로드 실패</div>
                    <p>서버 연결 오류가 발생했습니다.</p>
                </div>
            </div>
        `;
        
        // 폼 다시 표시
        setTimeout(() => {
            uploadForm.style.display = 'block';
        }, 3000);
    }
}

// 문서 비교 처리
async function compareDocuments() {
    const doc1Id = doc1Select.value;
    const doc2Id = doc2Select.value;
    
    if (!doc1Id || !doc2Id) {
        showNotification('두 문서를 모두 선택해주세요.', 'error');
        return;
    }
    
    if (doc1Id === doc2Id) {
        showNotification('서로 다른 문서를 선택해주세요.', 'error');
        return;
    }
    
    // UI 상태 업데이트
    compareForm.style.display = 'none';
    compareProgressContainer.style.display = 'block';
    compareProgressBar.style.width = '0%';
    
    // 프로그레스 바 애니메이션
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 5;
        if (progress > 90) {
            clearInterval(progressInterval);
        }
        compareProgressBar.style.width = `${progress}%`;
    }, 300);
    
    try {
        const response = await fetch(`${API_BASE_URL}/compare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doc1_id: doc1Id,
                doc2_id: doc2Id
            })
        });
        
        clearInterval(progressInterval);
        compareProgressBar.style.width = '100%';
        
        const result = await response.json();
        
        if (response.ok) {
            // 비교 성공
            compareResult.style.display = 'block';
            
            const matchRate = result.result.match_rate;
            let statusClass = 'success';
            let statusText = '완료';
            
            if (matchRate < 50) {
                statusClass = 'error';
                statusText = '검토 필요';
            } else if (matchRate < 90) {
                statusClass = 'warning';
                statusText = '확인 필요';
            }
            
            compareResult.innerHTML = `
                <div class="alert alert-${statusClass}">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <div>문서 비교 완료</div>
                        <p>일치율: ${matchRate}% (${statusText})</p>
                    </div>
                </div>
                <button class="btn btn-primary" id="view-comparison-btn">
                    <i class="fas fa-eye"></i> 비교 결과 보기
                </button>
            `;
            
            // 비교 결과 보기 버튼에 이벤트 연결
            document.getElementById('view-comparison-btn').addEventListener('click', () => {
                closeCompareModal();
                openComparisonDetailModal(result.result.id);
            });
            
            // 비교 결과 목록 새로고침
            await loadComparisons();
            
            // 3초 후 모달 닫기 (버튼 클릭하지 않으면)
            setTimeout(() => {
                if (compareModal.style.display === 'block') {
                    closeCompareModal();
                }
            }, 5000);
            
        } else {
            // 비교 실패
            compareResult.style.display = 'block';
            compareResult.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div>
                        <div>비교 실패</div>
                        <p>${result.error || '문서 비교 중 오류가 발생했습니다.'}</p>
                    </div>
                </div>
            `;
            
            // 폼 다시 표시
            setTimeout(() => {
                compareForm.style.display = 'block';
            }, 3000);
        }
        
    } catch (error) {
        clearInterval(progressInterval);
        console.error('문서 비교 오류:', error);
        
        compareResult.style.display = 'block';
        compareResult.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <div>비교 실패</div>
                    <p>서버 연결 오류가 발생했습니다.</p>
                </div>
            </div>
        `;
        
        // 폼 다시 표시
        setTimeout(() => {
            compareForm.style.display = 'block';
        }, 3000);
    }
}

// 비교 결과 목록 로드
async function loadComparisons() {
    try {
        const response = await fetch(`${API_BASE_URL}/comparisons`);
        if (!response.ok) {
            throw new Error('비교 결과 목록을 불러오는데 실패했습니다.');
        }
        
        comparisons = await response.json();
        renderComparisonTable();
        updateMatchRateChart();
        
    } catch (error) {
        console.error('비교 결과 목록 로드 오류:', error);
        comparisonTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">비교 결과를 불러오는데 실패했습니다.</td>
            </tr>
        `;
    }
}

// 비교 결과 테이블 렌더링
function renderComparisonTable() {
    if (comparisons.length === 0) {
        comparisonTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">비교 결과가 없습니다.</td>
            </tr>
        `;
        return;
    }
    
    comparisonTableBody.innerHTML = '';
    
    comparisons.forEach(comparison => {
        // 일치율에 따른 색상 클래스
        let rateColorClass = 'success';
        if (comparison.match_rate < 50) {
            rateColorClass = 'danger';
        } else if (comparison.match_rate < 90) {
            rateColorClass = 'warning';
        }
        
        // 상태 레이블
        let statusClass = 'status-complete';
        let statusText = '완료';
        
        if (comparison.status === 'review_needed') {
            statusClass = 'status-failed';
            statusText = '검토 필요';
        }
        
        // 날짜 포맷
        const date = new Date(comparison.timestamp.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
        const dateFormatted = date.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' });
        
        // 문서 이름 가져오기
        const doc1 = documents.find(d => d.id === comparison.doc1_id) || { filename: '알 수 없는 문서' };
        const doc2 = documents.find(d => d.id === comparison.doc2_id) || { filename: '알 수 없는 문서' };
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${dateFormatted}</td>
            <td>${doc1.filename}</td>
            <td>${doc2.filename}</td>
            <td>
                <div class="progress-bar">
                    <div class="progress-fill ${rateColorClass}" style="width: ${comparison.match_rate}%"></div>
                </div>
                ${comparison.match_rate}%
            </td>
            <td><span class="status-label ${statusClass}">${statusText}</span></td>
            <td><a href="#" class="view-button" data-id="${comparison.id}">상세보기</a></td>
        `;
        
        // 상세보기 버튼에 이벤트 연결
        row.querySelector('.view-button').addEventListener('click', (e) => {
            e.preventDefault();
            openComparisonDetailModal(comparison.id);
        });
        
        comparisonTableBody.appendChild(row);
    });
}

// 비교 결과 상세 정보 로드
async function loadComparisonDetails(comparisonId) {
    try {
        const response = await fetch(`${API_BASE_URL}/comparisons/${comparisonId}`);
        if (!response.ok) {
            throw new Error('비교 결과를 불러오는데 실패했습니다.');
        }
        
        const comparison = await response.json();
        renderComparisonDetails(comparison);
        
    } catch (error) {
        console.error('비교 결과 로드 오류:', error);
        comparisonDetailContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <div>비교 결과를 불러오는데 실패했습니다.</div>
                </div>
            </div>
        `;
    }
}

// 비교 결과 상세 정보 렌더링
function renderComparisonDetails(comparison) {
    // 일치율에 따른 색상 클래스
    let rateColorClass = 'success';
    if (comparison.match_rate < 50) {
        rateColorClass = 'danger';
    } else if (comparison.match_rate < 90) {
        rateColorClass = 'warning';
    }
    
    // 날짜 포맷
    const date = new Date(comparison.timestamp.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
    const dateFormatted = date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    
    // 문서 이름 가져오기
    const doc1 = documents.find(d => d.id === comparison.doc1_id) || { filename: '알 수 없는 문서' };
    const doc2 = documents.find(d => d.id === comparison.doc2_id) || { filename: '알 수 없는 문서' };
    
    // 통계 정보
    const stats = comparison.stats || {
        total_products: 0,
        common_products: 0,
        doc1_only_count: 0,
        doc2_only_count: 0,
        differences_count: 0
    };
    
    // HTML 생성
    comparisonDetailContent.innerHTML = `
        <div class="comparison-summary">
            <h3>비교 요약</h3>
            <div class="summary-info">
                <p><strong>비교 날짜:</strong> ${dateFormatted}</p>
                <p><strong>문서 1:</strong> ${doc1.filename}</p>
                <p><strong>문서 2:</strong> ${doc2.filename}</p>
                <p><strong>일치율:</strong> <span class="text-${rateColorClass}">${comparison.match_rate}%</span></p>
            </div>
            
            <div class="statistics">
                <div class="stat-item">
                    <div class="stat-value">${stats.total_products}</div>
                    <div class="stat-label">총 상품</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.common_products}</div>
                    <div class="stat-label">공통 상품</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.differences_count}</div>
                    <div class="stat-label">차이점</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.doc1_only_count}</div>
                    <div class="stat-label">문서1 전용</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.doc2_only_count}</div>
                    <div class="stat-label">문서2 전용</div>
                </div>
            </div>
        </div>
        
        <div class="comparison-tabs">
            <ul class="tabs-nav">
                <li class="active" data-tab="differences">차이점 (${comparison.differences?.length || 0})</li>
                <li data-tab="doc1-only">문서1 전용 (${comparison.doc1_only?.length || 0})</li>
                <li data-tab="doc2-only">문서2 전용 (${comparison.doc2_only?.length || 0})</li>
                <li data-tab="matching">일치 항목 (${comparison.matching_products?.length || 0})</li>
            </ul>
            
            <div class="tab-content active" id="differences-tab">
                ${renderDifferencesTable(comparison.differences)}
            </div>
            
            <div class="tab-content" id="doc1-only-tab">
                ${renderDocOnlyTable(comparison.doc1_only, '문서1에만 있는 상품')}
            </div>
            
            <div class="tab-content" id="doc2-only-tab">
                ${renderDocOnlyTable(comparison.doc2_only, '문서2에만 있는 상품')}
            </div>
            
            <div class="tab-content" id="matching-tab">
                ${renderMatchingTable(comparison.matching_products)}
            </div>
        </div>
    `;
    
    // 탭 동작 설정
    const tabNavs = comparisonDetailContent.querySelectorAll('.tabs-nav li');
    const tabContents = comparisonDetailContent.querySelectorAll('.tab-content');
    
    tabNavs.forEach(nav => {
        nav.addEventListener('click', () => {
            const tabId = nav.dataset.tab;
            
            // 활성 탭 표시 업데이트
            tabNavs.forEach(n => n.classList.remove('active'));
            nav.classList.add('active');
            
            // 탭 콘텐츠 표시 업데이트
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// 차이점 테이블 렌더링
function renderDifferencesTable(differences) {
    if (!differences || differences.length === 0) {
        return '<p class="empty-message">차이점이 없습니다.</p>';
    }
    
    return `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>상품 코드</th>
                    <th>사이즈</th>
                    <th>필드</th>
                    <th>문서1 값</th>
                    <th>문서2 값</th>
                </tr>
            </thead>
            <tbody>
                ${differences.map(diff => `
                    <tr>
                        <td>${diff.product_code || 'N/A'}</td>
                        <td>${diff.size || 'N/A'}</td>
                        <td>${diff.field || 'N/A'}</td>
                        <td class="highlight">${diff.doc1_value || 'N/A'}</td>
                        <td class="highlight">${diff.doc2_value || 'N/A'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 문서 전용 상품 테이블 렌더링
function renderDocOnlyTable(products, title) {
    if (!products || products.length === 0) {
        return `<p class="empty-message">${title}이 없습니다.</p>`;
    }
    
    return `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>상품 코드</th>
                    <th>색상</th>
                    <th>사이즈</th>
                    <th>수량</th>
                </tr>
            </thead>
            <tbody>
                ${products.map(product => `
                    <tr>
                        <td>${product.product_code || 'N/A'}</td>
                        <td>${product.color || 'N/A'}</td>
                        <td>${product.size || 'N/A'}</td>
                        <td>${product.quantity || 'N/A'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 일치 항목 테이블 렌더링
function renderMatchingTable(products) {
    if (!products || products.length === 0) {
        return '<p class="empty-message">일치하는 항목이 없습니다.</p>';
    }
    
    return `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>상품 코드</th>
                    <th>색상</th>
                    <th>사이즈</th>
                    <th>수량</th>
                </tr>
            </thead>
            <tbody>
                ${products.map(product => `
                    <tr>
                        <td>${product.product_code || 'N/A'}</td>
                        <td>${product.color || 'N/A'}</td>
                        <td>${product.size || 'N/A'}</td>
                        <td>${product.quantity || 'N/A'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 매치율 차트 초기화
function initMatchRateChart() {
    const ctx = document.getElementById('match-rate-chart').getContext('2d');
    
    matchRateChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['일치', '불일치'],
            datasets: [{
                data: [0, 100],
                backgroundColor: [
                    '#4caf50',
                    '#e57373'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

// 매치율 차트 업데이트
function updateMatchRateChart() {
    if (!matchRateChart || comparisons.length === 0) {
        return;
    }
    
    // 모든 비교의 평균 일치율 계산
    const totalMatchRate = comparisons.reduce((sum, comp) => sum + comp.match_rate, 0);
    const averageMatchRate = Math.round(totalMatchRate / comparisons.length);
    
    // 차트 데이터 업데이트
    matchRateChart.data.datasets[0].data = [averageMatchRate, 100 - averageMatchRate];
    matchRateChart.update();
}

// 알림 목록 로드
function loadNotifications() {
    // 비교 결과 기반으로 알림 생성
    if (comparisons.length === 0) {
        notificationsList.innerHTML = '<p class="empty-message">알림이 없습니다.</p>';
        return;
    }
    
    notificationsList.innerHTML = '';
    
    // 최근 3개의 비교 결과에 대한 알림 생성
    const recentComparisons = comparisons.slice(0, 3);
    
    recentComparisons.forEach(comparison => {
        const doc1 = documents.find(d => d.id === comparison.doc1_id) || { filename: '알 수 없는 문서' };
        const doc2 = documents.find(d => d.id === comparison.doc2_id) || { filename: '알 수 없는 문서' };
        
        let type = 'success';
        let icon = 'check';
        let message = '완전 일치';
        
        if (comparison.match_rate < 50) {
            type = 'error';
            icon = 'exclamation-triangle';
            message = '검토 필요';
        } else if (comparison.match_rate < 90) {
            type = 'warning';
            icon = 'file-alt';
            message = '확인 필요';
        }
        
        // 날짜 포맷
        const date = new Date(comparison.timestamp.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
        const timeAgo = getTimeAgo(date);
        
        const notificationItem = document.createElement('div');
        notificationItem.className = `notification-item ${type}`;
        notificationItem.innerHTML = `
            <div class="notification-icon ${type}">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${doc1.filename} vs ${doc2.filename}</div>
                <div class="notification-message">${timeAgo} - 일치율 ${comparison.match_rate}% (${message})</div>
            </div>
        `;
        
        notificationItem.addEventListener('click', () => {
            openComparisonDetailModal(comparison.id);
        });
        
        notificationsList.appendChild(notificationItem);
    });
}

// 날짜로부터 경과 시간 계산
function getTimeAgo(date) {
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `${days}일 전`;
    } else if (hours > 0) {
        return `${hours}시간 전`;
    } else if (minutes > 0) {
        return `${minutes}분 전`;
    } else {
        return `${seconds}초 전`;
    }
}

// 알림 표시
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    
    let icon = 'check-circle';
    if (type === 'error') {
        icon = 'exclamation-triangle';
    } else if (type === 'warning') {
        icon = 'exclamation-circle';
    }
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <div>${message}</div>
    `;
    
    notificationArea.appendChild(notification);
    
    // 5초 후 알림 삭제
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}