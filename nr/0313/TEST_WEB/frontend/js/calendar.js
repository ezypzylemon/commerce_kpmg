document.addEventListener("DOMContentLoaded", function () {
    const currentMonthEl = document.getElementById("currentMonth");
    const prevMonthBtn = document.getElementById("prevMonth");
    const nextMonthBtn = document.getElementById("nextMonth");
    const calendarDaysEl = document.getElementById("calendar-days");
    let currentMonth = new Date();

    // 일정 데이터 추가
    const events = {
        "2025-03-05": "ABC 상사 계약 진행",
        "2025-03-10": "XYZ 주식회사 발주 확인",
        "2025-03-15": "LMN 유한회사 결제 대기",
        "2025-03-20": "Korean Co. 미팅",
        "2025-03-25": "Global Inc. 서류 제출"
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

    // 100개의 샘플 거래처 데이터를 생성 + 5개씩 페이지네이션 추가
    const transactionDataEl = document.getElementById("transactionData");
    const paginationEl = document.getElementById("pagination");
    if (!transactionDataEl) {
        console.error("거래 데이터 테이블을 찾을 수 없습니다.");
        return;
    }
    
    let transactions = [];
    for (let i = 1; i <= 100; i++) {
        let status = i % 2 === 0 ? "진행 중" : "완료";
        let buttonLabel = status === "진행 중" ? "계약서 작성" : "거래 내역 보기";
        transactions.push(`
            <tr>
                <td>거래처 ${i}</td>
                <td>2025-03-${(i % 30) + 1}</td>
                <td>수출 계약</td>
                <td>${status}</td>
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

    // 거래처 분석 차트 적용
    const clientChartCtx = document.getElementById("clientChart").getContext("2d");
    const transactionChartCtx = document.getElementById("transactionChart").getContext("2d");

    new Chart(clientChartCtx, {
        type: "pie",
        data: {
            labels: ["거래처 A", "거래처 B", "거래처 C"],
            datasets: [{
                data: [40, 35, 25],
                backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56"]
            }]
        }
    });

    new Chart(transactionChartCtx, {
        type: "bar",
        data: {
            labels: ["수출 계약", "발주 확인", "결제 대기"],
            datasets: [{
                data: [20, 50, 30],
                backgroundColor: ["#4BC0C0", "#FF9F40", "#9966FF"]
            }]
        }
    });
});