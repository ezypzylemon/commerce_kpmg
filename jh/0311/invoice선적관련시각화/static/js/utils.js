/**
 * OCR 문서 관리 시스템 유틸리티 스크립트
 * 스트림릿 애플리케이션과 함께 사용하기 위한 클라이언트 측 유틸리티 함수들
 */

// 페이지 로드 시 실행될 함수
document.addEventListener('DOMContentLoaded', function() {
  // 커스텀 컴포넌트 초기화
  initCustomComponents();
  
  // 이벤트 리스너 등록
  addEventListeners();
});

/**
 * 커스텀 UI 컴포넌트 초기화
 */
function initCustomComponents() {
  // 툴팁 초기화
  initTooltips();
  
  // 모달 초기화
  initModals();
  
  // 그래프 초기화
  initCharts();
}

/**
 * 툴팁 기능 초기화
 */
function initTooltips() {
  // 툴팁 속성이 있는 모든 요소를 찾아 이벤트 리스너 추가
  const tooltipElements = document.querySelectorAll('[data-tooltip]');
  tooltipElements.forEach(element => {
    element.addEventListener('mouseenter', showTooltip);
    element.addEventListener('mouseleave', hideTooltip);
  });
}

/**
 * 툴팁 표시 함수
 * @param {Event} event - 마우스 이벤트
 */
function showTooltip(event) {
  const tooltipText = event.target.getAttribute('data-tooltip');
  
  // 툴팁 엘리먼트 생성
  const tooltip = document.createElement('div');
  tooltip.className = 'custom-tooltip';
  tooltip.textContent = tooltipText;
  
  // 툴팁 위치 설정
  tooltip.style.position = 'absolute';
  tooltip.style.top = `${event.pageY + 10}px`;
  tooltip.style.left = `${event.pageX + 10}px`;
  tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
  tooltip.style.color = 'white';
  tooltip.style.padding = '5px 10px';
  tooltip.style.borderRadius = '4px';
  tooltip.style.fontSize = '12px';
  tooltip.style.zIndex = '1000';
  
  // 툴팁을 DOM에 추가
  document.body.appendChild(tooltip);
  
  // 툴팁 참조 저장
  event.target.tooltip = tooltip;
}

/**
 * 툴팁 숨김 함수
 * @param {Event} event - 마우스 이벤트
 */
function hideTooltip(event) {
  if (event.target.tooltip) {
    event.target.tooltip.remove();
    event.target.tooltip = null;
  }
}

/**
 * 모달 초기화 함수
 */
function initModals() {
  // 모달 열기 버튼에 이벤트 리스너 추가
  const modalOpenButtons = document.querySelectorAll('[data-modal-open]');
  modalOpenButtons.forEach(button => {
    button.addEventListener('click', openModal);
  });
  
  // 모달 닫기 버튼에 이벤트 리스너 추가
  const modalCloseButtons = document.querySelectorAll('[data-modal-close]');
  modalCloseButtons.forEach(button => {
    button.addEventListener('click', closeModal);
  });
}

/**
 * 모달 열기 함수
 * @param {Event} event - 클릭 이벤트
 */
function openModal(event) {
  const modalId = event.target.getAttribute('data-modal-open');
  const modal = document.getElementById(modalId);
  
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // 스크롤 방지
  }
}

/**
 * 모달 닫기 함수
 * @param {Event} event - 클릭 이벤트
 */
function closeModal(event) {
  const modalId = event.target.getAttribute('data-modal-close');
  const modal = document.getElementById(modalId);
  
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto'; // 스크롤 복원
  }
}

/**
 * 외부 클릭으로 모달 닫기
 * @param {Event} event - 클릭 이벤트
 */
function closeModalOnOutsideClick(event) {
  if (event.target.classList.contains('modal')) {
    event.target.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

/**
 * 이벤트 리스너 등록
 */
function addEventListeners() {
  // 모달 외부 클릭 시 닫기
  const modals = document.querySelectorAll('.modal');
  modals.forEach(modal => {
    modal.addEventListener('click', closeModalOnOutsideClick);
  });
  
  // 폼 제출 전 데이터 유효성 검사
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', validateForm);
  });
}

/**
 * 폼 유효성 검사
 * @param {Event} event - 폼 제출 이벤트
 */
function validateForm(event) {
  const form = event.target;
  const requiredFields = form.querySelectorAll('[required]');
  
  let isValid = true;
  
  // 필수 필드 검사
  requiredFields.forEach(field => {
    if (!field.value.trim()) {
      isValid = false;
      showFieldError(field, '이 필드는 필수입니다.');
    } else {
      clearFieldError(field);
    }
  });
  
  // 유효성 검사 실패 시 폼 제출 방지
  if (!isValid) {
    event.preventDefault();
  }
}

/**
 * 필드 오류 표시
 * @param {HTMLElement} field - 폼 필드
 * @param {string} message - 오류 메시지
 */
function showFieldError(field, message) {
  // 이미 오류 메시지가 있는지 확인
  let errorElement = field.nextElementSibling;
  if (!errorElement || !errorElement.classList.contains('error-message')) {
    errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.style.color = '#e74c3c';
    errorElement.style.fontSize = '12px';
    errorElement.style.marginTop = '4px';
    field.parentNode.insertBefore(errorElement, field.nextSibling);
  }
  
  errorElement.textContent = message;
  field.style.borderColor = '#e74c3c';
}

