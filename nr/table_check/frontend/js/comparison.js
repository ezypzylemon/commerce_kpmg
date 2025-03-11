// 문서 비교 관련 추가 함수들
document.addEventListener('DOMContentLoaded', () => {
    // 이미 main.js에서 비교 기능의 기본 세팅이 이루어짐
    // 이 파일에서는 추가적인 비교 기능을 구현
    initComparisonExtraFeatures();
});

// 비교 추가 기능 초기화
function initComparisonExtraFeatures() {
    // 비교 결과 필터링 기능
    setupComparisonFilters();
    
    // 비교 결과 정렬 기능
    setupComparisonSorting();
    
    // 비교 결과 엑셀 내보내기 기능
    setupExportToExcel();
}

// 비교 결과 필터링 설정
function setupComparisonFilters() {
    // 비교 결과 테이블 헤더에 필터 아이콘 추가
    const tableHeaders = document.querySelectorAll('#comparison-table th');
    
    tableHeaders.forEach(header => {
        if (header.textContent !== '작업') {
            const filterIcon = document.createElement('i');
            filterIcon.className = 'fas fa-filter filter-icon';
            filterIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                showFilterOptions(header, e);
            });
            
            header.appendChild(filterIcon);
        }
    });
}

// 필터 옵션 표시
function showFilterOptions(header, event) {
    // 이미 열려있는 필터 옵션 제거
    const existingFilters = document.querySelector('.status-filters');
    if (existingFilters) {
        existingFilters.remove();
    }
    
    // 필터 항목 설정
    let filterOptions = [];
    const columnIndex = getColumnIndex(header);
    const columnName = header.textContent.trim().replace('▲', '').replace('▼', '');
    
    // 열에 따라 필터 옵션 설정
    switch (columnName) {
        case '상태':
            filterOptions = [
                { label: '전체', value: 'all' },
                { label: '완료', value: 'complete' },
                { label: '검토 필요', value: 'review_needed' }
            ];
            break;
        case '일치율':
            filterOptions = [
                { label: '전체', value: 'all' },
                { label: '100%', value: '100' },
                { label: '90% 이상', value: '90' },
                { label: '50% 이상', value: '50' },
                { label: '50% 미만', value: 'below50' }
            ];
            break;
        default:
            return; // 다른 열에는 필터링 없음
    }
    
    // 필터 옵션 UI 생성
    const filterContainer = document.createElement('div');
    filterContainer.className = 'status-filters';
    
    filterOptions.forEach(option => {
        const filterOption = document.createElement('div');
        filterOption.className = 'filter-option';
        filterOption.innerHTML = `
            <span class="filter-check"><i class="fas fa-check"></i></span>
            <span>${option.label}</span>
        `;
        
        // 필터 적용 이벤트
        filterOption.addEventListener('click', () => {
            applyFilter(columnName, option.value);
            filterContainer.remove();
        });
        
        filterContainer.appendChild(filterOption);
    });
    
    // 위치 설정 및 표시
    const rect = header.getBoundingClientRect();
    filterContainer.style.top = `${rect.bottom}px`;
    filterContainer.style.left = `${rect.left}px`;
    
    document.body.appendChild(filterContainer);
    
    // 문서 클릭 시 필터 닫기
    document.addEventListener('click', function closeFilter(e) {
        if (!filterContainer.contains(e.target) && e.target !== header) {
            filterContainer.remove();
            document.removeEventListener('click', closeFilter);
        }
    });
}

// 열 인덱스 가져오기
function getColumnIndex(th) {
    const tableHeaders = Array.from(th.parentElement.children);
    return tableHeaders.indexOf(th);
}

// 필터 적용
function applyFilter(columnName, value) {
    const tableRows = document.querySelectorAll('#comparison-table-body tr');
    
    tableRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let show = true;
        
        if (columnName === '상태') {
            const statusCell = cells[4]; // 상태 열 인덱스
            const statusText = statusCell.textContent.trim();
            
            if (value !== 'all') {
                if (value === 'complete' && statusText !== '완료') {
                    show = false;
                } else if (value === 'review_needed' && statusText !== '검토 필요') {
                    show = false;
                }
            }
        } else if (columnName === '일치율') {
            const rateCell = cells[3]; // 일치율 열 인덱스
            const rateText = rateCell.textContent.trim();
            const rate = parseFloat(rateText);
            
            if (value !== 'all') {
                if (value === '100' && rate !== 100) {
                    show = false;
                } else if (value === '90' && rate < 90) {
                    show = false;
                } else if (value === '50' && rate < 50) {
                    show = false;
                } else if (value === 'below50' && rate >= 50) {
                    show = false;
                }
            }
        }
        
        row.style.display = show ? '' : 'none';
    });
}

