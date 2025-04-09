/**
 * news.js - 뉴스 분석 페이지 JavaScript 코드
 * 사용자 상호작용 및 데이터 시각화를 관리합니다.
 */

// DOM 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM 로드 완료, 초기화 시작');
    // 필터 및 설정 요소 초기화
    initializeFilters();
    
    // 탭 기능 초기화
    initializeTabs();
    
    // 자세히 보기 기능 초기화
    initializeDetailViews();
    
    // 추가 분석 요청 버튼 초기화
    initializeAnalysisButtons();
    
    // 시각화 요소 초기화
    initializeVisualizations();
    
    // *** 추가: 키워드 트렌드 초기 로딩 ***
    loadKeywordTrendIfNeeded();
});


console.log('loadKeywordTrendIfNeeded 함수 실행 시작');
/**
 * 필요한 경우 키워드 트렌드 데이터 로드
 */
/**
 * 필요한 경우 키워드 트렌드 데이터 로드
 */
// 키워드 트렌드 로드 함수
function loadKeywordTrendIfNeeded() {
    console.log('loadKeywordTrendIfNeeded 함수 실행');
    
    const trendContainer = document.querySelector('.trend-container');
    const noDataContainer = document.querySelector('.trend-container + .no-data');
    
    if ((trendContainer && trendContainer.innerHTML.trim() === '') || 
        (noDataContainer && noDataContainer.style.display !== 'none')) {
        
        console.log('키워드 트렌드 데이터 자동 로드');
        
        // 기간 값 가져오기
        const period = document.getElementById('period-selector')?.value || '7일';
        
        // API URL 생성
        let apiUrl = `/api/news/trend?period=${encodeURIComponent(period)}`;

        // custom 기간인 경우 시작일/종료일 추가
        if (period === 'custom') {
            const startDate = document.getElementById('start-date')?.value;
            const endDate = document.getElementById('end-date')?.value;
            
            if (startDate && endDate && startDate !== 'None' && endDate !== 'None') {
                apiUrl += `&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;
            }
        }
        
        console.log('API 호출 URL:', apiUrl);
        
        // 로딩 표시
        if (trendContainer) {
            trendContainer.innerHTML = '<div class="loading-indicator">로딩 중...</div>';
        }
        
        // 캐시 방지를 위한 타임스탬프 추가
        const timestamp = new Date().getTime();
        apiUrl += `&_=${timestamp}`;
        
        // AJAX 요청
        fetch(apiUrl)
            .then(response => {
                console.log('API 응답 상태:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('API 응답 데이터 키:', Object.keys(data));
                
                if (trendContainer && data.keyword_trend) {
                    console.log('트렌드 컨테이너에 데이터 삽입 시작');
                    
                    // HTML 데이터가 아닌 경우 확인
                    if (typeof data.keyword_trend !== 'string') {
                        console.error('keyword_trend가 문자열이 아닙니다:', typeof data.keyword_trend);
                        trendContainer.innerHTML = '<div class="error-message">데이터 형식이 올바르지 않습니다.</div>';
                        return;
                    }
                    
                    trendContainer.innerHTML = data.keyword_trend;
                    console.log('트렌드 컨테이너에 데이터 삽입 완료');
                    
                    // Plotly 초기화 확인
                    if (window.Plotly) {
                        console.log('Plotly 객체 존재함');
                        try {
                            // Plotly 차트 재계산 시도
                            const plotlyCharts = trendContainer.querySelectorAll('.js-plotly-plot');
                            console.log('찾은 Plotly 차트 수:', plotlyCharts.length);
                            
                            if (plotlyCharts.length > 0) {
                                window.setTimeout(() => {
                                    window.Plotly.Plots.resize(plotlyCharts[0]);
                                    console.log('Plotly 차트 리사이즈 완료');
                                }, 100);
                            }
                        } catch (e) {
                            console.error('Plotly 차트 초기화 오류:', e);
                        }
                    } else {
                        console.warn('Plotly 객체 없음');
                    }
                    // 데이터가 없는 경우
                    console.log('키워드 트렌드 데이터가 없습니다');
                    if (trendContainer) trendContainer.innerHTML = '';
                    if (noDataContainer) noDataContainer.style.display = 'block';
                }
            });
    }
}

/**
 * 현재 설정된 기간 정보 반환
 * @returns {string} URL 쿼리 문자열
 */
function getCurrentPeriod() {
    // 2번: 함수 실행 로깅
    console.log('getCurrentPeriod 함수 실행');
    
    const urlParams = new URLSearchParams(window.location.search);
    let period = urlParams.get('period') || '7일';
    
    console.log('URL에서 추출한 period 값:', period);
    
    let query = 'period=' + encodeURIComponent(period);
    
    // custom 기간인 경우에만 시작일/종료일 추가
    if (period === 'custom') {
        const startDate = urlParams.get('start_date');
        const endDate = urlParams.get('end_date');
        
        console.log('커스텀 기간 파라미터:', { startDate, endDate });
        
        if (startDate && endDate) {
            query += '&start_date=' + encodeURIComponent(startDate) + 
                     '&end_date=' + encodeURIComponent(endDate);
        }
    }
    
    // 2번: 최종 쿼리 문자열 로깅
    console.log('생성된 쿼리 문자열:', query);
    
    return query;
}

/* 현재 설정된 기간 정보 반환
* @returns {string} URL 쿼리 문자열
*
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
*/
/**
 * 필터 및 기간 설정 초기화
 */
function initializeFilters() {
    // 기간 선택 변경 이벤트
    const periodSelector = document.getElementById('period-selector');
    if (periodSelector) {
        periodSelector.addEventListener('change', function() {
            const period = this.value;
            
            // custom 기간 선택 시 날짜 선택기 표시
            const dateRangeContainer = document.getElementById('date-range-container');
            if (dateRangeContainer) {
                dateRangeContainer.style.display = period === 'custom' ? 'block' : 'none';
            }
        });
        
        // 초기 상태 설정
        if (periodSelector.value === 'custom') {
            const dateRangeContainer = document.getElementById('date-range-container');
            if (dateRangeContainer) {
                dateRangeContainer.style.display = 'block';
            }
        }
    }
    
    // 필터 적용 버튼
    const applyFilterBtn = document.getElementById('apply-filter-btn');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            const period = periodSelector ? periodSelector.value : '7일';
            
            let url = window.location.pathname + '?period=' + encodeURIComponent(period);
            
            // custom 기간인 경우 시작일/종료일 추가
            if (period === 'custom') {
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                
                if (startDate && endDate) {
                    url += '&start_date=' + encodeURIComponent(startDate) + 
                           '&end_date=' + encodeURIComponent(endDate);
                }
            }
            
            // 페이지 이동
            window.location.href = url;
        });
    }
}

/**
 * 탭 기능 초기화
 */
function initializeTabs() {
    const tabContainers = document.querySelectorAll('.tab-container');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.tab-item');
        const tabContents = container.querySelectorAll('.tab-content');
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', function() {
                // 모든 탭 비활성화
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // 선택한 탭 활성화
                this.classList.add('active');
                tabContents[index].classList.add('active');
            });
        });
        
        // 첫 번째 탭 기본 활성화
        if (tabs.length > 0 && tabContents.length > 0) {
            tabs[0].classList.add('active');
            tabContents[0].classList.add('active');
        }
    });
}

/**
 * 자세히 보기 기능 초기화
 */
function initializeDetailViews() {
    // 카드 클릭시 자세히 보기 (최신 뉴스 등)
    const articleItems = document.querySelectorAll('.article-item');
    
    articleItems.forEach(item => {
        item.addEventListener('click', function() {
            const detailSection = this.querySelector('.article-detail');
            if (detailSection) {
                // 클릭 시 상세 정보 토글
                detailSection.style.display = 
                    detailSection.style.display === 'none' || detailSection.style.display === '' ? 
                    'block' : 'none';
            }
        });
    });
}



/**
 * 추가 분석 버튼 초기화
 */
function initializeAnalysisButtons() {
    // TF-IDF 분석 버튼
    const tfidfAnalysisBtn = document.getElementById('tfidf-analysis-btn');
    if (tfidfAnalysisBtn) {
        tfidfAnalysisBtn.addEventListener('click', function() {
            const loadingIndicator = document.getElementById('tfidf-loading');
            const resultContainer = document.getElementById('tfidf-result');
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (resultContainer) resultContainer.innerHTML = '';
            
            // AJAX 요청
            fetch('/api/news/tfidf?' + getCurrentPeriod())
                .then(response => response.json())
                .then(data => {
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    
                    if (resultContainer && data.chart) {
                        resultContainer.innerHTML = data.chart;
                    }
                })
                .catch(error => {
                    console.error('TF-IDF 분석 요청 실패:', error);
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    if (resultContainer) {
                        resultContainer.innerHTML = '<div class="error-message">분석 중 오류가 발생했습니다.</div>';
                    }
                });
        });
    }
    
    // 토픽 모델링 분석 버튼
    const topicAnalysisBtn = document.getElementById('topic-analysis-btn');
    if (topicAnalysisBtn) {
        topicAnalysisBtn.addEventListener('click', function() {
            const loadingIndicator = document.getElementById('topic-loading');
            const resultContainer = document.getElementById('topic-result');
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (resultContainer) resultContainer.innerHTML = '';
            
            // AJAX 요청
            fetch('/api/news/topics?' + getCurrentPeriod())
                .then(response => response.json())
                .then(data => {
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    
                    if (resultContainer && data.charts) {
                        let html = '';
                        if (data.charts.distribution) {
                            html += '<div class="chart-container">' + data.charts.distribution + '</div>';
                        }
                        if (data.charts.heatmap) {
                            html += '<div class="chart-container">' + data.charts.heatmap + '</div>';
                        }
                        resultContainer.innerHTML = html;
                    }
                })
                .catch(error => {
                    console.error('토픽 분석 요청 실패:', error);
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    if (resultContainer) {
                        resultContainer.innerHTML = '<div class="error-message">분석 중 오류가 발생했습니다.</div>';
                    }
                });
        });
    }
    
    // 감성 분석 버튼
    const sentimentAnalysisBtn = document.getElementById('sentiment-analysis-btn');
    if (sentimentAnalysisBtn) {
        sentimentAnalysisBtn.addEventListener('click', function() {
            const loadingIndicator = document.getElementById('sentiment-loading');
            const resultContainer = document.getElementById('sentiment-result');
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (resultContainer) resultContainer.innerHTML = '';
            
            // AJAX 요청
            fetch('/api/news/sentiment?' + getCurrentPeriod())
                .then(response => response.json())
                .then(data => {
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    
                    if (resultContainer && data.charts) {
                        let html = '';
                        if (data.charts.pie_chart) {
                            html += '<div class="chart-container">' + data.charts.pie_chart + '</div>';
                        }
                        if (data.charts.time_chart) {
                            html += '<div class="chart-container">' + data.charts.time_chart + '</div>';
                        }
                        resultContainer.innerHTML = html;
                    }
                })
                .catch(error => {
                    console.error('감성 분석 요청 실패:', error);
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    if (resultContainer) {
                        resultContainer.innerHTML = '<div class="error-message">분석 중 오류가 발생했습니다.</div>';
                    }
                });
        });
    }
}

/**
 * 시각화 요소 초기화
 */
function initializeVisualizations() {
    // 클릭 가능한 키워드 추가
    const keywordItems = document.querySelectorAll('.keyword-list li');
    
    keywordItems.forEach(item => {
        item.addEventListener('click', function() {
            const keyword = this.querySelector('.keyword-text').textContent;
            searchKeyword(keyword);
        });
    });

    // 시계열 분석 버튼
    const timeseriesAnalysisBtn = document.getElementById('timeseries-analysis-btn');
    if (timeseriesAnalysisBtn) {
        timeseriesAnalysisBtn.addEventListener('click', function() {
            const loadingIndicator = document.getElementById('timeseries-loading');
            const resultContainer = document.getElementById('timeseries-result');
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (resultContainer) resultContainer.innerHTML = '';
            
            // 선택된 시간 단위 가져오기
            const timeUnit = document.querySelector('input[name="time-unit"]:checked').value;
            
            // AJAX 요청
            fetch(`/api/news/trend?unit=${timeUnit}&${getCurrentPeriod()}`)
                .then(response => response.json())
                .then(data => {
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    
                    if (resultContainer) {
                        if (data.time_chart) {
                            resultContainer.innerHTML = `
                                <div class="chart-container">
                                    <h5>시계열 분석 (${timeUnit === 'daily' ? '일별' : timeUnit === 'weekly' ? '주별' : '월별'})</h5>
                                    ${data.time_chart}
                                </div>
                            `;
                            
                            // 키워드 트렌드도 함께 추가
                            if (data.keyword_trend) {
                                resultContainer.innerHTML += `
                                    <div class="chart-container">
                                        <h5>키워드 트렌드</h5>
                                        ${data.keyword_trend}
                                    </div>
                                `;
                            }
                        } else {
                            resultContainer.innerHTML = '<div class="no-data">분석 데이터가 없습니다.</div>';
                        }
                    }
                })
                .catch(error => {
                    console.error('시계열 분석 요청 실패:', error);
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    if (resultContainer) {
                        resultContainer.innerHTML = '<div class="error-message">분석 중 오류가 발생했습니다.</div>';
                    }
                });
        });
    }

    
    // 워드클라우드 상호작용 (해당되는 경우)
    const wordcloudContainer = document.querySelector('.wordcloud-container');
    if (wordcloudContainer) {
        wordcloudContainer.addEventListener('click', function(event) {
            // 이미지 맵이나 SVG 요소가 있는 경우 처리
            // 이 부분은 워드클라우드 구현 방식에 따라 달라질 수 있음
        });
    }
    
    // 네트워크 그래프 상호작용
    // Plotly나 D3.js 등의 라이브러리로 구현된 그래프는
    // 해당 라이브러리의 이벤트 처리 방식을 사용
}

/**
 * 키워드 검색 실행
 * @param {string} keyword - 검색할 키워드
 */
function searchKeyword(keyword) {
    // 예시: 키워드로 기사 필터링 AJAX 요청
    console.log('키워드 검색:', keyword);
    
    const loadingIndicator = document.getElementById('search-loading');
    const resultContainer = document.getElementById('search-result');
    
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (resultContainer) resultContainer.innerHTML = '';
    
    // AJAX 요청
    fetch('/api/news/search?keyword=' + encodeURIComponent(keyword) + '&' + getCurrentPeriod())
        .then(response => response.json())
        .then(data => {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            
            if (resultContainer) {
                if (data.articles && data.articles.length > 0) {
                    let html = '<h5>검색 결과: "' + keyword + '"</h5><div class="search-articles">';
                    
                    data.articles.forEach(article => {
                        html += `
                            <div class="article-item">
                                <a href="${article.link}" target="_blank" class="article-link">
                                    <h6 class="mb-1">${article.title}</h6>
                                </a>
                                <p class="article-preview mb-1">${article.content?.substring(0, 100)}...</p>
                                <small class="text-muted">${article.upload_date}</small>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    resultContainer.innerHTML = html;
                } else {
                    resultContainer.innerHTML = '<div class="no-results">검색 결과가 없습니다.</div>';
                }
            }
        })
        .catch(error => {
            console.error('검색 요청 실패:', error);
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (resultContainer) {
                resultContainer.innerHTML = '<div class="error-message">검색 중 오류가 발생했습니다.</div>';
            }
        });
}

/**


/**
 * 워드클라우드 이미지 확대 보기
 * @param {string} imgSrc - 이미지 소스 URL
 */
function openImageModal(imgSrc) {
    const modal = document.getElementById('image-modal');
    if (!modal) return;
    
    const modalImg = modal.querySelector('.modal-img');
    if (modalImg) {
        modalImg.src = imgSrc;
    }
    
    modal.style.display = 'block';
}

/**
 * 모달 닫기
 */
function closeModal() {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('image-modal');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }
};