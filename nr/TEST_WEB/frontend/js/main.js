// 전역 변수 선언
let allProducts = []; // 모든 제품 데이터
let filteredProducts = []; // 필터링된 제품 데이터
let currentPage = 1;
const productsPerPage = 12;

// 카테고리 코드 매핑
const categoryMapping = {
    '001': '상의',
    '002': '아우터',
    '003': '바지',
    '020': '원피스',
    '022': '스커트',
    '004': '가방',
    '005': '신발',
    '006': '액세서리',
    '017': '스포츠/용품'
};

// 카테고리 코드를 숫자로 변환하는 맵
const categoryCodeToNum = {
    '001': 1,
    '002': 2,
    '003': 3,
    '020': 20,
    '022': 22,
    '004': 4,
    '005': 5,
    '006': 6,
    '017': 17
};

// 차트 객체 저장
let categoryChart, priceChart, ratingChart, brandChart;

// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 데이터 로드
    loadData();
    
    // 필터 이벤트 리스너 설정
    document.getElementById('categoryFilter').addEventListener('change', filterProducts);
    document.getElementById('sortBy').addEventListener('change', filterProducts);
});

// CSV 데이터 로드 함수
function loadData() {
    // 상대 경로에서 CSV 파일 로드 시도
    Papa.parse('../data/musinsa_fake_data.csv', {
        download: true,
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: function(results) {
            handleDataLoad(results.data);
        },
        error: function(error) {
            // 첫 번째 경로에서 실패하면 두 번째 경로 시도
            Papa.parse('data/musinsa_fake_data.csv', {
                download: true,
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                complete: function(results) {
                    handleDataLoad(results.data);
                },
                error: function(error) {
                    console.error('CSV 파일을 로드할 수 없습니다:', error);
                    // 테스트용 더미 데이터 생성
                    generateDummyData();
                }
            });
        }
    });
}

// 데이터 처리 함수
function handleDataLoad(data) {
    // 데이터 전처리
    allProducts = data.map(item => {
        // 숫자 문자열을 숫자로 변환 (가격, 평점 등)
        if (typeof item.price === 'string') {
            item.price = parseInt(item.price.replace(/[^\d]/g, '')) || 0;
        }
        
        // 평점이 없는 경우 0으로 설정
        if (item.rating === undefined || item.rating === null) {
            item.rating = 0;
        }
        
        // 리뷰 수가 없는 경우 0으로 설정
        if (item.review_count === undefined || item.review_count === null) {
            item.review_count = 0;
        }
        
        return item;
    });
    
    // 초기 필터링 적용
    filteredProducts = [...allProducts];
    
    // 대시보드 업데이트
    updateDashboard();
    
    // 제품 목록 및 페이지네이션 업데이트
    updateProductList();
}

// 테스트용 더미 데이터 생성 함수
function generateDummyData() {
    const categories = ['001', '002', '003', '020', '022', '004', '005', '006', '017'];
    const brands = ['나이키', '아디다스', '무신사 스탠다드', '커버낫', '디스이즈네버댓', '스톤아일랜드', '폴로', '메종키츠네', '아크네', '메종마르지엘라'];
    
    allProducts = [];
    
    // 카테고리당 약 17개 제품, 총 150개 제품 생성
    for (let i = 1; i <= 150; i++) {
        const categoryIndex = Math.floor(i / 17) % categories.length;
        const categoryCode = categories[categoryIndex];
        
        const product = {
            product_id: i,
            category: categoryMapping[categoryCode],
            category_code: categoryCodeToNum[categoryCode],
            link: `https://www.musinsa.com/products/${i}`,
            brand: brands[Math.floor(Math.random() * brands.length)],
            name: `더미 제품 ${i} - ${categoryMapping[categoryCode]}`,
            price: Math.floor(Math.random() * 150000) + 10000,
            rating: (Math.random() * 3 + 2).toFixed(1), // 2.0에서 5.0 사이
            review_count: Math.floor(Math.random() * 1000)
        };
        
        allProducts.push(product);
    }
    
    // 초기 필터링 적용
    filteredProducts = [...allProducts];
    
    // 대시보드 업데이트
    updateDashboard();
    
    // 제품 목록 및 페이지네이션 업데이트
    updateProductList();
}

