from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Union, Optional
import calendar
import locale

# 한국어 로캘 설정 (Windows)
try:
    locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Korean_Korea.949')
    except:
        pass  # 로캘 설정 실패 무시

def get_today() -> datetime:
    """오늘 날짜 반환
    
    Returns:
        오늘 날짜의 datetime 객체
    """
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def get_date_range(days: int = 30) -> Tuple[datetime, datetime]:
    """오늘부터 지정된 일수 이전까지의 날짜 범위 반환
    
    Args:
        days: 이전 일수
        
    Returns:
        (시작일, 종료일) 튜플
    """
    end_date = get_today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def format_date(date: datetime, format_str: str = '%Y-%m-%d') -> str:
    """날짜를 문자열로 변환
    
    Args:
        date: 변환할 날짜
        format_str: 날짜 형식 문자열
        
    Returns:
        포맷팅된 날짜 문자열
    """
    return date.strftime(format_str)

def parse_date(date_str: str, format_str: str = '%Y-%m-%d') -> datetime:
    """문자열을 날짜로 변환
    
    Args:
        date_str: 변환할 날짜 문자열
        format_str: 날짜 형식 문자열
        
    Returns:
        datetime 객체
    """
    return datetime.strptime(date_str, format_str)

def format_relative_date(date: datetime) -> str:
    """날짜를 상대적인 표현으로 변환 (예: '오늘', '내일', '3일 전')
    
    Args:
        date: 변환할 날짜
        
    Returns:
        상대적 날짜 표현 문자열
    """
    today = get_today()
    delta = (date.date() - today.date()).days
    
    if delta == 0:
        return '오늘'
    elif delta == 1:
        return '내일'
    elif delta == -1:
        return '어제'
    elif delta > 0:
        return f'{delta}일 후'
    else:
        return f'{abs(delta)}일 전'

def get_month_calendar(year: int, month: int) -> List[List[int]]:
    """지정된 연월의 달력 데이터 반환
    
    Args:
        year: 연도
        month: 월
        
    Returns:
        주별로 그룹화된 날짜 리스트 (0은 해당 월에 속하지 않는 날짜)
    """
    return calendar.monthcalendar(year, month)

def get_week_dates(date: datetime = None) -> List[datetime]:
    """지정된 날짜가 속한 주의 모든 날짜 반환
    
    Args:
        date: 기준 날짜 (None인 경우 오늘)
        
    Returns:
        해당 주의 모든 날짜 리스트
    """
    if date is None:
        date = get_today()
    
    # 월요일을 기준으로 주 시작
    weekday = date.weekday()
    start_of_week = date - timedelta(days=weekday)
    
    return [start_of_week + timedelta(days=i) for i in range(7)]

def get_days_left_in_month() -> int:
    """이번 달에 남은 일수 계산
    
    Returns:
        이번 달에 남은 일수
    """
    today = get_today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return last_day - today.day + 1

def get_korean_weekday(date: datetime = None) -> str:
    """날짜의 한국어 요일명 반환
    
    Args:
        date: 날짜 (None인 경우 오늘)
        
    Returns:
        한국어 요일명
    """
    if date is None:
        date = get_today()
    
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    return weekdays[date.weekday()]

def add_days(date: datetime, days: int) -> datetime:
    """날짜에 일수 더하기
    
    Args:
        date: 기준 날짜
        days: 더할 일수
        
    Returns:
        계산된 날짜
    """
    return date + timedelta(days=days)

def add_months(date: datetime, months: int) -> datetime:
    """날짜에 월 더하기
    
    Args:
        date: 기준 날짜
        months: 더할 월 수
        
    Returns:
        계산된 날짜
    """
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return date.replace(year=year, month=month, day=day)

def dates_to_list(start_date: datetime, end_date: datetime) -> List[datetime]:
    """두 날짜 사이의 모든 날짜 목록 생성
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        
    Returns:
        두 날짜 사이의 모든 날짜 리스트
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date = current_date + timedelta(days=1)
    
    return dates

def is_business_day(date: datetime) -> bool:
    """영업일(평일) 여부 확인
    
    Args:
        date: 확인할 날짜
        
    Returns:
        영업일 여부
    """
    return date.weekday() < 5  # 월(0)~금(4)

def get_business_days(start_date: datetime, end_date: datetime) -> List[datetime]:
    """두 날짜 사이의 영업일(평일) 목록 반환
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        
    Returns:
        영업일(평일) 목록
    """
    return [date for date in dates_to_list(start_date, end_date) if is_business_day(date)]

def calculate_business_days(start_date: datetime, end_date: datetime) -> int:
    """두 날짜 사이의 영업일(평일) 수 계산
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        
    Returns:
        영업일(평일) 수
    """
    return len(get_business_days(start_date, end_date))

def add_business_days(date: datetime, days: int) -> datetime:
    """영업일(평일) 기준으로 날짜 더하기
    
    Args:
        date: 기준 날짜
        days: 더할 영업일 수
        
    Returns:
        계산된 날짜
    """
    if days == 0:
        return date
    
    dir_mod = 1 if days > 0 else -1
    days = abs(days)
    
    result = date
    while days > 0:
        result = result + timedelta(days=dir_mod)
        if is_business_day(result):
            days -= 1
    
    return result
