// calendar.js - 일정 관리 페이지 스크립트

// API 기본 URL 설정 (개발 환경)
const API_BASE_URL = 'http://localhost:5000/orders';

// 이벤트 카테고리별 색상 매핑
const CATEGORY_COLORS = {
    'personal': '#4CAF50',  // 개인 일정 (초록색)
    'business': '#2196F3',  // 업무 일정 (파란색)
    'shipping': '#FF9800',  // 선적 일정 (주황색)
    'default': '#9E9E9E'    // 기본 회색
};

// 브랜드별 색상 매핑 (추가됨)
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
let personalEvents = [];          // 개인 일정 배열
let businessEvents = [];          // 업무 일정 배열
let shippingEvents = [];          // 선적 일정 배열
let currentView = 'month';        // 현재 뷰 모드 (month, week, day)
let selectedEvent = null;         // 현재 선택된 이벤트
let selectedDate = null;          // 선택된 날짜

// 추가된 변수
let allInvoices = [];             // 모든 인보이스 문서
let allOrders = [];               // 모든 오더시트 문서
let matchedDocumentPairs = [];    // 일치하는 문서 쌍 배열

// 로컬 스토리지 키
const PERSONAL_EVENTS_KEY = 'personalEvents';
const BUSINESS_EVENTS_KEY = 'businessEvents';

document.addEventListener('DOMContentLoaded', function() {
    // 캘린더 초기화
    initCalendar();
    
    // 로컬 스토리지에서 개인 및 업무 일정 불러오기
    loadEventsFromLocalStorage();
    
    // 선적 일정 데이터 로드
    loadShippingEvents();
    
    // 뷰 모드 전환 버튼 이벤트 리스너
    document.getElementById('monthViewBtn').addEventListener('click', function() {
        switchView('month');
    });
    
    document.getElementById('weekViewBtn').addEventListener('click', function() {
        switchView('week');
    });
    
    document.getElementById('dayViewBtn').addEventListener('click', function() {
        switchView('day');
    });
    
    // 캘린더 네비게이션 이벤트 리스너
    document.getElementById('prevMonth').addEventListener('click', function() {
        navigatePrevious();
    });
    
    document.getElementById('nextMonth').addEventListener('click', function() {
        navigateNext();
    });
    
    // 필터 체크박스 이벤트 리스너
    document.getElementById('filter-personal').addEventListener('change', applyFilters);
    document.getElementById('filter-business').addEventListener('change', applyFilters);
    document.getElementById('filter-shipping').addEventListener('change', applyFilters);
    
    // 새 일정 추가 버튼 이벤트 리스너
    document.getElementById('addEventBtn').addEventListener('click', function() {
        openAddEventModal(new Date());
    });
    
    // 모달 닫기 버튼 이벤트 리스너
    document.querySelectorAll('.modal-close').forEach(button => {
        button.addEventListener('click', function() {
            closeModal(this.closest('.modal').id);
        });
    });
    
    // 모달 배경 클릭 시 닫기
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function() {
            closeModal(this.parentElement.id);
        });
    });
    
    // 반복 일정 체크박스 이벤트 리스너
    document.getElementById('eventRepeat').addEventListener('change', function() {
        const repeatOptions = document.getElementById('repeatOptions');
        repeatOptions.style.display = this.checked ? 'block' : 'none';
    });
    
    // 일정 저장 버튼 이벤트 리스너
    document.getElementById('saveEventBtn').addEventListener('click', saveEvent);
    
    // 일정 취소 버튼 이벤트 리스너
    document.getElementById('cancelEventBtn').addEventListener('click', function() {
        closeModal('eventModal');
    });
    
    // 일정 삭제 버튼 이벤트 리스너
    document.getElementById('deleteEventBtn').addEventListener('click', deleteEvent);
    
    // 일정 수정 버튼 이벤트 리스너
    document.getElementById('editEventBtn').addEventListener('click', editEvent);
    
    // 검색 기능
    const searchInput = document.getElementById('searchEvent');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                searchEvents(this.value);
            }
        });
    }
});

// 캘린더 초기화
function initCalendar() {
    updateCalendarHeader();
    renderCalendar();
}

// 캘린더 헤더 업데이트 (현재 날짜 표시)
function updateCalendarHeader() {
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    document.getElementById('currentMonth').textContent = `${currentDate.getFullYear()}년 ${monthNames[currentDate.getMonth()]}`;
}

