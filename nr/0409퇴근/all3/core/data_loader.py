import os
import random
from datetime import datetime, timedelta

# 샘플 데이터 생성을 위한 함수들
# 실제 환경에서는 데이터베이스나 API 연동으로 대체해야 함

def get_top_keywords(period, magazine):
    """
    특정 기간 및 매거진에 대한 상위 5개 키워드와 수치 반환
    
    Args:
        period (str): 기간 설정 (예: '1주', '1달')
        magazine (str): 매거진 선택 (예: 'W', 'Vogue', 'WWD')
        
    Returns:
        list: 상위 5개 키워드와 수치 리스트
    """
    # 이미지 2에서 확인된 데이터 기반 키워드와 수치
    # 모든 매거진에 동일한 데이터를 사용하지만 실제로는 매거진별로 다른 데이터가 있을 것임
    return [
        {'keyword': '브랜드', 'count': 1187},
        {'keyword': '패션', 'count': 634},
        {'keyword': '한국', 'count': 615},
        {'keyword': '섬유', 'count': 597},
        {'keyword': '제품', 'count': 545}
    ]

def get_card_news(period, magazine):
    """
    특정 기간 및 매거진에 대한 카드 뉴스 항목 반환
    
    Args:
        period (str): 기간 설정
        magazine (str): 매거진 선택
        
    Returns:
        list: 카드 뉴스 항목 리스트
    """
    # 매거진별 샘플 카드뉴스
    card_news = {
        'W': [
            {
                'title': '2025 S/S 컬렉션 핫 트렌드',
                'summary': '이번 시즌 런웨이를 뜨겁게 달군 패션 트렌드를 분석합니다.',
                'image_url': '/static/images/card1.jpg',
                'link': '#'
            },
            {
                'title': '스트리트 패션의 귀환',
                'summary': '길거리 패션이 다시 한번 주목받고 있는 이유를 알아봅니다.',
                'image_url': '/static/images/card1.jpg',
                'link': '#'
            }
        ],
        'Vogue': [
            {
                'title': '파스텔 컬러의 시대',
                'summary': '올해 가장 인기있는 파스텔 색상 코디 방법을 소개합니다.',
                'image_url': '/static/images/card1.jpg',
                'link': '#'
            },
            {
                'title': '빈티지 룩 완성하기',
                'summary': '구제 의류로 스타일리시한 빈티지 룩을 연출하는 방법',
                'image_url': '/static/images/card1.jpg',
                'link': '#'
            }
        ],
        'Dazed': [
            {
                'title': '테크웨어 브랜드 TOP 10',
                'summary': '기능성과 스타일을 모두 갖춘 테크웨어 브랜드를 소개합니다.',
                'image_url': '/static/images/card1.jpg',
                'link': '#'
            },
            {
                'title': '네온 컬러 활용법',
                'summary': '화려한 네온 컬러를 일상 스타일에 적용하는 방법',
                'image_url': '/static/images/card1.jpg',
                'link': '#'
            }
        ]
    }
    
    return card_news.get(magazine, [
        {
            'title': '샘플 패션 기사 제목',
            'summary': '샘플 패션 기사 요약',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': '샘플 패션 기사 제목 2',
            'summary': '샘플 패션 기사 요약 2',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        }
    ])

def get_trend_chart(period, keyword, chart_type):
    """
    특정 키워드의 추이 차트 URL 반환
    
    Args:
        period (str): 기간 설정
        keyword (str): 검색 키워드
        chart_type (str): 차트 유형 (type1 또는 type2)
        
    Returns:
        str: 차트 이미지 URL
    """
    # 실제로는 동적으로 차트를 생성하거나 미리 생성된 차트 이미지 반환
    return '/static/images/wordcloud.png'

def get_network_graph(period):
    """
    특정 기간의 키워드 네트워크 그래프 URL 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        str: 네트워크 그래프 이미지 URL
    """
    return '/static/images/wordcloud.png'

def get_category_chart(period):
    """
    특정 기간의 카테고리 분포 차트 URL 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        str: 파이 차트 이미지 URL
    """
    return '/static/images/wordcloud.png'

def get_category_keywords(period):
    """
    특정 기간의 카테고리별 키워드 및 비율 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        list: 카테고리 정보 리스트
    """
    # 이미지 1에서 확인된 카테고리 분포 데이터
    return [
        {'name': '의류', 'percent': 45},
        {'name': '신발', 'percent': 25},
        {'name': '액세서리', 'percent': 15},
        {'name': '가방', 'percent': 10},
        {'name': '기타', 'percent': 5}
    ]

def get_wordcloud(period):
    """
    특정 기간의 워드클라우드 이미지 URL 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        str: 워드클라우드 이미지 URL
    """
    return '/static/images/wordcloud.png'

