// static/js/musinsa.js

document.addEventListener('DOMContentLoaded', function() {
  // 현재 페이지 ID 설정
  const pageId = 'musinsa';
  
  // 필터 초기화 (기존 period_filter.js에서 제공하는 함수 호출)
  if (typeof initPeriodFilter === 'function') {
    initPeriodFilter(pageId);
  }
  
  // 탭 전환 기능 초기화
  initTabs();
  
  // 브랜드 카드 클릭 이벤트 초기화
  initBrandCards();
  
  // 히트맵 클릭 이벤트 초기화
  initHeatmapInteraction();
});

/**
 * 탭 전환 기능 초기화
 */
function initTabs() {
  const tabs = document.querySelectorAll('.tab');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      // 모든 탭에서 active 클래스 제거
      tabs.forEach(t => t.classList.remove('active'));
      
      // 클릭한 탭에 active 클래스 추가
      this.classList.add('active');
      
      // 모든 탭 컨텐츠 숨기기
      const tabContents = document.querySelectorAll('.tab-content');
      tabContents.forEach(content => content.classList.remove('active'));
      
      // 선택한 탭의 컨텐츠 표시
      const tabId = this.getAttribute('data-tab');
      const targetContent = document.getElementById(tabId + '-tab');
      if (targetContent) {
        targetContent.classList.add('active');
      }
    });
  });
}

/**
 * 브랜드 카드 클릭 이벤트 초기화
 */
function initBrandCards() {
  const brandItems = document.querySelectorAll('.brand-item');
  
  brandItems.forEach(item => {
    item.addEventListener('click', function() {
      // 모든 아이템에서 active 클래스 제거
      brandItems.forEach(b => b.classList.remove('active'));
      
      // 클릭한 아이템에 active 클래스 추가
      this.classList.add('active');
      
      // 브랜드 정보 가져오기
      const brandId = this.getAttribute('data-brand-id');
      const brandText = this.querySelector('.brand-text').textContent;
      // 브랜드 이름 추출 (번호 제거)
      const brandName = brandText.split('. ')[1];
      
      // 브랜드 상세 정보 API 호출
      fetchBrandDetails(brandName);
    });
  });
}

/**
 * 브랜드 상세 정보 API 호출
 * @param {string} brandName - 브랜드 이름
 */
function fetchBrandDetails(brandName) {
  // 로딩 메시지 표시
  const detailContainer = document.getElementById('brand-detail');
  if (detailContainer) {
    // 기존 차트 컨테이너와 데이터 없음 메시지 참조
    const chartContainer = document.getElementById('detail-chart-container');
    const noDataMessage = document.getElementById('detail-no-data');
    
    // 차트 컨테이너 숨기기, 로딩 표시
    if (chartContainer) chartContainer.style.display = 'none';
    if (noDataMessage) noDataMessage.style.display = 'none';
    
    // 브랜드 이름 업데이트
    const brandNameElement = detailContainer.querySelector('.detail-brand-name');
    if (brandNameElement) {
      brandNameElement.textContent = brandName;
      // 로딩 표시 추가
      brandNameElement.innerHTML = `${brandName} <small style="font-size: 0.8rem; color: #999;">(로딩 중...)</small>`;
    }
  }
  
  // API 호출
  fetch(`/api/brand-details?brand=${encodeURIComponent(brandName)}`)
    .then(response => {
      if (!response.ok) {
        throw new Error('브랜드 정보를 불러올 수 없습니다.');
      }
      return response.json();
    })
    .then(details => {
      updateBrandDetailUI(details);
    })
    .catch(error => {
      console.error('브랜드 상세 정보 조회 오류:', error);
      displayErrorMessage(error.message);
    });
}

/**
 * 브랜드 상세 정보 UI 업데이트
 * @param {Object} details - 브랜드 상세 정보
 */
function updateBrandDetailUI(details) {
  // 상세 컨테이너 참조
  const detailContainer = document.getElementById('brand-detail');
  if (!detailContainer) return;
  
  // 기본 정보 업데이트
  const brandNameElement = detailContainer.querySelector('.detail-brand-name');
  const detailCategory = detailContainer.querySelector('.detail-category');
  const statValues = detailContainer.querySelectorAll('.stat-value');
  
  if (brandNameElement) brandNameElement.textContent = details.name;
  if (detailCategory) detailCategory.textContent = `카테고리: ${details.category}`;
  
  // 통계 값 업데이트
  if (statValues && statValues.length >= 3) {
    // 가격대 정보
    const priceRange = `${details.price_info.min_price}~${details.price_info.max_price}`;
    statValues[0].textContent = priceRange;
    
    // 성별 정보
    statValues[1].textContent = details.gender.join(', ');
    
    // 언급량 또는 평점 정보
    statValues[2].textContent = details.rating_info.avg_rating;
  }
  
  // 차트 컨테이너 업데이트
  const chartContainer = document.getElementById('detail-chart-container');
  const noDataMessage = document.getElementById('detail-no-data');
  
  if (chartContainer) {
    chartContainer.style.display = 'block';
    if (noDataMessage) noDataMessage.style.display = 'none';
    
    // 차트 데이터 생성
    chartContainer.innerHTML = `
      <div style="font-size: 0.9rem; margin-bottom: 10px; text-align: center;">
        <strong>${details.name}</strong> 월별 언급량 추이
      </div>
      <div style="display: flex; height: 100px; align-items: flex-end; justify-content: space-between; padding: 0 10px;">
        ${generateBarChart(details.monthly_data || generateDummyMonthlyData())}
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #999; margin-top: 5px; padding: 0 10px;">
        ${generateMonthLabels()}
      </div>
    `;
  }
}

