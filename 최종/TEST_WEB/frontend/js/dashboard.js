// js/dashboard.js - 대시보드 페이지 스크립트

// API 기본 URL 설정 (백엔드와 일치시켜야 함)
const API_BASE_URL = 'http://localhost:5000/orders';

document.addEventListener('DOMContentLoaded', function() {
    // 초기 데이터 로드
    loadDashboardData();
    
    // 필터 적용 버튼 이벤트 리스너
    const applyFilterBtn = document.getElementById('applyFilter');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            loadDashboardData();
        });
    }
    
    // 검색 입력란 이벤트 리스너
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                loadDashboardData();
            }
        });
    }
    
    // 빠른 액션 버튼 이벤트 리스너 설정
    setupQuickActionButtons();
});

// 대시보드 데이터 로드 및 표시
async function loadDashboardData() {
    try {
        showLoadingState();
        
        // 필터 값 가져오기
        const filters = getFilterValues();
        
        // 필요한 모든 데이터 병렬로 로드
        const [
            documentsData,
            statisticsData,
            recentComparisons
        ] = await Promise.all([
            fetchDocuments(),
            fetchStatistics(filters),
            fetchRecentComparisons(filters)
        ]);
        
        // 주요 지표 업데이트
        updateMetricsCards(statisticsData);
        
        // 차트 업데이트
        updateCharts(statisticsData);
        
        // 알림 목록 업데이트
        updateAlertsList(recentComparisons);
        
        // 최근 문서 테이블 업데이트
        updateRecentDocumentsTable(recentComparisons);
        
        // 일치율 추이 차트 업데이트
        updateTrendChart(statisticsData.daily_stats);
        
        hideLoadingState();
    } catch (error) {
        console.error('대시보드 데이터 로드 오류:', error);
        showErrorMessage('데이터를 불러오는 중 오류가 발생했습니다.');
        hideLoadingState();
    }
}

// 필터 값 가져오기
function getFilterValues() {
    const startDate = document.getElementById('startDate')?.value || '';
    const endDate = document.getElementById('endDate')?.value || '';
    const searchTerm = document.getElementById('searchInput')?.value || '';
    
    // 브랜드 필터
    const brands = [];
    const brandAll = document.getElementById('brand-all');
    
    if (!brandAll || !brandAll.checked) {
        // 전체 브랜드가 선택되지 않은 경우, 개별 브랜드 체크박스 확인
        const brandCheckboxes = document.querySelectorAll('.checkbox-list input[id^="brand-"]:not(#brand-all)');
        
        brandCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                // brand-toga -> TOGA VIRILIS와 같이 변환 필요
                const brandId = checkbox.id.replace('brand-', '');
                if (brandId === 'toga') brands.push('TOGA VIRILIS');
                else if (brandId === 'wild') brands.push('WILD DONKEY');
                else if (brandId === 'athletics') brands.push('ATHLETICS FTWR');
                else if (brandId === 'baserange') brands.push('BASERANGE');
                else if (brandId === 'nounou') brands.push('NOU NOU');
            }
        });
    }
    
    // 상태 필터
    const statuses = [];
    const statusAll = document.getElementById('status-all');
    
    if (!statusAll || !statusAll.checked) {
        // 전체 상태가 선택되지 않은 경우, 개별 상태 체크박스 확인
        const statusCheckboxes = document.querySelectorAll('.checkbox-list input[id^="status-"]:not(#status-all)');
        
        statusCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                statuses.push(checkbox.id.replace('status-', ''));
            }
        });
    }
    
    return {
        start_date: startDate,
        end_date: endDate,
        search: searchTerm,
        brands: brands,
        statuses: statuses
    };
}

// 문서 목록 가져오기
async function fetchDocuments() {
    try {
        const [invoiceResponse, orderResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/documents/invoice`),
            fetch(`${API_BASE_URL}/documents/order`)
        ]);
        
        if (!invoiceResponse.ok || !orderResponse.ok) {
            throw new Error('문서 데이터를 가져오는데 실패했습니다.');
        }
        
        const invoiceData = await invoiceResponse.json();
        const orderData = await orderResponse.json();
        
        return {
            invoices: invoiceData.invoices || [],
            orders: orderData.orders || [],
            total: (invoiceData.invoices?.length || 0) + (orderData.orders?.length || 0)
        };
    } catch (error) {
        console.error('문서 데이터 로드 오류:', error);
        return { invoices: [], orders: [], total: 0 };
    }
}

// 통계 데이터 가져오기
async function fetchStatistics(filters) {
    try {
        // 필터 파라미터 구성
        const params = new URLSearchParams();
        
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.brands && filters.brands.length === 1) params.append('brand', filters.brands[0]);
        
        const response = await fetch(`${API_BASE_URL}/statistics?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error('통계 데이터를 가져오는데 실패했습니다.');
        }
        
        return await response.json();
    } catch (error) {
        console.error('통계 데이터 로드 오류:', error);
        return {
            total_comparisons: 0,
            avg_match_percentage: 0,
            low_match_count: 0,
            brand_stats: [],
            daily_stats: []
        };
    }
}

