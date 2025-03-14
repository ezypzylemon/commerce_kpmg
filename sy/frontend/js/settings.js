document.addEventListener('DOMContentLoaded', function () {
    // 테마 변경 버튼
    const themeButtons = document.querySelectorAll('.theme-btn');
    themeButtons.forEach(button => {
        button.addEventListener('click', function () {
            themeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            const theme = this.getAttribute('data-theme');
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme); // 로컬 스토리지에 테마 저장
        });
    });

    // 저장된 테마 불러오기
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        themeButtons.forEach(button => {
            if (button.getAttribute('data-theme') === savedTheme) {
                button.classList.add('active');
            }
        });
    }

    // 알림 설정 토글
    const notificationToggle = document.getElementById('notifications');
    notificationToggle.addEventListener('change', function () {
        if (this.checked) {
            console.log('알림 활성화');
        } else {
            console.log('알림 비활성화');
        }
    });

    // 폰트 크기 변경
    const fontSizeInput = document.getElementById('font-size');
    fontSizeInput.addEventListener('change', function () {
        const fontSize = this.value;
        document.documentElement.style.fontSize = fontSize + 'px';
        localStorage.setItem('fontSize', fontSize); // 로컬 스토리지에 폰트 크기 저장
    });

    // 저장된 폰트 크기 불러오기
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        document.documentElement.style.fontSize = savedFontSize + 'px';
        fontSizeInput.value = savedFontSize;
    }

    // 설정 저장 버튼
    const saveButtons = document.querySelectorAll('.setting-action .btn-primary');
    saveButtons.forEach(button => {
        button.addEventListener('click', function () {
            alert('설정이 저장되었습니다.');
        });
    });
});