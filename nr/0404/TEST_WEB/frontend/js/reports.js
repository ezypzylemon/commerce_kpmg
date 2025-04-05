// js/reports.js - 보고서 페이지 스크립트

// API 기본 URL 설정
const API_BASE_URL = 'http://localhost:5000/orders';

document.addEventListener('DOMContentLoaded', function() {
    // 초기 데이터 로드
    loadReportData();
    
    // 필터 적용 버튼 이벤트 리스너
    const applyFilterBtn = document.getElementById('applyReportFilter');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            loadReportData();
        });
    }
    
    // 뷰 전환 버튼 이벤트 리스너
    const viewButtons = document.querySelectorAll('.btn-group .btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 활성 버튼 클래스 전환
            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 뷰 전환 처리
            const viewType = this.id.replace('view', '').toLowerCase();
            switchView(viewType);
        });
    });
    
    // 다운로드 버튼 이벤트 리스너
    document.getElementById('downloadReport')?.addEventListener('click', function() {
        generateAndDownloadReport();
    });
    
    // 차트 다운로드 버튼들 이벤트 리스너
    document.querySelectorAll('[id$="Chart"]').forEach(chart => {
        const downloadButton = document.querySelector(`#download${chart.id.charAt(0).toUpperCase() + chart.id.slice(1)}`);
        if (downloadButton) {
            downloadButton.addEventListener('click', function() {
                downloadChart(chart.id);
            });
        }
    });
});

// 보고서 데이터 로드 및 표시
async function loadReportData() {
    try {
        showLoadingState();
        
        // 필터 값 가져오기
        const filters = getFilterValues();
        
        // 필요한 모든 데이터 병렬로 로드
        const [
            documentsData,
            statisticsData,
            comparisonData
        ] = await Promise.all([
            fetchDocuments(),
            fetchStatistics(filters),
            fetchComparisonData(filters)
        ]);
        
        // 주요 지표 업데이트
        updateMetricsCards(documentsData, statisticsData);
        
        // 브랜드별 주문 금액 차트 업데이트
        updateBrandOrderChart(documentsData);
        
        // 월별 발주 금액 추이 차트 업데이트
        updateMonthlyTrendChart(documentsData);
        
        // 품목 카테고리 차트 업데이트
        updateCategoryPieChart(documentsData);
        
        // 시즌별 발주 비율 차트 업데이트
        updateSeasonPieChart(documentsData);
        
        // 브랜드별 품목 분석 테이블 업데이트
        updateBrandAnalysisTable(documentsData);
        
        // 품목 성장률 분석 차트 업데이트
        updateGrowthRateChart(documentsData);
        
        hideLoadingState();
    } catch (error) {
        console.error('보고서 데이터 로드 오류:', error);
        showErrorMessage('데이터를 불러오는 중 오류가 발생했습니다.');
        hideLoadingState();
    }
}

// 필터 값 가져오기
function getFilterValues() {
    const startDate = document.getElementById('reportStartDate')?.value || '';
    const endDate = document.getElementById('reportEndDate')?.value || '';
    const reportType = document.getElementById('reportType')?.value || '모든 보고서';
    const dataGrouping = document.getElementById('dataGrouping')?.value || '월별';
    
    return {
        start_date: startDate,
        end_date: endDate,
        report_type: reportType,
        data_grouping: dataGrouping
    };
}

// 문서 데이터 가져오기
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
        
        // 문서 데이터 처리 및 가공
        const processedData = processDocumentData(invoiceData.invoices || [], orderData.orders || []);
        
        return {
            invoices: invoiceData.invoices || [],
            orders: orderData.orders || [],
            brands: processedData.brands,
            brandOrders: processedData.brandOrders,
            seasons: processedData.seasons,
            monthlyData: processedData.monthlyData,
            categories: processedData.categories
        };
    } catch (error) {
        console.error('문서 목록 로드 오류:', error);
        return {
            invoices: [],
            orders: [],
            brands: [],
            brandOrders: [],
            seasons: {},
            monthlyData: [],
            categories: {}
        };
    }
}