// 비교 결과 정렬 설정
function setupComparisonSorting() {
    const tableHeaders = document.querySelectorAll('#comparison-table th');
    
    tableHeaders.forEach(header => {
        if (header.textContent !== '작업') {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                sortComparisonTable(header);
            });
        }
    });
}

// 비교 테이블 정렬
function sortComparisonTable(header) {
    const tableBody = document.getElementById('comparison-table-body');
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    
    // 현재 정렬 방향 확인
    const isAscending = header.classList.contains('sort-asc');
    
    // 모든 헤더에서 정렬 클래스 제거
    document.querySelectorAll('#comparison-table th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        th.textContent = th.textContent.replace('▲', '').replace('▼', '');
    });
    
    // 새 정렬 방향 설정
    const sortDirection = isAscending ? 'desc' : 'asc';
    header.classList.add(`sort-${sortDirection}`);
    
    // 정렬 화살표 표시
    const arrow = sortDirection === 'asc' ? '▲' : '▼';
    header.textContent = `${header.textContent.trim()} ${arrow}`;
    
    // 열 인덱스 가져오기
    const columnIndex = getColumnIndex(header);
    
    // 정렬 함수
    rows.sort((a, b) => {
        const cellA = a.cells[columnIndex].textContent.trim();
        const cellB = b.cells[columnIndex].textContent.trim();
        
        // 날짜 정렬
        if (columnIndex === 0) {
            const dateA = new Date(cellA.split('-').reverse().join('-'));
            const dateB = new Date(cellB.split('-').reverse().join('-'));
            return sortDirection === 'asc' ? dateA - dateB : dateB - dateA;
        }
        
        // 일치율 정렬
        if (columnIndex === 3) {
            const rateA = parseFloat(cellA);
            const rateB = parseFloat(cellB);
            return sortDirection === 'asc' ? rateA - rateB : rateB - rateA;
        }
        
        // 텍스트 정렬
        return sortDirection === 'asc' ? 
            cellA.localeCompare(cellB, 'ko') : 
            cellB.localeCompare(cellA, 'ko');
    });
    
    // 정렬된 행 다시 삽입
    rows.forEach(row => {
        tableBody.appendChild(row);
    });
}

// 엑셀 내보내기 설정
function setupExportToExcel() {
    // 상세 비교 모달에 내보내기 버튼 추가
    document.addEventListener('DOMContentLoaded', () => {
        // 이벤트 위임 사용
        document.addEventListener('click', (e) => {
            if (e.target && e.target.id === 'comparison-detail-modal') {
                const modalHeader = e.target.querySelector('.modal-header');
                
                // 이미 버튼이 있는지 확인
                if (!modalHeader.querySelector('#export-excel-btn')) {
                    const exportButton = document.createElement('button');
                    exportButton.id = 'export-excel-btn';
                    exportButton.className = 'download-button';
                    exportButton.innerHTML = '<i class="fas fa-file-excel"></i> Excel 내보내기';
                    exportButton.addEventListener('click', exportComparisonToExcel);
                    
                    modalHeader.appendChild(exportButton);
                }
            }
        });
    });
}