// 제품 필터링 함수
function filterProducts() {
    const categorySelect = document.getElementById('categoryFilter');
    const sortSelect = document.getElementById('sortBy');
    
    const selectedCategory = categorySelect.value;
    const sortOption = sortSelect.value;
    
    // 카테고리 필터링
    if (selectedCategory === 'all') {
        filteredProducts = [...allProducts];
    } else {
        const categoryCode = categoryCodeToNum[selectedCategory];
        filteredProducts = allProducts.filter(product => product.category_code === categoryCode);
    }
    
    // 정렬
    switch (sortOption) {
        case 'price_asc':
            filteredProducts.sort((a, b) => a.price - b.price);
            break;
        case 'price_desc':
            filteredProducts.sort((a, b) => b.price - a.price);
            break;
        case 'rating_desc':
            filteredProducts.sort((a, b) => b.rating - a.rating);
            break;
        case 'review_desc':
            filteredProducts.sort((a, b) => b.review_count - a.review_count);
            break;
    }
    
    // 페이지 초기화
    currentPage = 1;
    
    // 대시보드 업데이트
    updateDashboard();
    
    // 제품 목록 및 페이지네이션 업데이트
    updateProductList();
}

// 대시보드 업데이트 함수
function updateDashboard() {
    // 요약 통계 업데이트
    updateSummaryStats();
    
    // 차트 업데이트
    updateCharts();
}

// 요약 통계 업데이트 함수
function updateSummaryStats() {
    const totalProducts = filteredProducts.length;
    
    // 평균 가격 계산
    const totalPrice = filteredProducts.reduce((sum, product) => sum + (product.price || 0), 0);
    const avgPrice = totalPrice / totalProducts || 0;
    
    // 평균 평점 계산
    const totalRating = filteredProducts.reduce((sum, product) => sum + (product.rating || 0), 0);
    const avgRating = totalRating / totalProducts || 0;
    
    // 총 리뷰 수 계산
    const totalReviews = filteredProducts.reduce((sum, product) => sum + (product.review_count || 0), 0);
    
    // 통계 표시
    document.getElementById('totalProducts').textContent = totalProducts.toLocaleString();
    document.getElementById('avgPrice').textContent = Math.round(avgPrice).toLocaleString() + '원';
    document.getElementById('avgRating').textContent = avgRating.toFixed(1);
    document.getElementById('totalReviews').textContent = totalReviews.toLocaleString();
}

// 차트 업데이트 함수
function updateCharts() {
    // 카테고리별 상품 수 데이터 준비
    const categoryData = {};
    for (const code in categoryMapping) {
        categoryData[categoryMapping[code]] = 0;
    }
    
    allProducts.forEach(product => {
        if (product.category && categoryData.hasOwnProperty(product.category)) {
            categoryData[product.category]++;
        }
    });
    
    // 카테고리별 가격 데이터 준비
    const categoryPriceData = {};
    const categoryRatingData = {};
    const categoryCount = {};
    
    allProducts.forEach(product => {
        if (product.category) {
            if (!categoryPriceData[product.category]) {
                categoryPriceData[product.category] = 0;
                categoryRatingData[product.category] = 0;
                categoryCount[product.category] = 0;
            }
            
            categoryPriceData[product.category] += (product.price || 0);
            categoryRatingData[product.category] += (product.rating || 0);
            categoryCount[product.category]++;
        }
    });
    
    // 평균 계산
    for (const category in categoryPriceData) {
        if (categoryCount[category] > 0) {
            categoryPriceData[category] = Math.round(categoryPriceData[category] / categoryCount[category]);
            categoryRatingData[category] = parseFloat((categoryRatingData[category] / categoryCount[category]).toFixed(1));
        }
    }
    
    // 브랜드 데이터 준비
    const brandData = {};
    allProducts.forEach(product => {
        if (product.brand) {
            brandData[product.brand] = (brandData[product.brand] || 0) + 1;
        }
    });
    
    // 상위 10개 브랜드 추출
    const topBrands = Object.entries(brandData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .reduce((obj, [key, value]) => {
            obj[key] = value;
            return obj;
        }, {});
    
    // 차트 업데이트 또는 생성
    updateCategoryChart(categoryData);
    updatePriceChart(categoryPriceData);
    updateRatingChart(categoryRatingData);
    updateBrandChart(topBrands);
}

// 카테고리 차트 업데이트 함수
function updateCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    // 기존 차트 삭제
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    // 새 차트 생성
    categoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: '상품 수',
                data: Object.values(data),
                backgroundColor: 'rgba(0, 120, 255, 0.7)',
                borderColor: 'rgba(0, 120, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// 가격 차트 업데이트 함수
function updatePriceChart(data) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // 기존 차트 삭제
    if (priceChart) {
        priceChart.destroy();
    }
    
    // 새 차트 생성
    priceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: '평균 가격 (원)',
                data: Object.values(data),
                backgroundColor: 'rgba(255, 159, 64, 0.7)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString() + '원';
                        }
                    }
                }
            }
        }
    });
}