// 문서 데이터 처리 및 가공
function processDocumentData(invoices, orders) {
    // 브랜드 목록 추출
    const brandSet = new Set();
    [...invoices, ...orders].forEach(doc => {
        if (doc.brand) brandSet.add(doc.brand);
    });
    const brands = Array.from(brandSet);
    
    // 브랜드별 주문 금액 계산
    const brandOrders = {};
    brands.forEach(brand => {
        brandOrders[brand] = 0;
        
        // 해당 브랜드의 오더 문서 필터링
        const brandOrders = orders.filter(order => order.brand === brand);
        
        // 각 오더 문서의 total_amount 합산
        brandOrders.forEach(order => {
            if (order.total_amount) {
                // 'EUR 1500.00' 형식에서 숫자만 추출
                const amountMatch = order.total_amount.match(/[\d.]+/);
                if (amountMatch) {
                    brandOrders[brand] += parseFloat(amountMatch[0]);
                }
            }
        });
    });
    
    // 시즌별 발주 비율 계산
    const seasons = {};
    orders.forEach(order => {
        if (order.season) {
            // 시즌을 SS/FW 카테고리로 분류
            let seasonCategory = 'Other';
            if (order.season.includes('SS')) {
                seasonCategory = 'SS';
            } else if (order.season.includes('FW')) {
                seasonCategory = 'FW';
            }
            
            if (!seasons[seasonCategory]) seasons[seasonCategory] = 0;
            
            // 금액 추출 및 합산
            if (order.total_amount) {
                const amountMatch = order.total_amount.match(/[\d.]+/);
                if (amountMatch) {
                    seasons[seasonCategory] += parseFloat(amountMatch[0]);
                }
            }
        }
    });
    
    // 월별 데이터 가공
    const monthlyData = processMonthlyData(orders);
    
    // 품목 카테고리 데이터 가공
    const categories = processCategoryData(orders);
    
    return {
        brands,
        brandOrders,
        seasons,
        monthlyData,
        categories
    };
}

// 월별 데이터 가공
function processMonthlyData(orders) {
    // 현재 연도 및 작년 연도
    const currentYear = new Date().getFullYear();
    const lastYear = currentYear - 1;
    
    // 월별 데이터 초기화
    const monthlyData = {
        [currentYear]: Array(12).fill(0),
        [lastYear]: Array(12).fill(0)
    };
    
    // 오더 데이터로 월별 금액 합산
    orders.forEach(order => {
        if (order.created_at && order.total_amount) {
            const orderDate = new Date(order.created_at);
            const orderYear = orderDate.getFullYear();
            const orderMonth = orderDate.getMonth();
            
            // 현재 또는 작년 데이터인 경우만 처리
            if (orderYear === currentYear || orderYear === lastYear) {
                // 금액 추출 및 합산
                const amountMatch = order.total_amount.match(/[\d.]+/);
                if (amountMatch) {
                    monthlyData[orderYear][orderMonth] += parseFloat(amountMatch[0]);
                }
            }
        }
    });
    
    return monthlyData;
}

// 품목 카테고리 데이터 가공
function processCategoryData(orders) {
    // 간단한 카테고리 매핑 (실제 구현에서는 더 정확한 분류 필요)
    const categoryMap = {
        'SHIRT': '셔츠/블라우스',
        'BLOUSE': '셔츠/블라우스',
        'JEAN': '청바지/팬츠',
        'PANTS': '청바지/팬츠',
        'JACKET': '아우터',
        'COAT': '아우터',
        'SHOE': '신발',
        'SNEAKER': '신발',
        'BAG': '액세서리',
        'SCARF': '액세서리'
    };
    
    // 카테고리별 금액 합산
    const categories = {
        '셔츠/블라우스': 0,
        '청바지/팬츠': 0,
        '아우터': 0,
        '신발': 0,
        '액세서리': 0
    };
    
    // 오더 문서의 아이템 기반으로 카테고리 분류 (가상 데이터 생성)
    // 실제 구현에서는 문서의 항목 데이터를 가져와야 함
    orders.forEach(order => {
        if (order.total_amount) {
            const amountMatch = order.total_amount.match(/[\d.]+/);
            if (amountMatch) {
                const totalAmount = parseFloat(amountMatch[0]);
                
                // 간단한 예시 분배 (실제 구현에서는 실제 항목 데이터 사용)
                // 예시: 총액을 카테고리별로 임의 비율로 분배
                categories['셔츠/블라우스'] += totalAmount * 0.3;  // 30%
                categories['청바지/팬츠'] += totalAmount * 0.25;   // 25%
                categories['아우터'] += totalAmount * 0.2;         // 20%
                categories['신발'] += totalAmount * 0.15;          // 15%
                categories['액세서리'] += totalAmount * 0.1;       // 10%
            }
        }
    });
    
    return categories;
}

