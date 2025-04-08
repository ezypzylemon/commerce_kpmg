"""
차트 생성을 위한 유틸리티 함수 모듈 - 코드 중복 제거
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (서버 환경용)
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from flask import url_for
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 색상 팔레트 - 흰색 배경
COLORS = {
    'bg_dark': '#ffffff',       # 배경색을 흰색으로 변경
    'card_bg': '#ffffff',       # 카드 배경색
    'teal': '#36D6BE',          # 주요 청록색 
    'teal_gradient': '#8AEFDB', # 청록색 그라데이션 끝
    'purple': '#6B5AED',        # 보라색
    'red': '#FF5A5A',           # 빨간색
    'blue': '#4A78E1',          # 파란색
    'orange': '#FFA26B',        # 주황색
    'text_dark': '#1e2b3c',     # 어두운 텍스트 색상
    'text_secondary': '#6c7293',# 보조 텍스트 색상
    'light_bg': '#f8f9fc',      # 연한 배경색
    'border': '#e4e9f2',        # 테두리 색상
}

class ChartUtils:
    """차트 생성 유틸리티 클래스"""
    
    @staticmethod
    def get_font_path():
        """OS별 폰트 경로 자동 설정"""
        import platform
        
        system = platform.system()
        if system == "Windows":
            return "C:/Windows/Fonts/malgun.ttf"
        elif system == "Darwin":  # macOS
            mac_fonts = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleGothic.ttf",
                "/Library/Fonts/NanumGothic.ttf"
            ]
            for path in mac_fonts:
                if os.path.exists(path):
                    return path
            logger.warning("macOS에서 한글 폰트를 찾을 수 없습니다.")
        elif system == "Linux":
            linux_fonts = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]
            for path in linux_fonts:
                if os.path.exists(path):
                    return path
            logger.warning("Linux에서 기본 폰트를 찾을 수 없습니다.")
        
        # 기본 폰트 반환
        return None
    
    @staticmethod
    def ensure_static_dirs():
        """정적 디렉토리 확인 및 생성"""
        img_dir = os.path.join('static', 'images')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        return img_dir
    
    @staticmethod
    def create_gradient_color(c1, c2, n=100):
        """두 색상 사이의 그라데이션 색상 생성"""
        c1_rgb = mcolors.to_rgb(c1)
        c2_rgb = mcolors.to_rgb(c2)
        
        mix_pcts = [i/(n-1) for i in range(n)]
        rgb_colors = [tuple(x*(1-pct) + y*pct for x, y in zip(c1_rgb, c2_rgb)) for pct in mix_pcts]
        
        return rgb_colors
    
    @staticmethod
    def apply_modern_style(ax, title=None):
        """모던 스타일을 차트에 적용"""
        # 배경색 설정
        ax.set_facecolor(COLORS['card_bg'])
        
        # 그리드 스타일 설정
        ax.grid(True, linestyle='--', alpha=0.2, color=COLORS['text_secondary'], axis='y')
        ax.set_axisbelow(True)  # 그리드를 데이터 아래에 배치
        
        # 테두리 제거
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # 틱 설정
        ax.tick_params(axis='x', colors=COLORS['text_secondary'], length=0)
        ax.tick_params(axis='y', colors=COLORS['text_secondary'], length=0)
        
        # x축 레이블 간격 설정
        if len(ax.get_xticklabels()) > 10:
            for i, label in enumerate(ax.get_xticklabels()):
                if i % 2 != 0:
                    label.set_visible(False)
        
        # 타이틀 설정
        if title:
            ax.set_title(title, fontsize=15, fontweight='bold', color=COLORS['text_dark'], pad=15)
        
        # 레이블 설정
        if ax.get_xlabel():
            ax.set_xlabel(ax.get_xlabel(), fontsize=12, color=COLORS['text_secondary'], labelpad=10)
        if ax.get_ylabel():
            ax.set_ylabel(ax.get_ylabel(), fontsize=12, color=COLORS['text_secondary'], labelpad=10)
    
    @staticmethod
    def save_chart(fig, filename, facecolor=COLORS['card_bg'], bbox_inches='tight', dpi=100):
        """
        차트 저장 헬퍼 함수
        
        Args:
            fig: matplotlib 그림 객체
            filename (str): 저장할 파일 이름
            facecolor: 배경색
            bbox_inches: 경계 설정
            dpi: 해상도
            
        Returns:
            str: 저장된 차트 URL
        """
        try:
            # 디렉토리 확인
            img_dir = ChartUtils.ensure_static_dirs()
            file_path = os.path.join(img_dir, filename)
            
            # 그림 저장
            fig.savefig(file_path, facecolor=facecolor, bbox_inches=bbox_inches, dpi=dpi)
            plt.close(fig)
            
            # URL 반환
            return url_for('static', filename=f'images/{filename}')
        except Exception as e:
            logger.error(f"차트 저장 오류: {e}")
            return url_for('static', filename='images/error.png')
    
    @staticmethod
    def format_date_axis(ax, interval=7):
        """
        날짜 축 포맷 설정
        
        Args:
            ax: matplotlib 축 객체
            interval (int): 날짜 간격 (일)
        """
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    
    @staticmethod
    def add_value_labels(ax, horizontal=False, spacing=5, fmt='.1f'):
        """
        막대 그래프에 값 레이블 추가
        
        Args:
            ax: matplotlib 축 객체
            horizontal (bool): 수평 막대 여부
            spacing (int): 레이블 간격
            fmt (str): 포맷 문자열
        """
        for rect in ax.patches:
            # 값과 위치 가져오기
            if horizontal:
                value = rect.get_width()
                x = rect.get_width() + spacing
                y = rect.get_y() + rect.get_height() / 2
                ha, va = 'left', 'center'
            else:
                value = rect.get_height()
                x = rect.get_x() + rect.get_width() / 2
                y = rect.get_height() + spacing
                ha, va = 'center', 'bottom'
            
            # 값 텍스트 추가
            ax.annotate(
                f'{value:{fmt}}', 
                (x, y), 
                ha=ha, 
                va=va, 
                fontsize=9, 
                color=COLORS['text_secondary']
            )