// 엑셀로 내보내기
function exportComparisonToExcel() {
    // 여기서는 실제 엑셀 다운로드 대신 CSV 형식으로 다운로드
    const comparisonId = comparisonDetailModal.dataset.comparisonId;
    
    fetch(`${API_BASE_URL}/comparisons/${comparisonId}`)
        .then(response => response.json())
        .then(comparison => {
            // CSV 헤더
            let csvContent = "data:text/csv;charset=utf-8,";
            
            // 비교 정보
            csvContent += "비교 정보\n";
            csvContent += "비교 ID," + comparison.id + "\n";
            csvContent += "일치율," + comparison.match_rate + "%\n";
            csvContent += "상태," + (comparison.status === 'review_needed' ? '검토 필요' : '완료') + "\n\n";
            
            // 차이점 섹션
            csvContent += "차이점\n";
            csvContent += "상품 코드,사이즈,필드,문서1 값,문서2 값\n";
            
            if (comparison.differences && comparison.differences.length > 0) {
                comparison.differences.forEach(diff => {
                    csvContent += `${diff.product_code || 'N/A'},${diff.size || 'N/A'},${diff.field || 'N/A'},${diff.doc1_value || 'N/A'},${diff.doc2_value || 'N/A'}\n`;
                });
            } else {
                csvContent += "차이점 없음\n";
            }
            
            csvContent += "\n";
            
            // 문서1 전용 항목
            csvContent += "문서1 전용 항목\n";
            csvContent += "상품 코드,색상,사이즈,수량\n";
            
            if (comparison.doc1_only && comparison.doc1_only.length > 0) {
                comparison.doc1_only.forEach(item => {
                    csvContent += `${item.product_code || 'N/A'},${item.color || 'N/A'},${item.size || 'N/A'},${item.quantity || 'N/A'}\n`;
                });
            } else {
                csvContent += "문서1 전용 항목 없음\n";
            }
            
            csvContent += "\n";
            
            // 문서2 전용 항목
            csvContent += "문서2 전용 항목\n";
            csvContent += "상품 코드,색상,사이즈,수량\n";
            
            if (comparison.doc2_only && comparison.doc2_only.length > 0) {
                comparison.doc2_only.forEach(item => {
                    csvContent += `${item.product_code || 'N/A'},${item.color || 'N/A'},${item.size || 'N/A'},${item.quantity || 'N/A'}\n`;
                });
            } else {
                csvContent += "문서2 전용 항목 없음\n";
            }
            
            csvContent += "\n";
            
            // 일치 항목 섹션
            csvContent += "일치 항목\n";
            csvContent += "상품 코드,색상,사이즈,수량\n";
            
            if (comparison.matching_products && comparison.matching_products.length > 0) {
                comparison.matching_products.forEach(item => {
                    csvContent += `${item.product_code || 'N/A'},${item.color || 'N/A'},${item.size || 'N/A'},${item.quantity || 'N/A'}\n`;
                });
            } else {
                csvContent += "일치 항목 없음\n";
            }
            
            // 날짜를 파일명에 포함
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10);
            const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, '-');
            
            // 다운로드 링크 생성
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `비교결과_${dateStr}_${timeStr}.csv`);
            document.body.appendChild(link);
            
            // 다운로드 링크 클릭
            link.click();
            
            // 링크 제거
            document.body.removeChild(link);
        })
        .catch(error => {
            console.error('내보내기 오류:', error);
            showNotification('내보내기 중 오류가 발생했습니다.', 'error');
        });
}

// 비교 결과 분석 함수 (특정 브랜드/항목에 대한 일치율 추이 분석)
function analyzeComparisonTrends() {
    // 이 기능은 향후 구현 예정
    console.log("비교 결과 추이 분석 - 아직 구현되지 않음");
}

// 비교 결과 문서화 (PDF 보고서 생성)
function generateComparisonReport(comparisonId) {
    // 이 기능은 향후 구현 예정
    console.log("PDF 보고서 생성 - 아직 구현되지 않음");
    showNotification('PDF 보고서 생성 기능이 준비 중입니다.', 'warning');
}

// 재검증 요청 함수 (관리자에게 문서 재검토 요청)
function requestRevalidation(comparisonId) {
    // 이 기능은 향후 구현 예정
    console.log("재검증 요청 - 아직 구현되지 않음");
    showNotification('재검증 요청 기능이 준비 중입니다.', 'warning');
}

// 비교 상세 모달 열릴 때 실행될 확장 기능들
function comparisonDetailModalExtensions() {
    // 이 함수는 상세 모달이 열릴 때 호출됨
    
    // 1. 통계 시각화 기능 추가
    addStatisticsVisualization();
    
    // 2. 특이사항 하이라이팅
    highlightImportantDifferences();
    
    // 3. 액션 아이템 추천
    suggestActionItems();
}

// 통계 시각화 기능
function addStatisticsVisualization() {
    // 이 기능은 향후 구현 예정
    console.log("통계 시각화 - 아직 구현되지 않음");
}

// 중요 차이점 하이라이팅
function highlightImportantDifferences() {
    // 이 기능은 향후 구현 예정
    console.log("중요 차이점 하이라이팅 - 아직 구현되지 않음");
}

// 액션 아이템 추천
function suggestActionItems() {
    // 이 기능은 향후 구현 예정
    console.log("액션 아이템 추천 - 아직 구현되지 않음");
}