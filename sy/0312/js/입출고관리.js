document.addEventListener("DOMContentLoaded", function () {
    // 샘플 입출고 데이터 (품목명, 날짜, 유형, 수량, 브랜드, 상태)
    const transactionData = [
        { item: "운동화 A", date: "2025-01-10", type: "입고", quantity: 100, brand: "Nike", status: "완료" },
        { item: "운동화 A", date: "2025-01-15", type: "출고", quantity: 30, brand: "Nike", status: "완료" },
        { item: "티셔츠 B", date: "2025-01-20", type: "입고", quantity: 50, brand: "Adidas", status: "진행 중" },
        { item: "운동화 A", date: "2025-02-01", type: "입고", quantity: 200, brand: "Nike", status: "완료" },
        { item: "운동화 A", date: "2025-02-10", type: "출고", quantity: 50, brand: "Nike", status: "완료" },
        { item: "티셔츠 B", date: "2025-02-15", type: "출고", quantity: 20, brand: "Adidas", status: "진행 중" },
        { item: "운동화 C", date: "2025-02-20", type: "입고", quantity: 100, brand: "Puma", status: "검토 필요" },
        { item: "운동화 A", date: "2025-03-01", type: "출고", quantity: 100, brand: "Nike", status: "완료" },
        { item: "운동화 C", date: "2025-03-05", type: "출고", quantity: 30, brand: "Puma", status: "진행 중" },
        { item: "티셔츠 B", date: "2025-03-10", type: "입고", quantity: 100, brand: "Adidas", status: "완료" },
        { item: "운동화 A", date: "2025-03-15", type: "입고", quantity: 50, brand: "Nike", status: "완료" },
        { item: "티셔츠 B", date: "2025-03-20", type: "출고", quantity: 50, brand: "Adidas", status: "완료" },
        { item: "운동화 C", date: "2025-03-25", type: "입고", quantity: 50, brand: "Puma", status: "완료" },
        { item: "운동화 A", date: "2025-04-01", type: "입고", quantity: 100, brand: "Nike", status: "진행 중" },
        { item: "운동화 C", date: "2025-04-05", type: "출고", quantity: 20, brand: "Puma", status: "완료" },
        { item: "티셔츠 B", date: "2025-04-10", type: "입고", quantity: 200, brand: "Adidas", status: "완료" },
        { item: "운동화 A", date: "2025-04-15", type: "출고", quantity: 30, brand: "Nike", status: "완료" },
        { item: "티셔츠 B", date: "2025-04-20", type: "출고", quantity: 100, brand: "Adidas", status: "진행 중" },
    ];

    /** ========== 📊 데이터 집계 함수 ========== */
    function aggregateData(data) {
        let totalInbound = 0;
        let totalOutbound = 0;
        let currentStock = 0;
        const monthlyData = {};
        const brandData = {};

        data.forEach(item => {
            if (item.type === "입고") {
                totalInbound += item.quantity;
                currentStock += item.quantity;
            } else if (item.type === "출고") {
                totalOutbound += item.quantity;
                currentStock -= item.quantity;
            }

            // 월별 데이터 집계
            const month = item.date.substring(0, 7);
            if (!monthlyData[month]) {
                monthlyData[month] = { 입고: 0, 출고: 0 };
            }
            monthlyData[month][item.type] += item.quantity;

            // 브랜드별 데이터 집계
            if (!brandData[item.brand]) {
                brandData[item.brand] = { 입고: 0, 출고: 0 };
            }
            brandData[item.brand][item.type] += item.quantity;
        });

        return {
            totalInbound,
            totalOutbound,
            currentStock,
            monthlyData,
            brandData
        };
    }

    /** ========== 📈 차트 생성 함수 ========== */
    function createChart(ctx, labels, inData, outData, type = 'bar') {
        new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '입고',
                        data: inData,
                        backgroundColor: '#4263eb',
                        borderColor: '#fff',
                        borderWidth: 1
                    },
                    {
                        label: '출고',
                        data: outData,
                        backgroundColor: '#e8590c',
                        borderColor: '#fff',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    /** ========== 📋 테이블 렌더링 함수 ========== */
    function renderTable(data) {
        const tableBody = document.getElementById("transactionTableBody");
        tableBody.innerHTML = "";

        data.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${item.item}</td>
                <td>${item.date}</td>
                <td>${item.type}</td>
                <td>${item.quantity}</td>
                <td>${item.brand}</td>
                <td class="status ${item.status}">${item.status}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    /** ========== 🔄 데이터 및 화면 업데이트 함수 ========== */
    function updateDashboard(data) {
        const aggregatedData = aggregateData(data);

        // 요약 정보 업데이트
        document.getElementById("total-inbound").textContent = aggregatedData.totalInbound + " 건";
        document.getElementById("total-outbound").textContent = aggregatedData.totalOutbound + " 건";
        document.getElementById("current-stock").textContent = aggregatedData.currentStock + " 개";

        // 월별 입출고 차트 데이터 추출
        const monthlyLabels = Object.keys(aggregatedData.monthlyData);
        const monthlyIn = monthlyLabels.map(month => aggregatedData.monthlyData[month].입고);
        const monthlyOut = monthlyLabels.map(month => aggregatedData.monthlyData[month].출고);

        // 브랜드별 입출고 차트 데이터 추출
        const brandLabels = Object.keys(aggregatedData.brandData);
        const brandIn = brandLabels.map(brand => aggregatedData.brandData[brand].입고);
        const brandOut = brandLabels.map(brand => aggregatedData.brandData[brand].출고);

        // 차트 렌더링 (이전 코드 활용)
        const monthlyChartCanvas = document.getElementById('monthlyInOutChart');
        if (monthlyChartCanvas) {
            const monthlyContext = monthlyChartCanvas.getContext('2d');
            if (monthlyContext) {
                console.log('월별 입출고 추이 Chart 초기화 성공');
                createChart(monthlyContext, monthlyLabels, monthlyIn, monthlyOut, 'line'); // 월별 추이는 line 차트로 변경
            } else {
                console.error('monthlyInOutChart에서 2D 컨텍스트 초기화 실패');
            }
        } else {
            console.error('monthlyInOutChart 캔버스 요소를 찾을 수 없음');
        }

        const brandChartCanvas = document.getElementById('brandInOutChart');
        if (brandChartCanvas) {
            const brandContext = brandChartCanvas.getContext('2d');
            if (brandContext) {
                console.log('브랜드별 입출고 비율 Chart 초기화 성공');
                createChart(brandContext, brandLabels, brandIn, brandOut, 'pie');
            } else {
                console.error('brandInOutChart에서 2D 컨텍스트 초기화 실패');
            }
        } else {
            console.error('brandInOutChart 캔버스 요소를 찾을 수 없음');
        }


        // 테이블 렌더링
        renderTable(data);
    }

    // 초기 데이터 로드 및 화면 업데이트
    updateDashboard(transactionData);

    // 필터링 기능 (이 부분은 현재 HTML 구조에 맞춰 구현해야 함)
    document.getElementById("filter-btn").addEventListener("click", function () {
        // 필터링 로직 구현 (현재는 모든 데이터 표시)
        updateDashboard(transactionData);
    });
});