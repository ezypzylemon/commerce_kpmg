import pandas as pd
import re
import os
from datetime import datetime

class DataProcessor:
    """수집된 데이터를 처리하는 클래스"""
    
    def __init__(self, logger=None):
        """
        데이터 처리기 초기화
        
        Args:
            logger: 로깅을 위한 로거 객체
        """
        self.logger = logger
    
    def log(self, message, level='info'):
        """로깅 헬퍼 함수"""
        if self.logger:
            if level == 'info':
                self.logger.info(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)
    
    def process_date(self, date_str):
        """날짜 문자열을 표준 형식으로 변환합니다."""
        if not date_str:
            return ""
        
        try:
            # ISO 형식인 경우
            if 'T' in date_str and ('Z' in date_str or '+' in date_str):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 다른 형식 처리
            date_formats = [
                '%Y-%m-%d',
                '%Y년 %m월 %d일',
                '%Y. %m. %d.',
                '%B %d, %Y'
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # 처리할 수 없는 형식이면 원본 반환
            return date_str
            
        except Exception as e:
            self.log(f"날짜 변환 실패: {str(e)}", 'error')
            return date_str
    
    def clean_text(self, text):
        """텍스트 데이터를 정리합니다."""
        if not text:
            return ""
        
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 특수 문자 처리 (옵션)
        # text = re.sub(r'[^\w\s\.\,\!\?\#\@]', '', text)
        
        return text
    
    def process_hashtags(self, hashtags):
        """해시태그 목록을 처리합니다."""
        if not hashtags:
            return []
        
        # 중복 제거
        unique_hashtags = list(set(hashtags))
        
        # 해시태그에서 # 기호 제거 (옵션)
        # unique_hashtags = [tag.replace('#', '') for tag in unique_hashtags]
        
        return unique_hashtags
    
    def process_data(self, all_data):
        """모든 수집 데이터를 처리합니다."""
        processed_data = {
            'keyword': all_data.get('keyword', []),
            'text': [],
            'hashtags': [],
            'likes': [],
            'comments': [],
            'date': [],
            'image_url': [],
            'video_views': []
        }
        
        # 각 필드 처리
        for i in range(len(all_data.get('text', []))):
            # 텍스트 정리
            processed_data['text'].append(
                self.clean_text(all_data['text'][i]) if i < len(all_data['text']) else ""
            )
            
            # 해시태그 처리
            processed_data['hashtags'].append(
                self.process_hashtags(all_data['hashtags'][i]) if i < len(all_data['hashtags']) else []
            )
            
            # 날짜 처리
            processed_data['date'].append(
                self.process_date(all_data['date'][i]) if i < len(all_data['date']) else ""
            )
            
            # 나머지 필드는 그대로 복사
            for field in ['likes', 'comments', 'image_url', 'video_views']:
                processed_data[field].append(
                    all_data[field][i] if i < len(all_data[field]) else ""
                )
        
        return processed_data
    
    def save_to_csv(self, data, file_path='data/instagram_data.csv'):
        """데이터를 CSV 파일로 저장합니다."""
        try:
            # 데이터프레임 생성
            df = pd.DataFrame(data)
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # CSV로 저장
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            self.log(f"{len(df)}개 게시물 데이터를 '{file_path}'에 저장했습니다.")
            
            return True
        except Exception as e:
            self.log(f"CSV 저장 실패: {str(e)}", 'error')
            return False
    
    def get_data_summary(self, data):
        """데이터에 대한 요약 통계를 생성합니다."""
        if not data or 'text' not in data or len(data['text']) == 0:
            return "수집된 데이터가 없습니다."
        
        # 기본 통계
        post_count = len(data['text'])
        keyword_count = len(set(data['keyword'])) if 'keyword' in data else 0
        
        # 해시태그 통계
        all_hashtags = []
        for tags in data['hashtags']:
            if tags:
                all_hashtags.extend(tags)
        
        unique_hashtags = len(set(all_hashtags))
        
        # 인기 해시태그 (상위 5개)
        popular_hashtags = {}
        for tag in all_hashtags:
            popular_hashtags[tag] = popular_hashtags.get(tag, 0) + 1
        
        top_hashtags = sorted(popular_hashtags.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 요약 문자열 생성
        summary = f"데이터 요약:\n"
        summary += f"- 총 게시물 수: {post_count}\n"
        summary += f"- 수집 키워드 수: {keyword_count}\n"
        summary += f"- 고유 해시태그 수: {unique_hashtags}\n"
        summary += f"- 인기 해시태그 (상위 5개):\n"
        
        for tag, count in top_hashtags:
            summary += f"  - {tag}: {count}개 게시물\n"
        
        return summary