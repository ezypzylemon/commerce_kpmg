import os
import shutil
import tempfile
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any, BinaryIO, Union

def create_temp_directory() -> str:
    """임시 디렉토리 생성
    
    Returns:
        생성된 임시 디렉토리 경로
    """
    return tempfile.mkdtemp()

def save_uploaded_file(file_obj: BinaryIO, directory: str = None) -> str:
    """업로드된 파일을 디스크에 저장
    
    Args:
        file_obj: 파일 객체
        directory: 저장할 디렉토리 (None인 경우 임시 디렉토리 생성)
        
    Returns:
        저장된 파일 경로
    """
    if directory is None:
        directory = create_temp_directory()
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, file_obj.name)
    with open(file_path, "wb") as f:
        f.write(file_obj.getbuffer())
    
    return file_path

def save_dataframe_to_excel(df: pd.DataFrame, output_path: str = None, prefix: str = "export") -> str:
    """DataFrame을 Excel 파일로 저장
    
    Args:
        df: 저장할 DataFrame
        output_path: 출력 파일 경로 (None인 경우 임시 파일 생성)
        prefix: 파일명 접두사
        
    Returns:
        저장된 Excel 파일 경로
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.xlsx"
        output_path = os.path.join(tempfile.gettempdir(), filename)
    
    # 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Excel 파일 저장
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    return output_path

def save_dataframe_to_csv(df: pd.DataFrame, output_path: str = None, prefix: str = "export") -> str:
    """DataFrame을 CSV 파일로 저장
    
    Args:
        df: 저장할 DataFrame
        output_path: 출력 파일 경로 (None인 경우 임시 파일 생성)
        prefix: 파일명 접두사
        
    Returns:
        저장된 CSV 파일 경로
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.csv"
        output_path = os.path.join(tempfile.gettempdir(), filename)
    
    # 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # CSV 파일 저장 (한글 깨짐 방지 인코딩)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    return output_path

def get_file_extension(filename: str) -> str:
    """파일 확장자 추출
    
    Args:
        filename: 파일명
        
    Returns:
        확장자 (소문자로 변환됨)
    """
    return os.path.splitext(filename)[-1].lower()

def get_file_size(file_path: str) -> int:
    """파일 크기 조회 (바이트 단위)
    
    Args:
        file_path: 파일 경로
        
    Returns:
        파일 크기 (바이트)
    """
    return os.path.getsize(file_path)

def format_file_size(size_bytes: int) -> str:
    """파일 크기를 사람이 읽기 쉬운 형식으로 변환
    
    Args:
        size_bytes: 바이트 단위 파일 크기
        
    Returns:
        포맷팅된 파일 크기 문자열 (KB, MB, GB)
    """
    # 1024 바이트 = 1 킬로바이트
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def is_valid_pdf(file_path: str) -> bool:
    """파일이 유효한 PDF인지 확인
    
    Args:
        file_path: 파일 경로
        
    Returns:
        PDF 유효성 여부
    """
    # 간단한 확장자 체크
    if get_file_extension(file_path) != '.pdf':
        return False
    
    # PDF 시그니처 확인
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            return header == b'%PDF-'
    except:
        return False

def clean_temp_files(directory: str = None) -> None:
    """임시 파일/디렉토리 정리
    
    Args:
        directory: 정리할 디렉토리 (None인 경우 기본 임시 디렉토리)
    """
    if directory is None:
        directory = tempfile.gettempdir()
    
    # 임시 디렉토리가 없으면 무시
    if not os.path.exists(directory):
        return
    
    # 디렉토리 삭제
    try:
        shutil.rmtree(directory)
    except Exception as e:
        print(f"임시 파일 정리 실패: {e}")
