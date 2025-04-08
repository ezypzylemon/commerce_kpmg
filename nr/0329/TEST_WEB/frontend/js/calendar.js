// calendar.js - 거래처 및 일정 관리 페이지 스크립트

// API 기본 URL 설정 (개발 환경)
const API_BASE_URL = 'http://localhost:5000/orders';

// 브랜드별 색상 매핑
const BRAND_COLORS = {
    'TOGA VIRILIS': '#4263eb',    // 파란색
    'WILD DONKEY': '#2b8a3e',     // 초록색
    'ATHLETICS FTWR': '#e8590c',  // 주황색
    'BASERANGE': '#7950f2',       // 보라색
    'NOU NOU': '#e03131',         // 빨간색
    'default': '#868e96'          // 기본 회색
};

// 캘린더 데이터
let currentDate = new Date();
let calendarEvents = [];          // 캘린더에 표시할 이벤트 배열
let matchedDocumentPairs = [];    // 일치하는 문서 쌍 배열
let allInvoices = [];             // 모든 인보이스 문서
let allOrders = [];               // 모든 오더시트 문서

document.addEventListener('DOMContentLoaded', function() {
    // 캘린더 초기화
    initCalendar();
    
    // 데이터 로드
    loadData();
    
    // 이벤트 리스너 추가
    document.getElementById('prevMonth').addEventListener('click', function() {
        changeMonth(-1);
    });
    
    document.getElementById('nextMonth').addEventListener('click', function() {
        changeMonth(1);
    });
    
    // 필터 적용 버튼
    const filterButton = document.querySelector('.sidebar-filters .btn-primary');
    if (filterButton) {
        filterButton.addEventListener('click', function() {
            applyFilters();
        });
    }
    
    // 검색 기능
    const searchInput = document.getElementById('searchClient');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const searchText = this.value.toLowerCase();
                filterTransactionsBySearch(searchText);
            }
        });
    }
    
    // 차트 초기화 (빈 데이터로)
    initCharts();
});

// 캘린더 초기화
function initCalendar() {
    updateCalendarHeader();
    renderCalendar();
}

// 캘린더 헤더 업데이트 (연월 표시)
function updateCalendarHeader() {
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    document.getElementById('currentMonth').textContent = `${currentDate.getFullYear()}년 ${monthNames[currentDate.getMonth()]}`;
}

// 캘린더 렌더링
function renderCalendar() {
    const calendarDays = document.getElementById('calendar-days');
    calendarDays.innerHTML = ''; // 기존 내용 초기화
    
    // 현재 월의 첫날과 마지막날
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    
    // 첫날의 요일 (0: 일요일, 6: 토요일)
    const firstDayOfWeek = firstDay.getDay();
    
    // 이전 달의 마지막 날짜들
    const lastMonthLastDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate();
    
    // 이전 달의 날짜 표시
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const dayElement = createDayElement(lastMonthLastDay - i, true);
        calendarDays.appendChild(dayElement);
    }
    
    // 현재 달의 날짜 표시
    for (let i = 1; i <= lastDay.getDate(); i++) {
        const isToday = isCurrentDay(i);
        const dayElement = createDayElement(i, false, isToday);
        
        // 해당 날짜의 이벤트 추가
        const currentDateStr = formatDate(new Date(currentDate.getFullYear(), currentDate.getMonth(), i));
        const dayEvents = calendarEvents.filter(event => event.date === currentDateStr);
        
        // 이벤트 추가
        dayEvents.forEach(event => {
            const eventElement = createEventElement(event);
            dayElement.appendChild(eventElement);
        });
        
        calendarDays.appendChild(dayElement);
    }
    
    // 다음 달의 시작 날짜들 (필요한 경우)
    const totalDaysDisplayed = firstDayOfWeek + lastDay.getDate();
    const remainingDays = 42 - totalDaysDisplayed; // 6주 * 7일 = 42 (최대 달력 표시 일수)
    
    for (let i = 1; i <= remainingDays; i++) {
        if (totalDaysDisplayed + i <= 35) { // 5주까지만 표시
            const dayElement = createDayElement(i, true, false, true);
            calendarDays.appendChild(dayElement);
        }
    }
}