// 캘린더 렌더링 (현재 뷰에 따라)
function renderCalendar() {
    if (currentView === 'month') {
        renderMonthView();
    } else if (currentView === 'week') {
        renderWeekView();
    } else if (currentView === 'day') {
        renderDayView();
    }
    
    // 메트릭 카드 업데이트
    updateMetrics();
}

// 월간 뷰 렌더링
function renderMonthView() {
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
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, lastMonthLastDay - i);
        const dayElement = createDayElement(date, true);
        calendarDays.appendChild(dayElement);
    }
    
    // 현재 달의 날짜 표시
    for (let i = 1; i <= lastDay.getDate(); i++) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), i);
        const isToday = isCurrentDay(date);
        const dayElement = createDayElement(date, false, isToday);
        calendarDays.appendChild(dayElement);
    }
    
    // 다음 달의 시작 날짜들 (필요한 경우)
    const totalDaysDisplayed = firstDayOfWeek + lastDay.getDate();
    const remainingDays = 42 - totalDaysDisplayed; // 6주 * 7일 = 42 (최대 달력 표시 일수)
    
    for (let i = 1; i <= remainingDays; i++) {
        if (totalDaysDisplayed + i <= 35) { // 5주까지만 표시
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, i);
            const dayElement = createDayElement(date, true);
            calendarDays.appendChild(dayElement);
        }
    }
}

// 주간 뷰 렌더링 (아직 구현 안됨)
function renderWeekView() {
    // 미구현
    renderMonthView(); // 임시로 월간 뷰로 대체
}

// 일간 뷰 렌더링 (아직 구현 안됨)
function renderDayView() {
    // 미구현
    renderMonthView(); // 임시로 월간 뷰로 대체
}

// 날짜 요소 생성
function createDayElement(date, isInactive, isToday = false) {
    const dayElement = document.createElement('div');
    dayElement.className = 'calendar-day';
    
    if (isInactive) {
        dayElement.classList.add('inactive');
    }
    
    if (isToday) {
        dayElement.classList.add('today');
    }
    
    // 주말 구분
    if (date.getDay() === 0) { // 일요일
        dayElement.classList.add('sunday');
    } else if (date.getDay() === 6) { // 토요일
        dayElement.classList.add('saturday');
    }
    
    // 날짜 표시
    const dayNumberElement = document.createElement('span');
    dayNumberElement.textContent = date.getDate();
    dayElement.appendChild(dayNumberElement);
    
    // 날짜 속성 추가
    const dateStr = formatDate(date);
    dayElement.setAttribute('data-date', dateStr);
    
    // 해당 날짜의 이벤트 필터링
    const dayEvents = filterEvents(dateStr);
    
    // 일정이 많은 날 및 불일치가 많은 날 강조 표시
    if (dayEvents.length > 0) {
        dayElement.classList.add('has-events');
        if (dayEvents.length >= 4) {
            dayElement.classList.add('many-events');
        }
    }
    
    // 이벤트 추가 (최대 3개까지 표시)
    const maxVisibleEvents = 3;
    const visibleEvents = dayEvents.slice(0, maxVisibleEvents);
    const remainingEvents = dayEvents.length - maxVisibleEvents;
    
    visibleEvents.forEach(event => {
        const eventElement = createEventElement(event);
        dayElement.appendChild(eventElement);
    });
    
    // 더 많은 이벤트가 있는 경우 표시
    if (remainingEvents > 0) {
        const moreElement = document.createElement('div');
        moreElement.className = 'more-events';
        moreElement.textContent = `+${remainingEvents}개 더보기`;
        moreElement.onclick = function(e) {
            e.stopPropagation();
            showDayEvents(date, dayEvents);
        };
        dayElement.appendChild(moreElement);
    }
    
    // 날짜 클릭 이벤트 (새 일정 추가)
    dayElement.addEventListener('click', function() {
        openAddEventModal(date);
    });
    
    return dayElement;
}

