document.addEventListener("DOMContentLoaded", function () {
    const currentMonthEl = document.getElementById("currentMonth");
    const prevMonthBtn = document.getElementById("prevMonth");
    const nextMonthBtn = document.getElementById("nextMonth");
    const calendarDaysEl = document.getElementById("calendar-days");
    let currentMonth = new Date();

    // 📌 해외 의류 브랜드 관련 일정 데이터
    const events = {
        "2025-03-05": "TOGA VIRILIS 신상품 입고",
        "2025-03-10": "WILD DONKEY 해외 발주",
        "2025-03-15": "ATHLETICS FTWR 물류센터 도착",
        "2025-03-20": "BASERANGE 결제 마감일",
        "2025-03-25": "NOU NOU 신제품 론칭"
    };

    function updateCalendar() {
        const monthNames = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"];
        currentMonthEl.textContent = `${currentMonth.getFullYear()}년 ${monthNames[currentMonth.getMonth()]}`;
        renderCalendar();
    }

    function renderCalendar() {
        calendarDaysEl.innerHTML = "";
        const firstDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
        const lastDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);
        let dayCount = lastDay.getDate();
        let startDay = firstDay.getDay();
        
        for (let i = 0; i < startDay; i++) {
            let emptyCell = document.createElement("div");
            emptyCell.classList.add("day", "empty");
            calendarDaysEl.appendChild(emptyCell);
        }
        
        for (let i = 1; i <= dayCount; i++) {
            let dayCell = document.createElement("div");
            dayCell.classList.add("day");
            dayCell.textContent = i;
            
            let eventKey = `${currentMonth.getFullYear()}-03-${i.toString().padStart(2, "0")}`;
            if (events[eventKey]) {
                let eventText = document.createElement("div");
                eventText.classList.add("event");
                eventText.textContent = events[eventKey];
                dayCell.appendChild(eventText);
            }
            
            calendarDaysEl.appendChild(dayCell);
        }
    }

    prevMonthBtn.addEventListener("click", function () {
        currentMonth.setMonth(currentMonth.getMonth() - 1);
        updateCalendar();
    });

    nextMonthBtn.addEventListener("click", function () {
        currentMonth.setMonth(currentMonth.getMonth() + 1);
        updateCalendar();
    });

    updateCalendar();

    // 📌 브랜드 입출고 데이터를 동적으로 추가
    const transactionDataEl = document.getElementById("transactionData");
    const paginationEl = document.getElementById("pagination");
    if (!transactionDataEl) {
        console.error("거래 데이터 테이블을 찾을 수 없습니다.");
        return;
    }
    
    let brands = ["TOGA VIRILIS", "WILD DONKEY", "ATHLETICS FTWR", "BASERANGE", "NOU NOU"];
    let currencies = ["USD", "KRW", "EUR", "JPY", "CNY"];
    let stockStatuses = ["입고 완료", "출고 중", "입고 대기", "출고 완료"];
    let paymentStatuses = ["결제 완료", "미결제", "결제 중"];

    let transactions = [];
    for (let i = 0; i < 50; i++) {
        let brand = brands[i % brands.length];
        let currency = currencies[i % currencies.length];
        let stockStatus = stockStatuses[i % stockStatuses.length];
        let paymentStatus = paymentStatuses[i % paymentStatuses.length];
        let buttonLabel = paymentStatus === "결제 완료" ? "거래 내역 보기" : "계약서 작성";

        transactions.push(`
            <tr>
                <td>${brand}</td>
                <td>${currency}</td>
                <td>${stockStatus}</td>
                <td>${paymentStatus}</td>
                <td><button class='btn'>${buttonLabel}</button></td>
            </tr>`);
    }

    const rowsPerPage = 5;
    let currentPage = 1;

    function renderTablePage(page) {
        transactionDataEl.innerHTML = transactions.slice((page - 1) * rowsPerPage, page * rowsPerPage).join('');
    }

    function renderPagination() {
        paginationEl.innerHTML = "";
        let totalPages = Math.ceil(transactions.length / rowsPerPage);
        for (let i = 1; i <= totalPages; i++) {
            let pageButton = document.createElement("button");
            pageButton.textContent = i;
            pageButton.classList.add("page-btn");
            if (i === currentPage) pageButton.classList.add("active");
            pageButton.addEventListener("click", function () {
                currentPage = i;
                renderTablePage(currentPage);
                renderPagination();
            });
            paginationEl.appendChild(pageButton);
        }
    }

    renderTablePage(currentPage);
    renderPagination();

    // 📊 거래처 분석 차트 적용
    const clientChartCtx = document.getElementById("clientChart").getContext("2d");
    const transactionChartCtx = document.getElementById("transactionChart").getContext("2d");

    new Chart(clientChartCtx, {
        type: "pie",
        data: {
            labels: brands,
            datasets: [{
                data: [25, 20, 30, 15, 10],
                backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
            }]
        }
    });

    new Chart(transactionChartCtx, {
        type: "bar",
        data: {
            labels: stockStatuses,
            datasets: [{
                data: [10, 20, 15, 5],
                backgroundColor: ["#4BC0C0", "#FF9F40", "#9966FF", "#FF6384"]
            }]
        }
    });
});
