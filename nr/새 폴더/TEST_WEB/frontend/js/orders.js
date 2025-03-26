// orders.js - 발주 및 계약 관리 페이지 스크립트

// API 기본 URL 설정 (개발 환경)
const API_BASE_URL = 'http://localhost:5000/orders';

document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 선택
    const documentGrid = document.querySelector('.document-grid');
    const searchInput = document.querySelector('.search-box input');
    const docTypeFilter = document.querySelector('select[name="docType"]');
    const brandFilter = document.querySelector('select[name="brand"]');
    const dateFromInput = document.querySelector('.date-inputs input:first-child');
    const dateToInput = document.querySelector('.date-inputs input:last-child');
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
    
    // 샘플 데이터가 없을 경우 자동 생성
    if (!sessionStorage.getItem('ocr_documents')) {
        console.log("샘플 데이터 자동 생성");
        generateSampleData();
    }
    
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
                const docType = btn.textContent.trim().toLowerCase();
                if (docType === '모든 문서') {
                    loadDocuments();
                } else if (docType === '발주서') {
                    loadDocuments({ docType: 'purchase_order' });
                } else if (docType === '인보이스') {
                    loadDocuments({ docType: 'invoice' });
                } else if (docType === '계약서') {
                    loadDocuments({ docType: 'contract' });
                }
            });
        });
    }

    // 문서 목록 로드 함수 (세션 스토리지만 사용하도록 수정)
    function loadDocuments(filters = {}) {
        console.log("문서 로딩 시작 - 세션 스토리지만 사용");
        
        if (!documentGrid) {
            console.error("문서 그리드 요소를 찾을 수 없습니다.");
            return;
        }
        
        // 로딩 표시
        documentGrid.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 문서 로드 중...</div>';
        
        // 세션 스토리지에서 데이터 가져오기
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        console.log("세션 스토리지에서 문서 데이터 로드:", documents.length, "개", documents);
        
        // 필터 적용
        let filteredDocs = documents;
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
                doc.date && new Date(doc.date) >= fromDate
            );
        }
        
        if (filters.dateTo) {
            const toDate = new Date(filters.dateTo);
            toDate.setHours(23, 59, 59, 999); // 날짜 범위의 끝
            filteredDocs = filteredDocs.filter(doc => 
                doc.date && new Date(doc.date) <= toDate
            );
        }
        
        // 문서 표시
        if (filteredDocs.length > 0) {
            renderDocumentGrid(filteredDocs);
        } else {
            documentGrid.innerHTML = '<div class="empty-state">문서가 없습니다. 새 문서를 업로드해주세요.</div>';
        }
        
        // 지표 업데이트
        updateMetrics(documents);
    }
    
    // 지표 업데이트 함수
    function updateMetrics(documents) {
        // 총 발주 수 업데이트
        const totalOrdersEl = document.getElementById('totalOrders');
        if (totalOrdersEl) {
            const orderCount = documents.filter(doc => doc.document_type === 'purchase_order').length;
            totalOrdersEl.textContent = orderCount;
        }
        
        // 계약 건수 업데이트
        const totalContractsEl = document.getElementById('totalContracts');
        if (totalContractsEl) {
            const contractCount = documents.filter(doc => doc.document_type === 'contract').length;
            totalContractsEl.textContent = contractCount;
        }
        
        // 불일치 수 업데이트
        const totalMismatchesEl = document.getElementById('totalMismatches');
        if (totalMismatchesEl) {
            const mismatchCount = documents.filter(doc => doc.match_rate && doc.match_rate < 90).length;
            totalMismatchesEl.textContent = mismatchCount;
        }
        
        // 총 금액 업데이트
        const totalAmountEl = document.getElementById('totalAmount');
        if (totalAmountEl) {
            let totalAmount = 0;
            documents.forEach(doc => {
                if (doc.amount && !isNaN(parseFloat(doc.amount))) {
                    totalAmount += parseFloat(doc.amount);
                }
            });
            totalAmountEl.textContent = `₩${totalAmount.toLocaleString()}`;
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
            // undefined 필드 확인 및 기본값 설정
            const safeDoc = {
                id: doc.id || generateUniqueId(),
                filename: doc.filename || '파일명 없음',
                date: doc.date || '날짜 없음',
                document_type: doc.document_type || 'unknown',
                status: doc.status || 'complete',
                match_rate: doc.match_rate || 100,
                brand: doc.brand || '정보 없음',
                amount: doc.amount || '정보 없음'
            };
            
            // 문서 유형에 따른 아이콘 및 클래스
            let docTypeClass = 'invoice';
            let docTypeLabel = '인보이스';
            
            if (safeDoc.document_type === 'purchase_order') {
                docTypeClass = 'po';
                docTypeLabel = '발주서';
            } else if (safeDoc.document_type === 'contract') {
                docTypeClass = 'contract';
                docTypeLabel = '계약서';
            }
            
            // 일치율에 따른 클래스
            let matchClass = 'high';
            if (safeDoc.match_rate < 80) matchClass = 'medium';
            if (safeDoc.match_rate < 60) matchClass = 'low';
            
            // 상태에 따른 배지
            let statusBadge = '<span class="status-badge complete">완료</span>';
            if (safeDoc.status === 'review') {
                statusBadge = '<span class="status-badge review">검토 필요</span>';
            } else if (safeDoc.status === 'processing') {
                statusBadge = '<span class="status-badge processing">처리 중</span>';
            }
            
            // 금액 표시 형식 처리
            let amountDisplay = safeDoc.amount;
            if (amountDisplay !== '정보 없음') {
                // 숫자로 변환 가능한지 확인
                const numAmount = Number(amountDisplay);
                if (!isNaN(numAmount)) {
                    amountDisplay = `₩${numAmount.toLocaleString()}`;
                }
            }
            
            // 문서 아이템 HTML
            gridHtml += `
                <div class="document-item" data-id="${safeDoc.id}">
                    <div class="document-header">
                        <span class="doc-type ${docTypeClass}">${docTypeLabel}</span>
                        <span class="doc-date">${safeDoc.date}</span>
                        <div class="doc-actions">
                            <button class="btn btn-icon btn-sm doc-menu-btn"><i class="fas fa-ellipsis-v"></i></button>
                        </div>
                    </div>
                    <div class="document-body">
                        <h3 class="doc-title">${safeDoc.filename}</h3>
                        <div class="match-indicator ${matchClass}">
                            <span class="match-label">일치율</span>
                            <span class="match-value">${safeDoc.match_rate}%</span>
                        </div>
                        <div class="doc-info">
                            <div class="info-item">
                                <span class="info-label">브랜드:</span>
                                <span class="info-value">${safeDoc.brand}</span>
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
                            <button class="btn btn-icon btn-sm view-btn" data-id="${safeDoc.id}"><i class="fas fa-eye"></i></button>
                            <button class="btn btn-icon btn-sm edit-btn" data-id="${safeDoc.id}"><i class="fas fa-edit"></i></button>
                            <button class="btn btn-icon btn-sm download-btn" data-id="${safeDoc.id}"><i class="fas fa-download"></i></button>
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
                const docId = this.getAttribute('data-id');
                downloadDocument(docId);
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
        
        if (searchInput && searchInput.value) {
            filters.search = searchInput.value;
        }
        
        if (docTypeFilter && docTypeFilter.value && docTypeFilter.value !== '모든 문서') {
            filters.docType = docTypeFilter.value;
        }
        
        if (brandFilter && brandFilter.value && brandFilter.value !== '모든 브랜드') {
            filters.brand = brandFilter.value;
        }
        
        if (dateFromInput && dateFromInput.value) {
            filters.dateFrom = dateFromInput.value;
        }
        
        if (dateToInput && dateToInput.value) {
            filters.dateTo = dateToInput.value;
        }
        
        loadDocuments(filters);
    }
    
    // 문서 상세 보기 함수 (세션 스토리지만 사용하도록 수정)
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
        
        // 세션 스토리지에서 문서 정보 확인
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        const doc = documents.find(d => d.id === docId);
        
        if (doc) {
            // 세션 스토리지에 데이터가 있으면 사용
            console.log('세션 스토리지에서 문서 정보 사용:', doc);
            updateDocumentDetailView(doc);
            
            // 비교 버튼 설정
            setupCompareButton(doc);
        } else {
            console.error('문서 ID를 찾을 수 없음:', docId);
            alert('문서 정보를 찾을 수 없습니다.');
        }
    }
    
    // 비교 버튼 설정 함수
    function setupCompareButton(currentDoc) {
        const compareButton = document.getElementById('compareButton');
        if (!compareButton) return;
        
        compareButton.onclick = function() {
            // 비교 가능한 다른 문서 목록 가져오기
            const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
            const otherDocs = documents.filter(d => d.id !== currentDoc.id);
            
            // 비교할 문서 선택 옵션 생성
            if (compareDocSelect) {
                compareDocSelect.innerHTML = '<option value="">선택하세요</option>';
                
                otherDocs.forEach(doc => {
                    const docTypeLabel = getDocumentTypeLabel(doc.document_type);
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
                        
                        // 클라이언트 측 문서 비교 실행
                        compareDocumentsInSession(currentDoc.id, selectedDocId);
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
        };
    }
    
    // 문서 유형 라벨 가져오기
    function getDocumentTypeLabel(docType) {
        const docTypeLabels = {
            'invoice': '인보이스',
            'purchase_order': '발주서',
            'contract': '계약서',
            'unknown': '알 수 없음'
        };
        
        return docTypeLabels[docType] || docType;
    }
    
    // 문서 상세 정보 화면 업데이트
    function updateDocumentDetailView(doc) {
        // 문서 미리보기 업데이트
        if (documentPreview) {
            documentPreview.src = doc.preview_url || 'https://placehold.co/300x400/gray/white?text=PDF+Preview';
        }
        
        // 문서 정보 업데이트
        updateDocumentInfo(doc);
        
        // 문서 품목 테이블 업데이트
        updateDocumentItems(doc.items || doc.preview_data || []);
        
        // 버튼 업데이트
        if (downloadButton) {
            downloadButton.onclick = function() {
                downloadDocument(doc.id);
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
            'date': '생성일',
            'created_date': '생성일',
            'brand': '브랜드',
            'season': '시즌',
            'total_amount': '총 금액',
            'amount': '총 금액',
            'total_quantity': '총 수량',
            'total_products': '총 수량'
        };
        
        // 정보 표시 형식 변환
        const formatValue = (key, value) => {
            if (key === 'document_type') {
                return getDocumentTypeLabel(value);
            } else if (key === 'total_amount' || key === 'amount') {
                const numVal = Number(value);
                return isNaN(numVal) ? value : `₩${numVal.toLocaleString()}`;
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
    
    // 문서 품목 테이블 업데이트 함수
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
        
        // 첫 번째 항목의 키를 기준으로 열 제목 결정
        const firstItem = items[0];
        const keys = Object.keys(firstItem);
        
        // 항목 필드 매핑 (표시할 필드 결정)
        let nameField = keys.find(k => k.toLowerCase().includes('product') || k.toLowerCase().includes('name')) || 'Product_Code';
        let qtyField = keys.find(k => k.toLowerCase().includes('quantity') || k.toLowerCase().includes('qty')) || 'Quantity';
        let priceField = keys.find(k => k.toLowerCase().includes('price') || k.toLowerCase().includes('wholesale')) || 'Wholesale_Price';
        let totalField = keys.find(k => k.toLowerCase().includes('total') && k.toLowerCase().includes('price')) || '';
        
        items.forEach(item => {
            const name = item[nameField] || '-';
            const qty = item[qtyField] || '0';
            const price = item[priceField] || '0';
            
            // 총액 계산 또는 표시
            let total = '-';
            if (totalField && item[totalField]) {
                total = item[totalField];
            } else {
                // 총액 계산 시도
                const numQty = Number(qty);
                const numPrice = Number(price);
                if (!isNaN(numQty) && !isNaN(numPrice)) {
                    total = (numQty * numPrice).toFixed(2);
                }
            }
            
            // 가격 형식화
            const formattedPrice = isNaN(Number(price)) ? price : `₩${Number(price).toLocaleString()}`;
            const formattedTotal = isNaN(Number(total)) ? total : `₩${Number(total).toLocaleString()}`;
            
            tableHtml += `
                <tr>
                    <td>${name}</td>
                    <td>${qty}</td>
                    <td>${formattedPrice}</td>
                    <td>${formattedTotal}</td>
                </tr>
            `;
        });
        
        documentDetailTable.innerHTML = tableHtml;
        
        // 테이블 푸터 업데이트 (있다면)
        const totalAmountCell = document.getElementById('itemTotalAmount');
        if (totalAmountCell) {
            // 총액 계산
            let total = 0;
            items.forEach(item => {
                const qty = Number(item[qtyField] || 0);
                const price = Number(item[priceField] || 0);
                if (!isNaN(qty) && !isNaN(price)) {
                    total += qty * price;
                }
            });
            
            totalAmountCell.textContent = `₩${total.toLocaleString()}`;
        }
    }
    
    // 문서 다운로드 함수
    function downloadDocument(docId) {
        console.log('문서 다운로드:', docId);
        
        // 세션 스토리지에서 엑셀 파일명 확인
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        const doc = documents.find(d => d.id === docId);
        
        if (doc && doc.excel_filename) {
            // 엑셀 파일이 있으면 다운로드
            window.open(`${API_BASE_URL}/download/${doc.excel_filename}`, '_blank');
        } else {
            // API 호출
            window.open(`${API_BASE_URL}/download/${docId}`, '_blank');
        }
    }
    
    // 문서 편집 함수
    function editDocument(docId) {
        // 현재는 기능 미구현 - 추후 구현 예정
        alert('문서 편집 기능은 현재 개발 중입니다.');
    }
    
    // 세션 스토리지 기반 문서 비교 함수
    function compareDocumentsInSession(doc1Id, doc2Id) {
        console.log('문서 비교 시작:', doc1Id, doc2Id);
        
        // 세션 스토리지에서 문서 정보 확인
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        const doc1 = documents.find(d => d.id === doc1Id);
        const doc2 = documents.find(d => d.id === doc2Id);
        
        if (!doc1 || !doc2) {
            alert('비교할 문서를 찾을 수 없습니다.');
            return;
        }
        
        // 비교 결과 초기화
        const result = {
            document_types: {
                doc1: doc1.document_type,
                doc2: doc2.document_type
            },
            matches: [],
            mismatches: [],
            summary: {
                total_items: 0,
                matched_items: 0,
                mismatched_items: 0,
                match_percentage: 0
            }
        };
        
        // 문서 유형이 다른 경우 경고
        if (doc1.document_type !== doc2.document_type) {
            console.warn('문서 유형이 다릅니다:', doc1.document_type, doc2.document_type);
        }
        
        // 상품 정보 가져오기
        const products1 = doc1.items || doc1.preview_data || [];
        const products2 = doc2.items || doc2.preview_data || [];
        
        // 공통 키 필드 (상품코드) 찾기
        let keyField = findCommonKeyField(products1, products2);
        
        // 상품별 맵 생성
        const products1Map = createProductMap(products1, keyField);
        const products2Map = createProductMap(products2, keyField);
        
        // 모든 제품 키 합집합
        const allProductKeys = new Set([...Object.keys(products1Map), ...Object.keys(products2Map)]);
        result.summary.total_items = allProductKeys.size;
        
        // 상품별 비교
        allProductKeys.forEach(key => {
            const product1 = products1Map[key];
            const product2 = products2Map[key];
            
            if (!product1 || !product2) {
                // 한쪽에만 존재하는 항목
                result.mismatches.push({
                    product_key: key,
                    doc1_exists: !!product1,
                    doc2_exists: !!product2,
                    reason: '한쪽 문서에만 존재'
                });
                result.summary.mismatched_items++;
                return;
            }
            
            // 상품 필드 비교
            const fieldComparison = compareProductFields(product1, product2);
            
            if (fieldComparison.mismatched_fields.length > 0) {
                result.mismatches.push({
                    product_key: key,
                    product_name: product1[keyField] || key,
                    doc1_exists: true,
                    doc2_exists: true,
                    mismatched_fields: fieldComparison.mismatched_fields
                });
                result.summary.mismatched_items++;
            } else {
                result.matches.push({
                    product_key: key,
                    product_name: product1[keyField] || key,
                    size: product1.Size || product1.size || '',
                    quantity: product1.Quantity || product1.quantity || '',
                    price: product1.Wholesale_Price || product1.wholesale_price || product1.unit_price || ''
                });
                result.summary.matched_items++;
            }
        });
        
        // 일치율 계산
        if (result.summary.total_items > 0) {
            result.summary.match_percentage = Math.round(
                (result.summary.matched_items / result.summary.total_items) * 100
            );
        }
        
        // 문서 1의 일치율 업데이트
        updateDocumentMatchRate(doc1Id, result.summary.match_percentage);
        
        // 비교 결과 표시
        showComparisonResult(result);
        
        return result;
    }
    
    // 공통 키 필드 찾기 함수
    function findCommonKeyField(products1, products2) {
        if (!products1.length || !products2.length) return 'Product_Code';
        
        // 가능한 키 필드 후보
        const keyFieldCandidates = [
            'Product_Code', 'product_code', 'item_code', 'Style', 'style', 'custom_code'
        ];
        
        // 두 상품 목록 모두에 존재하는 필드 찾기
        for (const field of keyFieldCandidates) {
            if (products1[0].hasOwnProperty(field) && products2[0].hasOwnProperty(field)) {
                return field;
            }
        }
        
        // 기본값 반환
        return Object.keys(products1[0])[0];
    }
    
    // 상품 맵 생성 함수
    function createProductMap(products, keyField) {
        const productMap = {};
        
        products.forEach(product => {
            // 키 생성
            let key = product[keyField];
            
            // 키가 없는 경우 안전한 대체키 생성
            if (!key) {
                // 키 후보들 중 존재하는 것 사용
                const keyCandidates = ['Product_Code', 'product_code', 'Style', 'style', 'Size', 'size'];
                for (const candidateField of keyCandidates) {
                    if (product[candidateField]) {
                        key = product[candidateField];
                        break;
                    }
                }
                
                // 그래도 없으면 인덱스로 대체
                if (!key) {
                    key = `item_${products.indexOf(product)}`;
                }
            }
            
            // 사이즈가 있으면 키에 추가 (동일 제품, 다른 사이즈 구분)
            const size = product.Size || product.size;
            if (size) {
                key = `${key}_${size}`;
            }
            
            productMap[key] = product;
        });
        
        return productMap;
    }
    
    // 상품 필드 비교 함수
    function compareProductFields(product1, product2) {
        const result = {
            matched_fields: [],
            mismatched_fields: []
        };
        
        // 비교할 필드 쌍 정의
        const fieldsToCompare = [
            { field1: 'Quantity', field2: 'quantity', display: '수량' },
            { field1: 'Wholesale_Price', field2: 'wholesale_price', display: '단가' },
            { field1: 'Size', field2: 'size', display: '사이즈' },
            { field1: 'Color', field2: 'color', display: '색상' }
        ];
        
        // 필드별 비교
        fieldsToCompare.forEach(({ field1, field2, display }) => {
            const value1 = product1[field1] !== undefined ? product1[field1] : product1[field2];
            const value2 = product2[field1] !== undefined ? product2[field1] : product2[field2];
            
            // 값이 모두 존재하는 경우만 비교
            if (value1 !== undefined && value2 !== undefined) {
                // 값 정규화
                const value1Norm = normalizeValue(value1);
                const value2Norm = normalizeValue(value2);
                
                if (value1Norm === value2Norm) {
                    result.matched_fields.push(display);
                } else {
                    result.mismatched_fields.push({
                        field: display,
                        value1: value1,
                        value2: value2
                    });
                }
            }
        });
        
        return result;
    }
    
    // 값 정규화 함수
    function normalizeValue(value) {
        // 문자열로 변환
        let strValue = String(value).trim();
        
        // 숫자 정규화
        if (!isNaN(parseFloat(strValue))) {
            const numValue = parseFloat(strValue);
            // 소수점 이하가 0인 경우 정수로 변환
            if (numValue === Math.floor(numValue)) {
                strValue = String(Math.floor(numValue));
            }
        }
        
        // 대소문자 통일
        strValue = strValue.toLowerCase();
        
        // 통화 기호 및 쉼표 제거
        strValue = strValue.replace(/[$€₩]/g, '').replace(/,/g, '');
        
        return strValue;
    }
    
    // 문서 일치율 업데이트 함수
    function updateDocumentMatchRate(docId, matchRate) {
        // 세션 스토리지에서 문서 정보 가져오기
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        const docIndex = documents.findIndex(d => d.id === docId);
        
        if (docIndex >= 0) {
            // 일치율 업데이트
            documents[docIndex].match_rate = matchRate;
            
            // 세션 스토리지에 저장
            sessionStorage.setItem('ocr_documents', JSON.stringify(documents));
            
            // UI 업데이트 (있다면)
            const matchIndicator = document.querySelector(`.document-item[data-id="${docId}"] .match-value`);
            if (matchIndicator) {
                matchIndicator.textContent = `${matchRate}%`;
                
                // 클래스 업데이트
                const indicator = matchIndicator.closest('.match-indicator');
                if (indicator) {
                    indicator.classList.remove('high', 'medium', 'low');
                    if (matchRate >= 80) {
                        indicator.classList.add('high');
                    } else if (matchRate >= 60) {
                        indicator.classList.add('medium');
                    } else {
                        indicator.classList.add('low');
                    }
                }
            }
        }
    }
    
    // 비교 결과 표시 함수
    function showComparisonResult(result) {
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
                                <span class="product-name">${item.product_key}</span>
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
        
        resultHtml += '</div>';
        
        // 결과 표시
        compareResult.innerHTML = resultHtml;
        compareResult.style.display = 'block';
    }
    
    // 백엔드 API 호출 문서 비교 함수 (백업용)
    function compareDocuments(doc1Id, doc2Id) {
        // API 요청 데이터
        const requestData = {
            document1_id: doc1Id,
            document2_id: doc2Id
        };
        
        // API 요청
        fetch(`${API_BASE_URL}/compare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('문서 비교에 실패했습니다.');
            }
            return response.json();
        })
        .then(result => {
            // 비교 결과 표시
            showComparisonResult(result.result);
        })
        .catch(error => {
            console.error('문서 비교 중 오류:', error);
            alert('문서 비교에 실패했습니다: ' + error.message);
            
            // 오류 발생 시 클라이언트 측 비교로 대체
            console.log('클라이언트 측 비교로 대체합니다.');
            compareDocumentsInSession(doc1Id, doc2Id);
        });
    }
    
    // 새 문서 버튼 이벤트
    const newDocumentBtn = document.querySelector('.header-actions .btn-primary');
    if (newDocumentBtn) {
        newDocumentBtn.addEventListener('click', function() {
            window.location.href = 'upload.html';
        });
    }
    
    // 샘플 데이터 생성 함수 (개발용)
    function generateSampleData() {
        const sampleDocuments = [
            {
                id: 'doc1',
                filename: 'invoice_2023_001.pdf',
                excel_filename: 'invoice_2023_001.xlsx',
                document_type: 'invoice',
                date: '2023-11-20',
                brand: 'TOGA VIRILIS',
                season: '2024SS',
                status: 'complete',
                match_rate: 85,
                amount: '1250000',
                items: [
                    { Product_Code: 'AJ101', Color: 'BLACK LEATHER', Size: '39', Quantity: '5', Wholesale_Price: '150000' },
                    { Product_Code: 'AJ102', Color: 'WHITE LEATHER', Size: '40', Quantity: '3', Wholesale_Price: '120000' }
                ]
            },
            {
                id: 'doc2',
                filename: 'order_2023_001.pdf',
                excel_filename: 'order_2023_001.xlsx',
                document_type: 'purchase_order',
                date: '2023-11-15',
                brand: 'ATHLETICS FTWR',
                season: '2024SS',
                status: 'complete',
                match_rate: 60,
                amount: '980000',
                items: [
                    { Product_Code: 'AJ201', Color: 'BLACK POLIDO', Size: '41', Quantity: '4', Wholesale_Price: '130000' },
                    { Product_Code: 'AJ202', Color: 'BROWN LEATHER', Size: '42', Quantity: '6', Wholesale_Price: '110000' }
                ]
            },
            {
                id: 'doc3',
                filename: 'contract_2023_001.pdf',
                excel_filename: 'contract_2023_001.xlsx',
                document_type: 'contract',
                date: '2023-10-05',
                brand: 'WILD DONKEY',
                season: '2024FW',
                status: 'review',
                match_rate: 45,
                amount: '2500000',
                items: []
            }
        ];
        
        sessionStorage.setItem('ocr_documents', JSON.stringify(sampleDocuments));
        console.log('샘플 데이터가 생성되었습니다.');
    }
    
    // 고유 ID 생성 함수
    function generateUniqueId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    }
    
    // 디버깅 도구 추가 (개발 모드에서만)
    function addDebugTools() {
        // 개발 환경인지 확인
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            const devToolsDiv = document.createElement('div');
            devToolsDiv.className = 'dev-tools mt-4 p-3 bg-light border';
            devToolsDiv.innerHTML = `
                <h5>문서 디버깅 도구</h5>
                <button id="show-session-data" class="btn btn-info btn-sm">세션 스토리지 데이터 보기</button>
                <button id="generate-sample-data" class="btn btn-warning btn-sm ml-2">샘플 데이터 재생성</button>
                <button id="clear-session-data" class="btn btn-danger btn-sm ml-2">세션 데이터 삭제</button>
                <div id="debug-output" class="mt-3 p-2 bg-dark text-light" style="max-height: 300px; overflow: auto; display: none;"></div>
            `;
            
            // 페이지에 디버깅 도구 추가
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.appendChild(devToolsDiv);
                
                // 이벤트 리스너 추가
                document.getElementById('show-session-data').addEventListener('click', function() {
                    const debugOutput = document.getElementById('debug-output');
                    const sessionData = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
                    
                    debugOutput.style.display = 'block';
                    debugOutput.innerHTML = `<pre>${JSON.stringify(sessionData, null, 2)}</pre>`;
                });
                
                document.getElementById('generate-sample-data').addEventListener('click', function() {
                    generateSampleData();
                    loadDocuments(); // 문서 목록 다시 로드
                });
                
                document.getElementById('clear-session-data').addEventListener('click', function() {
                    sessionStorage.removeItem('ocr_documents');
                    alert('세션 데이터가 삭제되었습니다. 페이지를 새로고침하세요.');
                    loadDocuments(); // 문서 목록 다시 로드
                });
            }
        }
    }
    
    // 페이지 로드 시 디버깅 도구 추가
    addDebugTools();
});