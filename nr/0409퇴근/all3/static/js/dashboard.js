/**
 * dashboard.js - 통합 대시보드 페이지 JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('대시보드 초기화 시작');
    
    // 현재 페이지 ID 설정
    const pageId = 'dashboard';
    
    // 기간 필터 초기화
    if (typeof initPeriodFilter === 'function') {
      initPeriodFilter(pageId);
    } else {
      console.warn('기간 필터 함수를 찾을 수 없습니다.');
    }
    
    // 리포트 탭 전환 기능
    initReportTabs();
    
    // 캘린더 기능 초기화
    initCalendar();
    
    // 트렌드 데이터 로드
    loadTrendData();
    
    // 차트 리사이즈 처리
    handleChartResize();
  });
  
  /**
   * 리포트 탭 초기화
   */
  function initReportTabs() {
    const reportTabs = document.querySelectorAll('.report-tab');
    const reportPanels = document.querySelectorAll('.report-panel');
    
    reportTabs.forEach(tab => {
      tab.addEventListener('click', function() {
        const tabId = this.dataset.tab;
        
        // 모든 탭 비활성화
        reportTabs.forEach(t => t.classList.remove('active'));
        reportPanels.forEach(p => p.classList.remove('active'));
        
        // 선택한 탭 활성화
        this.classList.add('active');
        document.getElementById(tabId)?.classList.add('active');
      });
    });
  }
  
  /**
   * 캘린더 기능 초기화
   */
  function initCalendar() {
    const prevMonthBtn = document.querySelector('.prev-month');
    const nextMonthBtn = document.querySelector('.next-month');
    const currentMonthEl = document.getElementById('current-month');
    
    if (prevMonthBtn && nextMonthBtn && currentMonthEl) {
      // 현재 표시된 월 정보
      let currentDate = new Date();
      
      // 초기 월 표시
      currentMonthEl.textContent = formatMonth(currentDate);
      
      // 이전 달 버튼
      prevMonthBtn.addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() - 1);
        currentMonthEl.textContent = formatMonth(currentDate);
        updateCalendarData(currentDate);
      });
      
      // 다음 달 버튼
      nextMonthBtn.addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() + 1);
        currentMonthEl.textContent = formatMonth(currentDate);
        updateCalendarData(currentDate);
      });
      
      // 초기 캘린더 데이터 로드
      updateCalendarData(currentDate);
    } else {
      console.warn('캘린더 요소를 찾을 수 없습니다.');
    }
  }
  
  /**
   * 캘린더 데이터 업데이트
   * @param {Date} date - 표시할 달의 날짜 객체
   */
  function updateCalendarData(date) {
    console.log(`${date.getFullYear()}년 ${date.getMonth() + 1}월 데이터 요청`);
    
    // 예시로 로딩 표시 추가
    const calendarDays = document.querySelector('.calendar-days');
    if (calendarDays) {
      calendarDays.innerHTML = '<div class="calendar-loading">로딩 중...</div>';
    }
    
    // API 엔드포인트 URL (실제 구현 시 사용)
    const apiUrl = `/api/calendar-events?year=${date.getFullYear()}&month=${date.getMonth() + 1}`;
    
    // AJAX 요청으로 데이터 가져오기 (실제 구현 시 사용)
    /* 
    fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        renderCalendar(date, data.events);
      })
      .catch(error => {
        console.error('캘린더 데이터 로드 오류:', error);
        // 오류 시 빈 캘린더 렌더링
        renderCalendar(date, []);
      });
    */
    
    // 샘플 데이터로 임시 구현 (실제 구현에서는 서버 데이터 사용)
    setTimeout(() => {
      renderCalendar(date, [
        { date: new Date(date.getFullYear(), date.getMonth(), 3), title: '서울패션위크' },
        { date: new Date(date.getFullYear(), date.getMonth(), 15), title: '패션 아트 전시회' },
        { date: new Date(date.getFullYear(), date.getMonth(), 25), title: '지속가능 패션 포럼' }
      ]);
    }, 500);
  }
  
  /**
   * 캘린더 렌더링
   * @param {Date} date - 표시할 달의 날짜 객체
   * @param {Array} events - 이벤트 목록
   */
  function renderCalendar(date, events) {
    const calendarDays = document.querySelector('.calendar-days');
    if (!calendarDays) return;
    
    // 해당 월의 첫 날과 마지막 날
    const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
    const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    
    // 첫 날의 요일 (0: 일요일, 6: 토요일)
    const firstDayOfWeek = firstDay.getDay();
    
    // HTML 생성
    let html = '';
    
    // 첫 날 이전의 빈 칸
    for (let i = 0; i < firstDayOfWeek; i++) {
      html += '<div class="calendar-day empty"></div>';
    }
    
    // 해당 월의 날짜 채우기
    for (let day = 1; day <= lastDay.getDate(); day++) {
      const currentDate = new Date(date.getFullYear(), date.getMonth(), day);
      
      // 이벤트가 있는지 확인
      const hasEvent = events.some(event => 
        event.date.getDate() === day &&
        event.date.getMonth() === currentDate.getMonth() &&
        event.date.getFullYear() === currentDate.getFullYear()
      );
      
      // 이벤트가 있으면 클래스 추가
      const eventClass = hasEvent ? 'has-event' : '';
      
      // 이벤트 제목 데이터 속성 추가
      const eventTitle = hasEvent 
        ? events.find(event => 
            event.date.getDate() === day &&
            event.date.getMonth() === currentDate.getMonth() &&
            event.date.getFullYear() === currentDate.getFullYear()
          ).title 
        : '';
      
      html += `<div class="calendar-day ${eventClass}" data-events="${eventTitle}">${day}</div>`;
    }
    
    // 캘린더 업데이트
    calendarDays.innerHTML = html;
    
    // 날짜 클릭 이벤트 재설정
    document.querySelectorAll('.calendar-day').forEach(day => {
      day.addEventListener('click', function() {
        if (this.classList.contains('empty')) return;
        
        // 선택한 날짜 하이라이트
        document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
        this.classList.add('selected');
        
        // 이벤트 정보 표시
        const events = this.getAttribute('data-events');
        if (events) {
          updateEventDetails(date.getFullYear(), date.getMonth() + 1, parseInt(this.textContent), events);
        }
      });
    });
    
    // 이벤트 목록 업데이트
    updateEventList(events);
  }
  
  /**
   * 이벤트 목록 업데이트
   * @param {Array} events - 이벤트 목록
   */
  function updateEventList(events) {
    const eventList = document.querySelector('.event-list');
    if (!eventList) return;
    
    if (events.length === 0) {
      eventList.innerHTML = '<div class="no-events">이번 달 등록된 이벤트가 없습니다.</div>';
      return;
    }
    
    let html = '';
    events.forEach(event => {
      const dateStr = `${event.date.getMonth() + 1}월 ${event.date.getDate()}일`;
      html += `
        <div class="event-item">
          <span class="event-date">${dateStr}</span>
          <span class="event-title">${event.title}</span>
          <span class="event-location">${event.location || '장소 미정'}</span>
        </div>
      `;
    });
    
    eventList.innerHTML = html;
  }
  
  /**
   * 선택된 날짜의 이벤트 상세 정보 업데이트
   * @param {number} year - 년도
   * @param {number} month - 월
   * @param {number} day - 일
   * @param {string} eventTitle - 이벤트 제목
   */
  function updateEventDetails(year, month, day, eventTitle) {
    const eventDetails = document.querySelector('.event-details');
    if (!eventDetails) return;
    
    // 이벤트 제목이 있는 경우 상세 정보 표시
    if (eventTitle) {
      eventDetails.innerHTML = `
        <h5>${month}월 ${day}일 이벤트</h5>
        <div class="event-detail-card">
          <div class="event-title">${eventTitle}</div>
          <div class="event-time">10:00 AM - 6:00 PM</div>
          <div class="event-description">
            ${eventTitle}와 관련된 상세 정보입니다. 실제 구현에서는 서버에서 이벤트 상세 정보를 가져와 표시합니다.
          </div>
        </div>
      `;
    }
  }
  
  /**
   * 트렌드 데이터 로드
   */
  function loadTrendData() {
    // 현재 기간 설정 가져오기
    const period = getCurrentPeriod();
    
    // 통합 트렌드 데이터 API 엔드포인트 (실제 구현 시 사용)
    const apiUrl = `/api/integrated-trends?${period}`;
    
    console.log('트렌드 데이터 로드 요청:', apiUrl);
    
    // AJAX 요청으로 데이터 가져오기 (실제 구현 시 사용)
    /* 
    fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        updateTrendData(data);
      })
      .catch(error => {
        console.error('트렌드 데이터 로드 오류:', error);
      });
    */
  }
  
  /**
   * 트렌드 데이터 업데이트
   * @param {Object} data - 트렌드 데이터
   */
  function updateTrendData(data) {
    // 키워드 리스트 업데이트
    if (data.topKeywords) {
      const keywordList = document.querySelector('.keyword-list');
      if (keywordList) {
        let html = '';
        data.topKeywords.forEach((keyword, index) => {
          const isTopThree = index < 3 ? 'top-three' : '';
          html += `
            <div class="keyword-item ${isTopThree}">
              <span class="keyword-rank">${index + 1}</span>
              <div class="keyword-details">
                <span class="keyword-text">${keyword.text}</span>
                <span class="keyword-description">${keyword.description}</span>
              </div>
            </div>
          `;
        });
        keywordList.innerHTML = html;
      }
    }
    
    // 트렌드 인사이트 업데이트
    if (data.trendInsight) {
      const insightContent = document.querySelector('.trend-insight .insight-content p');
      if (insightContent) {
        insightContent.textContent = data.trendInsight;
      }
    }
    
    // 바잉 인사이트 업데이트
    if (data.buyingInsight) {
      const buyingContent = document.querySelector('.buying-recommendations p');
      if (buyingContent) {
        buyingContent.textContent = data.buyingInsight.summary;
      }
      
      const recommendationList = document.querySelector('.recommendation-list');
      if (recommendationList && data.buyingInsight.recommendations) {
        let html = '';
        data.buyingInsight.recommendations.forEach(rec => {
          html += `
            <li>
              <span class="product-category">${rec.category}</span>
              <span class="product-name">${rec.name}</span>
              <span class="recommendation-reason">${rec.reason}</span>
            </li>
          `;
        });
        recommendationList.innerHTML = html;
      }
    }
    
    // 셀링 인사이트 업데이트
    if (data.sellingInsight) {
      const sellingContent = document.querySelector('.marketing-recommendations p');
      if (sellingContent) {
        sellingContent.textContent = data.sellingInsight.summary;
      }
      
      const marketingKeywords = document.querySelector('.marketing-keywords');
      if (marketingKeywords && data.sellingInsight.keywords) {
        let html = '';
        data.sellingInsight.keywords.forEach(kw => {
          html += `
            <div class="marketing-keyword">
              <span class="keyword-text">#${kw.text}</span>
              <span class="keyword-stats">${kw.stats}</span>
            </div>
          `;
        });
        marketingKeywords.innerHTML = html;
      }
    }
    
    // 리포트 데이터 업데이트
    if (data.keywordReports) {
      data.keywordReports.forEach((report, index) => {
        const reportPanel = document.getElementById(`keyword${index + 1}`);
        if (reportPanel) {
          const reportTitle = reportPanel.querySelector('h4');
          if (reportTitle) {
            reportTitle.textContent = `${report.keyword} 분석 리포트`;
          }
          
          const reportSummary = reportPanel.querySelector('.report-summary p');
          if (reportSummary) {
            reportSummary.textContent = report.summary;
          }
        }
      });
    }
  }
  
  /**
   * 현재 설정된 기간 정보 반환
   * @returns {string} URL 쿼리 문자열
   */
  function getCurrentPeriod() {
    const urlParams = new URLSearchParams(window.location.search);
    let period = urlParams.get('period') || '7일';
    
    let query = 'period=' + encodeURIComponent(period);
    
    // custom 기간인 경우에만 시작일/종료일 추가
    if (period === 'custom') {
      const startDate = urlParams.get('start_date');
      const endDate = urlParams.get('end_date');
      
      if (startDate && endDate) {
        query += '&start_date=' + encodeURIComponent(startDate) + 
                 '&end_date=' + encodeURIComponent(endDate);
      }
    }
    
    return query;
  }
  
  /**
   * 차트 리사이즈 처리
   */
  function handleChartResize() {
    window.addEventListener('resize', function() {
      const plotlyCharts = document.querySelectorAll('.js-plotly-plot');
      if (window.Plotly && plotlyCharts.length > 0) {
        plotlyCharts.forEach(chart => {
          window.Plotly.Plots.resize(chart);
        });
      }
    });
  }
  
  /**
   * 날짜 형식 도우미 함수
   * @param {Date} date - 날짜 객체
   * @returns {string} 형식화된 연월 문자열
   */
  function formatMonth(date) {
    return `${date.getFullYear()}년 ${date.getMonth() + 1}월`;
  }