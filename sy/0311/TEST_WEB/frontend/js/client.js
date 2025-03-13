document.addEventListener("DOMContentLoaded", function () {
    const currentMonthElement = document.getElementById("currentMonth");
    const calendarDays = document.querySelector(".calendar-days");
    const transactionTable = document.getElementById("transactionData");

    let currentMonth = 2; // 3월 (JavaScript는 0부터 시작)
    let currentYear = 2025;

    const transactions = [
        { date: "2025-03-05", client: "ABC 상사", detail: "선적 완료", status: "shipping" },
        { date: "2025-03-10", client: "DEF 트레이딩", detail: "비용 정산 진행", status: "payment" },
        { date: "2025-03-15", client: "XYZ 무역", detail: "거래 완료", status: "completed" }
    ];

    function generateCalendar() {
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        
        calendarDays.innerHTML = "";
        currentMonthElement.textContent = `${currentYear}년 ${currentMonth + 1}월`;

        for (let i = 0; i < firstDay; i++) {
            let emptyDiv = document.createElement("div");
            emptyDiv.classList.add("calendar-day", "empty");
            calendarDays.appendChild(emptyDiv);
        }

        for (let i = 1; i <= daysInMonth; i++) {
            let dayDiv = document.createElement("div");
            dayDiv.classList.add("calendar-day");
            dayDiv.innerHTML = `<span>${i}</span>`;

            transactions.forEach(t => {
                let transactionDate = new Date(t.date);
                if (transactionDate.getFullYear() === currentYear && transactionDate.getMonth() === currentMonth && transactionDate.getDate() === i) {
                    let eventDiv = document.createElement("div");
                    eventDiv.classList.add("calendar-event", t.status);
                    eventDiv.textContent = t.detail;
                    dayDiv.appendChild(eventDiv);
                }
            });

            calendarDays.appendChild(dayDiv);
        }
    }

    function loadTransactions() {
        transactionTable.innerHTML = "";
        transactions.forEach(t => {
            let row = `<tr>
                <td>${t.client}</td>
                <td>${t.date}</td>
                <td>${t.detail}</td>
                <td class="status ${t.status}">${t.detail}</td>
            </tr>`;
            transactionTable.innerHTML += row;
        });
    }

    document.getElementById("prevMonth").addEventListener("click", function () {
        currentMonth = currentMonth === 0 ? 11 : currentMonth - 1;
        generateCalendar();
    });

    document.getElementById("nextMonth").addEventListener("click", function () {
        currentMonth = currentMonth === 11 ? 0 : currentMonth + 1;
        generateCalendar();
    });

    generateCalendar();
    loadTransactions();
});