// 날짜 요소 생성
function createDayElement(day, isInactive, isToday = false, isNextMonth = false) {
    const dayElement = document.createElement('div');
    dayElement.className = 'calendar-day';
    if (isInactive) {
        dayElement.classList.add('inactive');
    }
    if (isToday) {
        dayElement.classList.add('today');
    }
    
    // 날짜 숫자
    const dayNumberElement = document.createElement('span');
    dayNumberElement.textContent = day;
    dayElement.appendChild(dayNumberElement);
    
    // data-date 속성 추가
    let year = currentDate.getFullYear();
    let month = currentDate.getMonth();
    
    if (isInactive && !isNextMonth) {
        // 이전 달
        if (month === 0) {
            month = 11;
            year--;
        } else {
            month--;
        }
    } else if (isInactive && isNextMonth) {
        // 다음 달
        if (month === 11) {
            month = 0;
            year++;
        } else {
            month++;
        }
    }
    
    const dateObj = new Date(year, month, day);
    dayElement.setAttribute('data-date', formatDate(dateObj));
    
    return dayElement;
}

// 이벤트 요소 생성
function createEventElement(event) {
    const eventElement = document.createElement('div');
    eventElement.className = `calendar-event ${event.type}`;
    eventElement.style.backgroundColor = event.color || BRAND_COLORS['default'];
    eventElement.textContent = event.title;
    
    // 툴팁 추가 (상세 정보)
    eventElement.title = `${event.title}\n${event.date}\n${event.description || ''}`;
    
    // 클릭 이벤트 추가
    eventElement.addEventListener('click', function(e) {
        e.stopPropagation();
        showEventDetails(event);
    });
    
    return eventElement;
}

// 현재 날짜인지 확인
function isCurrentDay(day) {
    const today = new Date();
    return currentDate.getFullYear() === today.getFullYear() && 
           currentDate.getMonth() === today.getMonth() && 
           day === today.getDate();
}

