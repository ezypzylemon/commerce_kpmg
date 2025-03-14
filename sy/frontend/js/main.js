// 공통 함수 (여러 페이지에서 사용될 수 있는 함수들을 정의)
const commonFunctions = {
    // 날짜 포맷 변경 함수 (예시)
    formatDate: function(dateString) {
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `<span class="math-inline">\{year\}\-</span>{month}-${day}`;
    },

    // 숫자 포맷 변경 함수 (예시)
    formatNumber: function(number) {
        return number.toLocaleString();
    },

    // 테이블 행 생성 함수 (데이터 객체와 테이블 ID를 인자로 받음)
    createTableRow: function(data, tableId) {
        const tableBody = document.getElementById(tableId);
        if (!tableBody) {
            console.error(`Table body with id "${tableId}" not found.`);
            return;
        }

        const row = tableBody.insertRow();
        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                const cell = row.insertCell();
                cell.textContent = data[key];
            }
        }
        return row;
    },

    // 페이지네이션 생성 함수 (전체 아이템 수, 페이지당 아이템 수, 현재 페이지)
    createPagination: function(totalItems, itemsPerPage, currentPage, paginationId) {
        const pagination = document.getElementById(paginationId);
        if (!pagination) {
            console.error(`Pagination element with id "${paginationId}" not found.`);
            return;
        }
        pagination.innerHTML = ''; // 기존 내용 초기화

        const totalPages = Math.ceil(totalItems / itemsPerPage);

        // 이전 페이지 링크
        if (currentPage > 1) {
            const prevLink = document.createElement('a');
            prevLink.href = '#';
            prevLink.textContent = '이전';
            prevLink.addEventListener('click', () => {
                // TODO: 이전 페이지 로드 함수 호출
                console.log('이전 페이지 클릭됨');
            });
            pagination.appendChild(prevLink);
        }

        // 페이지 번호 링크
        for (let i = 1; i <= totalPages; i++) {
            const pageLink = document.createElement('a');
            pageLink.href = '#';
            pageLink.textContent = i;
            if (i === currentPage) {
                pageLink.classList.add('active');
            }
            pageLink.addEventListener('click', () => {
                // TODO: 해당 페이지 로드 함수 호출
                console.log(`${i} 페이지 클릭됨`);
            });
            pagination.appendChild(pageLink);
        }

        // 다음 페이지 링크
        if (currentPage < totalPages) {
            const nextLink = document.createElement('a');
            nextLink.href = '#';
            nextLink.textContent = '다음';
            nextLink.addEventListener('click', () => {
                // TODO: 다음 페이지 로드 함수 호출
                console.log('다음 페이지 클릭됨');
            });
            pagination.appendChild(nextLink);
        }
    },
    // ... 기타 필요한 공통 함수들을 정의
};

// 각 페이지에 해당하는 스크립트 (개별 js 파일로 분리하는 것이 좋음)

