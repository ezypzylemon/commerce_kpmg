"""
캐싱 관련 유틸리티 함수 모듈
"""
import logging
from functools import wraps
from config import CACHE_TIMEOUT

# 로깅 설정
logger = logging.getLogger(__name__)

class CacheHelper:
    """캐싱 관련 기능을 제공하는 클래스"""
    
    @staticmethod
    def get_cache_key(prefix, **kwargs):
        """
        캐시 키 생성 함수
        
        Args:
            prefix (str): 캐시 키 접두사
            **kwargs: 캐시 키에 포함될 파라미터
            
        Returns:
            str: 생성된 캐시 키
        """
        # 키 생성에 사용할 값들을 정렬하여 일관된 순서 보장
        sorted_items = sorted(kwargs.items())
        key_parts = [prefix] + [f"{k}:{v}" for k, v in sorted_items if v is not None]
        return "_".join(key_parts)
    
    @staticmethod
    def cache_result(cache, prefix, timeout=CACHE_TIMEOUT):
        """
        함수 결과를 캐싱하는 데코레이터
        
        Args:
            cache: 캐시 객체
            prefix (str): 캐시 키 접두사
            timeout (int): 캐시 유효 시간(초)
            
        Returns:
            function: 데코레이터 함수
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 캐시 키 생성
                cache_key = CacheHelper.get_cache_key(prefix, **kwargs)
                
                # 캐시에서 데이터 조회
                result = cache.get(cache_key)
                if result is not None:
                    logger.debug(f"캐시에서 데이터 로드: {cache_key}")
                    return result
                
                # 캐시에 없으면 함수 실행 후 결과 캐싱
                result = f(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
                logger.debug(f"캐시에 데이터 저장: {cache_key}")
                return result
            return decorated_function
        return decorator
    
    @staticmethod
    def invalidate_cache(cache, prefix, **kwargs):
        """
        특정 패턴의 캐시를 무효화하는 함수
        
        Args:
            cache: 캐시 객체
            prefix (str): 무효화할 캐시 키 접두사
            **kwargs: 무효화할 캐시 키에 포함된 파라미터
            
        Returns:
            bool: 무효화 성공 여부
        """
        try:
            if kwargs:
                # 특정 키 무효화
                cache_key = CacheHelper.get_cache_key(prefix, **kwargs)
                cache.delete(cache_key)
                logger.info(f"캐시 무효화: {cache_key}")
            else:
                # 접두사로 시작하는 모든 키 무효화 (캐시 구현에 따라 다름)
                if hasattr(cache, 'delete_many'):
                    # 여러 키를 한 번에 삭제할 수 있는 경우
                    pattern = f"{prefix}*"
                    cache.delete_many(pattern)
                    logger.info(f"패턴 기반 캐시 무효화: {pattern}")
                else:
                    # 개별적으로 삭제해야 하는 경우 (Simple 캐시는 전체 삭제만 가능)
                    cache.clear()
                    logger.info(f"전체 캐시 무효화")
            return True
        except Exception as e:
            logger.error(f"캐시 무효화 오류: {e}")
            return False