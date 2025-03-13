document.addEventListener("DOMContentLoaded", function () {
    // 샘플 입고 데이터 (문서명, 날짜, 브랜드, 상태)
    const inventoryData = [
        { date: "2025-01-15", brand: "Nike", status: "완료" },
        { date: "2025-01-20", brand: "Adidas", status: "진행 중" },
        { date: "2025-02-10", brand: "Puma", status: "검토 필요" },
        { date: "2025-02-25", brand: "Nike", status: "완료" },
        { date: "2025-03-05", brand: "Reebok", status: "진행 중" },
        { date: "2025-03-10", brand: "Adidas", status: "완료" },
        { date: "2025-03-15", brand: "Puma", status: "검토 필요" },
        { date: "2025-04-01", brand: "Nike", status: "진행 중" },
        { date: "2025-04-05", brand: "Reebok", status: "완료" },
        { date: "2025-04-20", brand: "Adidas", status: "완료" },
    ];

    /** ========== 📊 월별 입고 추이 데이터 처리 ========== */
    function getMonthlyData() {
        const monthlyCounts = {};
        inventoryData.forEach(item => {
            let month = item.date.substring(0, 7); // "YYYY-MM" 형식 추출
            monthlyCounts[month] = (monthlyCounts[month] || 0) + 1;
        });

        return {
            labels: Object.keys(monthlyCounts),
            data: Object.values(monthlyCounts)
        };
    }

    /** ========== 📊 브랜드별 입고 비율 데이터 처리 ========== */
    function getBrandData() {
        const brandCounts = {};
        inventoryData.forEach(item => {
            brandCounts[item.brand] = (brandCounts[item.brand] || 0) + 1;
        });

        return {
            labels: Object.keys(brandCounts),
            data: Object.values(brandCounts)
        };
    }

    /** ========== 📈 차트 생성 함수 ========== */
    function createChart(ctx, labels, data, label, type = 'bar') {
        new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: ['#4263eb', '#2b8a3e', '#e8590c', '#f1c40f'],
                    borderColor: '#fff',
                    borderWidth: 1
                }]
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

    // 📌 차트 렌더링
    createChart(
        document.getElementById("inventoryTrendChart").getContext("2d"),
        getMonthlyData().labels,
        getMonthlyData().data,
        "월별 입고 건수"
    );

    createChart(
        document.getElementById("brandInventoryChart").getContext("2d"),
        getBrandData().labels,
        getBrandData().data,
        "브랜드별 입고 비율",
        "pie"
    );

    /** ========== 📋 최근 입고 내역 테이블 업데이트 ========== */
    function updateTable() {
        const tableBody = document.querySelector(".recent-inventory tbody");
        tableBody.innerHTML = "";

        inventoryData.forEach(item => {
            let row = `
                <tr>
                    <td>${item.brand}_IN_${item.date.replace(/-/g, "_")}.pdf</td>
                    <td>${item.date}</td>
                    <td class="status ${item.status}">${item.status}</td>
                </tr>`;
            tableBody.innerHTML += row;
        });
    }

    updateTable();
});
