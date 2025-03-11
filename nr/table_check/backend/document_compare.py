import pandas as pd
import os
import uuid
import logging
from datetime import datetime
import difflib
import re

# 로그 디렉토리 생성
if not os.path.exists('logs'):
    os.makedirs('logs')

# 로깅 설정
logger = logging.getLogger('document_compare')
handler = logging.FileHandler('logs/document_compare.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def normalize_product_code(code):
    """
    제품 코드 정규화 (대소문자 구분 없애기, 공백 제거)
    """
    if not code:
        return ""
    return str(code).upper().replace(' ', '').strip()

def normalize_size(size):
    """
    사이즈 정규화 (문자열로 변환, 앞 뒤 공백 제거)
    """
    if not size:
        return ""
    return str(size).strip()

def similarity_score(str1, str2):
    """
    두 문자열 간의 유사도 점수 계산 (0-100)
    """
    if not str1 and not str2:
        return 100  # 둘 다 비어있으면 완전 일치
    if not str1 or not str2:
        return 0  # 둘 중 하나만 비어있으면 완전 불일치
    
    # difflib의 SequenceMatcher 사용
    similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
    return round(similarity * 100, 2)

def compare_documents(doc1_id, doc2_id, documents):
    """
    두 문서를 비교하여 일치 여부를 분석하는 함수
    
    Args:
        doc1_id: 첫 번째 문서 ID
        doc2_id: 두 번째 문서 ID
        documents: 문서 저장소
        
    Returns:
        dict: 비교 결과 (일치율, 차이점 목록)
    """
    doc1 = documents[doc1_id]
    doc2 = documents[doc2_id]
    
    logger.info(f"문서 비교 시작: {doc1['original_filename']} vs {doc2['original_filename']}")
    
    # 문서 데이터 로드
    try:
        df1 = pd.read_excel(doc1['output_excel'])
        df2 = pd.read_excel(doc2['output_excel'])
    except Exception as e:
        logger.error(f"엑셀 파일 로드 오류: {str(e)}")
        raise Exception(f"엑셀 파일 로드 오류: {str(e)}")
    
    # 결과 저장용 딕셔너리
    comparison_results = {
        'match_rate': 0,
        'differences': [],
        'matching_products': [],
        'doc1_only': [],
        'doc2_only': [],
        'stats': {
            'total_products': 0,
            'common_products': 0,
            'doc1_only_count': 0,
            'doc2_only_count': 0,
            'differences_count': 0
        }
    }
    
    # 비교를 위한 정규화된 코드 칼럼 추가
    df1['normalized_code'] = df1['Product_Code'].apply(normalize_product_code)
    df2['normalized_code'] = df2['Product_Code'].apply(normalize_product_code)
    
    # 사이즈 정규화
    df1['normalized_size'] = df1['Size'].apply(normalize_size)
    df2['normalized_size'] = df2['Size'].apply(normalize_size)
    
    # 두 문서의 공통 Product_Code 찾기
    doc1_product_codes = set(df1['normalized_code'].unique())
    doc2_product_codes = set(df2['normalized_code'].unique())
    common_codes = doc1_product_codes & doc2_product_codes
    all_codes = doc1_product_codes | doc2_product_codes
    
    # 기본 통계 업데이트
    comparison_results['stats']['total_products'] = len(all_codes)
    comparison_results['stats']['common_products'] = len(common_codes)
    comparison_results['stats']['doc1_only_count'] = len(doc1_product_codes - doc2_product_codes)
    comparison_results['stats']['doc2_only_count'] = len(doc2_product_codes - doc1_product_codes)
    
    # 기본 일치율 계산
    if len(all_codes) > 0:
        comparison_results['match_rate'] = round(len(common_codes) / len(all_codes) * 100, 2)
    
    # 문서1에만 있는 제품
    doc1_only_codes = doc1_product_codes - doc2_product_codes
    for code in doc1_only_codes:
        product_rows = df1[df1['normalized_code'] == code]
        for _, row in product_rows.iterrows():
            comparison_results['doc1_only'].append({
                'product_code': row.get('Product_Code', 'N/A'),
                'size': row.get('Size', 'N/A'),
                'color': row.get('Color', 'N/A'),
                'quantity': row.get('Quantity', 'N/A')
            })
    
    # 문서2에만 있는 제품
    doc2_only_codes = doc2_product_codes - doc1_product_codes
    for code in doc2_only_codes:
        product_rows = df2[df2['normalized_code'] == code]
        for _, row in product_rows.iterrows():
            comparison_results['doc2_only'].append({
                'product_code': row.get('Product_Code', 'N/A'),
                'size': row.get('Size', 'N/A'),
                'color': row.get('Color', 'N/A'),
                'quantity': row.get('Quantity', 'N/A')
            })
    
    # 공통 제품 비교
    for code in common_codes:
        df1_products = df1[df1['normalized_code'] == code]
        df2_products = df2[df2['normalized_code'] == code]
        
        # 각 공통 제품의 사이즈별 비교
        df1_sizes = set(df1_products['normalized_size'])
        df2_sizes = set(df2_products['normalized_size'])
        
        # 공통 사이즈
        common_sizes = df1_sizes & df2_sizes
        
        for size in common_sizes:
            df1_item = df1_products[df1_products['normalized_size'] == size].iloc[0]
            df2_item = df2_products[df2_products['normalized_size'] == size].iloc[0]
            
            # 비교할 중요 필드 목록
            important_fields = [
                ('Quantity', '수량'),
                ('Wholesale_EUR', '도매가'),
                ('선적시작일', '선적시작일'),
                ('선적완료일', '선적완료일'),
                ('예상도착일', '예상도착일')
            ]
            
            # 필드별 비교
            has_difference = False
            for field, field_name in important_fields:
                if field in df1_item and field in df2_item:
                    df1_value = str(df1_item.get(field, 'N/A')).strip()
                    df2_value = str(df2_item.get(field, 'N/A')).strip()
                    
                    # 값이 없는 경우 건너뛰기
                    if df1_value == 'N/A' and df2_value == 'N/A':
                        continue
                    
                    # 값 비교 (비교할 때는 유사도 점수 사용)
                    similarity = similarity_score(df1_value, df2_value)
                    
                    if similarity < 90:  # 90% 이하 유사도는 차이로 간주
                        has_difference = True
                        comparison_results['differences'].append({
                            'product_code': df1_item.get('Product_Code', 'N/A'),
                            'size': df1_item.get('Size', 'N/A'),
                            'field': field_name,
                            'doc1_value': df1_value,
                            'doc2_value': df2_value,
                            'similarity': similarity
                        })
            
            # 차이가 없으면 일치 항목으로 추가
            if not has_difference:
                comparison_results['matching_products'].append({
                    'product_code': df1_item.get('Product_Code', 'N/A'),
                    'size': df1_item.get('Size', 'N/A'),
                    'color': df1_item.get('Color', 'N/A'),
                    'quantity': df1_item.get('Quantity', 'N/A')
                })
        
        # 문서1에만 있는 사이즈
        for size in df1_sizes - df2_sizes:
            df1_item = df1_products[df1_products['normalized_size'] == size].iloc[0]
            comparison_results['doc1_only'].append({
                'product_code': df1_item.get('Product_Code', 'N/A'),
                'size': df1_item.get('Size', 'N/A'),
                'color': df1_item.get('Color', 'N/A'),
                'quantity': df1_item.get('Quantity', 'N/A')
            })
        
        # 문서2에만 있는 사이즈
        for size in df2_sizes - df1_sizes:
            df2_item = df2_products[df2_products['normalized_size'] == size].iloc[0]
            comparison_results['doc2_only'].append({
                'product_code': df2_item.get('Product_Code', 'N/A'),
                'size': df2_item.get('Size', 'N/A'),
                'color': df2_item.get('Color', 'N/A'),
                'quantity': df2_item.get('Quantity', 'N/A')
            })
    
    # 차이점 개수 업데이트
    comparison_results['stats']['differences_count'] = len(comparison_results['differences'])
    
    # 디테일 점수 계산 (공통 제품 내에서의 일치율)
    total_common_fields = len(comparison_results['matching_products']) * 5  # 5개 필드
    total_diff_fields = len(comparison_results['differences'])
    
    detail_score = 100
    if total_common_fields + total_diff_fields > 0:
        detail_score = round(total_common_fields / (total_common_fields + total_diff_fields) * 100, 2)
    
    # 최종 일치율은 제품 존재 일치율과 세부 필드 일치율의 가중 평균
    product_existence_weight = 0.7
    detail_weight = 0.3
    
    final_score = (comparison_results['match_rate'] * product_existence_weight) + (detail_score * detail_weight)
    comparison_results['match_rate'] = round(final_score, 2)
    
    logger.info(f"문서 비교 완료: 일치율 {comparison_results['match_rate']}%, 차이점 {len(comparison_results['differences'])}개")
    
    return comparison_results

def compare_with_existing(new_doc_id, new_doc_data, documents, comparisons):
    """
    새 문서와 기존 문서들을 비교하여 가장 유사한 문서 찾기
    
    Args:
        new_doc_id: 새 문서 ID
        new_doc_data: 새 문서 데이터
        documents: 문서 저장소
        comparisons: 비교 결과 저장소
        
    Returns:
        dict: 비교 결과
    """
    logger.info(f"새 문서와 기존 문서 비교 시작: {new_doc_id}")
    
    if not documents or len(documents) <= 1:
        logger.info("비교할 문서가 없습니다.")
        return {"status": "no_comparison", "message": "비교할 문서가 없습니다."}
    
    # 새 문서의 제품 코드 추출
    new_product_codes = set()
    for item in new_doc_data:
        if 'Product_Code' in item:
            normalized_code = normalize_product_code(item['Product_Code'])
            if normalized_code:
                new_product_codes.add(normalized_code)
    
    if not new_product_codes:
        logger.warning("새 문서에서 제품 코드를 찾을 수 없습니다.")
        return {"status": "no_product_codes", "message": "새 문서에서 제품 코드를 찾을 수 없습니다."}
    
    best_match = {
        "doc_id": None,
        "match_rate": 0,
        "common_products": 0
    }
    
    # 새 문서를 제외한 문서들과 비교
    for doc_id, doc in documents.items():
        if doc_id == new_doc_id:
            continue
            
        if not os.path.exists(doc['output_excel']):
            logger.warning(f"문서 {doc_id}의 엑셀 파일이 존재하지 않습니다: {doc['output_excel']}")
            continue
            
        try:
            existing_df = pd.read_excel(doc['output_excel'])
            # 제품 코드 정규화
            existing_df['normalized_code'] = existing_df['Product_Code'].apply(normalize_product_code)
            existing_product_codes = set(existing_df['normalized_code'].unique())
            
            # 빈 코드 제거
            existing_product_codes = {code for code in existing_product_codes if code}
            
            # 공통 제품 찾기
            common_codes = new_product_codes & existing_product_codes
            all_codes = new_product_codes | existing_product_codes
            
            # 일치율 계산
            match_rate = 0
            if len(all_codes) > 0:
                match_rate = round(len(common_codes) / len(all_codes) * 100, 2)
                
            # 더 좋은 일치율이면 업데이트
            if match_rate > best_match["match_rate"]:
                best_match = {
                    "doc_id": doc_id,
                    "filename": doc['original_filename'],
                    "type": doc['type'],
                    "match_rate": match_rate,
                    "common_products": len(common_codes),
                    "total_products": len(all_codes)
                }
        except Exception as e:
            logger.error(f"비교 중 오류: {str(e)}")
            continue
    
    # 일치율이 있으면 비교 결과 저장
    if best_match["match_rate"] > 0:
        logger.info(f"가장 유사한 문서 발견: {best_match.get('filename', 'Unknown')}, 일치율: {best_match['match_rate']}%")
        
        comp_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 상세 비교 필요한 경우
        if best_match["match_rate"] >= 40:
            # 전체 비교 실행
            try:
                result = compare_documents(new_doc_id, best_match["doc_id"], documents)
                
                # 비교 결과 저장
                comparisons[comp_id] = {
                    'id': comp_id,
                    'doc1_id': new_doc_id,
                    'doc2_id': best_match["doc_id"],
                    'timestamp': timestamp,
                    'match_rate': result['match_rate'],
                    'differences': result['differences'],
                    'doc1_only': result['doc1_only'],
                    'doc2_only': result['doc2_only'],
                    'matching_products': result['matching_products'],
                    'stats': result['stats'],
                    'status': 'complete' if result['match_rate'] > 90 else 'review_needed'
                }
                
                return {
                    'status': 'comparison_found',
                    'comparison_id': comp_id,
                    'best_match': best_match,
                    'details': comparisons[comp_id]
                }
            except Exception as e:
                logger.error(f"상세 비교 중 오류: {str(e)}")
                return {
                    'status': 'comparison_error',
                    'best_match': best_match,
                    'error': str(e)
                }
        
        # 간단한 비교 결과만 반환
        return {
            'status': 'comparison_found',
            'best_match': best_match
        }
    
    logger.info("일치하는 문서가 없습니다.")
    return {"status": "no_match", "message": "일치하는 문서가 없습니다."}