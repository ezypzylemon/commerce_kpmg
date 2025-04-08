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

// 캘린더 데이터
let currentDate = new Date();
let calendarEvents = [];          // 캘린더에 표시할 이벤트 배열
let personalEvents = [];          // 개인 일정 배열
let businessEvents = [];          // 업무 일정 배열
let shippingEvents = [];          // 선적 일정 배열
let currentView = 'month';        // 현재 뷰 모드 (month, week, day)
let selectedEvent = null;         // 현재 선택된 이벤트
let selectedDate = null;          // 선택된 날짜

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
    
    // 불일치가 많은 날짜 표시 (가상 데이터)
    const mismatchDates = [
        '2025-03-05', '2025-03-12', '2025-03-18', '2025-03-25'
    ];
    
    if (mismatchDates.includes(dateStr)) {
        dayElement.classList.add('has-mismatches');
        
        // 5%, 18일은 불일치가 매우 많은 날로 가정
        if (dateStr === '2025-03-18') {
            dayElement.classList.add('many-mismatches');
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
    eventElement.className = `calendar-event ${event.category}`;
    
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
    
    // 툴팁 추가 (상세 정보)
    let tooltipContent = `${event.title}`;
    if (event.startTime && event.endTime) {
        tooltipContent += `\n${event.startTime} - ${event.endTime}`;
    } else if (event.allDay) {
        tooltipContent += "\n종일";
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
                (event.category === 'shipping' && showShipping)) {
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
    if (selectedEvent.category === 'shipping') {
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
    if (selectedEvent.category === 'shipping') {
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
    categoryElement.textContent = getCategoryName(event.category);
    categoryElement.className = `event-category ${event.category}`;
    
    // 날짜 표시
    const dateObj = new Date(event.date);
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
    
    if (event.category === 'shipping') {
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

// 선적 일정 데이터 로드
function loadShippingEvents() {
    // API 호출
    fetchShippingData()
        .then(data => {
            // 선적 일정 배열 업데이트
            shippingEvents = data;
            
            // 전체 이벤트 목록 업데이트
            updateAllEvents();
            
            // 캘린더 다시 렌더링
            renderCalendar();
        })
        .catch(error => {
            console.error('선적 일정 로드 중 오류 발생:', error);
            
            // 오류 시 빈 배열 사용
            shippingEvents = [];
            
            // 전체 이벤트 목록 업데이트
            updateAllEvents();
            
            // 캘린더 다시 렌더링
            renderCalendar();
        });
}

// 선적 일정 API 호출
async function fetchShippingData() {
    try {
        // 인보이스 및 오더 문서 목록 가져오기
        const [invoiceResponse, orderResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/documents/invoice`),
            fetch(`${API_BASE_URL}/documents/order`)
        ]);
        
        if (!invoiceResponse.ok || !orderResponse.ok) {
            throw new Error('문서 데이터를 가져오는데 실패했습니다.');
        }
        
        const invoiceData = await invoiceResponse.json();
        const orderData = await orderResponse.json();
        
        // 비교 결과 이력 가져오기
        const comparisonResponse = await fetch(`${API_BASE_URL}/comparison-history?limit=100`);
        if (!comparisonResponse.ok) {
            throw new Error('비교 결과 데이터를 가져오는데 실패했습니다.');
        }
        
        const comparisonData = await comparisonResponse.json();
        
        // 선적 일정 추출 및 변환
        return extractShippingEvents(invoiceData, orderData, comparisonData);
    } catch (error) {
        console.error('API 호출 중 오류:', error);
        throw error;
    }
}

// 선적 일정 추출 함수
function extractShippingEvents(invoiceData, orderData, comparisonData) {
    const shippingEvents = [];
    
    // 오더 문서에서 선적 일정 추출
    if (orderData && orderData.orders && orderData.orders.length > 0) {
        // 각 오더 문서 처리
        orderData.orders.forEach(order => {
            // 오더 상세 정보 가져오기 (비동기 처리는 생략)
            const orderDetail = order;
            
            // 선적 시작일 추출
            if (orderDetail.items && orderDetail.items.length > 0) {
                // 품목별 선적 일정 생성
                orderDetail.items.forEach((item, index) => {
                    // 선적 시작일 추출
                    if (item.shipping_start) {
                        const shippingDate = parseDate(item.shipping_start);
                        if (shippingDate) {
                            shippingEvents.push({
                                id: `ship-start-${order.id}-${index}`,
                                title: `${order.brand} 선적 시작 - ${item.model_name || item.model_code}`,
                                date: formatDate(shippingDate),
                                category: 'shipping',
                                description: `${item.model_name || item.model_code} 선적 시작`,
                                documentId: order.id,
                                itemId: item.id || index
                            });
                        }
                    }
                    
                    // 선적 완료일 추출
                    if (item.shipping_end) {
                        const shippingEndDate = parseDate(item.shipping_end);
                        if (shippingEndDate) {
                            shippingEvents.push({
                                id: `ship-end-${order.id}-${index}`,
                                title: `${order.brand} 선적 완료 - ${item.model_name || item.model_code}`,
                                date: formatDate(shippingEndDate),
                                category: 'shipping',
                                description: `${item.model_name || item.model_code} 선적 완료`,
                                documentId: order.id,
                                itemId: item.id || index
                            });
                        }
                    }
                });
            }
        });
    }
    
    // 일치/불일치 결과 기반 이벤트 생성
    if (comparisonData && comparisonData.comparisons && comparisonData.comparisons.length > 0) {
        comparisonData.comparisons.forEach(comparison => {
            // 낮은 일치율(<80%)인 경우만 강조
            if (comparison.match_percentage < 80) {
                const comparisonDate = new Date(comparison.comparison_date);
                shippingEvents.push({
                    id: `mismatch-${comparison.id}`,
                    title: `${comparison.brand || '브랜드'} 문서 불일치 (${comparison.match_percentage.toFixed(0)}%)`,
                    date: formatDate(comparisonDate),
                    category: 'shipping',
                    description: `일치율: ${comparison.match_percentage.toFixed(1)}%, ` +
                                 `불일치 항목: ${comparison.mismatched_items}개`,
                    documentId: comparison.document1_id,
                    document2Id: comparison.document2_id
                });
            }
        });
    }
    
    return shippingEvents;
}

// 특정 날짜에 대한 모든 이벤트 표시
function showDayEvents(date, events) {
    alert(`${formatDisplayDate(date)}의 모든 일정 (${events.length}개)`);
    
    // 향후 구현: 일간 뷰로 전환하여 해당 날짜의 모든 이벤트 표시
}

// 날짜 파싱 (다양한 형식 지원)
function parseDate(dateString) {
    if (!dateString) return null;
    
    // 문자열 정리
    dateString = dateString.trim();
    
    // MM/DD/YYYY 형식
    const usMatch = dateString.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (usMatch) {
        const [_, month, day, year] = usMatch;
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
    
    // DD-MM-YYYY 형식
    const euMatch = dateString.match(/^(\d{1,2})-(\d{1,2})-(\d{4})$/);
    if (euMatch) {
        const [_, day, month, year] = euMatch;
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
    
    // YYYY-MM-DD 형식
    const isoMatch = dateString.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (isoMatch) {
        const [_, year, month, day] = isoMatch;
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
    
    // 기타 형식은 Date 생성자로 시도
    const dateObj = new Date(dateString);
    return isNaN(dateObj.getTime()) ? null : dateObj;
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
            (event.description && event.description.toLowerCase().includes(searchText.toLowerCase()))
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
        const resultDate = new Date(firstResult.date);
        
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
        if (event.title) {
            // 제목에서 브랜드 추출 시도
            const brandMatch = event.title.match(/^(TOGA VIRILIS|WILD DONKEY|ATHLETICS FTWR|BASERANGE|NOU NOU)/);
            if (brandMatch) {
                uniqueBrands.add(brandMatch[1]);
            }
        }
    });
    
    // 진행 중/완료된 거래 수 계산
    const today = new Date();
    today.setHours(0, 0, 0, 0); // 오늘 날짜의 시작으로 설정
    
    let inProgressCount = 0;
    let completedCount = 0;
    
    shippingEvents.forEach(event => {
        if (event.title && event.title.includes('선적 시작')) {
            const eventDate = new Date(event.date);
            eventDate.setHours(0, 0, 0, 0);
            
            // 시작일이 오늘 이후인 경우 진행 중으로 간주
            if (eventDate >= today) {
                inProgressCount++;
            }
        } else if (event.title && event.title.includes('선적 완료')) {
            const eventDate = new Date(event.date);
            eventDate.setHours(0, 0, 0, 0);
            
            // 완료일이 오늘 이전인 경우 완료된 것으로 간주
            if (eventDate < today) {
                completedCount++;
            }
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