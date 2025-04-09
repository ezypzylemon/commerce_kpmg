// 기간 필터 초기화 및 이벤트 처리
function initPeriodFilter(pageId) {
  console.log('기간 필터 초기화: ' + pageId);
  
  // 기간 선택 드롭다운 이벤트 처리
  const periodSelect = document.getElementById(`period-filter-${pageId}`);
  const customPeriodContainer = document.getElementById(`custom-period-${pageId}`);
  
  if (periodSelect) {
    periodSelect.addEventListener('change', function() {
      const selectedPeriod = this.value;
      console.log('선택된 기간: ' + selectedPeriod);
      
      if (selectedPeriod === 'custom') {
        // 직접 설정 선택 시 날짜 입력 필드 표시
        customPeriodContainer.classList.remove('hidden');
        
        // 커스텀 이벤트 발생 (직접 설정 UI 표시)
        document.dispatchEvent(new CustomEvent('periodUIChanged', {
          detail: { period: selectedPeriod, action: 'showCustomUI' }
        }));
      } else {
        // 다른 옵션 클릭 시 해당 기간으로 페이지 이동
        const currentPath = window.location.pathname;
        const searchParams = new URLSearchParams(window.location.search);
        
        // 기존 파라미터 제거
        searchParams.delete('period');
        searchParams.delete('start_date');
        searchParams.delete('end_date');
        
        // 새 파라미터 설정
        searchParams.set('period', selectedPeriod);
        
        // 기간 변경 이벤트 발생
        document.dispatchEvent(new CustomEvent('periodChanged', {
          detail: { period: selectedPeriod }
        }));
        
        // 페이지 이동
        window.location.href = `${currentPath}?${searchParams.toString()}`;
      }
    });
  }
  
  // Flatpickr 초기화
  initDatepickers(pageId);
}

// Flatpickr 달력 초기화
function initDatepickers(pageId) {
  const startDate = document.getElementById(`start-date-${pageId}`);
  const endDate = document.getElementById(`end-date-${pageId}`);
  
  if (startDate && endDate) {
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);
    
    // URL에서 날짜 파라미터 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const startDateParam = urlParams.get('start_date');
    const endDateParam = urlParams.get('end_date');
    
    // Flatpickr 초기화
    const startDatePicker = flatpickr(`#start-date-${pageId}`, {
      locale: 'ko',
      dateFormat: "Y-m-d",
      maxDate: "today",
      defaultDate: startDateParam || oneMonthAgo,
      onChange: function(selectedDates, dateStr) {
        if (dateStr) {
          endDatePicker.set('minDate', dateStr);
        }
      }
    });
    
    const endDatePicker = flatpickr(`#end-date-${pageId}`, {
      locale: 'ko',
      dateFormat: "Y-m-d",
      maxDate: "today",
      defaultDate: endDateParam || today,
      onChange: function(selectedDates, dateStr) {
        if (dateStr) {
          startDatePicker.set('maxDate', dateStr);
        }
      }
    });
  }
}

// 직접 설정 날짜 적용 함수
function applyCustomDate(pageId) {
  const startDate = document.getElementById(`start-date-${pageId}`).value;
  const endDate = document.getElementById(`end-date-${pageId}`).value;
  
  if (!startDate || !endDate) {
    alert('시작 날짜와 종료 날짜를 모두 선택해주세요.');
    return;
  }
  
  // 현재 URL 구성
  const currentPath = window.location.pathname;
  const searchParams = new URLSearchParams(window.location.search);
  
  // 기존 파라미터 제거
  searchParams.delete('period');
  searchParams.delete('start_date');
  searchParams.delete('end_date');
  
  // 새 파라미터 설정
  searchParams.set('period', 'custom');
  searchParams.set('start_date', startDate);
  searchParams.set('end_date', endDate);
  
  // 기간 변경 이벤트 발생
  document.dispatchEvent(new CustomEvent('periodChanged', {
    detail: { 
      period: 'custom', 
      startDate: startDate, 
      endDate: endDate 
    }
  }));
  
  // 페이지 이동
  window.location.href = `${currentPath}?${searchParams.toString()}`;
}

// 페이지 로드 시 필터 초기화
document.addEventListener('DOMContentLoaded', function() {
  // 현재 페이지 ID 확인
  const path = window.location.pathname;
  const pageId = path.substring(1) || 'dashboard'; // 경로에서 첫 번째 슬래시 이후의 문자열
  
  // 필터 초기화
  initPeriodFilter(pageId);
}); 