async function fetchRecentComparisons(filters) {
    try {
        // 필터 파라미터 구성
        const params = new URLSearchParams();
        
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
        // 수동 비교된 문서만 가져오도록 쿼리 파라미터 추가
        params.append('manually_compared', 'true');
        
        const response = await fetch(`${API_BASE_URL}/comparison-history?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error('비교 결과 데이터를 가져오는데 실패했습니다.');
        }
        
        return await response.json();
    } catch (error) {
        console.error('비교 결과 데이터 로드 오류:', error);
        return {
            comparisons: [],
            total_count: 0
        };
    }
}


// 주요 지표 카드 업데이트
function updateMetricsCards(statistics) {
    // 문서 수 업데이트
    const totalDocumentsElement = document.getElementById('totalDocumentsCount');
    if (totalDocumentsElement) {
        // 비교 결과 수로 대체 (실제 구현에서는 전체 문서 수가 필요할 수 있음)
        totalDocumentsElement.textContent = statistics.total_comparisons || 0;
    }
    
    // 평균 일치율 업데이트
    const avgMatchRateElement = document.getElementById('averageMatchRate');
    if (avgMatchRateElement) {
        avgMatchRateElement.textContent = `${statistics.avg_match_percentage || 0}%`;
    }
    
    // 검토 필요 문서 수 업데이트
    const reviewNeededElement = document.getElementById('reviewNeededCount');
    if (reviewNeededElement) {
        reviewNeededElement.textContent = statistics.low_match_count || 0;
    }
    
    // 이번 주 처리 문서 수 업데이트
    const processedThisWeekElement = document.getElementById('processedThisWeek');
    if (processedThisWeekElement) {
        // 일주일간의 총 비교 수를 계산
        const weeklyCount = statistics.daily_stats?.reduce((sum, day) => sum + day.comparison_count, 0) || 0;
        processedThisWeekElement.textContent = weeklyCount;
        
        // 증감율 업데이트 (이번 주 vs 지난 주)
        const deltaElement = document.getElementById('processedDelta');
        if (deltaElement) {
            // 실제 구현에서는 지난 주 데이터와 비교 필요
            // 현재는 임의의 증가율 표시
            if (weeklyCount > 0) {
                deltaElement.textContent = '+5';
                deltaElement.classList.add('positive');
            } else {
                deltaElement.textContent = '0';
                deltaElement.classList.remove('positive');
            }
        }
    }
}

// 차트 업데이트
function updateCharts(statistics) {
    // 일치/불일치 비율 파이 차트
    updateMatchRateChart(statistics);
    
    // 다른 차트들도 필요에 따라 추가
}

// 일치/불일치 비율 차트 업데이트
function updateMatchRateChart(statistics) {
    const ctx = document.getElementById('matchRateChart');
    if (!ctx) return;
    
    // 평균 일치율
    const matchRate = statistics.avg_match_percentage || 0;
    const mismatchRate = 100 - matchRate;
    
    // 기존 차트 인스턴스 확인 및 파괴
    if (window.matchRateChartInstance) {
        window.matchRateChartInstance.destroy();
    }
    
    // 새로운 차트 생성
    window.matchRateChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['일치', '불일치'],
            datasets: [{
                data: [matchRate, mismatchRate],
                backgroundColor: ['#4CAF50', '#E57373'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            family: "'Noto Sans KR', sans-serif",
                            size: 12
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map(function(label, i) {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label} (${value.toFixed(1)}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        strokeStyle: data.datasets[0].backgroundColor[i],
                                        lineWidth: 0,
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${value.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
    
    // 범례 업데이트
    updateMatchRateLegend(matchRate, mismatchRate);
}

// 일치/불일치 비율 범례 업데이트
function updateMatchRateLegend(matchRate, mismatchRate) {
    const legendContainer = document.getElementById('matchRateLegend');
    if (!legendContainer) return;
    
    // 범례 HTML 생성
    legendContainer.innerHTML = `
        <div class="legend-item">
            <span class="legend-color" style="background-color: #4CAF50;"></span>
            <span>일치 (${matchRate.toFixed(1)}%)</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #E57373;"></span>
            <span>불일치 (${mismatchRate.toFixed(1)}%)</span>
        </div>
    `;
}

// 알림 목록 업데이트 함수 수정
function updateAlertsList(comparisonData) {
    const alertsList = document.getElementById('alertsList');
    if (!alertsList) return;
    
    // 수동 비교된 문서만 필터링
    const manuallyComparedItems = comparisonData.comparisons.filter(comp => comp.manually_compared);
    
    // 낮은 일치율 문서만 필터링 (80% 미만)
    const lowMatchItems = manuallyComparedItems.filter(comp => comp.match_percentage < 80);
    
    // 알림 컨테이너 초기화
    alertsList.innerHTML = '';
    
    // 알림 목록이 비어있는 경우
    if (lowMatchItems.length === 0) {
        alertsList.innerHTML = '<div class="info-message">검토가 필요한 문서가 없습니다.</div>';
        return;
    }
    
    // 상위 3개 항목만 표시
    const topItems = lowMatchItems.slice(0, 3);
    
    topItems.forEach(item => {
        // 일치율에 따른 알림 클래스 결정
        let alertClass = 'warning';
        if (item.match_percentage < 60) alertClass = 'error';
        
        // 브랜드 정보
        const brand = item.document1.brand || item.document2.brand || '알 수 없음';
        
        // 날짜 형식 변환
        const comparisonDate = new Date(item.comparison_date);
        const today = new Date();
        const diffTime = Math.abs(today - comparisonDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const dateText = diffDays <= 1 ? '오늘' : `${diffDays}일 전`;
        
        // 알림 아이템 HTML 생성
        const alertHtml = `
            <div class="alert-item ${alertClass}">
                <div class="alert-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="alert-content">
                    <h4>${brand} 검토 필요</h4>
                    <p>${dateText} - 일치율 ${item.match_percentage.toFixed(1)}%</p>
                </div>
                <button class="btn btn-icon view-comparison" data-doc1="${item.document1.id}" data-doc2="${item.document2.id}">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        // 알림 목록에 추가
        alertsList.insertAdjacentHTML('beforeend', alertHtml);
    });
    
    // 문서 보기 버튼 이벤트 리스너 추가
    const viewButtons = alertsList.querySelectorAll('.view-comparison');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const doc1Id = this.getAttribute('data-doc1');
            const doc2Id = this.getAttribute('data-doc2');
            window.location.href = `orders.html?doc1=${doc1Id}&doc2=${doc2Id}`;
        });
    });
}

