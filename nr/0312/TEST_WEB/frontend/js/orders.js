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
    const documentPreview = document.querySelector('.doc-preview img');
    const documentInfoItems = document.querySelectorAll('.detail-item');
    const documentDetailTable = document.querySelector('.detail-table tbody');
    const editButton = document.querySelector('.document-detail .btn-primary');
    const downloadButton = document.querySelector('.document-detail .btn-outline');
    
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
    
    function loadDocuments(filters = {}) {
        // 로딩 표시
        console.log('문서 로드 함수 시작');
        
        // 먼저 DOM 요소 확인
        if (!documentGrid) {
            console.error('문서 그리드 요소를 찾을 수 없습니다. 선택자: .document-grid');
            return;
        }
        
        documentGrid.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 문서 로드 중...</div>';
        
        // 세션 스토리지 데이터 먼저 확인
        const sessionData = sessionStorage.getItem('ocr_documents');
        console.log('세션 스토리지 데이터 존재 여부:', !!sessionData);
        
        // API 요청 시도
        console.log('API 호출 시도:', `${API_BASE_URL}/documents`);
        fetch(`${API_BASE_URL}/documents`)
            .then(response => {
                console.log('API 응답 상태:', response.status);
                if (!response.ok) {
                    throw new Error('서버에서 문서를 불러올 수 없습니다.');
                }
                return response.json();
            })
            .then(data => {
                console.log('API 응답 데이터:', data);
                // 기존 코드...
            })
            .catch(error => {
                console.error('API 호출 오류:', error);
                
                // 세션 스토리지 데이터 처리
                try {
                    const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
                    console.log('세션 스토리지에서 로드한 문서 수:', documents.length);
                    
                    if (documents.length > 0) {
                        renderDocumentGrid(documents);
                    } else {
                        documentGrid.innerHTML = '<div class="empty-state">문서가 없습니다. 새 문서를 업로드해주세요.</div>';
                    }
                } catch (parseError) {
                    console.error('세션 스토리지 데이터 파싱 오류:', parseError);
                    documentGrid.innerHTML = '<div class="error-state">데이터 로드 중 오류가 발생했습니다.</div>';
                }
            });
    }
    
    // 문서 그리드 렌더링 함수 (개선됨)
    function renderDocumentGrid(documents) {
        console.log('렌더링할 문서 데이터:', documents);
        
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
    
    // 문서 상세 보기 함수 (개선됨)
    function viewDocument(docId) {
        // 이미 선택된 문서인 경우 무시
        if (selectedDocumentId === docId) return;
        
        console.log('문서 상세 정보 보기:', docId);
        selectedDocumentId = docId;
        
        // 문서 상세 영역 표시
        if (documentDetail) {
            documentDetail.style.display = 'block';
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
        
        // 먼저 세션 스토리지에서 문서 정보 확인
        const documents = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
        const doc = documents.find(d => d.id === docId);
        
        if (doc) {
            // 세션 스토리지에 데이터가 있으면 사용
            console.log('세션 스토리지에서 문서 정보 사용:', doc);
            updateDocumentDetailView(doc);
        } else {
            // API 요청
            fetch(`${API_BASE_URL}/document/${docId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('문서 상세 정보를 불러오는데 실패했습니다.');
                    }
                    return response.json();
                })
                .then(doc => {
                    // 문서 정보 업데이트
                    updateDocumentDetailView(doc);
                })
                .catch(error => {
                    console.error('문서 상세 정보 로드 중 오류:', error);
                    alert('문서 상세 정보를 불러오는데 실패했습니다.');
                });
        }
    }
    
    // 문서 상세 정보 화면 업데이트
    function updateDocumentDetailView(doc) {
        // 문서 미리보기 업데이트
        if (documentPreview) {
            documentPreview.src = doc.preview_url || 'https://via.placeholder.com/300x400?text=PDF+Preview';
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
    
    // 문서 정보 업데이트 함수 (개선됨)
    function updateDocumentInfo(doc) {
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
                const types = {
                    'purchase_order': '발주서',
                    'invoice': '인보이스',
                    'contract': '계약서',
                    'order_confirmation': '오더컨펌'
                };
                return types[value] || value;
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
    
    // 문서 품목 테이블 업데이트 함수 (개선됨)
    function updateDocumentItems(items) {
        if (!documentDetailTable) return;
        
        if (!items || items.length === 0) {
            documentDetailTable.innerHTML = '<tr><td colspan="4">품목 정보가 없습니다.</td></tr>';
            return;
        }
        
        let tableHtml = '';
        
        // 첫 번째 항목의 키를 기준으로 열 제목 결정
        const firstItem = items[0];
        const keys = Object.keys(firstItem);
        
        // 항목 필드 매핑 (표시할 필드 결정)
        let nameField = keys.find(k => k.toLowerCase().includes('product') || k.toLowerCase().includes('name')) || 'product_name';
        if (nameField === 'product_name' && !keys.includes(nameField)) {
            nameField = 'Product_Code';
        }
        
        let qtyField = keys.find(k => k.toLowerCase().includes('quantity') || k.toLowerCase().includes('qty')) || 'quantity';
        if (qtyField === 'quantity' && !keys.includes(qtyField)) {
            qtyField = 'Quantity';
        }
        
        let priceField = keys.find(k => k.toLowerCase().includes('price') || k.toLowerCase().includes('wholesale')) || 'unit_price';
        if (priceField === 'unit_price' && !keys.includes(priceField)) {
            priceField = 'Wholesale_Price';
        }
        
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
    
    // 문서 다운로드 함수 (개선됨)
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
    
    // 문서 비교 함수
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
            showComparisonResult(result);
        })
        .catch(error => {
            console.error('문서 비교 중 오류:', error);
            alert('문서 비교에 실패했습니다: ' + error.message);
        });
    }
    
    // 비교 결과 표시 함수
    function showComparisonResult(result) {
        // 현재는 간단한 알림으로 대체
        const matchPercentage = result.summary?.match_percentage || 0;
        alert(`문서 비교 결과: 일치율 ${matchPercentage}%`);
        
        // 추후 모달 또는 상세 비교 페이지로 확장 예정
    }
    
    // 새 문서 버튼 이벤트
    const newDocumentBtn = document.querySelector('.header-actions .btn-primary');
    if (newDocumentBtn) {
        newDocumentBtn.addEventListener('click', function() {
            window.location.href = 'upload.html';
        });
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
                <button id="generate-sample-data" class="btn btn-warning btn-sm ml-2">샘플 데이터 생성</button>
                <button id="clear-session-data" class="btn btn-danger btn-sm ml-2">세션 데이터 삭제</button>
                <div id="debug-output" class="mt-3 p-2 bg-dark text-light" style="max-height: 300px; overflow: auto; display: none;"></div>
            `;
            
            // 페이지에 디버깅 도구 추가
            document.querySelector('.main-content').appendChild(devToolsDiv);
            
            // 이벤트 리스너 추가
            document.getElementById('show-session-data').addEventListener('click', function() {
                const debugOutput = document.getElementById('debug-output');
                const sessionData = JSON.parse(sessionStorage.getItem('ocr_documents') || '[]');
                
                debugOutput.style.display = 'block';
                debugOutput.innerHTML = `<pre>${JSON.stringify(sessionData, null, 2)}</pre>`;
            });
            
            document.getElementById('generate-sample-data').addEventListener('click', function() {
                generateSampleData();
            });
            
            document.getElementById('clear-session-data').addEventListener('click', function() {
                sessionStorage.removeItem('ocr_documents');
                alert('세션 데이터가 삭제되었습니다. 페이지를 새로고침하세요.');
                loadDocuments(); // 문서 목록 다시 로드
            });
        }
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
        alert('샘플 데이터가 생성되었습니다.');
        loadDocuments(); // 문서 목록 다시 로드
    }

    // 고유 ID 생성 함수
    function generateUniqueId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    }

    // 페이지 로드 시 디버깅 도구 추가
    addDebugTools();
}); // DOMContentLoaded 이벤트 리스너 종료