// 대시보드 (dashboard.js)
const dashboard = {
    init: function() {
        // TODO: 대시보드 초기화 코드 (차트 생성, 데이터 로드 등)
        this.renderBrandInOutChart();
        this.renderTransactionChart();
        this.initCalendar();
    },

    renderBrandInOutChart: function() {
        // Chart.js를 사용하여 원형 차트 그리기
        const ctx = document.getElementById('brandInOutChart').getContext('2d');
        const brandInOutChart = new Chart(ctx, {
            type: 'pie', // 원형 차트
            data: {
                labels: ['TOGA VIRILIS', 'WILD DONKEY', 'ATHLETICS FTWR', 'BASERANGE', 'NOU NOU'],
                datasets: [{
                    data: [30, 25, 20, 15, 10], // 브랜드별 데이터 (합이 100이 되도록)
                    backgroundColor: [
                        '#003f5c',
                        '#58508d',
                        '#bc5090',
                        '#ff6361',
                        '#ffa600'
                    ],
                    hoverOffset: 4 // 마우스 오버 시 효과
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    },

    renderTransactionChart: function() {
        // 유형별 거래 비율 차트
        const transactionCtx = document.getElementById('transactionChart').getContext('2d');
        const transactionChart = new Chart(transactionCtx, {
            type: 'pie', // 원형 차트
            data: {
                labels: ['의류', '신발', '액세서리', '가방', '기타'],
                datasets: [{
                    data: [40, 25, 15, 10, 10], // 유형별 데이터 (합이 100이 되도록)
                    backgroundColor: [
                        '#264653',
                        '#2a9d8f',
                        '#e9c46a',
                        '#f4a261',
                        '#e76f51'
                    ],
                    hoverOffset: 4 // 마우스 오버 시 효과
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    },
    initCalendar: function() {
        const calendarDays = document.getElementById('calendar-days');
        const currentMonthSpan = document.getElementById('currentMonth');
        const prevMonthButton = document.getElementById('prevMonth');
        const nextMonthButton = document.getElementById('nextMonth');

        let currentDate = new Date();
        let currentMonth = currentDate.getMonth();
        let currentYear = currentDate.getFullYear();

        function generateCalendar(year, month) {
            calendarDays.innerHTML = '';

            const firstDayOfMonth = new Date(year, month, 1);
            const lastDayOfMonth = new Date(year, month + 1, 0);
            const daysInMonth = lastDayOfMonth.getDate();
            const startDayOfWeek = firstDayOfMonth.getDay();

            currentMonthSpan.textContent = `${year}년 ${month + 1}월`;

            // Add empty cells for days before the first day of the month
            for (let i = 0; i < startDayOfWeek; i++) {
                const emptyCell = document.createElement('div');
                emptyCell.classList.add('calendar-day', 'empty');
                calendarDays.appendChild(emptyCell);
            }

            // Add cells for each day of the month
            for (let i = 1; i <= daysInMonth; i++) {
                const dayCell = document.createElement('div');
                dayCell.classList.add('calendar-day');
                dayCell.textContent = i;

                // Add event listener for day click (you can customize this)
                dayCell.addEventListener('click', () => {
                    alert(`Clicked on <span class="math-inline">\{year\}\-</span>{month + 1}-${i}`);
                });

                calendarDays.appendChild(dayCell);
            }
        }

        function navigateMonth(direction) {
            if (direction === 'prev') {
                currentMonth--;
                if (currentMonth < 0) {
                    currentMonth = 11;
                    currentYear--;
                }
            } else if (direction === 'next') {
                currentMonth++;
                if (currentMonth > 11) {
                    currentMonth = 0;
                    currentYear++;
                }
            }
            generateCalendar(currentYear, currentMonth);
        }

        // Initialize calendar
        generateCalendar(currentYear, currentMonth);

        // Add event listeners for navigation buttons
        prevMonthButton.addEventListener('click', () => navigateMonth('prev'));
        nextMonthButton.addEventListener('click', () => navigateMonth('next'));
    }
    // ... 기타 대시보드 관련 함수
};

// 문서 업로드 (upload.js)
const upload = {
    init: function() {
        // TODO: 문서 업로드 페이지 초기화 코드
        this.setupEventListeners();
    },

    setupEventListeners: function() {
        // TODO: 파일 드롭 영역, 파일 선택 버튼 등에 이벤트 리스너 추가
        const dropzone = document.querySelector('.upload-dropzone');
        const fileInput = document.querySelector('#file-input');

        // 드롭 영역에 파일 드롭 이벤트 리스너 등록
        dropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', function() {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropzone.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                // TODO: 파일 처리 로직 구현 (예: uploadFiles(files))
                console.log('파일 드롭됨:', files);
            }
        });

        // 파일 선택 버튼 클릭 이벤트 리스너 등록
        // fileInput.addEventListener('change', function() {
        //     const files = fileInput.files;
        //     if (files && files.length > 0) {
        //         // TODO: 파일 처리 로직 구현 (예: uploadFiles(files))
        //         console.log('파일 선택됨:', files);
        //     }
        // });
    },

    uploadFiles: function(files) {
        // TODO: 파일 업로드 로직 구현 (AJAX, FormData 등 활용)
    },
    // ... 기타 문서 업로드 관련 함수
};

// 발주 및 계약 관리 (orders.js)
const orders = {
    init: function() {
        // TODO: 발주 및 계약 관리 페이지 초기화 코드
        this.loadDocumentList();
        this.setupSearch();
        this.setupFilters();
    },
    loadDocumentList: function() {
        // TODO: 서버에서 문서 목록을 가져오는 코드 (AJAX 호출 등)
        const documents = [
            {
                "id": "doc001",
                "type": "invoice",
                "date": "2025-03-09",
                "title": "AF_Sports_Invoice_22-03-2025.pdf",
                "matchRate": 92,
                "brand": "ATHLETICS FTWR",
                "amount": "₩8,750,000",
                "status": "complete"
            },
            {
                "id": "doc002",
                "type": "po",
                "date": "2025-03-08",
                "title": "UrbanStreet_PO_18-03-2025.pdf",
                "matchRate": 78,
                "brand": "WILD DONKEY",
                "amount": "₩4,320,000",
                "status": "review"
            },
            {
                "id": "doc003",
                "type": "invoice",
                "date": "2025-03-07",
                "title": "MetroStyles_Invoice_10-03-2025.pdf",
                "matchRate": 45,
                "brand": "BASERANGE",
                "amount": "₩3,150,000",
                "status": "review"
            },
            {
                "id": "doc004",
                "type": "contract",
                "date": "2025-03-05",
                "title": "FitPlus_Contract_05-03-2025.pdf",
                "matchRate": 89,
                "brand": "TOGA VIRILIS",
                "contractPeriod": "1년",
                "status": "complete"
            },
            {
                "id": "doc005",
                "type": "po",
                "date": "2025-03-04",
                "title": "NouNou_PO_04-03-2025.pdf",
                "matchRate": 95,
                "brand": "NOU NOU",
                "amount": "₩5,875,000",
                "status": "complete"
            }
        ];

        // 문서 목록을 표시하는 코드
        const documentGrid = document.querySelector('.document-grid');
        documentGrid.innerHTML = ''; // 기존 내용 초기화

        documents.forEach(doc => {
            const documentItem = this.createDocumentItem(doc);
            documentGrid.appendChild(documentItem);
        });

        // 페이지네이션 생성 (예시)
        // const totalItems = documents.length;
        // const itemsPerPage = 10; // 페이지당 표시할 아이템 수
        // const currentPage = 1; // 현재 페이지 번호
        // commonFunctions.createPagination(totalItems, itemsPerPage, currentPage, 'pagination');
    },
    createDocumentItem: function(doc) {
        const documentItem = document.createElement('div');
        documentItem.classList.add('document-item');

        const documentHeader = document.createElement('div');
        documentHeader.classList.add('document-header');

        const docType = document.createElement('span');
        docType.classList.add('doc-type', doc.type);
        docType.textContent = doc.type === 'po' ? '발주서' : doc.type === 'invoice' ? '인보이스' : '계약서';

        const docDate = document.createElement('span');
        docDate.classList.add('doc-date');
        docDate.textContent = doc.date;

        const docActions = document.createElement('div');
        docActions.classList.add('doc-actions');

        const ellipsisButton = document.createElement('button');
        ellipsisButton.classList.add('btn', 'btn-icon', 'btn-sm');
        ellipsisButton.innerHTML = '<i class="fas fa-ellipsis-v"></i>';

        docActions.appendChild(ellipsisButton);
        documentHeader.appendChild(docType);
        documentHeader.appendChild(docDate);
        documentHeader.appendChild(docActions);

        const documentBody = document.createElement('div');
        documentBody.classList.add('document-body');

        const docTitle = document.createElement('h3');
        docTitle.classList.add('doc-title');
        docTitle.textContent = doc.title;

        const matchIndicator = document.createElement('div');
        matchIndicator.classList.add('match-indicator', doc.matchRate > 80 ? 'high' : doc.matchRate > 60 ? 'medium' : 'low');

        const matchLabel = document.createElement('span');
        matchLabel.classList.add('match-label');
        matchLabel.textContent = '일치율';

        const matchValue = document.createElement('span');
        matchValue.classList.add('match-value');
        matchValue.textContent = `${doc.matchRate}%`;

        matchIndicator.appendChild(matchLabel);
        matchIndicator.appendChild(matchValue);
        documentBody.appendChild(docTitle);
        documentBody.appendChild(matchIndicator);

        const docInfo = document.createElement('div');
        docInfo.classList.add('doc-info');

        const infoItem1 = document.createElement('div');
        infoItem1.classList.add('info-item');
        const infoLabel1 = document.createElement('span');
        infoLabel1.classList.add('info-label');
        infoLabel1.textContent = '브랜드:';
        const infoValue1 = document.createElement('span');
        infoValue1.classList.add('info-value');
        infoValue1.textContent = doc.brand;
        infoItem1.appendChild(infoLabel1);
        infoItem1.appendChild(infoValue1);
        docInfo.appendChild(infoItem1);

        const infoItem2 = document.createElement('div');
        infoItem2.classList.add('info-item');
        const infoLabel2 = document.createElement('span');
        infoLabel2.classList.add('info-label');
        infoLabel2.textContent = doc.type === 'contract' ? '계약 기간:' : '금액:';
        const infoValue2 = document.createElement('span');
        infoValue2.classList.add('info-value');
        infoValue2.textContent = doc.type === 'contract' ? doc.contractPeriod : doc.amount;
        infoItem2.appendChild(infoLabel2);
        infoItem2.appendChild(infoValue2);
        docInfo.appendChild(infoItem2);

        documentBody.appendChild(docInfo);

        const documentFooter = document.createElement('div');
        documentFooter.classList.add('document-footer');

        const statusBadge = document.createElement('span');
        statusBadge.classList.add('status-badge', doc.status);
        statusBadge.textContent = doc.status === 'complete' ? '완료' : doc.