// 이벤트 요소 생성
function createEventElement(event) {
    const eventElement = document.createElement('div');
    
    // 기본 클래스 및 확정 상태 클래스 추가
    eventElement.className = `calendar-event ${event.category || event.type || 'default'}`;
    
    // 확정 상태에 따른 클래스 추가
    if (event.is_confirmed !== undefined) {
        eventElement.classList.add(event.is_confirmed ? 'confirmed' : 'pending');
    }
    
    // 브랜드 색상 적용 (추가된 부분)
    if (event.brand && BRAND_COLORS[event.brand]) {
        eventElement.style.backgroundColor = BRAND_COLORS[event.brand];
    } else if (event.color) {
        eventElement.style.backgroundColor = event.color;
    }
    
    // 선적 일정인 경우 추가 처리
    if (event.category === 'shipping' || event.type === 'pending' || event.type === 'complete') {
        // 선적 시작/완료 구분
        const isStart = event.schedule_type === 'start' || event.type === 'pending';
        eventElement.classList.add(isStart ? 'shipping-start' : 'shipping-end');
    }
    
    // 시간 정보 추가
    let eventTitle = event.title;
    if (event.allDay) {
        eventTitle = `${eventTitle} (종일)`;
    } else if (event.startTime) {
        eventTitle = `${event.startTime.slice(0, 5)} ${eventTitle}`;
    }
    
    eventElement.textContent = eventTitle;
    
    // 반복 일정인 경우 아이콘 추가
    if (event.repeat) {
        const repeatIcon = document.createElement('i');
        repeatIcon.className = 'fas fa-sync-alt event-repeat-icon';
        eventElement.appendChild(repeatIcon);
    }
    
    // 툴팁 및 상세 정보 구성
    let tooltipContent = `${event.title}`;
    
    // 선적 일정의 경우 추가 정보 포함
    if (event.category === 'shipping' || event.type === 'pending' || event.type === 'complete') {
        tooltipContent += `\n브랜드: ${event.brand || ''}`;
        tooltipContent += `\n모델: ${event.model_name || event.model_code || ''}`;
        tooltipContent += `\n일정 유형: ${event.schedule_type === 'start' || event.type === 'pending' ? '선적 시작' : '선적 완료'}`;
        
        // 추가 메타데이터 포함
        if (event.meta && event.meta.total_quantity) {
            tooltipContent += `\n총 수량: ${event.meta.total_quantity}`;
        }
        
        // 확정 상태 표시
        tooltipContent += `\n상태: ${event.is_confirmed ? '확정됨' : '미확정'}`;
    }
    
    if (event.description) {
        tooltipContent += `\n${event.description}`;
    }
    
    eventElement.title = tooltipContent;
    
    // 클릭 이벤트 추가 (이벤트 상세 보기)
    eventElement.addEventListener('click', function(e) {
        e.stopPropagation();
        showEventDetails(event);
    });
    
    return eventElement;
}

// 특정 날짜의 현재 날짜 여부 확인
function isCurrentDay(date) {
    const today = new Date();
    return date.getFullYear() === today.getFullYear() && 
           date.getMonth() === today.getMonth() && 
           date.getDate() === today.getDate();
}