// 최근 문서 테이블 업데이트 함수 수정
function updateRecentDocumentsTable(comparisonData) {
    const tableBody = document.getElementById('comparisonResultsTable');
    if (!tableBody) return;
    
    // 테이블 초기화
    tableBody.innerHTML = '';
    
    // 수동 비교된 문서만 필터링
    const manuallyComparedComparisons = comparisonData.comparisons.filter(comp => comp.manually_compared);
    
    // 데이터가 없는 경우
    if (manuallyComparedComparisons.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">비교된 문서가 없습니다.</td>
            </tr>
        `;
        return;
    }
    
    // 비교 결과를 쌍으로 그룹화하여 표시
    manuallyComparedComparisons.forEach(comparison => {
        // 이하 기존 코드와 동일 (기존 로직 유지)
        // ... (이전 코드 복사)
    });
}

// 페이지네이션 업데이트
function updatePagination(totalCount, currentPage, itemsPerPage) {
    const paginationElement = document.getElementById('documentsPagination');
    if (!paginationElement) return;
    
    // 총 페이지 수 계산
    const totalPages = Math.ceil(totalCount / itemsPerPage);
    
    // 페이지네이션이 필요한지 확인
    if (totalPages <= 1) {
        paginationElement.innerHTML = '';
        return;
    }
    
    // 페이지네이션 HTML 생성
    let paginationHtml = `
        <button class="btn btn-sm" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i>
        </button>
    `;
    
    // 표시할 페이지 범위 결정
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    
    // 시작 페이지가 맨 앞에 가깝다면 더 많은 페이지 표시
    if (startPage <= 3) {
        endPage = Math.min(totalPages, 5);
    }
    
    // 마지막 페이지가 맨 뒤에 가깝다면 더 앞쪽 페이지 표시
    if (endPage >= totalPages - 2) {
        startPage = Math.max(1, totalPages - 4);
    }
    
    // 페이지 버튼 생성
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <button class="btn btn-sm ${i === currentPage ? 'active' : ''}" data-page="${i}">
                ${i}
            </button>
        `;
    }
    
    // 다음 페이지 버튼
    paginationHtml += `
        <button class="btn btn-sm" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    paginationElement.innerHTML = paginationHtml;
    
    // 페이지 버튼 이벤트 리스너 추가
    const pageButtons = paginationElement.querySelectorAll('.btn[data-page]');
    pageButtons.forEach(button => {
        button.addEventListener('click', function() {
            const page = parseInt(this.getAttribute('data-page'));
            // 해당 페이지 데이터 로드 (추후 구현)
        });
    });
}

// 테이블 버튼 이벤트 리스너 추가
function addTableButtonListeners() {
    // 문서 보기 버튼
    const viewButtons = document.querySelectorAll('.view-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const doc1Id = this.getAttribute('data-doc1');
            const doc2Id = this.getAttribute('data-doc2');
            // orders.html로 이동하면서 비교 문서 ID 전달
            window.location.href = `orders.html?doc1=${doc1Id}&doc2=${doc2Id}`;
        });
    });
    
    // 내보내기 버튼
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const comparisonId = this.getAttribute('data-id');
            // 추후 내보내기 기능 구현
            alert(`비교 결과 ${comparisonId}를 내보냅니다.`);
        });
    });
}

// 일치율 추이 차트 업데이트
function updateTrendChart(dailyStats) {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;
    
    // 날짜 및 일치율 데이터 추출
    const dates = dailyStats.map(item => item.date);
    const matchRates = dailyStats.map(item => item.avg_match_percentage);
    
    // 기존 차트 인스턴스 확인 및 파괴
    if (window.trendChartInstance) {
        window.trendChartInstance.destroy();
    }
    
    // 새로운 차트 생성
    window.trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '평균 일치율',
                data: matchRates,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#4CAF50',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    min: Math.max(0, Math.min(...matchRates) - 10),
                    max: Math.min(100, Math.max(...matchRates) + 10),
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `일치율: ${context.raw.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}

// 빠른 액션 버튼 이벤트 리스너 설정
function setupQuickActionButtons() {
    // 새 문서 업로드 버튼
    const newDocumentBtn = document.getElementById('newDocumentBtn');
    if (newDocumentBtn) {
        newDocumentBtn.addEventListener('click', function() {
            window.location.href = 'upload.html';
        });
    }
    
    // OCR 재처리 버튼
    const reprocessOcrBtn = document.getElementById('reprocessOcrBtn');
    if (reprocessOcrBtn) {
        reprocessOcrBtn.addEventListener('click', function() {
            alert('OCR 재처리 기능은 개발 중입니다.');
        });
    }
    
    // 보고서 생성 버튼
    const generateReportBtn = document.getElementById('generateReportBtn');
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', function() {
            window.location.href = 'reports.html';
        });
    }
    
    // AI 문서 비교 버튼
    const compareDocumentsBtn = document.getElementById('compareDocumentsBtn');
    if (compareDocumentsBtn) {
        compareDocumentsBtn.addEventListener('click', function() {
            window.location.href = 'orders.html?compare=true';
        });
    }
}

