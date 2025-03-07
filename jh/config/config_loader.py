import yaml
import os

class ConfigLoader:
    """설정 파일을 로드하는 클래스"""
    
    def __init__(self, config_path='config/config.yaml'):
        """
        설정 로더 초기화
        
        Args:
            config_path (str): 설정 파일 경로
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """설정 파일을 로드하고 반환합니다."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def get_config(self):
        """전체 설정을 반환합니다."""
        return self.config
    
    def get_browser_config(self):
        """브라우저 설정을 반환합니다."""
        return self.config.get('browser', {})
    
    def get_selectors(self, section=None):
        """
        선택자 설정을 반환합니다.
        
        Args:
            section (str, optional): 특정 섹션의 선택자. 기본값은 None으로 전체 선택자를 반환합니다.
        
        Returns:
            dict: 선택자 설정
        """
        selectors = self.config.get('selectors', {})
        if section and section in selectors:
            return selectors[section]
        return selectors
    
    def get_limits(self):
        """제한 설정을 반환합니다."""
        return self.config.get('limits', {})
    
    def get_keywords(self):
        """키워드 목록을 반환합니다."""
        return self.config.get('keywords', [])