/**
 * 필드 오류 지우기
 * @param {HTMLElement} field - 폼 필드
 */
function clearFieldError(field) {
  const errorElement = field.nextElementSibling;
  if (errorElement && errorElement.classList.contains('error-message')) {
    errorElement.remove();
  }
  field.style.borderColor = '';
}

/**
 * 알림 메시지 표시
 * @param {string} message - 알림 메시지
 * @param {string} type - 알림 유형 (success, error, warning, info)
 * @param {number} duration - 표시 지속 시간 (밀리초)
 */
function showNotification(message, type = 'info', duration = 3000) {
  // 알림 컨테이너 확인 또는 생성
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }
  
  // 알림 엘리먼트 생성
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <div class="notification-content">${message}</div>
    <button class="notification-close">&times;</button>
  `;
  
  // 알림 스타일 설정
  notification.style.backgroundColor = getNotificationColor(type);
  notification.style.color = 'white';
  notification.style.padding = '12px';
  notification.style.marginBottom = '10px';
  notification.style.borderRadius = '4px';
  notification.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
  notification.style.display = 'flex';
  notification.style.justifyContent = 'space-between';
  notification.style.alignItems = 'center';
  notification.style.width = '300px';
  notification.style.maxWidth = '100%';
  notification.style.transition = 'all 0.3s ease';
  notification.style.opacity = '0';
  
  // 닫기 버튼 스타일
  const closeButton = notification.querySelector('.notification-close');
  closeButton.style.background = 'none';
  closeButton.style.border = 'none';
  closeButton.style.color = 'white';
  closeButton.style.fontSize = '20px';
  closeButton.style.cursor = 'pointer';
  
  // 컨테이너에 알림 추가
  container.appendChild(notification);
  
  // 애니메이션 효과를 위해 setTimeout 사용
  setTimeout(() => {
    notification.style.opacity = '1';
  }, 10);
  
  // 닫기 버튼 이벤트 리스너
  closeButton.addEventListener('click', () => {
    closeNotification(notification);
  });
  
  // 자동 닫기
  if (duration > 0) {
    setTimeout(() => {
      closeNotification(notification);
    }, duration);
  }
}

/**
 * 알림 메시지 닫기
 * @param {HTMLElement} notification - 알림 엘리먼트
 */
function closeNotification(notification) {
  notification.style.opacity = '0';
  setTimeout(() => {
    notification.remove();
  }, 300);
}

/**
 * 알림 유형에 따른 색상 반환
 * @param {string} type - 알림 유형
 * @returns {string} 색상 코드
 */
function getNotificationColor(type) {
  switch (type) {
    case 'success':
      return '#2ecc71';
    case 'error':
      return '#e74c3c';
    case 'warning':
      return '#f39c12';
    case 'info':
    default:
      return '#3498db';
  }
}

/**
 * 차트 초기화 함수
 */
function initCharts() {
  // 스트림릿과 통합된 차트는 스트림릿에서 자동으로 처리되므로
  // 이 함수는 필요 시 커스텀 차트 요소를 초기화하는 데 사용될 수 있습니다
}

/**
 * 파일 확장자 가져오기
 * @param {string} filename - 파일명
 * @returns {string} 파일 확장자
 */
function getFileExtension(filename) {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
}

/**
 * 파일 크기 형식화
 * @param {number} bytes - 바이트 단위 크기
 * @returns {string} 형식화된 파일 크기
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 날짜 형식화
 * @param {Date|string} date - 날짜 객체 또는 문자열
 * @param {string} format - 날짜 형식 (예: 'YYYY-MM-DD')
 * @returns {string} 형식화된 날짜 문자열
 */
function formatDate(date, format = 'YYYY-MM-DD') {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

/**
 * 엘리먼트 스크롤 가능하게 만들기
 * @param {HTMLElement} element - 스크롤 가능하게 만들 엘리먼트
 */
function makeScrollable(element) {
  element.style.overflow = 'auto';
}

/**
 * 이미지 미리보기 생성
 * @param {File} file - 이미지 파일
 * @param {HTMLElement} previewElement - 미리보기를 표시할 엘리먼트
 */
function createImagePreview(file, previewElement) {
  if (!file.type.startsWith('image/')) {
    previewElement.innerHTML = '이미지 파일이 아닙니다.';
    return;
  }
  
  const reader = new FileReader();
  reader.onload = function(e) {
    previewElement.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; max-height: 300px;">`;
  };
  reader.readAsDataURL(file);
}

/**
 * 스트림릿 세션 상태 업데이트 트리거
 * 이 함수는 Streamlit이 제공하는 함수를 사용하므로 실제 환경에서 테스트 필요
 * @param {string} key - 상태 키
 * @param {any} value - 새 값
 */
function updateStreamlitState(key, value) {
  // Streamlit에 이벤트 발송
  if (window.parent.Streamlit) {
    window.parent.Streamlit.setComponentValue({
      type: 'updateState',
      key: key,
      value: value
    });
  }
}

// 외부에서 사용할 수 있도록 함수 내보내기
window.ocrUtils = {
  showNotification,
  formatFileSize,
  formatDate,
  createImagePreview,
  getFileExtension
};