// 날짜 형식 변환 (YYYY-MM-DD)
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 날짜 형식 변환 (표시용)
function formatDisplayDate(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${year}년 ${month}월 ${day}일`;
}

// 해당 날짜의 이벤트 필터링
function filterEvents(dateStr) {
    let filteredEvents = [];
    
    // 필터 상태 확인
    const showPersonal = document.getElementById('filter-personal').checked;
    const showBusiness = document.getElementById('filter-business').checked;
    const showShipping = document.getElementById('filter-shipping').checked;
    
    // 전체 이벤트 목록에서 해당 날짜의 이벤트 필터링
    calendarEvents.forEach(event => {
        if (event.date === dateStr) {
            // 카테고리 필터 적용
            if ((event.category === 'personal' && showPersonal) ||
                (event.category === 'business' && showBusiness) ||
                (event.category === 'shipping' && showShipping) ||
                // 추가된 타입 지원
                (event.type === 'pending' && showShipping) ||
                (event.type === 'complete' && showShipping)) {
                filteredEvents.push(event);
            }
        }
    });
    
    // 시간 순 정렬 (종일 이벤트가 먼저, 그 다음 시작 시간 순)
    filteredEvents.sort((a, b) => {
        if (a.allDay && !b.allDay) return -1;
        if (!a.allDay && b.allDay) return 1;
        if (!a.startTime || !b.startTime) return 0;
        return a.startTime.localeCompare(b.startTime);
    });
    
    return filteredEvents;
}

// 뷰 모드 전환
function switchView(viewMode) {
    // 이전 뷰 모드 상태 제거
    document.getElementById('monthViewBtn').classList.remove('active');
    document.getElementById('weekViewBtn').classList.remove('active');
    document.getElementById('dayViewBtn').classList.remove('active');
    
    // 새 뷰 모드 상태 추가
    document.getElementById(`${viewMode}ViewBtn`).classList.add('active');
    
    // 뷰 모드 설정
    currentView = viewMode;
    
    // 캘린더 다시 렌더링
    renderCalendar();
}

// 이전 달/주/일로 이동
function navigatePrevious() {
    if (currentView === 'month') {
        currentDate.setMonth(currentDate.getMonth() - 1);
    } else if (currentView === 'week') {
        currentDate.setDate(currentDate.getDate() - 7);
    } else if (currentView === 'day') {
        currentDate.setDate(currentDate.getDate() - 1);
    }
    
    updateCalendarHeader();
    renderCalendar();
}

// 다음 달/주/일로 이동
function navigateNext() {
    if (currentView === 'month') {
        currentDate.setMonth(currentDate.getMonth() + 1);
    } else if (currentView === 'week') {
        currentDate.setDate(currentDate.getDate() + 7);
    } else if (currentView === 'day') {
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    updateCalendarHeader();
    renderCalendar();
}

// 필터 적용
function applyFilters() {
    renderCalendar();
}

// 새 일정 추가 모달 열기
function openAddEventModal(date) {
    // 선택한 날짜 저장
    selectedDate = date;
    
    // 현재 선택된 이벤트 초기화
    selectedEvent = null;
    
    // 모달 제목 설정
    document.getElementById('eventModalTitle').textContent = '새 일정 추가';
    
    // 폼 초기화
    const form = document.getElementById('eventForm');
    form.reset();
    
    // 날짜 설정
    document.getElementById('eventDate').value = formatDate(date);
    
    // 반복 옵션 숨김
    document.getElementById('repeatOptions').style.display = 'none';
    
    // 오늘 날짜라면 현재 시간을 기본값으로 설정
    if (isCurrentDay(date)) {
        const now = new Date();
        const currentHour = String(now.getHours()).padStart(2, '0');
        const currentMinute = String(Math.floor(now.getMinutes() / 5) * 5).padStart(2, '0');
        document.getElementById('eventStartTime').value = `${currentHour}:${currentMinute}`;
        
        // 종료 시간은 1시간 후로 설정
        const endHour = String((now.getHours() + 1) % 24).padStart(2, '0');
        document.getElementById('eventEndTime').value = `${endHour}:${currentMinute}`;
    }
    
    // 모달 표시
    showModal('eventModal');
}

// 이벤트 저장
function saveEvent() {
    // 폼 데이터 가져오기
    const title = document.getElementById('eventTitle').value;
    const date = document.getElementById('eventDate').value;
    const startTime = document.getElementById('eventStartTime').value;
    const endTime = document.getElementById('eventEndTime').value;
    const category = document.getElementById('eventCategory').value;
    const description = document.getElementById('eventDescription').value;
    const repeat = document.getElementById('eventRepeat').checked;
    
    // 필수 필드 검증
    if (!title || !date) {
        alert('제목과 날짜는 필수 입력 항목입니다.');
        return;
    }
    
    // 반복 일정 설정
    let repeatType = null;
    let repeatUntil = null;
    
    if (repeat) {
        repeatType = document.getElementById('repeatType').value;
        repeatUntil = document.getElementById('repeatUntil').value;
    }
    
    // 이벤트 객체 생성
    const event = {
        id: selectedEvent ? selectedEvent.id : Date.now().toString(), // 기존 ID 유지 또는 새 ID 생성
        title: title,
        date: date,
        startTime: startTime,
        endTime: endTime,
        allDay: !startTime && !endTime,
        category: category,
        description: description,
        repeat: repeat,
        repeatType: repeatType,
        repeatUntil: repeatUntil
    };
    
    // 이벤트 저장 또는 업데이트
    if (selectedEvent) {
        // 기존 이벤트 업데이트
        updateExistingEvent(event);
    } else {
        // 새 이벤트 추가
        addNewEvent(event);
    }
    
    // 로컬 스토리지에 저장
    saveEventsToLocalStorage();
    
    // 모달 닫기
    closeModal('eventModal');
    
    // 캘린더 새로고침
    renderCalendar();
}

// 새 이벤트 추가
function addNewEvent(event) {
    if (event.category === 'personal') {
        personalEvents.push(event);
    } else if (event.category === 'business') {
        businessEvents.push(event);
    }
    
    // 전체 이벤트 목록 업데이트
    updateAllEvents();
}

// 기존 이벤트 업데이트
function updateExistingEvent(updatedEvent) {
    if (selectedEvent.category === 'personal') {
        const index = personalEvents.findIndex(event => event.id === updatedEvent.id);
        if (index !== -1) {
            personalEvents[index] = updatedEvent;
        }
    } else if (selectedEvent.category === 'business') {
        const index = businessEvents.findIndex(event => event.id === updatedEvent.id);
        if (index !== -1) {
            businessEvents[index] = updatedEvent;
        }
    }
    
    // 전체 이벤트 목록 업데이트
    updateAllEvents();
}

// 이벤트 삭제
function deleteEvent() {
    if (!selectedEvent) return;
    
    // 확인 메시지
    if (!confirm('이 일정을 삭제하시겠습니까?')) return;
    
    // 선적 일정은 삭제 불가
    if (selectedEvent.category === 'shipping' || selectedEvent.type === 'pending' || selectedEvent.type === 'complete') {
        alert('선적 일정은 삭제할 수 없습니다.');
        return;
    }
    
    // 이벤트 배열에서 제거
    if (selectedEvent.category === 'personal') {
        personalEvents = personalEvents.filter(event => event.id !== selectedEvent.id);
    } else if (selectedEvent.category === 'business') {
        businessEvents = businessEvents.filter(event => event.id !== selectedEvent.id);
    }
    
    // 로컬 스토리지 업데이트
    saveEventsToLocalStorage();
    
    // 전체 이벤트 목록 업데이트
    updateAllEvents();
    
    // 모달 닫기
    closeModal('eventDetailModal');
    
    // 캘린더 새로고침
    renderCalendar();
}

// 이벤트 수정 모드로 전환
function editEvent() {
    if (!selectedEvent) return;
    
    // 선적 일정은 편집 불가
    if (selectedEvent.category === 'shipping' || selectedEvent.type === 'pending' || selectedEvent.type === 'complete') {
        alert('선적 일정은 편집할 수 없습니다.');
        return;
    }
    
    // 상세 모달 닫기
    closeModal('eventDetailModal');
    
    // 폼 필드 채우기
    document.getElementById('eventModalTitle').textContent = '일정 수정';
    document.getElementById('eventTitle').value = selectedEvent.title;
    document.getElementById('eventDate').value = selectedEvent.date;
    document.getElementById('eventStartTime').value = selectedEvent.startTime || '';
    document.getElementById('eventEndTime').value = selectedEvent.endTime || '';
    document.getElementById('eventCategory').value = selectedEvent.category;
    document.getElementById('eventDescription').value = selectedEvent.description || '';
    
    // 반복 설정
    document.getElementById('eventRepeat').checked = selectedEvent.repeat || false;
    const repeatOptions = document.getElementById('repeatOptions');
    repeatOptions.style.display = selectedEvent.repeat ? 'block' : 'none';
    
    if (selectedEvent.repeat) {
        document.getElementById('repeatType').value = selectedEvent.repeatType || 'daily';
        document.getElementById('repeatUntil').value = selectedEvent.repeatUntil || '';
    }
    
    // 추가/편집 모달 열기
    showModal('eventModal');
}

// 모달 열기
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'block';
    }
}

// 모달 닫기
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

// 이벤트 상세 정보 표시
function showEventDetails(event) {
    // 선택한 이벤트 저장
    selectedEvent = event;
    
    // 제목 표시
    document.getElementById('detailEventTitle').textContent = event.title;
    
    // 카테고리 설정
    const categoryElement = document.getElementById('detailEventCategory');
    categoryElement.textContent = getCategoryName(event.category || event.type);
    categoryElement.className = `event-category ${event.category || event.type || 'default'}`;
    
    // 날짜 표시
    const dateObj = parseDate(event.date);
    document.getElementById('detailEventDate').textContent = formatDisplayDate(dateObj);
    
    // 시간 표시
    let timeText = '종일';
    if (event.startTime && event.endTime) {
        timeText = `${event.startTime} - ${event.endTime}`;
    }
    document.getElementById('detailEventTime').textContent = timeText;
    
    // 반복 정보 표시
    let repeatText = '반복 없음';
    if (event.repeat) {
        repeatText = getRepeatText(event.repeatType, event.repeatUntil);
    }
    document.getElementById('detailEventRepeat').textContent = repeatText;
    
    // 설명 표시
    document.getElementById('detailEventDescription').textContent = event.description || '설명 없음';
    
    // 편집/삭제 버튼 표시 여부 설정
    const editBtn = document.getElementById('editEventBtn');
    const deleteBtn = document.getElementById('deleteEventBtn');
    
    if (event.category === 'shipping' || event.type === 'pending' || event.type === 'complete') {
        // 선적 일정은 편집/삭제 불가
        editBtn.style.display = 'none';
        deleteBtn.style.display = 'none';
     } else {
        editBtn.style.display = 'inline-flex';
        deleteBtn.style.display = 'inline-flex';
     }
     
     // 모달 표시
     showModal('eventDetailModal');
     }
     
     // 카테고리 이름 가져오기
     function getCategoryName(category) {
        switch (category) {
            case 'personal': return '개인 일정';
            case 'business': return '업무 일정';
            case 'shipping': return '선적 일정';
            case 'pending': return '선적 시작';
            case 'complete': return '선적 완료';
            default: return '기타 일정';
        }
     }
     
     // 반복 텍스트 생성
     function getRepeatText(repeatType, repeatUntil) {
        let typeText = '';
        switch (repeatType) {
            case 'daily': typeText = '매일'; break;
            case 'weekly': typeText = '매주'; break;
            case 'monthly': typeText = '매월'; break;
            default: typeText = '반복';
        }
        
        if (repeatUntil) {
            const untilDate = new Date(repeatUntil);
            return `${typeText} (${untilDate.getFullYear()}년 ${untilDate.getMonth() + 1}월 ${untilDate.getDate()}일까지)`;
        }
        
        return typeText;
     }
     
     // 로컬 스토리지에서 이벤트 불러오기
     function loadEventsFromLocalStorage() {
        // 개인 일정 불러오기
        const storedPersonalEvents = localStorage.getItem(PERSONAL_EVENTS_KEY);
        if (storedPersonalEvents) {
            personalEvents = JSON.parse(storedPersonalEvents);
        }
        
        // 업무 일정 불러오기
        const storedBusinessEvents = localStorage.getItem(BUSINESS_EVENTS_KEY);
        if (storedBusinessEvents) {
            businessEvents = JSON.parse(storedBusinessEvents);
        }
        
        // 전체 이벤트 목록 업데이트
        updateAllEvents();
     }
     
     // 로컬 스토리지에 이벤트 저장
     function saveEventsToLocalStorage() {
        // 개인 일정 저장
        localStorage.setItem(PERSONAL_EVENTS_KEY, JSON.stringify(personalEvents));
        
        // 업무 일정 저장
        localStorage.setItem(BUSINESS_EVENTS_KEY, JSON.stringify(businessEvents));
     }
     
     // 선적 일정 데이터 로드 (수정된 함수)
     function loadShippingEvents() {
        // 기존 API 호출 대신 문서 기반 처리로 전환
        loadDocumentsAndProcess()
            .then(() => {
                console.log('문서 처리 완료, 선적 일정 생성됨');
                
                // 전체 이벤트 목록 업데이트
                updateAllEvents();
                
                // 캘린더 다시 렌더링
                renderCalendar();
            })
            .catch(error => {
                console.error('선적 일정 로드 중 오류 발생:', error);
                
                // 오류 상세 정보 로깅
                if (error.response) {
                    console.error('서버 응답 에러:', error.response);
                } else if (error.request) {
                    console.error('서버 응답 없음:', error.request);
                } else {
                    console.error('요청 설정 에러:', error.message);
                }
                
                // 대체 방식으로 API 호출 시도
                tryFallbackAPICall();
            });
     }
     
     // 대체 API 호출 시도 (기존 방식)
     function tryFallbackAPICall() {
        console.log('대체 API 호출 시도 중...');
        
        fetch(`${API_BASE_URL}/calendar/events`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API 호출 실패: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('API에서 받은 일정 데이터:', data);
                
                // shipping_events 배열을 사용
                if (data.shipping_events && Array.isArray(data.shipping_events)) {
                    shippingEvents = data.shipping_events.map(event => ({
                        id: `ship-${event.id}`,
                        title: event.title,
                        date: event.date,
                        category: 'shipping',
                        description: event.description,
                        is_confirmed: event.is_confirmed,
                        schedule_type: event.schedule_type,
                        brand: event.brand,
                        model_code: event.model_code,
                        model_name: event.model_name
                    }));
                } else {
                    console.warn('API에서 유효한 선적 일정 데이터를 받지 못했습니다');
                    shippingEvents = [];
                }
                
                // 전체 이벤트 목록 업데이트
                updateAllEvents();
                
                // 캘린더 다시 렌더링
                renderCalendar();
            })
            .catch(error => {
                console.error('대체 API 호출 실패:', error);
                shippingEvents = [];
                updateAllEvents();
                renderCalendar();
            });
     }
     
     // 문서 로드 및 처리 (새로운 함수)
     async function loadDocumentsAndProcess() {
        try {
            console.log('문서 로드 및 처리 시작');
            
            // 인보이스 데이터 로드
            const invoiceResponse = await fetch(`${API_BASE_URL}/documents/invoice`);
            if (!invoiceResponse.ok) {
                throw new Error(`인보이스 로드 실패: ${invoiceResponse.status}`);
            }
            const invoiceData = await invoiceResponse.json();
            allInvoices = invoiceData.invoices || [];
            console.log(`${allInvoices.length}개의 인보이스 문서 로드됨`);
            
            // 오더시트 데이터 로드
            const orderResponse = await fetch(`${API_BASE_URL}/documents/order`);
            if (!orderResponse.ok) {
                throw new Error(`오더시트 로드 실패: ${orderResponse.status}`);
            }
            const orderData = await orderResponse.json();
            allOrders = orderData.orders || [];
            console.log(`${allOrders.length}개의 오더시트 문서 로드됨`);
            
            // 문서 처리 및 일정 생성
            await processDocuments();
            
            return true;
        } catch (error) {
            console.error('문서 로드 및 처리 중 오류:', error);
            throw error;
        }
     }
     
     // 문서 처리 및 선적 일정 생성 (새로운 함수)
     async function processDocuments() {
        try {
            shippingEvents = []; // 기존 선적 일정 초기화
            matchedDocumentPairs = []; // 일치 문서 쌍 초기화
            
            console.log(`인보이스 개수: ${allInvoices.length}, 오더시트 개수: ${allOrders.length}`);
            
            // 처리된 쌍을 추적하기 위한 셋
            const processedPairs = new Set();
            
            // 가능한 모든 인보이스와 오더시트 조합에 대해 비교
            for (const invoice of allInvoices) {
                for (const order of allOrders) {
                    // 두 문서가 같은 브랜드에 속하는지 확인 (최적화)
                    if (invoice.brand === order.brand || invoice.brand === '자동 감지' || order.brand === '자동 감지') {
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
                            
                            // 비교 결과에서 일치 항목 확인
                            const matchPercentage = compareResult.summary.match_percentage;
                            console.log(`비교 결과: ${invoice.id} vs ${order.id} = ${matchPercentage}%`);
                            
                            // 일치율이 80% 이상인 문서 쌍만 처리
                            if (matchPercentage >= 80) {
                                console.log(`일치하는 문서 쌍 발견: ${invoice.id} vs ${order.id}, 일치율: ${matchPercentage}%`);
                                // 일치하는 문서 쌍 추가
                                matchedDocumentPairs.push({
                                    invoice,
                                    order,
                                    matches: compareResult.matches,
                                    brand: invoice.brand
                                });
                                
                                // 오더 문서의 상세 정보 가져옴
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
                                                    type: 'pending',
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
                                                    type: 'complete',
                                                    items: [],
                                                    brand: invoice.brand
                                                };
                                            }
                                            // 도착일이 다른 경우만 추가
                                            if (!startDate || formatDate(startDate) !== formatDate(endDate)) {
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
                                            if (shipData.type === 'pending') {
                                                eventTitle += '↗'; // 출발 아이콘
                                            } else {
                                                eventTitle += '↘'; // 도착 아이콘
                                            }
                                            
                                            // 완벽한 브랜드명 찾기
                                            let fullBrandName = invoice.brand;
                                            if (fullBrandName === '자동 감지') {
                                                fullBrandName = order.brand;
                                            }
                                            
                                            // 이벤트 색상 결정
                                            let eventColor;
                                            // 전체 브랜드명으로 먼저 시도
                                            if (BRAND_COLORS[fullBrandName]) {
                                                eventColor = BRAND_COLORS[fullBrandName];
                                            } 
                                            // 단축된 브랜드명으로 시도
                                            else if (fullBrandName.startsWith('TOGA')) {
                                                eventColor = BRAND_COLORS['TOGA VIRILIS'];
                                            } else if (fullBrandName.startsWith('WILD')) {
                                                eventColor = BRAND_COLORS['WILD DONKEY'];
                                            } else if (fullBrandName.startsWith('ATHLETICS')) {
                                                eventColor = BRAND_COLORS['ATHLETICS FTWR'];
                                            } else if (fullBrandName.startsWith('BASE')) {
                                                eventColor = BRAND_COLORS['BASERANGE'];
                                            } else if (fullBrandName.startsWith('NOU')) {
                                                eventColor = BRAND_COLORS['NOU NOU'];
                                            } else {
                                                eventColor = BRAND_COLORS['default'];
                                            }
                                            
                                            // 이벤트 객체 생성
                                            const calendarEvent = {
                                                id: `${order.id}-${dateKey}-${shipData.type}`,
                                                date: shipData.date,
                                                title: eventTitle,
                                                type: shipData.type,
                                                color: eventColor,
                                                brand: fullBrandName,
                                                description: `${shipData.items.length}개 품목`,
                                                items: shipData.items,
                                                document: {
                                                    invoice_id: invoice.id,
                                                    order_id: order.id
                                                },
                                                model_name: modelName,
                                                model_code: modelCode,
                                                // 선적 일정에 대한 추가 정보
                                                schedule_type: shipData.type === 'pending' ? 'start' : 'end',
                                                is_confirmed: true  // 문서 일치로 확정된 일정
                                            };
                                            
                                            // 이벤트 배열에 추가
                                            shippingEvents.push(calendarEvent);
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
            
            console.log(`총 ${shippingEvents.length}개의 선적 일정 이벤트가 생성되었습니다.`);
            
        } catch (error) {
            console.error('문서 처리 중 오류 발생:', error);
            throw error;
        }
     }
     
     // 날짜 문자열을 Date 객체로 변환 (다양한 형식 지원)
     function parseDate(dateString) {
        if (!dateString) return null;
        
        // 문자열 정리
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
        
        // 기타 형식 (YYYYMMDD, 등)
        const numericFormat = /^(\d{4})(\d{2})(\d{2})$/;
        const numericMatch = dateString.match(numericFormat);
        if (numericMatch) {
            const [_, year, month, day] = numericMatch;
            return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
        }
        
        // 기타 형식은 Date 생성자로 시도
        const dateObj = new Date(dateString);
        return isNaN(dateObj.getTime()) ? null : dateObj;
     }
     
     // 특정 날짜에 대한 모든 이벤트 표시
     function showDayEvents(date, events) {
        alert(`${formatDisplayDate(date)}의 모든 일정 (${events.length}개)`);
        
        // 향후 구현: 일간 뷰로 전환하여 해당 날짜의 모든 이벤트 표시
     }
     
     // 전체 이벤트 목록 업데이트
     function updateAllEvents() {
        // 모든 이벤트 합치기
        calendarEvents = [
            ...personalEvents,
            ...businessEvents,
            ...shippingEvents
        ];
     }
     
     // 이벤트 검색
     function searchEvents(searchText) {
        if (!searchText.trim()) {
            // 검색어가 없으면 전체 표시
            renderCalendar();
            return;
        }
        
        // 이벤트 검색 결과를 배열로 저장
        const searchResults = calendarEvents.filter(event => {
            return (
                event.title.toLowerCase().includes(searchText.toLowerCase()) ||
                (event.description && event.description.toLowerCase().includes(searchText.toLowerCase())) ||
                (event.brand && event.brand.toLowerCase().includes(searchText.toLowerCase()))
            );
        });
        
        // 결과가 없는 경우
        if (searchResults.length === 0) {
            alert(`'${searchText}' 검색 결과가 없습니다.`);
            return;
        }
        
        // 첫 번째 결과의 날짜로 이동
        if (searchResults.length > 0) {
            const firstResult = searchResults[0];
            const resultDate = parseDate(firstResult.date);
            
            // 현재 날짜 업데이트
            currentDate = new Date(resultDate.getFullYear(), resultDate.getMonth(), 1);
            
            // 캘린더 새로고침
            updateCalendarHeader();
            renderCalendar();
            
            // 결과 메시지
            alert(`'${searchText}' 검색 결과: ${searchResults.length}개 일정 찾음`);
        }
     }
     
     // 통계 지표 업데이트
     function updateMetrics() {
        // 브랜드 수 계산 (중복 제거)
        const uniqueBrands = new Set();
        shippingEvents.forEach(event => {
            if (event.brand) {
                uniqueBrands.add(event.brand);
            }
        });
        
        // 진행 중/완료된 거래 수 계산
        const today = new Date();
        today.setHours(0, 0, 0, 0); // 오늘 날짜의 시작으로 설정
        
        let inProgressCount = 0;
        let completedCount = 0;
        
        shippingEvents.forEach(event => {
            if (event.type === 'pending') {
                const eventDate = parseDate(event.date);
                if (eventDate >= today) {
                    inProgressCount++;
                } else {
                    completedCount++;
                }
            } else if (event.type === 'complete') {
                completedCount++;
            }
        });
        
        // 오늘의 일정 수 계산
        const todayDateStr = formatDate(today);
        const todayEvents = calendarEvents.filter(event => event.date === todayDateStr);
        
        // 지표 업데이트
        document.getElementById('total-clients').textContent = uniqueBrands.size;
        document.getElementById('in-progress-count').textContent = `${inProgressCount}건`;
        document.getElementById('completed-count').textContent = `${completedCount}건`;
        document.getElementById('today-events').textContent = `${todayEvents.length}건`;
     }