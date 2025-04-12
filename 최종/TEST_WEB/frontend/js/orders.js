// orders.js - 발주 및 계약 관리 페이지 스크립트

// API 기본 URL 설정 (개발 환경)
const API_BASE_URL = 'http://localhost:5000/orders';

document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 선택
    const documentGrid = document.querySelector('.document-grid');
    const searchInput = document.querySelector('.search-box input');
    const filterButton = document.querySelector('.sidebar-filters .btn-primary');
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    // 문서 상세 정보 요소
    const documentDetail = document.querySelector('.document-detail');
    const documentPreview = documentDetail ? document.querySelector('.doc-preview img') : null;
    const documentInfoItems = documentDetail ? document.querySelectorAll('.detail-item') : [];
    const documentDetailTable = documentDetail ? document.querySelector('.detail-table tbody') : null;
    const editButton = documentDetail ? document.querySelector('.document-detail .btn-primary') : null;
    const downloadButton = documentDetail ? document.querySelector('.document-detail .btn-outline') : null;
    
    // 모달 요소
    const compareModal = document.getElementById('compareModal');
    const compareDocSelect = document.getElementById('compareDocSelect');
    const startCompareBtn = document.getElementById('startCompareBtn');
    const cancelCompareBtn = document.getElementById('cancelCompareBtn');
    const compareResult = document.getElementById('compareResult');
    
    // 현재 선택된 문서 ID
    let selectedDocumentId = null;
    
    // 초기 데이터 로드
    loadDocuments();
    
    // URL 파라미터에서 문서 ID 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const docIdFromUrl = urlParams.get('doc');
    if (docIdFromUrl) {
        // 페이지 로드 후 해당 문서 표시
        setTimeout(() => {
            viewDocument(docIdFromUrl);
        }, 500);
    }
    
    // 검색 이벤트 리스너
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                loadDocuments({
                    search: searchInput.value
                });
            }
        });
    }
    
    // 필터 버튼 이벤트 리스너
    if (filterButton) {
        filterButton.addEventListener('click', function() {
            applyFilters();
        });
    }
    
    // 탭 버튼 이벤트 리스너
    if (tabButtons.length > 0) {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                // 활성 탭 토글
                tabButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // 탭에 따른 문서 유형 필터링
                const tabText = btn.textContent.trim().toLowerCase();
                if (tabText === '모든 문서') {
                    loadDocuments();
                } else if (tabText === '발주서') {
                    loadDocuments({ docType: 'order' });
                } else if (tabText === '인보이스') {
                    loadDocuments({ docType: 'invoice' });
                } else if (tabText === '계약서') {
                    loadDocuments({ docType: 'contract' });
                }
            });
        });
    }

    // 문서 목록 로드 함수 (API 사용)
    function loadDocuments(filters = {}) {
        console.log("문서 로딩 시작 - API 사용");
        
        if (!documentGrid) {
            console.error("문서 그리드 요소를 찾을 수 없습니다.");
            return;
        }
        
        // 로딩 표시
        documentGrid.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 문서 로드 중...</div>';
        
        // 인보이스 및 오더 데이터 가져오기
        Promise.all([
            fetch(`${API_BASE_URL}/documents/invoice`).then(response => response.json()),
            fetch(`${API_BASE_URL}/documents/order`).then(response => response.json())
        ])
        .then(([invoiceData, orderData]) => {
            // 모든 문서 목록 병합
            let allDocuments = [
                ...(invoiceData.invoices || []).map(doc => ({...doc, document_type: 'invoice'})),
                ...(orderData.orders || []).map(doc => ({...doc, document_type: 'order'}))
            ];
            
            console.log("API에서 로드한 문서:", allDocuments.length, "개");
            
            // 필터 적용
            let filteredDocs = allDocuments;
            
            if (filters.search) {
                const searchTerm = filters.search.toLowerCase();
                filteredDocs = filteredDocs.filter(doc => 
                    (doc.filename && doc.filename.toLowerCase().includes(searchTerm)) || 
                    (doc.brand && doc.brand.toLowerCase().includes(searchTerm))
                );
            }
            
            if (filters.docType) {
                filteredDocs = filteredDocs.filter(doc => doc.document_type === filters.docType);
            }
            
            if (filters.brand) {
                filteredDocs = filteredDocs.filter(doc => 
                    doc.brand && doc.brand.toLowerCase() === filters.brand.toLowerCase()
                );
            }
            
            if (filters.dateFrom) {
                const fromDate = new Date(filters.dateFrom);
                filteredDocs = filteredDocs.filter(doc => 
                    doc.created_at && new Date(doc.created_at) >= fromDate
                );
            }
            
            if (filters.dateTo) {
                const toDate = new Date(filters.dateTo);
                toDate.setHours(23, 59, 59, 999); // 날짜 범위의 끝
                filteredDocs = filteredDocs.filter(doc => 
                    doc.created_at && new Date(doc.created_at) <= toDate
                );
            }
            
            // 문서 표시
            if (filteredDocs.length > 0) {
                renderDocumentGrid(filteredDocs);
            } else {
                documentGrid.innerHTML = '<div class="empty-state">문서가 없습니다. 새 문서를 업로드해주세요.</div>';
            }
            
            // 지표 업데이트
            updateMetrics(allDocuments);
        })
        .catch(error => {
            console.error("문서 로드 중 오류:", error);
            documentGrid.innerHTML = `<div class="error-message">문서 로드 중 오류가 발생했습니다: ${error.message}</div>`;
        });
    }
    
    // 지표 업데이트 함수
    function updateMetrics(documents) {
        // 총 발주 수 업데이트
        const totalOrdersEl = document.getElementById('totalOrders');
        if (totalOrdersEl) {
            const orderCount = documents.filter(doc => doc.document_type === 'order').length;
            totalOrdersEl.textContent = orderCount;
        }
        
        // 계약 건수 업데이트
        const totalContractsEl = document.getElementById('totalContracts');
        if (totalContractsEl) {
            const contractCount = documents.filter(doc => doc.document_type === 'contract').length;
            totalContractsEl.textContent = contractCount;
        }
        
        // 불일치 수 업데이트 - 현재는 정확한 데이터가 없으므로 0으로 표시
        const totalMismatchesEl = document.getElementById('totalMismatches');
        if (totalMismatchesEl) {
            totalMismatchesEl.textContent = '0';
        }
        
        // 총 금액 업데이트
        const totalAmountEl = document.getElementById('totalAmount');
        if (totalAmountEl) {
            let totalAmount = 0;
            documents.forEach(doc => {
                if (doc.total_amount) {
                    // 'EUR 1500.00' 형식에서 숫자만 추출
                    const amountMatch = doc.total_amount.match(/[\d.]+/);
                    if (amountMatch) {
                        totalAmount += parseFloat(amountMatch[0]);
                    }
                }
            });
            totalAmountEl.textContent = `€${totalAmount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
    }
    
    // 문서 그리드 렌더링 함수
    function renderDocumentGrid(documents) {
        console.log('렌더링할 문서 데이터:', documents);
        
        if (!documentGrid) {
            console.error("문서 그리드 요소를 찾을 수 없습니다.");
            return;
        }
        
        if (!documents || documents.length === 0) {
            documentGrid.innerHTML = '<div class="empty-state">문서가 없습니다. 새 문서를 업로드해주세요.</div>';
            return;
        }
        
        let gridHtml = '';
        
        documents.forEach(doc => {
            // 문서 유형에 따른 아이콘 및 클래스
            let docTypeClass = 'invoice';
            let docTypeLabel = '인보이스';
            
            if (doc.document_type === 'order') {
                docTypeClass = 'po';
                docTypeLabel = '발주서';
            } else if (doc.document_type === 'contract') {
                docTypeClass = 'contract';
                docTypeLabel = '계약서';
            }
            
            // 일치율에 따른 클래스
            // 현재는 정확한 일치율 정보가 없으므로 기본값으로 설정
            const matchRate = 100;
            let matchClass = 'high';
            if (matchRate < 80) matchClass = 'medium';
            if (matchRate < 60) matchClass = 'low';
            
            // 상태에 따른 배지
            let statusBadge = '<span class="status-badge complete">완료</span>';
            
            // 금액 표시 형식 처리
            let amountDisplay = doc.total_amount || '정보 없음';
            
            // 문서 생성일 포맷팅
            const createdDate = doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '날짜 없음';
            
            // 문서 아이템 HTML
            gridHtml += `
                <div class="document-item" data-id="${doc.id}">
                    <div class="document-header">
                        <span class="doc-type ${docTypeClass}">${docTypeLabel}</span>
                        <span class="doc-date">${createdDate}</span>
                        <div class="doc-actions">
                            <button class="btn btn-icon btn-sm doc-menu-btn"><i class="fas fa-ellipsis-v"></i></button>
                        </div>
                    </div>
                    <div class="document-body">
                        <h3 class="doc-title">${doc.filename}</h3>
                        <div class="match-indicator ${matchClass}">
                            <span class="match-label">일치율</span>
                            <span class="match-value">${matchRate}%</span>
                        </div>
                        <div class="doc-info">
                            <div class="info-item">
                                <span class="info-label">브랜드:</span>
                                <span class="info-value">${doc.brand || '정보 없음'}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">금액:</span>
                                <span class="info-value">${amountDisplay}</span>
                            </div>
                        </div>
                    </div>
                    <div class="document-footer">
                        ${statusBadge}
                        <div class="footer-actions">
                            <button class="btn btn-icon btn-sm view-btn" data-id="${doc.id}"><i class="fas fa-eye"></i></button>
                            <button class="btn btn-icon btn-sm edit-btn" data-id="${doc.id}"><i class="fas fa-edit"></i></button>
                            <button class="btn btn-icon btn-sm download-btn" data-id="${doc.id}" data-filename="${doc.excel_filename}"><i class="fas fa-download"></i></button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        documentGrid.innerHTML = gridHtml;
        
        // 문서 아이템 이벤트 리스너 추가
        addDocumentItemEventListeners();
    }
    
    // 문서 아이템 이벤트 리스너 추가 함수
    function addDocumentItemEventListeners() {
        // 문서 보기 버튼
        const viewButtons = document.querySelectorAll('.view-btn');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation(); // 이벤트 버블링 방지
                const docId = this.getAttribute('data-id');
                viewDocument(docId);
            });
        });
        
        // 문서 편집 버튼
        const editButtons = document.querySelectorAll('.edit-btn');
        editButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation(); // 이벤트 버블링 방지
                const docId = this.getAttribute('data-id');
                editDocument(docId);
            });
        });
        
        // 문서 다운로드 버튼
        const downloadButtons = document.querySelectorAll('.download-btn');
        downloadButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation(); // 이벤트 버블링 방지
                const filename = this.getAttribute('data-filename');
                if (filename) {
                    window.open(`${API_BASE_URL}/download/${filename}`, '_blank');
                }
            });
        });
        
        // 문서 아이템 클릭 (문서 상세 보기)
        const documentItems = document.querySelectorAll('.document-item');
        documentItems.forEach(item => {
            item.addEventListener('click', function(e) {
                // 버튼 클릭은 제외
                if (e.target.closest('.btn')) return;
                
                const docId = this.getAttribute('data-id');
                viewDocument(docId);
            });
        });
    }
    
    // 필터 적용 함수
    function applyFilters() {
        const filters = {};
        
        // 검색어
        const searchInput = document.querySelector('.search-box input');
        if (searchInput && searchInput.value) {
            filters.search = searchInput.value;
        }
        
        // 문서 타입 
        const checkedTypes = [];
        if (document.getElementById('doc-po')?.checked) checkedTypes.push('order');
        if (document.getElementById('doc-invoice')?.checked) checkedTypes.push('invoice');
        if (document.getElementById('doc-contract')?.checked) checkedTypes.push('contract');
        
        if (checkedTypes.length === 1) {
            filters.docType = checkedTypes[0];
        }
        
        // 브랜드
        const brandSelect = document.querySelector('select[name="brand"]');
        if (brandSelect && brandSelect.value !== '모든 브랜드') {
            filters.brand = brandSelect.value;
        }
        
        // 날짜 범위
        const dateInputs = document.querySelectorAll('.date-inputs input');
        if (dateInputs.length >= 2) {
            if (dateInputs[0].value) {
                filters.dateFrom = dateInputs[0].value;
            }
            if (dateInputs[1].value) {
                filters.dateTo = dateInputs[1].value;
            }
        }
        
        loadDocuments(filters);
    }
    
    // 문서 상세 보기 함수 (API 사용)
    function viewDocument(docId) {
        // 이미 선택된 문서인 경우 무시
        if (selectedDocumentId === docId) return;
        
        console.log('문서 상세 정보 보기:', docId);
        selectedDocumentId = docId;
        
        // 문서 상세 영역 표시
        if (documentDetail) {
            documentDetail.style.display = 'block';
        } else {
            console.warn('문서 상세 영역 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 선택된 문서 강조
        const documentItems = document.querySelectorAll('.document-item');
        documentItems.forEach(item => {
            item.classList.remove('selected');
            if (item.getAttribute('data-id') === docId) {
                item.classList.add('selected');
                // 필요한 경우 화면이 보이게 스크롤
                item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
        
        // API에서 문서 정보 가져오기
        fetch(`${API_BASE_URL}/document/${docId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('문서 정보를 가져오는데 실패했습니다');
                }
                return response.json();
            })
            .then(data => {
                // 문서 정보 업데이트
                updateDocumentDetailView(data);
                
                // 비교 버튼 설정
                setupCompareButton(data);
            })
            .catch(error => {
                console.error('문서 정보 가져오기 오류:', error);
                alert('문서 정보를 가져오는데 실패했습니다: ' + error.message);
            });
    }
    
    // 비교 버튼 설정 함수
    function setupCompareButton(currentDoc) {
        const compareButton = document.getElementById('compareButton');
        if (!compareButton) return;
        
        compareButton.onclick = function() {
            // 현재 선택된 문서와 다른 문서 타입 선택
            let targetDocType = currentDoc.document_type === 'invoice' ? 'order' : 'invoice';
            let targetEndpoint = targetDocType === 'invoice' ? 'documents/invoice' : 'documents/order';
            
            // 비교할 문서 목록 가져오기
            fetch(`${API_BASE_URL}/${targetEndpoint}`)
                .then(response => response.json())
                .then(data => {
                    // 문서 목록 가져오기
                    const documents = targetDocType === 'invoice' ? data.invoices : data.orders;
                    
                    // 비교할 문서 선택 옵션 생성
                    if (compareDocSelect) {
                        compareDocSelect.innerHTML = '<option value="">선택하세요</option>';
                        
                        documents.forEach(doc => {
                            const docTypeLabel = targetDocType === 'invoice' ? '인보이스' : '발주서';
                            compareDocSelect.innerHTML += `<option value="${doc.id}">${doc.filename} (${docTypeLabel})</option>`;
                        });
                    }
                    
                    // 모달 표시
                    if (compareModal) {
                        compareModal.style.display = 'block';
                        
                        // 비교 시작 버튼 이벤트
                        if (startCompareBtn) {
                            startCompareBtn.onclick = function() {
                                const selectedDocId = compareDocSelect.value;
                                if (!selectedDocId) {
                                    alert('비교할 문서를 선택해주세요.');
                                    return;
                                }
                                
                                // API 호출하여 문서 비교
                                compareDocumentsAPI(currentDoc.id, selectedDocId);
                            };
                        }
                        
                        // 취소 버튼 이벤트
                        if (cancelCompareBtn) {
                            cancelCompareBtn.onclick = function() {
                                compareModal.style.display = 'none';
                                if (compareResult) {
                                    compareResult.style.display = 'none';
                                }
                            };
                        }
                        
                        // 모달 닫기 버튼 이벤트
                        const closeBtn = compareModal.querySelector('.modal-close');
                        if (closeBtn) {
                            closeBtn.onclick = function() {
                                compareModal.style.display = 'none';
                                if (compareResult) {
                                    compareResult.style.display = 'none';
                                }
                            };
                        }
                        
                        // 모달 오버레이 클릭 시 닫기
                        const overlay = compareModal.querySelector('.modal-overlay');
                        if (overlay) {
                            overlay.onclick = function() {
                                compareModal.style.display = 'none';
                                if (compareResult) {
                                    compareResult.style.display = 'none';
                                }
                            };
                        }
                    }
                })
                .catch(error => {
                    console.error('비교할 문서 목록 가져오기 오류:', error);
                    alert('비교할 문서 목록을 가져오지 못했습니다: ' + error.message);
                });
        };
    }
    
    // 문서 상세 정보 화면 업데이트
    function updateDocumentDetailView(doc) {
        // 문서 미리보기 업데이트
        if (documentPreview) {
            documentPreview.src = 'https://placehold.co/300x400/gray/white?text=PDF+Preview';
        }
        
        // 문서 정보 업데이트
        updateDocumentInfo(doc);
        
        // 문서 품목 테이블 업데이트
        updateDocumentItems(doc.items || []);
        
        // 버튼 업데이트
        if (downloadButton) {
            downloadButton.onclick = function() {
                window.open(`${API_BASE_URL}/download/${doc.excel_filename}`, '_blank');
            };
        }
        
        if (editButton) {
            editButton.onclick = function() {
                editDocument(doc.id);
            };
        }
    }
    
    // 문서 정보 업데이트 함수
    function updateDocumentInfo(doc) {
        if (!documentInfoItems || documentInfoItems.length === 0) {
            console.warn('문서 정보 항목 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 정보 항목 매핑
        const infoMapping = {
            'document_id': '문서 ID',
            'id': '문서 ID',
            'document_type': '문서 타입',
            'created_at': '생성일',
            'brand': '브랜드',
            'season': '시즌',
            'total_amount': '총 금액',
            'total_quantity': '총 수량'
        };
        
        // 정보 표시 형식 변환
        const formatValue = (key, value) => {
            if (key === 'document_type') {
                return value === 'invoice' ? '인보이스' : '발주서';
            } else if (key === 'created_at') {
                return new Date(value).toLocaleString();
            }
            return value;
        };
        
        // 정보 항목 업데이트
        documentInfoItems.forEach(item => {
            const labelElement = item.querySelector('.detail-label');
            const valueElement = item.querySelector('.detail-value');
            
            if (labelElement && valueElement) {
                const label = labelElement.textContent.replace(':', '');
                
                // 매핑된 키 찾기
                for (const [key, mappedLabel] of Object.entries(infoMapping)) {
                    if (mappedLabel === label && doc[key] !== undefined) {
                        valueElement.textContent = formatValue(key, doc[key]);
                        break;
                    }
                }
            }
        });
    }
    
    function updateDocumentItems(items) {
        if (!documentDetailTable) {
            console.warn('문서 품목 테이블 요소를 찾을 수 없습니다.');
            return;
        }
        
        if (!items || items.length === 0) {
            documentDetailTable.innerHTML = '<tr><td colspan="4">품목 정보가 없습니다.</td></tr>';
            return;
        }
        
        let tableHtml = '';
        
        // 항목 필드 매핑 (표시할 필드 결정)
        items.forEach(item => {
            const name = item.model_name || item.model_code || '-';
            const qty = item.quantity || '0';
            const price = item.wholesale_price || '0';
            const total = item.total_price || '-';
            
            tableHtml += `
                <tr>
                    <td>${name}</td>
                    <td>${qty}</td>
                    <td>${price}</td>
                    <td>${total}</td>
                </tr>
            `;
        });
        
        documentDetailTable.innerHTML = tableHtml;
        
        // 테이블 푸터 업데이트 (있다면)
        const totalAmountCell = document.getElementById('itemTotalAmount');
        if (totalAmountCell) {
            // 총액 계산 또는 표시
            let total = 0;
            items.forEach(item => {
                // 총액이 있으면 사용, 없으면 수량 * 가격 계산
                if (item.total_price) {
                    const match = item.total_price.match(/[\d.]+/);
                    if (match) {
                        total += parseFloat(match[0]);
                    }
                } else if (item.quantity && item.wholesale_price) {
                    const qty = parseInt(item.quantity);
                    const match = item.wholesale_price.match(/[\d.]+/);
                    if (match) {
                        const price = parseFloat(match[0]);
                        if (!isNaN(qty) && !isNaN(price)) {
                            total += qty * price;
                        }
                    }
                }
            });
            
            totalAmountCell.textContent = `€${total.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
    }
    
     // API를 사용한 문서 비교 함수
     function compareDocumentsAPI(doc1Id, doc2Id) {
        // 로딩 표시
        if (compareResult) {
            compareResult.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 문서 비교 중...</div>';
            compareResult.style.display = 'block';
        }
        
        // API 호출
        fetch(`${API_BASE_URL}/compare/${doc1Id}/${doc2Id}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('문서 비교에 실패했습니다');
                }
                return response.json();
            })
            .then(result => {
                // 비교 결과 표시
                showComparisonResult(result, doc1Id, doc2Id);
                // 캘린더 추가 로직은 제거하고 버튼 클릭 시 실행하도록 변경
            })
            .catch(error => {
                console.error('문서 비교 중 오류:', error);
                if (compareResult) {
                    compareResult.innerHTML = `<div class="error-message">문서 비교 중 오류가 발생했습니다: ${error.message}</div>`;
                }
            });
    }

// 캘린더에 추가할 이벤트 생성 함수
function createCalendarEvents(comparisonResult, doc1Id, doc2Id) {
    const events = [];
    
    // 두 문서 중 발주서(order) 식별
    const orderDocId = comparisonResult.document_types.doc1 === 'order' ? doc1Id : doc2Id;
    console.log("발주서 ID:", orderDocId);
    
    // 날짜 파싱 함수 추가
    function parseDate(dateStr) {
        if (!dateStr || dateStr.trim() === '') return null;
        
        // 날짜 형식: "13 May 25"와 같은 형식을 처리
        const months = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        };
        
        const parts = dateStr.trim().split(' ');
        if (parts.length === 3) {
            const day = parts[0].padStart(2, '0');
            const month = months[parts[1]];
            const year = '20' + parts[2]; // "25" -> "2025"
            
            if (day && month && year) {
                return `${year}-${month}-${day}`;
            }
        }
        
        // 기본 날짜 반환
        return new Date().toISOString().split('T')[0];
    }
    
    // 발주서 상세 정보 가져오기
    return fetch(`${API_BASE_URL}/document/${orderDocId}`)
        .then(response => response.json())
        .then(orderData => {
            console.log("발주서 상세 정보:", orderData);
            
            // 일치 항목에 대해 이벤트 생성
            comparisonResult.matches.forEach(match => {
                // 일치 항목의 모델 코드/이름 가져오기
                const productKey = match.product_key;
                const productName = match.product_name;
                
                console.log("매칭 시도:", {
                    productKey: productKey,
                    productName: productName
                });
                
                // 발주서에서 해당 모델의 항목 찾기
                const orderItem = orderData.items.find(item => 
                    (item.model_code && item.model_code.toLowerCase() === productKey.toLowerCase()) || 
                    (item.model_name && item.model_name.includes(productName))
                );
                
                console.log("매칭된 발주서 항목:", orderItem);
                
                // 해당 항목에 선적 일정이 있는 경우
                if (orderItem) {
                    // 시작 일정이 있는 경우
                    if (orderItem.shipping_start) {
                        console.log("선적 시작일:", orderItem.shipping_start);
                        const parsedStartDate = parseDate(orderItem.shipping_start);
                        console.log("파싱된 시작일:", parsedStartDate);
                        
                        events.push({
                            title: `${orderData.brand} - ${productName} (시작)`,
                            date: parsedStartDate,
                            category: 'shipping',
                            description: `품목: ${productName}\n수량: ${match.quantity}\n가격: ${match.price}`,
                            schedule_type: 'start',
                            model_code: orderItem.model_code,
                            model_name: orderItem.model_name,
                            document_id: orderDocId,
                            document_type: 'order',
                            brand: orderData.brand
                        });
                    } else {
                        // 시작 일정이 없는 경우 현재 날짜 사용
                        events.push({
                            title: `${orderData.brand} - ${productName} (시작)`,
                            date: new Date().toISOString().split('T')[0],
                            category: 'shipping',
                            description: `품목: ${productName}\n수량: ${match.quantity}\n가격: ${match.price}`,
                            schedule_type: 'start',
                            model_code: orderItem.model_code,
                            model_name: orderItem.model_name,
                            document_id: orderDocId,
                            document_type: 'order',
                            brand: orderData.brand
                        });
                    }
                    
                    // 종료 일정이 있는 경우
                    if (orderItem.shipping_end) {
                        console.log("선적 종료일:", orderItem.shipping_end);
                        const parsedEndDate = parseDate(orderItem.shipping_end);
                        console.log("파싱된 종료일:", parsedEndDate);
                        
                        events.push({
                            title: `${orderData.brand} - ${productName} (완료)`,
                            date: parsedEndDate,
                            category: 'shipping',
                            description: `품목: ${productName}\n수량: ${match.quantity}\n가격: ${match.price}`,
                            schedule_type: 'end',
                            model_code: orderItem.model_code,
                            model_name: orderItem.model_name,
                            document_id: orderDocId,
                            document_type: 'order',
                            brand: orderData.brand
                        });
                    } else {
                        // 종료 일정이 없는 경우 현재 날짜 +30일 사용
                        const endDate = new Date();
                        endDate.setDate(endDate.getDate() + 30);
                        events.push({
                            title: `${orderData.brand} - ${productName} (완료)`,
                            date: endDate.toISOString().split('T')[0],
                            category: 'shipping',
                            description: `품목: ${productName}\n수량: ${match.quantity}\n가격: ${match.price}`,
                            schedule_type: 'end',
                            model_code: orderItem.model_code,
                            model_name: orderItem.model_name,
                            document_id: orderDocId,
                            document_type: 'order',
                            brand: orderData.brand
                        });
                    }
                } else {
                    // 해당 항목이 발주서에서 찾아지지 않는 경우, 기본 이벤트 생성
                    console.log("매칭된 발주서 항목을 찾을 수 없음:", productName);
                    
                    // 시작 일정 이벤트
                    const eventDate = new Date().toISOString().split('T')[0];
                    events.push({
                        title: `${comparisonResult.document_types.doc1} vs ${comparisonResult.document_types.doc2} - ${productName} (시작)`,
                        date: eventDate,
                        category: 'shipping',
                        description: `품목: ${productName}\n수량: ${match.quantity}\n가격: ${match.price}`,
                        schedule_type: 'start',
                        document_id: orderDocId,
                        document_type: 'comparison',
                        brand: orderData.brand || ''
                    });
                    
                    // 종료 일정 이벤트
                    const endDate = new Date();
                    endDate.setDate(endDate.getDate() + 30);
                    events.push({
                        title: `${comparisonResult.document_types.doc1} vs ${comparisonResult.document_types.doc2} - ${productName} (완료)`,
                        date: endDate.toISOString().split('T')[0],
                        category: 'shipping',
                        description: `품목: ${productName}\n수량: ${match.quantity}\n가격: ${match.price}`,
                        schedule_type: 'end',
                        document_id: orderDocId,
                        document_type: 'comparison',
                        brand: orderData.brand || ''
                    });
                }
            });
            
            console.log("생성된 이벤트:", events);
            return events;
        });
}

// 캘린더에 일정 추가 API 호출 함수 수정
function addEventsToCalendar(events, doc1Id, doc2Id) {
    // 추가 정보: 수동 비교 플래그 및 문서 ID 포함
    const requestData = {
        events: events,
        manually_compared: true,
        document1_id: doc1Id,
        document2_id: doc2Id
    };
    
    fetch(`${API_BASE_URL}/calendar/events`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('캘린더에 일정 추가 실패');
        }
        return response.json();
    })
    .then(result => {
        alert('캘린더에 일정이 추가되었습니다.');
    })
    .catch(error => {
        console.error('캘린더에 일정 추가 중 오류:', error);
        alert('캘린더에 일정 추가 중 오류가 발생했습니다.');
    });
}
    
    // 문서 편집 함수
    function editDocument(docId) {
        // 현재는 기능 미구현 - 추후 구현 예정
        alert('문서 편집 기능은 현재 개발 중입니다.');
    }
    
    // 문서 비교 결과 표시 함수 수정
    function showComparisonResult(result, doc1Id, doc2Id) {
        if (!compareResult) {
            console.warn('비교 결과 컨테이너를 찾을 수 없습니다.');
            return;
        }

        // 일치율에 따른 클래스
        let matchClass = 'high';
        if (result.summary.match_percentage < 80) matchClass = 'medium';
        if (result.summary.match_percentage < 60) matchClass = 'low';

        // 결과 HTML 생성
        let resultHtml = `
        <div class="comparison-result">
        <div class="result-header">
        <h3>비교 결과</h3>
        <div class="match-badge ${matchClass}">일치율: ${result.summary.match_percentage}%</div>
        </div>
        <div class="result-summary">
        <p>총 ${result.summary.total_items}개 항목 중 ${result.summary.matched_items}개 일치, ${result.summary.mismatched_items}개 불일치</p>
        </div>
        `;

        // 불일치 항목 표시
        if (result.mismatches.length > 0) {
            resultHtml += '<div class="mismatched-items"><h4>불일치 항목</h4>';

            result.mismatches.forEach(item => {
                if (item.doc1_exists && item.doc2_exists) {
                    // 양쪽 다 존재하는 경우 필드 불일치 표시
                    resultHtml += `
                    <div class="mismatch-item">
                        <div class="mismatch-header">
                            <span class="product-name">${item.product_name}</span>
                        </div>
                    `;

                    // 불일치 필드 표시
                    item.mismatched_fields.forEach(field => {
                        resultHtml += `
                        <div class="field-mismatch">
                            <span class="field-name">${field.field}:</span>
                            <div class="value-comparison">
                                <div>
                                    <span class="value-label">문서 1:</span>
                                    <span class="value">${field.value1}</span>
                                </div>
                                <div>
                                    <span class="value-label">문서 2:</span>
                                    <span class="value">${field.value2}</span>
                                </div>
                            </div>
                        </div>
                        `;
                    });

                    resultHtml += '</div>';
                } else {
                    // 한쪽에만 존재하는 경우
                    resultHtml += `
                    <div class="mismatch-item">
                        <div class="mismatch-header">
                            <span class="product-name">${item.product_name}</span>
                        </div>
                        <div class="reason">
                            ${item.doc1_exists ? '문서 2에 없음' : '문서 1에 없음'}
                        </div>
                    </div>
                    `;
                }
            });

            resultHtml += '</div>';
        }

        // 일치 항목 표시
        if (result.matches.length > 0) {
            resultHtml += '<div class="matched-items"><h4>일치 항목</h4>';
            resultHtml += '<div class="matches-summary">다음 항목들은 두 문서에서 일치합니다:</div>';
            resultHtml += '<div class="matches-grid">';

            result.matches.forEach(item => {
                resultHtml += `
                <div class="match-item">
                    <div class="match-name">${item.product_name}</div>
                    <div class="match-details">
                        <span class="match-quantity">${item.quantity}개</span>
                        <span class="match-price">${item.price}</span>
                    </div>
                    <div class="match-sizes">${item.size}</div>
                </div>
                `;
            });

            resultHtml += '</div></div>';
        }

        // 캘린더 추가 버튼 추가 - 기존 로직 유지하되 버튼 텍스트 변경
        resultHtml += '<div class="comparison-actions">';
        resultHtml += '<button class="btn btn-primary" id="addToCalendarBtn">캘린더에 일정 추가</button>';
        resultHtml += '</div>';

        resultHtml += '</div>';

        // 결과 표시
        compareResult.innerHTML = resultHtml;
        compareResult.style.display = 'block';

            // 캘린더 추가 버튼 클릭 이벤트 핸들러 연결
    const addToCalendarBtn = document.getElementById('addToCalendarBtn');
    if (addToCalendarBtn) {
        addToCalendarBtn.addEventListener('click', () => {
            // 비교 결과에서 일정 생성 (비동기 처리)
            createCalendarEvents(result, doc1Id, doc2Id)
                .then(eventsToAdd => {
                    // 캘린더에 일정 추가 API 호출
                    addEventsToCalendar(eventsToAdd, doc1Id, doc2Id);
                });
        });
    }
    }
});