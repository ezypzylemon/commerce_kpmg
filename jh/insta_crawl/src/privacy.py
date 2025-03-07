import re
import os
import json
import pickle
from datetime import datetime, timedelta
import urllib.parse
from cryptography.fernet import Fernet

class PrivacyHandler:
    """개인정보 보호 관련 기능을 제공하는 클래스"""
    
    def __init__(self, retention_days=30, logger=None):
        """
        개인정보 처리 핸들러 초기화
        
        Args:
            retention_days (int): 데이터 보존 기간(일)
            logger: 로깅을 위한 로거 객체
        """
        self.retention_days = retention_days
        self.collection_date = datetime.now()
        self.deletion_date = self.collection_date + timedelta(days=retention_days)
        self.logger = logger
        
        # 암호화 키 생성 또는 로드
        self.encryption_key = self._get_encryption_key()
    
    def log(self, message, level='info'):
        """로깅 헬퍼 함수"""
        if self.logger:
            if level == 'info':
                self.logger.info(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)
        else:
            print(message)
    
    def _get_encryption_key(self):
        """암호화 키를 가져오거나 생성합니다."""
        key_file = 'data/encryption_key.key'
        
        try:
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
                return key
            else:
                # 키 파일이 없으면 새로 생성
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                return key
        except Exception as e:
            self.log(f"암호화 키 처리 실패: {str(e)}", 'error')
            # 백업 키 생성
            return Fernet.generate_key()
    
    def anonymize_data(self, data):
        """개인 식별 정보를 익명화합니다."""
        if not data:
            return data
        
        anonymized = {}
        for key, value in data.items():
            if key == 'text':
                # 텍스트에서 @mentions 익명화
                anonymized[key] = [
                    re.sub(r'@\w+', '@user', text) if text else ""
                    for text in value
                ]
            elif key == 'image_url':
                # 이미지 URL에서 사용자 ID 부분 익명화
                anonymized[key] = []
                for url in value:
                    if url:
                        try:
                            parsed_url = urllib.parse.urlparse(url)
                            path_parts = parsed_url.path.split('/')
                            if len(path_parts) > 2:
                                # URL 경로에서 사용자 ID 부분을 'anonymized'로 대체
                                path_parts[1] = 'anonymized'
                                new_path = '/'.join(path_parts)
                                new_url = parsed_url._replace(path=new_path).geturl()
                                anonymized[key].append(new_url)
                            else:
                                anonymized[key].append(url)
                        except Exception:
                            anonymized[key].append(url)
                    else:
                        anonymized[key].append("")
            else:
                # 다른 필드는 그대로 복사
                anonymized[key] = value.copy() if isinstance(value, list) else value
        
        return anonymized
    
    def encrypt_data(self, data):
        """개인 데이터를 암호화합니다."""
        if not data:
            return data
        
        encrypted = {}
        fernet = Fernet(self.encryption_key)
        
        for key, value in data.items():
            if key in ['text', 'hashtags']:
                # 텍스트 및 해시태그 암호화
                encrypted[key] = []
                for item in value:
                    if isinstance(item, str) and item:
                        encrypted[key].append(fernet.encrypt(item.encode()).decode())
                    elif isinstance(item, list):
                        encrypted_tags = []
                        for tag in item:
                            if tag:
                                encrypted_tags.append(fernet.encrypt(tag.encode()).decode())
                            else:
                                encrypted_tags.append("")
                        encrypted[key].append(encrypted_tags)
                    else:
                        encrypted[key].append(item)
            else:
                # 다른 필드는 그대로 복사
                encrypted[key] = value.copy() if isinstance(value, list) else value
        
        return encrypted
    
    def decrypt_data(self, encrypted_data):
        """암호화된 데이터를 복호화합니다."""
        if not encrypted_data:
            return encrypted_data
        
        decrypted = {}
        fernet = Fernet(self.encryption_key)
        
        for key, value in encrypted_data.items():
            if key in ['text', 'hashtags']:
                # 텍스트 및 해시태그 복호화
                decrypted[key] = []
                for item in value:
                    if isinstance(item, str) and item:
                        try:
                            decrypted[key].append(fernet.decrypt(item.encode()).decode())
                        except Exception:
                            decrypted[key].append(item)  # 복호화 실패 시 원본 유지
                    elif isinstance(item, list):
                        decrypted_tags = []
                        for tag in item:
                            if tag:
                                try:
                                    decrypted_tags.append(fernet.decrypt(tag.encode()).decode())
                                except Exception:
                                    decrypted_tags.append(tag)  # 복호화 실패 시 원본 유지
                            else:
                                decrypted_tags.append("")
                        decrypted[key].append(decrypted_tags)
                    else:
                        decrypted[key].append(item)
            else:
                # 다른 필드는 그대로 복사
                decrypted[key] = value.copy() if isinstance(value, list) else value
        
        return decrypted
    
    def schedule_deletion(self, file_path):
        """데이터 자동 삭제를 스케줄링합니다."""
        deletion_info = {
            'file_path': file_path,
            'deletion_date': self.deletion_date.isoformat()
        }
        
        # 삭제 정보 저장
        deletion_file = 'data/scheduled_deletion.json'
        os.makedirs(os.path.dirname(deletion_file), exist_ok=True)
        
        existing_deletions = []
        if os.path.exists(deletion_file):
            try:
                with open(deletion_file, 'r', encoding='utf-8') as f:
                    existing_deletions = json.load(f)
            except Exception:
                existing_deletions = []
        
        existing_deletions.append(deletion_info)
        
        with open(deletion_file, 'w', encoding='utf-8') as f:
            json.dump(existing_deletions, f, indent=2)
        
        self.log(f"파일 '{file_path}'의 삭제가 {self.deletion_date.strftime('%Y-%m-%d')}로 예약됨")
    
    def generate_data_receipt(self, data, output_file='data/data_collection_receipt.txt'):
        """데이터 수집 영수증을 생성합니다."""
        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("인스타그램 데이터 수집 영수증\n")
            f.write("==============================\n\n")
            f.write(f"수집 일시: {self.collection_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"자동 삭제 예정일: {self.deletion_date.strftime('%Y-%m-%d')}\n\n")
            
            if 'keyword' in data and data['keyword']:
                f.write(f"수집된 키워드: {', '.join(set(data['keyword']))}\n")
            
            if 'text' in data:
                f.write(f"총 게시물 수: {len(data['text'])}\n\n")
            
            f.write("사용 목적: 연구 및 분석\n\n")
            f.write("개인정보 처리:\n")
            f.write("- 모든 개인 식별 정보는 익명화되었습니다.\n")
            f.write("- 원본 데이터는 암호화되어 저장되었습니다.\n")
            f.write("- 데이터는 연구 목적으로만 사용되며, 제3자에게 공유되지 않습니다.\n")
            f.write(f"- 모든 데이터는 {self.deletion_date.strftime('%Y-%m-%d')}에 자동 삭제됩니다.\n\n")
            
            f.write("권리 행사:\n")
            f.write("귀하의 데이터가 포함되었다고 생각되는 경우,\n")
            f.write("privacy@example.com로 문의하여 확인 및 삭제를 요청할 수 있습니다.\n")
        
        self.log(f"데이터 수집 영수증이 '{output_file}'에 생성되었습니다.")
        return output_file