/**
 * 더미 월간 데이터 생성 (API가 데이터를 제공하지 않을 경우)
 * @returns {Array} 월간 데이터 배열
 */
function generateDummyMonthlyData() {
  return [
    { month: '1월', count: Math.floor(Math.random() * 1000 + 800) },
    { month: '2월', count: Math.floor(Math.random() * 1000 + 900) },
    { month: '3월', count: Math.floor(Math.random() * 1000 + 1000) },
    { month: '4월', count: Math.floor(Math.random() * 1000 + 1100) },
    { month: '5월', count: Math.floor(Math.random() * 1000 + 1200) },
    { month: '6월', count: Math.floor(Math.random() * 1000 + 1300) }
  ];
}

/**
 * 월 레이블 생성
 * @returns {string} 월 레이블 HTML
 */
function generateMonthLabels() {
  const months = ['1월', '2월', '3월', '4월', '5월', '6월'];
  return months.map(month => `<span>${month}</span>`).join('');
}

/**
 * 간단한 바 차트 생성
 * @param {Array} data - 차트 데이터
 * @returns {string} 바 차트 HTML
 */
function generateBarChart(data) {
  // 최대값 찾기
  const maxValue = Math.max(...data.map(item => item.count));
  
  // 각 월별 바 생성
  return data.map(item => {
    const height = (item.count / maxValue) * 100;
    return `
      <div style="display: flex; flex-direction: column; align-items: center; width: 30px;">
        <div style="height: ${height}%; width: 20px; background-color: #4a90e2; border-radius: 3px 3px 0 0;"></div>
      </div>
    `;
  }).join('');
}

/**
 * 오류 메시지 표시
 * @param {string} message - 오류 메시지
 */
function displayErrorMessage(message) {
  const detailContainer = document.getElementById('brand-detail');
  if (!detailContainer) return;
  
  // 브랜드 이름 요소 참조
  const brandNameElement = detailContainer.querySelector('.detail-brand-name');
  if (brandNameElement) {
    // 오류 메시지 표시
    brandNameElement.innerHTML = brandNameElement.textContent.split(' <small')[0];
  }
  
  // 카테고리 요소 참조
  const detailCategory = detailContainer.querySelector('.detail-category');
  if (detailCategory) {
    detailCategory.textContent = '카테고리: -';
  }
  
  // 통계 값 초기화
  const statValues = detailContainer.querySelectorAll('.stat-value');
  if (statValues) {
    statValues.forEach(value => {
      value.textContent = '-';
    });
  }
  
  // 차트 컨테이너 숨기기
  const chartContainer = document.getElementById('detail-chart-container');
  if (chartContainer) {
    chartContainer.style.display = 'none';
  }
  
  // 데이터 없음 메시지 표시
  const noDataMessage = document.getElementById('detail-no-data');
  if (noDataMessage) {
    noDataMessage.style.display = 'block';
    noDataMessage.textContent = `${message} 다시 시도해주세요.`;
  }
}

/**
 * 히트맵 상호작용 초기화
 */
function initHeatmapInteraction() {
  const heatmapCells = document.querySelectorAll('.grid-row:not(.header-row) .grid-cell:not(:first-child)');
  
  heatmapCells.forEach(cell => {
    cell.addEventListener('click', function() {
      // 카테고리와 미디어 타입 가져오기
      const category = this.parentElement.querySelector('.grid-cell:first-child').textContent;
      const mediaType = this.parentElement.parentElement.querySelector('.header-row .grid-cell:nth-child(' + 
                       (Array.from(this.parentElement.children).indexOf(this) + 1) + ')').textContent;
      
      // 언급량 가져오기
      const count = this.textContent;
      
      // 알림 표시 (실제 구현에서는 모달 또는 상세 정보 표시)
      alert(`${category} 카테고리의 ${mediaType} 미디어 타입 언급량: ${count}`);
    });
  });
}