// 날짜 형식 변환 (YYYY-MM-DD)
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 문자열 날짜를 Date 객체로 변환 (다양한 형식 지원)
function parseDate(dateString) {
    if (!dateString) return null;
    
    dateString = dateString.trim();
    
    // MM/DD/YYYY 형식
    const usFormat = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
    const usMatch = dateString.match(usFormat);
    if (usMatch) {
        const [_, month, day, year] = usMatch;
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
    
    // DD-MM-YYYY 형식
    const euFormat = /^(\d{1,2})-(\d{1,2})-(\d{4})$/;
    const euMatch = dateString.match(euFormat);
    if (euMatch) {
        const [_, day, month, year] = euMatch;
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
    
    // YYYY-MM-DD 형식
    const isoFormat = /^(\d{4})-(\d{1,2})-(\d{1,2})$/;
    const isoMatch = dateString.match(isoFormat);
    if (isoMatch) {
        const [_, year, month, day] = isoMatch;
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
    
    // 기타 형식은 Date 생성자로 시도
    return new Date(dateString);
}

// 월 변경
function changeMonth(offset) {
    currentDate.setMonth(currentDate.getMonth() + offset);
    updateCalendarHeader();
    renderCalendar();
}

// 데이터 로드
async function loadData() {
    try {
        // 인보이스 데이터 로드
        const invoiceResponse = await fetch(`${API_BASE_URL}/documents/invoice`);
        const invoiceData = await invoiceResponse.json();
        allInvoices = invoiceData.invoices || [];
        
        // 오더시트 데이터 로드
        const orderResponse = await fetch(`${API_BASE_URL}/documents/order`);
        const orderData = await orderResponse.json();
        allOrders = orderData.orders || [];
        
        // 이벤트 데이터 생성
        await processDocuments();
        
        // 캘린더에 이벤트 표시
        renderCalendar();
        
        // 차트 업데이트
        updateCharts();
        
        // 거래처 목록 업데이트
        renderTransactionList();
        
        // 통계 지표 업데이트
        updateMetrics();
        
    } catch (error) {
        console.error('데이터 로드 중 오류 발생:', error);
        showError('데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

// 문서 처리 및 일치하는 항목 찾기
async function processDocuments() {
    try {
        calendarEvents = []; // 이벤트 초기화
        matchedDocumentPairs = []; // 일치 문서 쌍 초기화
        
        console.log(`인보이스 개수: ${allInvoices.length}, 오더시트 개수: ${allOrders.length}`);
        
        // 처리된 쌍을 추적하기 위한 셋
        const processedPairs = new Set();
        
        // 가능한 모든 인보이스와 오더시트 조합에 대해 비교
        for (const invoice of allInvoices) {
            for (const order of allOrders) {
                // 두 문서가 같은 브랜드에 속하는지 확인 (최적화)
                if (invoice.brand === order.brand) {
                    // 이미 처리된 쌍인지 확인
                    const pairKey = `${invoice.id}_${order.id}`;
                    if (processedPairs.has(pairKey)) {
                        console.log(`이미 처리된 쌍 건너뜀: ${pairKey}`);
                        continue;
                    }
                    
                    processedPairs.add(pairKey);
                    
                    try {
                        console.log(`문서 비교 시도: ${invoice.id} vs ${order.id}`);
                        // 문서 비교 API 호출
                        const compareResponse = await fetch(`${API_BASE_URL}/compare/${invoice.id}/${order.id}`);
                        const compareResult = await compareResponse.json();
                        
                        // 비교 결과에서 완전 일치 항목 확인
                        const matchPercentage = compareResult.summary.match_percentage;
                        console.log(`비교 결과: ${invoice.id} vs ${order.id} = ${matchPercentage}%`);
                        
                        // 일치율이 100%인 문서 쌍만 처리
                        // 디버깅을 위해 80% 이상도 허용하도록 임시 변경
                        if (matchPercentage >= 80) {
                            console.log(`일치하는 문서 쌍 발견: ${invoice.id} vs ${order.id}, 일치율: ${matchPercentage}%`);
                            // 일치하는 문서 쌍 추가
                            matchedDocumentPairs.push({
                                invoice,
                                order,
                                matches: compareResult.matches,
                                brand: invoice.brand
                            });
                            
                            // 이 시점에서 개별 항목에 대한 선적 정보를 가져오기 위해
                            // 오더 문서의 상세 정보를 가져옴
                            const orderDetailResponse = await fetch(`${API_BASE_URL}/document/${order.id}`);
                            const orderDetail = await orderDetailResponse.json();
                            
                            // 각 일치 항목에 대해 이벤트 생성
                            if (orderDetail.items && orderDetail.items.length > 0) {
                                // 제품별로 그룹화하기 위한 맵
                                const shipDateMap = {};
                                
                                // 각 항목의 선적 날짜 정보 수집
                                orderDetail.items.forEach(item => {
                                    // 날짜 확인 및 형식 변환
                                    const startDate = parseDate(item.shipping_start);
                                    const endDate = parseDate(item.shipping_end);
                                    
                                    // 유효한 날짜인 경우에만 처리
                                    if (startDate) {
                                        const dateStr = formatDate(startDate);
                                        if (!shipDateMap[dateStr]) {
                                            shipDateMap[dateStr] = {
                                                date: dateStr,
                                                type: 'start',
                                                items: [],
                                                brand: invoice.brand
                                            };
                                        }
                                        shipDateMap[dateStr].items.push(item);
                                    }
                                    
                                    if (endDate) {
                                        const dateStr = formatDate(endDate);
                                        if (!shipDateMap[dateStr]) {
                                            shipDateMap[dateStr] = {
                                                date: dateStr,
                                                type: 'end',
                                                items: [],
                                                brand: invoice.brand
                                            };
                                        }
                                        // 도착일이 다른 경우만 추가
                                        if (formatDate(startDate) !== formatDate(endDate)) {
                                            shipDateMap[dateStr].items.push(item);
                                        }
                                    }
                                });
                                
                                // 수집된 데이터로 이벤트 생성
                                for (const dateKey in shipDateMap) {
                                    const shipData = shipDateMap[dateKey];
                                    if (shipData.items.length > 0) {
                                        // 첫 번째 항목 정보 사용
                                        const firstItem = shipData.items[0];
                                        const otherItemsCount = shipData.items.length - 1;
                                        
                                        // 이벤트 텍스트 생성 (간결하게)
                                        const modelCode = firstItem.model_code || ''; 
                                        const modelName = firstItem.model_name || '';
                                        
                                        // 모델명이 있으면 그것을 우선적으로 사용, 없으면 모델코드 사용
                                        let itemName = '';
                                        if (modelName && modelName.length > 0) {
                                            // 모델명이 있는 경우 간결하게 표시
                                            if (modelName.includes('-')) {
                                                // 하이픈이 있는 경우 앞부분만 사용
                                                itemName = modelName.split('-')[0];
                                            } else {
                                                // 10자로 제한
                                                itemName = modelName.length > 10 ? modelName.substring(0, 10) + '...' : modelName;
                                            }
                                        } else if (modelCode) {
                                            itemName = modelCode;
                                        } else {
                                            itemName = '상품';
                                        }
                                        
                                        // 브랜드명 처리
                                        let brandName = shipData.brand || '';
                                        
                                        // '자동 감지'인 경우 다른 데이터에서 브랜드 추출 시도
                                        if (brandName === '자동 감지' || !brandName) {
                                            // 모델명에서 브랜드 추출 시도
                                            const modelName = firstItem.model_name || '';
                                            
                                            // 모델명에 특정 브랜드명이 포함되어 있는지 확인
                                            if (modelName.includes('TOGA')) {
                                                brandName = 'TOGA';
                                            } else if (modelName.includes('WILD')) {
                                                brandName = 'WILD';
                                            } else if (modelName.includes('ATHLETICS')) {
                                                brandName = 'ATHL';
                                            } else if (modelName.includes('BASERANGE')) {
                                                brandName = 'BASE';
                                            } else if (modelName.includes('NOU')) {
                                                brandName = 'NOUN';
                                            } else {
                                                // 모델 코드에서 브랜드 판별 시도
                                                const modelCode = firstItem.model_code || '';
                                                if (modelCode.startsWith('AJ')) {
                                                    brandName = 'TOGA'; // 예시: AJ로 시작하는 코드는 TOGA 브랜드로 가정
                                                } else if (modelCode.startsWith('WD')) {
                                                    brandName = 'WILD';
                                                } else {
                                                    brandName = 'ITEM'; // 추출 실패 시 기본값
                                                }
                                            }
                                        } else {
                                            // 브랜드명이 있으면 첫 4글자만 사용
                                            brandName = brandName.substring(0, 4);
                                        }
                                        
                                        // 짧고 간결한 이벤트 제목 생성
                                        let eventTitle = `${brandName}-${itemName}`;
                                        if (otherItemsCount > 0) {
                                            eventTitle += ` 외${otherItemsCount}`;
                                        }
                                        
                                        // 이벤트 타입에 따른 아이콘 추가
                                        if (shipData.type === 'start') {
                                            eventTitle += '↗'; // 출발 아이콘
                                        } else {
                                            eventTitle += '↘'; // 도착 아이콘
                                        }
                                        
                                        // 브랜드 정보는 툴팁에만 포함
                                        
                                        // 이벤트 색상 결정
                                        const eventColor = BRAND_COLORS[shipData.brand] || BRAND_COLORS['default'];
                                        
                                        // 이벤트 객체 생성
                                        const calendarEvent = {
                                            date: shipData.date,
                                            title: eventTitle,
                                            type: shipData.type === 'start' ? 'pending' : 'complete',
                                            color: eventColor,
                                            brand: shipData.brand,
                                            description: `${shipData.items.length}개 품목`,
                                            items: shipData.items,
                                            document: {
                                                invoice_id: invoice.id,
                                                order_id: order.id
                                            }
                                        };
                                        
                                        // 이벤트 배열에 추가
                                        calendarEvents.push(calendarEvent);
                                    }
                                }
                            }
                        } else {
                            console.log(`일치하지 않는 문서 쌍: ${invoice.id} vs ${order.id}, 일치율: ${matchPercentage}%`);
                        }
                    } catch (compareError) {
                        console.warn(`${invoice.id}와 ${order.id} 비교 중 오류:`, compareError);
                    }
                }
            }
        }
        
        console.log(`총 ${calendarEvents.length}개의 이벤트가 생성되었습니다.`);
        
    } catch (error) {
        console.error('문서 처리 중 오류 발생:', error);
        throw error;
    }
}

// 차트 초기화
function initCharts() {
    // 거래처별 거래 비율 차트
    const clientChartCtx = document.getElementById('clientChart').getContext('2d');
    window.clientChart = new Chart(clientChartCtx, {
        type: 'pie',
        data: {
            labels: ['데이터 로딩 중...'],
            datasets: [{
                data: [1],
                backgroundColor: ['#e9ecef']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
    
    // 거래 유형별 비율 차트
    const transactionChartCtx = document.getElementById('transactionChart').getContext('2d');
    window.transactionChart = new Chart(transactionChartCtx, {
        type: 'doughnut',
        data: {
            labels: ['데이터 로딩 중...'],
            datasets: [{
                data: [1],
                backgroundColor: ['#e9ecef']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// 차트 업데이트
function updateCharts() {
    // 브랜드별 이벤트 수 계산
    const brandCountMap = {};
    for (const event of calendarEvents) {
        if (!brandCountMap[event.brand]) {
            brandCountMap[event.brand] = 0;
        }
        brandCountMap[event.brand]++;
    }
    
    // 차트 데이터 변환
    const brands = Object.keys(brandCountMap);
    const brandCounts = brands.map(brand => brandCountMap[brand]);
    const brandColors = brands.map(brand => BRAND_COLORS[brand] || BRAND_COLORS['default']);
    
    // 거래처별 거래 비율 차트 업데이트
    if (window.clientChart) {
        window.clientChart.data.labels = brands;
        window.clientChart.data.datasets[0].data = brandCounts;
        window.clientChart.data.datasets[0].backgroundColor = brandColors;
        window.clientChart.update();
    }
    
    // 이벤트 유형별 카운트
    const typeCountMap = {
        '출발': 0,
        '도착': 0
    };
    
    for (const event of calendarEvents) {
        if (event.type === 'pending') {
            typeCountMap['출발']++;
        } else if (event.type === 'complete') {
            typeCountMap['도착']++;
        }
    }
    
    // 거래 유형별 차트 업데이트
    if (window.transactionChart) {
        window.transactionChart.data.labels = Object.keys(typeCountMap);
        window.transactionChart.data.datasets[0].data = Object.values(typeCountMap);
        window.transactionChart.data.datasets[0].backgroundColor = ['#4dabf7', '#40c057'];
        window.transactionChart.update();
    }
}

// 거래처 목록 렌더링
function renderTransactionList() {
    const tbody = document.getElementById('transactionData');
    if (!tbody) return;
    
    // 테이블 초기화
    tbody.innerHTML = '';
    
    // 일치 문서가 없는 경우
    if (matchedDocumentPairs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="5" class="text-center">일치하는 문서가 없습니다.</td>
        `;
        tbody.appendChild(row);
        return;
    }
    
    // 최근 10개 문서만 표시
    const recentPairs = [...matchedDocumentPairs].sort((a, b) => {
        const dateA = new Date(a.order.created_at);
        const dateB = new Date(b.order.created_at);
        return dateB - dateA; // 최신순 정렬
    }).slice(0, 10);
    
    // 테이블 행 추가
    recentPairs.forEach(pair => {
        const row = document.createElement('tr');
        
        // created_at 날짜 포맷팅
        const createdDate = new Date(pair.order.created_at);
        const formattedDate = `${createdDate.getFullYear()}-${String(createdDate.getMonth() + 1).padStart(2, '0')}-${String(createdDate.getDate()).padStart(2, '0')}`;
        
        row.innerHTML = `
            <td>${pair.brand}</td>
            <td>${formattedDate}</td>
            <td>${pair.matches.length}개 품목 일치</td>
            <td><span class="status-badge complete">완료</span></td>
            <td>
                <button class="btn btn-icon btn-sm view-btn" data-invoice="${pair.invoice.id}" data-order="${pair.order.id}">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-icon btn-sm download-btn" data-filename="${pair.order.excel_filename}">
                    <i class="fas fa-download"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // 테이블 행에 이벤트 리스너 추가
    addTableRowEventListeners();
}

// 테이블 행 이벤트 리스너 추가
function addTableRowEventListeners() {
    // 보기 버튼
    const viewButtons = document.querySelectorAll('.view-btn');
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const invoiceId = this.getAttribute('data-invoice');
            const orderId = this.getAttribute('data-order');
            window.location.href = `orders.html?doc=${orderId}`;
        });
    });
    
    // 다운로드 버튼
    const downloadButtons = document.querySelectorAll('.download-btn');
    downloadButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filename = this.getAttribute('data-filename');
            if (filename) {
                window.open(`${API_BASE_URL}/download/${filename}`, '_blank');
            }
        });
    });
}

// 이벤트 상세 정보 표시
function showEventDetails(event) {
    alert(`
        ${event.title}
        날짜: ${event.date}
        브랜드: ${event.brand}
        ${event.description}
        
        문서 ID: 
        - 인보이스: ${event.document.invoice_id}
        - 오더시트: ${event.document.order_id}
    `);
}

// 필터 적용
function applyFilters() {
    // 날짜 범위 가져오기
    const dateInputs = document.querySelectorAll('.date-inputs input');
    let startDate = null;
    let endDate = null;
    
    if (dateInputs.length >= 2) {
        startDate = dateInputs[0].value ? new Date(dateInputs[0].value) : null;
        endDate = dateInputs[1].value ? new Date(dateInputs[1].value) : null;
    }
    
    // 브랜드 필터 가져오기
    const selectedBrands = [];
    const brandAll = document.getElementById('brand-all');
    const brandCheckboxes = document.querySelectorAll('.checkbox-list input[id^="brand-"]:not(#brand-all)');
    
    if (brandAll && !brandAll.checked) {
        brandCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                // ID에서 브랜드 이름 추출 (예: brand-toga -> TOGA VIRILIS)
                const brandId = checkbox.id.replace('brand-', '');
                if (brandId === 'toga') selectedBrands.push('TOGA VIRILIS');
                else if (brandId === 'wild') selectedBrands.push('WILD DONKEY');
                else if (brandId === 'athletics') selectedBrands.push('ATHLETICS FTWR');
                else if (brandId === 'baserange') selectedBrands.push('BASERANGE');
                else if (brandId === 'nounou') selectedBrands.push('NOU NOU');
            }
        });
    }
    
    // 상태 필터 가져오기
    const selectedStatuses = [];
    const statusAll = document.getElementById('status-all');
    const statusCheckboxes = document.querySelectorAll('.checkbox-list input[id^="status-"]:not(#status-all)');
    
    if (statusAll && !statusAll.checked) {
        statusCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const statusId = checkbox.id.replace('status-', '');
                selectedStatuses.push(statusId);
            }
        });
    }
    
    // 필터링된 이벤트로 캘린더 재렌더링
    const filteredEvents = calendarEvents.filter(event => {
        const eventDate = parseDate(event.date);
        
        // 날짜 필터
        if (startDate && endDate) {
            if (eventDate < startDate || eventDate > endDate) {
                return false;
            }
        }
        
        // 브랜드 필터
        if (selectedBrands.length > 0 && !selectedBrands.includes(event.brand)) {
            return false;
        }
        
        // 상태 필터
        if (selectedStatuses.length > 0) {
            // 상태 매핑
            const eventStatus = 
                event.type === 'pending' ? 'progress' :
                event.type === 'complete' ? 'complete' : 'review';
            
            if (!selectedStatuses.includes(eventStatus)) {
                return false;
            }
        }
        
        return true;
    });
    
    // 필터링된 이벤트 적용
    calendarEvents = filteredEvents;
    renderCalendar();
    
    // 테이블 필터링 및 업데이트
    renderTransactionList();
}

// 검색어로 거래 필터링
function filterTransactionsBySearch(searchText) {
    if (!searchText) {
        // 검색어가 없으면 모든 항목 표시
        renderTransactionList();
        return;
    }
    
    // 검색어를 포함하는 브랜드 찾기
    const filteredPairs = matchedDocumentPairs.filter(pair => {
        return pair.brand.toLowerCase().includes(searchText);
    });
    
    // 임시로 전역 변수 보존
    const originalPairs = [...matchedDocumentPairs];
    matchedDocumentPairs = filteredPairs;
    
    // 목록 업데이트
    renderTransactionList();
    
    // 전역 변수 복원
    matchedDocumentPairs = originalPairs;
}

// 통계 지표 업데이트
function updateMetrics() {
    // 브랜드 수 계산 (중복 제거)
    const uniqueBrands = new Set();
    matchedDocumentPairs.forEach(pair => {
        if (pair.brand) {
            uniqueBrands.add(pair.brand);
        }
    });
    
    // 진행 중/완료 거래 수 계산
    const today = new Date();
    let inProgressCount = 0;
    let completedCount = 0;
    let todayEventCount = 0;
    
    calendarEvents.forEach(event => {
        const eventDate = parseDate(event.date);
        
        // 오늘 이벤트 카운트
        if (eventDate && eventDate.toDateString() === today.toDateString()) {
            todayEventCount++;
        }
        
        // 이벤트 타입에 따른 카운트
        if (event.type === 'pending' && eventDate >= today) {
            inProgressCount++;
        } else if (event.type === 'complete' || (event.type === 'pending' && eventDate < today)) {
            completedCount++;
        }
    });
    
    // 지표 업데이트
    document.getElementById('total-clients').textContent = uniqueBrands.size;
    document.getElementById('in-progress-count').textContent = `${inProgressCount}건`;
    document.getElementById('completed-count').textContent = `${completedCount}건`;
    document.getElementById('today-events').textContent = `${todayEventCount}건`;
}

// 오류 메시지 표시
function showError(message) {
    // 알림 생성
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    // 메인 콘텐츠의 상단에 추가
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(errorDiv, mainContent.firstChild);
        
        // 5초 후 자동 제거
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}