// 평점 차트 업데이트 함수
function updateRatingChart(data) {
    const ctx = document.getElementById('ratingChart').getContext('2d');
    
    // 기존 차트 삭제
    if (ratingChart) {
        ratingChart.destroy();
    }
    
    // 새 차트 생성
    ratingChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: '평균 평점',
                data: Object.values(data),
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// 브랜드 차트 업데이트 함수
function updateBrandChart(data) {
    const ctx = document.getElementById('brandChart').getContext('2d');
    
    // 기존 차트 삭제
    if (brandChart) {
        brandChart.destroy();
    }
    
    // 새 차트 생성
    brandChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: '제품 수',
                data: Object.values(data),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)',
                    'rgba(40, 159, 64, 0.7)',
                    'rgba(240, 120, 120, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(199, 199, 199, 1)',
                    'rgba(83, 102, 255, 1)',
                    'rgba(40, 159, 64, 1)',
                    'rgba(240, 120, 120, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 10
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value}개 (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 제품 목록 업데이트 함수
function updateProductList() {
    const productListContainer = document.getElementById('productList');
    const paginationContainer = document.getElementById('pagination');
    
    // 페이지네이션 계산
    const totalPages = Math.ceil(filteredProducts.length / productsPerPage);
    const startIndex = (currentPage - 1) * productsPerPage;
    const endIndex = Math.min(startIndex + productsPerPage, filteredProducts.length);
    
    // 컨테이너 초기화
    productListContainer.innerHTML = '';
    
    // 제품이 없는 경우 메시지 표시
    if (filteredProducts.length === 0) {
        productListContainer.innerHTML = '<div class="no-products">검색 결과가 없습니다.</div>';
        paginationContainer.innerHTML = '';
        return;
    }
    
    // 현재 페이지의 제품 표시
    for (let i = startIndex; i < endIndex; i++) {
        const product = filteredProducts[i];
        
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        
        // 가격 포맷팅
        const formattedPrice = product.price ? product.price.toLocaleString() + '원' : '-';
        
        // 평점 표시용 별점
        const stars = '★'.repeat(Math.round(product.rating || 0)) + '☆'.repeat(5 - Math.round(product.rating || 0));
        
        productCard.innerHTML = `
            <div class="product-info">
                <div class="product-brand">${product.brand || '-'}</div>
                <div class="product-name">${product.name || '제품명 없음'}</div>
                <div class="product-price">${formattedPrice}</div>
                <div class="product-rating">
                    <span>${stars}</span>
                    ${product.rating ? product.rating.toFixed(1) : '0.0'}
                </div>
                <div class="product-reviews">리뷰 ${product.review_count?.toLocaleString() || 0}개</div>
            </div>
        `;
        
        // 제품 클릭 시 링크 열기
        if (product.link) {
            productCard.style.cursor = 'pointer';
            productCard.addEventListener('click', function() {
                window.open(product.link, '_blank');
            });
        }
        
        productListContainer.appendChild(productCard);
    }
    
    // 페이지네이션 업데이트
    updatePagination(totalPages);
}

// 페이지네이션 업데이트 함수
function updatePagination(totalPages) {
    const paginationContainer = document.getElementById('pagination');
    paginationContainer.innerHTML = '';
    
    // 페이지가 1페이지면 페이지네이션 표시 안 함
    if (totalPages <= 1) {
        return;
    }
    
    // 처음 페이지 버튼
    if (currentPage > 1) {
        const firstPageBtn = document.createElement('button');
        firstPageBtn.textContent = '<<';
        firstPageBtn.addEventListener('click', () => {
            currentPage = 1;
            updateProductList();
        });
        paginationContainer.appendChild(firstPageBtn);
    }
    
    // 이전 페이지 버튼
    if (currentPage > 1) {
        const prevPageBtn = document.createElement('button');
        prevPageBtn.textContent = '<';
        prevPageBtn.addEventListener('click', () => {
            currentPage--;
            updateProductList();
        });
        paginationContainer.appendChild(prevPageBtn);
    }
    
    // 페이지 번호 버튼들
    const maxVisiblePages = 5; // 한 번에 보여줄 페이지 번호 수
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // 시작 페이지 조정
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        
        if (i === currentPage) {
            pageBtn.classList.add('active');
        }
        
        pageBtn.addEventListener('click', () => {
            currentPage = i;
            updateProductList();
        });
        
        paginationContainer.appendChild(pageBtn);
    }
    
    // 다음 페이지 버튼
    if (currentPage < totalPages) {
        const nextPageBtn = document.createElement('button');
        nextPageBtn.textContent = '>';
        nextPageBtn.addEventListener('click', () => {
            currentPage++;
            updateProductList();
        });
        paginationContainer.appendChild(nextPageBtn);
    }
    
    // 마지막 페이지 버튼
    if (currentPage < totalPages) {
        const lastPageBtn = document.createElement('button');
        lastPageBtn.textContent = '>>';
        lastPageBtn.addEventListener('click', () => {
            currentPage = totalPages;
            updateProductList();
        });
        paginationContainer.appendChild(lastPageBtn);
    }
}