def get_tfidf_chart(period):
    """
    특정 기간의 TF-IDF 차트 이미지 URL 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        str: TF-IDF 차트 이미지 URL
    """
    return '/static/images/wordcloud.png'

def get_news_items(period):
    """
    특정 기간의 뉴스 항목 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        list: 뉴스 항목 리스트
    """
    return [
        {
            'title': '패션 트렌드: 2025년 미니멀리즘의 부활',
            'summary': '단순함과 실용성이 강조된 미니멀 스타일이 런웨이를 장악하고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': '지속가능한 패션: 친환경 소재의 혁신',
            'summary': '재활용 소재와 친환경 공정으로 만든 의류가 주목받고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': '디지털 패션의 시대: NFT 의류 컬렉션',
            'summary': '가상 세계에서만 착용 가능한 디지털 의류의 인기가 급상승하고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        }
    ]

def get_musinsa_items(period):
    """
    특정 기간의 무신사 항목 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        list: 무신사 항목 리스트
    """
    return [
        {
            'title': '무신사 스탠다드 2025 S/S 컬렉션',
            'summary': '기본에 충실한 디자인에 트렌디한 요소를 가미한 새로운 시즌 컬렉션',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': '무신사 스토어 인기 브랜드 TOP 10',
            'summary': '지난 달 가장 많이 팔린 인기 브랜드를 소개합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': '무신사 스타일 2025 상반기 결산',
            'summary': '올해 상반기 무신사 유저들이 선택한 인기 스타일을 분석합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        }
    ]

def get_magazine_items(period):
    """
    특정 기간의 매거진 항목 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        list: 매거진 항목 리스트
    """
    return [
        {
            'title': 'W Korea: 2025 패션 키워드',
            'summary': '올해 주목해야 할 패션 키워드와 트렌드를 소개합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': 'Vogue Korea: 셀럽 스타일 분석',
            'summary': '국내외 셀럽들의 스트리트 패션을 분석합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        },
        {
            'title': 'Dazed Korea: 신진 디자이너 특집',
            'summary': '주목해야 할 신진 디자이너와 그들의 작품 세계를 소개합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#'
        }
    ]



# data_loader.py 파일에 추가할 get_news_items 함수

def get_news_items(period):
    """
    특정 기간의 뉴스 항목 반환
    
    Args:
        period (str): 기간 설정
        
    Returns:
        list: 뉴스 항목 리스트
    """
    # 현재 날짜 기준 가상 데이터 생성
    from datetime import datetime, timedelta
    today = datetime.now()
    
    return [
        {
            'title': '패션 트렌드: 2025년 미니멀리즘의 부활',
            'summary': '단순함과 실용성이 강조된 미니멀 스타일이 런웨이를 장악하고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#',
            'category': 'trend',
            'views': '3,540',
            'shares': '254',
            'date': (today - timedelta(days=2)).strftime('%Y-%m-%d')
        },
        {
            'title': '지속가능한 패션: 친환경 소재의 혁신',
            'summary': '재활용 소재와 친환경 공정으로 만든 의류가 주목받고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#',
            'category': 'sustainable',
            'views': '2,845',
            'shares': '198',
            'date': (today - timedelta(days=3)).strftime('%Y-%m-%d')
        },
        {
            'title': '디지털 패션의 시대: NFT 의류 컬렉션',
            'summary': '가상 세계에서만 착용 가능한 디지털 의류의 인기가 급상승하고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#',
            'category': 'trend',
            'views': '4,120',
            'shares': '321',
            'date': (today - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'title': '스트리트웨어 브랜드 성장세 지속',
            'summary': '젊은 소비자들 사이에서 스트리트웨어 브랜드의 인기가 계속해서 높아지고 있습니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#',
            'category': 'street',
            'views': '2,978',
            'shares': '183',
            'date': (today - timedelta(days=4)).strftime('%Y-%m-%d')
        },
        {
            'title': '2025 S/S 컬렉션 하이라이트',
            'summary': '이번 시즌 패션위크에서 주목받은 디자이너들의 컬렉션을 소개합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#',
            'category': 'collection',
            'views': '5,625',
            'shares': '487',
            'date': (today - timedelta(days=5)).strftime('%Y-%m-%d')
        },
        {
            'title': '럭셔리 브랜드들의 MZ세대 공략법',
            'summary': '전통적인 럭셔리 브랜드들이 젊은 소비자층을 끌어들이기 위한 전략을 분석합니다.',
            'image_url': '/static/images/card1.jpg',
            'link': '#',
            'category': 'brand',
            'views': '3,754',
            'shares': '265',
            'date': (today - timedelta(days=2)).strftime('%Y-%m-%d')
        }
    ]