// 로딩 상태 표시
function showLoadingState() {
    // 주요 지표 카드
    document.querySelectorAll('.metric-value').forEach(el => {
        el.classList.add('loading');
        el.dataset.originalText = el.textContent;
        el.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    });
    
    // 알림 목록
    const alertsList = document.getElementById('alertsList');
    if (alertsList) {
        alertsList.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 알림 로드 중...</div>';
    }
    
    // 최근 문서 테이블
    const tableBody = document.getElementById('recentDocumentsTableBody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7">
                    <div class="loading-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 데이터 로드 중...
                    </div>
                </td>
            </tr>
        `;
    }
}

// 로딩 상태 숨기기
function hideLoadingState() {
    // 주요 지표 카드의 로딩 상태 제거
    document.querySelectorAll('.metric-value.loading').forEach(el => {
        el.classList.remove('loading');
        if (el.dataset.originalText) {
            el.textContent = el.dataset.originalText;
            delete el.dataset.originalText;
        }
    });
}

// 오류 메시지 표시
function showErrorMessage(message) {
    // 알림 영역 사용
    const alertsList = document.getElementById('alertsList');
    if (alertsList) {
        alertsList.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${message}</div>`;
    }
    
    // 테이블 영역 사용
    const tableBody = document.getElementById('recentDocumentsTableBody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7">
                    <div class="error-message">
                        <i class="fas fa-exclamation-circle"></i> ${message}
                    </div>
                </td>
            </tr>
        `;
    }
}