// 통계 데이터 가져오기
async function fetchStatistics(filters) {
    try {
        // 필터 파라미터 구성
        const params = new URLSearchParams();
        
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
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

// 비교 데이터 가져오기
async function fetchComparisonData(filters) {
    try {
        // 필터 파라미터 구성
        const params = new URLSearchParams();
        
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
        const response = await fetch(`${API_BASE_URL}/comparison-history?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error('비교 데이터를 가져오는데 실패했습니다.');
        }
        
        return await response.json();
    } catch (error) {
        console.error('비교 데이터 로드 오류:', error);
        return {
            comparisons: [],
            total_count: 0
        };
    }
}

// 주요 지표 카드 업데이트
function updateMetricsCards(documentsData, statisticsData) {
    // 총 브랜드 수 업데이트
    const totalBrandsElement = document.getElementById('totalBrands');
    if (totalBrandsElement) {
        totalBrandsElement.textContent = documentsData.brands.length || '0';
    }
    
    // 총 품목 수 업데이트 (예시 데이터)
    const totalItemsElement = document.getElementById('totalItems');
    if (totalItemsElement) {
        // 오더 문서의 수량 합계로 대체 (실제 구현에서는 실제 품목 수 계산 필요)
        const totalItems = documentsData.orders.reduce((sum, order) => sum + (order.total_quantity || 0), 0);
        totalItemsElement.textContent = totalItems;
    }
    
    // 총 발주 금액 업데이트
    const totalOrderAmountElement = document.getElementById('totalOrderAmount');
    if (totalOrderAmountElement) {
        // 모든 오더의 total_amount 합산
        let totalAmount = 0;
        documentsData.orders.forEach(order => {
            if (order.total_amount) {
                const amountMatch = order.total_amount.match(/[\d.]+/);
                if (amountMatch) {
                    totalAmount += parseFloat(amountMatch[0]);
                }
            }
        });
        
        // 금액 포맷팅 (EUR 표시 및 천 단위 구분)
        totalOrderAmountElement.textContent = `€${totalAmount.toLocaleString(undefined, {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        })}`;
        
        // 증감율 업데이트 (가상 데이터)
        const deltaElement = document.getElementById('orderAmountDelta');
        if (deltaElement) {
            // 10% 증가로 가정 (실제 구현에서는 이전 기간과 비교 필요)
            deltaElement.textContent = '+10.5%';
            deltaElement.classList.add('positive');
        }
    }
    
    // 총 주문 건수 업데이트
    const totalOrdersElement = document.getElementById('totalOrders');
    if (totalOrdersElement) {
        totalOrdersElement.textContent = documentsData.orders.length;
        
        // 증감율 업데이트 (가상 데이터)
        const deltaElement = document.getElementById('ordersDelta');
        if (deltaElement) {
            // 8.7% 증가로 가정 (실제 구현에서는 이전 기간과 비교 필요)
            deltaElement.textContent = '+8.7%';
            deltaElement.classList.add('positive');
        }
    }
}

// 브랜드별 주문 금액 차트 업데이트
function updateBrandOrderChart(documentsData) {
    const ctx = document.getElementById('brandOrderChart');
    if (!ctx) return;
    
    // 브랜드 및 금액 데이터 추출
    const brands = documentsData.brands;
    const brandAmounts = brands.map(brand => documentsData.brandOrders[brand] || 0);
    
    // 기존 차트 인스턴스 확인 및 파괴
    if (window.brandOrderChartInstance) {
        window.brandOrderChartInstance.destroy();
    }
    
    // 새로운 차트 생성
    window.brandOrderChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: brands,
            datasets: [{
                label: '주문 금액 (EUR)',
                data: brandAmounts,
                backgroundColor: [
                    '#4263eb', '#6741d9', '#f03e3e', '#f76707', '#2b8a3e'
                ],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '€' + value.toLocaleString();
                        }
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
                            return '€' + context.raw.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// 월별 발주 금액 추이 차트 업데이트
function updateMonthlyTrendChart(documentsData) {
    const ctx = document.getElementById('monthlyTrendChart');
    if (!ctx) return;
    
    // 월별 라벨 생성
    const months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    
    // 연도 가져오기
    const currentYear = new Date().getFullYear();
    const lastYear = currentYear - 1;
    
    // 월별 데이터 가져오기
    const currentYearData = documentsData.monthlyData[currentYear] || Array(12).fill(0);
    const lastYearData = documentsData.monthlyData[lastYear] || Array(12).fill(0);
    
    // 기존 차트 인스턴스 확인 및 파괴
    if (window.monthlyTrendChartInstance) {
        window.monthlyTrendChartInstance.destroy();
    }
    
    // 새로운 차트 생성
    window.monthlyTrendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [
                {
                    label: `${currentYear}년`,
                    data: currentYearData,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: '#2196F3',
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: `${lastYear}년`,
                    data: lastYearData,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: '#4CAF50',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '€' + value.toLocaleString();
                        }
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
                    position: 'top',
                    align: 'end'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': €' + context.raw.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    // 범례 업데이트
    updateMonthlyTrendLegend(currentYear, lastYear);
}

// 월별 발주 금액 추이 범례 업데이트
function updateMonthlyTrendLegend(currentYear, lastYear) {
    const legendContainer = document.getElementById('monthlyTrendLegend');
    if (!legendContainer) return;
    
    // 범례 HTML 생성
    legendContainer.innerHTML = `
        <div class="legend-item">
            <span class="legend-color" style="background-color: #2196F3;"></span>
            <span>${currentYear}년</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #4CAF50;"></span>
            <span>${lastYear}년</span>
        </div>
    `;
}

// 품목 카테고리 파이 차트 업데이트
function updateCategoryPieChart(documentsData) {
    const ctx = document.getElementById('categoryPieChart');
    if (!ctx) return;
    
    // 카테고리 및 금액 데이터 추출
    const categories = Object.keys(documentsData.categories);
    const categoryAmounts = categories.map(category => documentsData.categories[category]);
    
    // 각 카테고리의 백분율 계산
    const total = categoryAmounts.reduce((sum, value) => sum + value, 0);
    const percentages = categoryAmounts.map(value => ((value / total) * 100).toFixed(1));
    
    // 색상 배열
    const colors = ['#4CAF50', '#2196F3', '#FFC107', '#FF5722', '#9C27B0'];
    
    // 기존 차트 인스턴스 확인 및 파괴
    if (window.categoryChartInstance) {
        window.categoryChartInstance.destroy();
    }
    
    // 새로운 차트 생성
    window.categoryChartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                data: percentages,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map(function(label, i) {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label} (${value}%)`,
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
                            return `${label}: ${value}%`;
                        }
                    }
                }
            }
        }
    });
}

// 시즌별 발주 비율 파이 차트 업데이트
function updateSeasonPieChart(documentsData) {
    const ctx = document.getElementById('seasonPieChart');
    if (!ctx) return;
    
    // 시즌 데이터 추출
    const seasons = Object.keys(documentsData.seasons);
    const seasonAmounts = seasons.map(season => documentsData.seasons[season]);
    
    // 각 시즌의 백분율 계산
    const total = seasonAmounts.reduce((sum, value) => sum + value, 0);
    const percentages = seasonAmounts.map(value => ((value / total) * 100).toFixed(1));
    
    // 색상 배열
    const colors = ['#FF9800', '#03A9F4']; // SS, FW 색상
    
    // 기존 차트 인스턴스 확인 및 파괴
    if (window.seasonChartInstance) {
        window.seasonChartInstance.destroy();
    }
    
    // 새로운 차트 생성
    window.seasonChartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: seasons,
            datasets: [{
                data: percentages,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map(function(label, i) {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label} (${value}%)`,
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
                            return `${label}: ${value}%`;
                        }
                    }
                }
            }
        }
    });
}

// 브랜드별 품목 분석 테이블 업데이트
function updateBrandAnalysisTable(documentsData) {
    const tableBody = document.getElementById('brandAnalysisTableBody');
    const tableFoot = document.getElementById('brandAnalysisTableFoot');
    
    if (!tableBody || !tableFoot) return;
    
    // 브랜드 목록
    const brands = documentsData.brands;
    
    // 카테고리별 합계 초기화
    const totals = {
        '셔츠/블라우스': 0,
        '청바지/팬츠': 0,
        '아우터': 0,
        '신발': 0,
        '액세서리': 0,
        '총계': 0
    };
    
    // 테이블 초기화
    tableBody.innerHTML = '';
    
    // 브랜드별 카테고리 금액 계산 (간소화된 버전)
    brands.forEach(brand => {
        // 해당 브랜드 오더 필터링
        const brandOrders = documentsData.orders.filter(order => order.brand === brand);
        
        // 총 금액 계산
        let totalAmount = 0;
        brandOrders.forEach(order => {
            if (order.total_amount) {
                const amountMatch = order.total_amount.match(/[\d.]+/);
                if (amountMatch) {
                    totalAmount += parseFloat(amountMatch[0]);
                }
            }
        });
        
        // 간소화된 카테고리별 분배 (실제 구현에서는 실제 품목 데이터 사용)
        const shirtAmount = totalAmount * 0.3;  // 30%
        const pantsAmount = totalAmount * 0.25; // 25%
        const outerAmount = totalAmount * 0.2;  // 20%
        const shoesAmount = totalAmount * 0.15; // 15%
        const accAmount = totalAmount * 0.1;    // 10%
        
        // 합계에 더하기
        totals['셔츠/블라우스'] += shirtAmount;
        totals['청바지/팬츠'] += pantsAmount;
        totals['아우터'] += outerAmount;
        totals['신발'] += shoesAmount;
        totals['액세서리'] += accAmount;
        totals['총계'] += totalAmount;
        
       // 비교 (증감율) 계산 - 가상 데이터
       let deltaText = '';
       let deltaClass = '';
       
       // 간소화된 랜덤 증감율 (실제 구현에서는 이전 기간과 비교 필요)
       const randomDelta = (Math.random() * 40 - 10).toFixed(0);
       
       if (parseInt(randomDelta) >= 0) {
           deltaText = `+${randomDelta}%`;
           deltaClass = 'trend-up';
       } else {
           deltaText = `${randomDelta}%`;
           deltaClass = 'trend-down';
       }
       
       // 테이블 행 추가
       const rowHtml = `
           <tr>
               <td class="brand-name">${brand}</td>
               <td>€${shirtAmount.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
               <td>€${pantsAmount.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
               <td>€${outerAmount.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
               <td>€${shoesAmount.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
               <td>€${accAmount.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
               <td>€${totalAmount.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
               <td><span class="${deltaClass}">${deltaText}</span></td>
           </tr>
       `;
       
       tableBody.insertAdjacentHTML('beforeend', rowHtml);
   });
   
   // 테이블 푸터 (합계) 업데이트
   const footerHtml = `
       <tr>
           <td>총계</td>
           <td>€${totals['셔츠/블라우스'].toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
           <td>€${totals['청바지/팬츠'].toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
           <td>€${totals['아우터'].toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
           <td>€${totals['신발'].toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
           <td>€${totals['액세서리'].toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
           <td>€${totals['총계'].toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
           <td><span class="trend-up">+10.5%</span></td>
       </tr>
   `;
   
   tableFoot.innerHTML = footerHtml;
}

// 품목 성장률 분석 차트 업데이트
function updateGrowthRateChart(documentsData) {
   const ctx = document.getElementById('growthRateChart');
   if (!ctx) return;
   
   // 카테고리 목록
   const categories = Object.keys(documentsData.categories);
   
   // 가상의 성장률 데이터 (실제 구현에서는 이전 기간과 비교 필요)
   const growthRates = [
       { category: '액세서리', growth: 28 },
       { category: '신발', growth: 18 },
       { category: '아우터', growth: 5 },
       { category: '청바지/팬츠', growth: 2 },
       { category: '셔츠/블라우스', growth: -3 }
   ];
   
   // 데이터 정렬 (성장률 기준 내림차순)
   growthRates.sort((a, b) => b.growth - a.growth);
   
   // 정렬된 카테고리 및 성장률 추출
   const sortedCategories = growthRates.map(item => item.category);
   const sortedGrowthRates = growthRates.map(item => item.growth);
   
   // 색상 배열
   const barColors = sortedGrowthRates.map(rate => 
       rate >= 0 ? '#4CAF50' : '#F44336'
   );
   
   // 기존 차트 인스턴스 확인 및 파괴
   if (window.growthRateChartInstance) {
       window.growthRateChartInstance.destroy();
   }
   
   // 새로운 차트 생성
   window.growthRateChartInstance = new Chart(ctx, {
       type: 'bar',
       data: {
           labels: sortedCategories,
           datasets: [{
               label: '성장률',
               data: sortedGrowthRates,
               backgroundColor: barColors,
               borderWidth: 0,
               borderRadius: 4
           }]
       },
       options: {
           indexAxis: 'y',  // 수평 막대 차트
           responsive: true,
           maintainAspectRatio: false,
           scales: {
               x: {
                   beginAtZero: true,
                   suggestedMin: -10,
                   suggestedMax: 30,
                   ticks: {
                       callback: function(value) {
                           return value + '%';
                       }
                   }
               },
               y: {
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
                           const value = context.raw;
                           return (value >= 0 ? '+' : '') + value + '%';
                       }
                   }
               }
           }
       }
   });
}

// 시즌 시간 옵션 업데이트
function updateSeasonOptions() {
   const seasonSelect = document.getElementById('seasonFilter');
   if (!seasonSelect) return;
   
   // 기존 시즌 옵션 제거 (첫 번째 옵션 제외)
   while (seasonSelect.options.length > 1) {
       seasonSelect.remove(1);
   }
   
   // 현재 연도 및 이전 연도
   const currentYear = new Date().getFullYear();
   
   // 시즌 옵션 추가
   for (let year = currentYear; year >= currentYear - 2; year--) {
       seasonSelect.add(new Option(`${year}SS`, `${year}SS`));
       seasonSelect.add(new Option(`${year}FW`, `${year}FW`));
   }
}

// 뷰 전환 함수
function switchView(viewType) {
   // 차트 컨테이너와 테이블 컨테이너
   const chartContainers = document.querySelectorAll('.chart-container, .report-charts');
   const tableContainer = document.querySelector('.brand-analysis');
   const summaryContainer = document.querySelector('.metrics-cards');
   
   // 뷰 타입에 따라 요소 표시/숨김
   switch (viewType) {
       case 'chart':
           // 차트만 표시
           chartContainers.forEach(container => container.style.display = 'block');
           tableContainer.style.display = 'block';
           summaryContainer.style.display = 'flex';
           break;
           
       case 'table':
           // 테이블만 표시
           chartContainers.forEach(container => container.style.display = 'none');
           tableContainer.style.display = 'block';
           summaryContainer.style.display = 'none';
           break;
           
       case 'summary':
           // 요약만 표시
           chartContainers.forEach(container => container.style.display = 'none');
           tableContainer.style.display = 'none';
           summaryContainer.style.display = 'flex';
           break;
           
       default:
           // 기본: 모두 표시
           chartContainers.forEach(container => container.style.display = 'block');
           tableContainer.style.display = 'block';
           summaryContainer.style.display = 'flex';
   }
}

// 보고서 생성 및 다운로드
function generateAndDownloadReport() {
   alert('보고서 다운로드 기능은 개발 중입니다.');
   // 추후 구현: 현재 보고서 데이터를 Excel/PDF로 변환하여 다운로드
}

// 차트 다운로드
function downloadChart(chartId) {
   const chart = document.getElementById(chartId);
   if (!chart) return;
   
   alert(`${chartId} 차트 다운로드 기능은 개발 중입니다.`);
   // 추후 구현: 차트를 이미지로 변환하여 다운로드
}

// 로딩 상태 표시
function showLoadingState() {
   // 주요 지표 카드
   document.querySelectorAll('.metric-value').forEach(el => {
       el.classList.add('loading');
       el.dataset.originalText = el.textContent;
       el.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
   });
   
   // 테이블
   const tableBody = document.getElementById('brandAnalysisTableBody');
   if (tableBody) {
       tableBody.innerHTML = `
           <tr>
               <td colspan="8">
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
   // 테이블 영역 사용
   const tableBody = document.getElementById('brandAnalysisTableBody');
   if (tableBody) {
       tableBody.innerHTML = `
           <tr>
               <td colspan="8">
                   <div class="error-message">
                       <i class="fas fa-exclamation-circle"></i> ${message}
                   </div>
               </td>
           </tr>
       `;
   }
}